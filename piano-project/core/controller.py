# core/controller.py

import threading
import time

from core.state_machine import StateMachine, State, Event
from hardware.led_controller import LedController
from hardware.pir_sensor import PIRSensor
from hardware.midi_io import MidiInput
from recording.recorder import Recorder
from practice.session import PracticeSession
from mqtt.client import MqttClient
import config


class Controller:
    def __init__(self):
        self.sm = StateMachine(initial_state=State.SLEEP)
        self.led = LedController(config.LED_PIN_MAP)
        self.pir = PIRSensor(config.PIR_PIN, bounce_ms=config.PIR_BOUNCE_MS)
        self.midi = MidiInput(config.MIDI_PORT_NAME)
        self.recorder = Recorder(config.RECORDINGS_DIR)
        self.practice = PracticeSession(config.SONGS_DIR)
        self.mqtt = MqttClient(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT, client_id="controller")

        self._lock = threading.RLock()
        self._last_activity = time.time()
        self._feedback_timer = None
        self._pending_filename = None
        self._pending_song_id = None

        # wiring
        self.pir.on_motion(lambda: self.handle_event(Event.PIR_DETECTED))
        self.midi.on_note(self._on_midi_note)
        self.mqtt.subscribe(config.MQTT_TOPIC_CMD, self._on_cmd_message)

    def start(self):
        self.midi.start()
        self.mqtt.connect()
        self.mqtt.loop_start()
        self.led.set_state(self.sm.state)
        self._publish_status()

    def stop(self):
        if self._feedback_timer:
            self._feedback_timer.cancel()
            self._feedback_timer = None
        self.midi.stop()
        self.mqtt.loop_stop()
        self.led.cleanup()
        self.pir.cleanup()

    # ---- event handling ----
    def handle_event(self, event):
        with self._lock:
            old_state = self.sm.state
            new_state, changed = self.sm.handle(event)

            if event == Event.PIR_DETECTED:
                self._last_activity = time.time()

            if not changed:
                if event.value.startswith("cmd_") and old_state in (State.RECORDING, State.PRACTICE):
                    self._publish_status(extra={"error": "busy"})
                return

            self._on_state_changed(old_state, new_state, event)

    def _on_state_changed(self, old_state, new_state, event):
        self.led.set_state(new_state)

        if new_state == State.RECORDING:
            self.recorder.start()

        if old_state == State.RECORDING and new_state == State.IDLE:
            saved = self.recorder.stop(self._pending_filename)
            self._pending_filename = None
            self._publish_status(extra={"saved_recording": saved})

        if new_state == State.PRACTICE:
            if self._pending_song_id:
                try:
                    self.practice.load_song(self._pending_song_id)
                    self.practice.start()
                except Exception as exc:
                    self.sm.state = State.IDLE
                    self.led.set_state(State.IDLE)
                    self._pending_song_id = None
                    self._publish_status(extra={"error": str(exc)})
                    return
            self._pending_song_id = None

        if old_state == State.PRACTICE and new_state == State.IDLE:
            self.practice.stop()

        if new_state == State.IDLE:
            self._last_activity = time.time()

        self._publish_status()

    # ---- MQTT command handling ----
    def _on_cmd_message(self, payload):
        if not isinstance(payload, dict):
            return

        action = payload.get("action")

        if action == "wake":
            self.handle_event(Event.CMD_WAKE)

        elif action == "sleep":
            self.handle_event(Event.CMD_SLEEP)

        elif action == "start_record":
            self.handle_event(Event.CMD_START_RECORD)

        elif action == "stop_record":
            self._pending_filename = payload.get("filename")
            self.handle_event(Event.CMD_STOP_RECORD)

        elif action == "start_practice":
            self._pending_song_id = payload.get("song_id")
            self.handle_event(Event.CMD_START_PRACTICE)

        elif action == "stop_practice":
            self.handle_event(Event.CMD_STOP_PRACTICE)

    # ---- MIDI handling ----
    def _on_midi_note(self, msg, ts):
        self.recorder.handle_note(msg, ts)

        if self.sm.state != State.PRACTICE:
            return

        result = self.practice.handle_note(msg, ts)
        if result is None:
            return

        self.led.set_practice_feedback(result["correct"])
        self._schedule_feedback_reset()

        if result["complete"]:
            self.handle_event(Event.PRACTICE_COMPLETE)
        else:
            self._publish_status()

    def _schedule_feedback_reset(self):
        if self._feedback_timer:
            self._feedback_timer.cancel()
        self._feedback_timer = threading.Timer(
            config.PRACTICE_FEEDBACK_SEC, self._reset_feedback
        )
        self._feedback_timer.start()

    def _reset_feedback(self):
        with self._lock:
            if self.sm.state == State.PRACTICE:
                self.led.reset_practice_indicator()

    # ---- idle timeout check (수동 sleep 전환으로 변경되어 현재는 사용하지 않음) ----
    def check_timeout(self):
        return

    # ---- status publish ----
    def _publish_status(self, extra=None):
        status = {
            "state": self.sm.state.value,
            "recordings": self.recorder.list_recordings(),
        }
        if self.sm.state == State.PRACTICE:
            status["practice"] = self.practice.get_progress()
        if extra:
            status.update(extra)

        self.mqtt.publish(config.MQTT_TOPIC_STATUS, status)
