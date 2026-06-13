# core/state_machine.py

from enum import Enum


class State(Enum):
    SLEEP = "sleep"
    IDLE = "idle"
    RECORDING = "recording"
    PRACTICE = "practice"


class Event(Enum):
    PIR_DETECTED = "pir_detected"
    CMD_WAKE = "cmd_wake"
    CMD_SLEEP = "cmd_sleep"
    CMD_START_RECORD = "cmd_start_record"
    CMD_STOP_RECORD = "cmd_stop_record"
    CMD_START_PRACTICE = "cmd_start_practice"
    CMD_STOP_PRACTICE = "cmd_stop_practice"
    PRACTICE_COMPLETE = "practice_complete"


# (현재 상태, 이벤트) -> 다음 상태
# 매핑에 없는 조합은 "무시"로 처리됨 (SLEEP 중 cmd_*, RECORDING/PRACTICE 중 다른 cmd 등)
TRANSITIONS = {
    (State.SLEEP, Event.PIR_DETECTED): State.IDLE,
    (State.SLEEP, Event.CMD_WAKE): State.IDLE,

    (State.IDLE, Event.PIR_DETECTED): State.IDLE,
    (State.IDLE, Event.CMD_SLEEP): State.SLEEP,
    (State.IDLE, Event.CMD_START_RECORD): State.RECORDING,
    (State.IDLE, Event.CMD_START_PRACTICE): State.PRACTICE,

    (State.RECORDING, Event.CMD_STOP_RECORD): State.IDLE,
    (State.RECORDING, Event.PIR_DETECTED): State.RECORDING,

    (State.PRACTICE, Event.CMD_STOP_PRACTICE): State.IDLE,
    (State.PRACTICE, Event.PRACTICE_COMPLETE): State.IDLE,
    (State.PRACTICE, Event.PIR_DETECTED): State.PRACTICE,
}


class StateMachine:
    def __init__(self, initial_state=State.SLEEP):
        self.state = initial_state

    def handle(self, event):
        """
        이벤트 처리.
        반환: (현재 상태, transitioned: bool)
          - transitioned=True  -> 상태가 실제로 바뀜
          - transitioned=False -> 무시된 이벤트 (정의되지 않은 전이)
        """
        next_state = TRANSITIONS.get((self.state, event))

        if next_state is None:
            return self.state, False

        changed = next_state != self.state
        self.state = next_state
        return self.state, changed
