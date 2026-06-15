# hardware/midi_io.py

import logging
import mido
import threading
import time

logger = logging.getLogger(__name__)

MIDI_THROUGH = "midi through"


def _is_midi_through(name):
    return MIDI_THROUGH in name.lower()


def _selectable_names(names):
    """Exclude virtual Midi Through ports unless they are the only option."""
    if len(names) <= 1:
        return list(names)
    filtered = [name for name in names if not _is_midi_through(name)]
    return filtered or list(names)


class MidiInput:
    def __init__(self, port_name=None):
        """
        port_name: None이면 첫 번째로 발견된 입력 포트를 자동 사용
        """
        self._callbacks = []
        self._port = None
        self._thread = None
        self._running = False
        self._lock = threading.RLock()
        names = self.list_ports()
        self.port_name = port_name if port_name in names else self._find_port(names)

    @staticmethod
    def list_ports():
        try:
            return mido.get_input_names()
        except Exception:
            logger.exception("Failed to list MIDI input ports")
            return []

    def _find_port(self, names=None):
        names = names if names is not None else self.list_ports()
        if not names:
            return None

        candidates = _selectable_names(names)
        for keyword in ("MIDI", "PIANO", "CASIO", "USB"):
            for name in candidates:
                if keyword in name.upper():
                    return name

        return candidates[0]

    def on_note(self, callback):
        """
        callback(msg, timestamp) 형태로 호출됨
        msg: mido.Message (note_on / note_off)
        timestamp: time.time() 기준 float
        """
        self._callbacks.append(callback)

    def start(self):
        with self._lock:
            if self._running:
                return
            if not self.port_name:
                self.port_name = self._find_port()
            if not self.port_name:
                logger.warning("No MIDI input port available; listener not started")
                return
            try:
                self._port = mido.open_input(self.port_name)
            except Exception:
                logger.exception("Failed to open MIDI input port: %s", self.port_name)
                self._port = None
                self._thread = None
                self._running = False
                return
            self._running = True
            self._thread = threading.Thread(target=self._listen, daemon=True)
            self._thread.start()

    def _listen(self):
        try:
            with self._lock:
                port = self._port
            if port is None:
                return
            for msg in port:
                with self._lock:
                    if not self._running or port is not self._port:
                        break
                if msg.type in ("note_on", "note_off"):
                    if msg.type == "note_on" and msg.velocity == 0:
                        continue
                    ts = time.time()
                    for cb in list(self._callbacks):
                        try:
                            cb(msg, ts)
                        except Exception:
                            logger.exception("MIDI callback failed")
        except Exception:
            with self._lock:
                running = self._running
            if running:
                logger.exception("MIDI input listener stopped unexpectedly")

    def stop(self):
        thread = None
        with self._lock:
            self._running = False
            if self._port:
                self._port.close()
                self._port = None
            thread = self._thread

        if thread:
            thread.join(timeout=1)
            with self._lock:
                if thread.is_alive():
                    logger.warning("MIDI input listener did not stop within timeout")
                elif self._thread is thread:
                    self._thread = None

    def set_port(self, port_name):
        """Switch to a new input port with rollback if opening the new port fails."""
        if not port_name:
            raise ValueError("port_name is required")

        with self._lock:
            if port_name == self.port_name and self._running:
                return

            previous_name = self.port_name
            previous_thread = self._thread
            was_running = self._running

            self._running = False
            if self._port:
                self._port.close()
                self._port = None
            self._thread = None

        if previous_thread:
            previous_thread.join(timeout=1)
            if previous_thread.is_alive():
                logger.warning("MIDI input listener did not stop within timeout")

        try:
            new_port = mido.open_input(port_name)
        except Exception as switch_exc:
            restore_exc = self._restore_previous_port(previous_name, was_running)
            if restore_exc:
                raise RuntimeError(
                    f"failed to switch to {port_name}; also failed to restore {previous_name}: {restore_exc}"
                ) from switch_exc
            raise

        with self._lock:
            self.port_name = port_name
            self._port = new_port
            if was_running:
                self._running = True
                self._thread = threading.Thread(target=self._listen, daemon=True)
                self._thread.start()
            else:
                self._running = False
                self._thread = None

    def _restore_previous_port(self, previous_name, was_running):
        with self._lock:
            self.port_name = previous_name
            self._port = None
            self._thread = None
            self._running = False

        if not was_running or not previous_name:
            return None

        try:
            restored_port = mido.open_input(previous_name)
        except Exception as exc:
            logger.exception("Failed to restore previous MIDI input port: %s", previous_name)
            return exc

        with self._lock:
            self._port = restored_port
            self._running = True
            self._thread = threading.Thread(target=self._listen, daemon=True)
            self._thread.start()
        return None
