# hardware/midi_io.py

import mido
import threading
import time

class MidiInput:
    def __init__(self, port_name=None):
        """
        port_name: None이면 첫 번째로 발견된 입력 포트를 자동 사용
        """
        self.port_name = port_name or self._find_port()
        self._callbacks = []
        self._port = None
        self._thread = None
        self._running = False

    def _find_port(self):
        names = mido.get_input_names()
        if not names:
            raise RuntimeError("연결된 USB-MIDI 입력 장치가 없습니다.")

        for keyword in ("MIDI", "PIANO", "CASIO", "USB"):
            for name in names:
                if keyword in name.upper():
                    return name

        return names[0]

    def on_note(self, callback):
        """
        callback(msg, timestamp) 형태로 호출됨
        msg: mido.Message (note_on / note_off)
        timestamp: time.time() 기준 float
        """
        self._callbacks.append(callback)

    def start(self):
        self._port = mido.open_input(self.port_name)
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self):
        for msg in self._port:
            if not self._running:
                break
            if msg.type in ("note_on", "note_off"):
                if msg.type == "note_on" and msg.velocity == 0:
                    continue
                ts = time.time()
                for cb in self._callbacks:
                    cb(msg, ts)

    def stop(self):
        self._running = False
        if self._port:
            self._port.close()
