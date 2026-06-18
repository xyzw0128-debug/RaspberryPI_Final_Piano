# core/state_machine.py

from enum import Enum


class State(Enum):
    SLEEP = "sleep"
    IDLE = "idle"
    PRACTICE = "practice"


class Event(Enum):
    PIR_DETECTED = "pir_detected"
    CMD_WAKE = "cmd_wake"
    CMD_SLEEP = "cmd_sleep"
    CMD_START_PRACTICE = "cmd_start_practice"
    CMD_STOP_PRACTICE = "cmd_stop_practice"
    PRACTICE_COMPLETE = "practice_complete"
    PRACTICE_START_FAILED = "practice_start_failed"


# (현재 상태, 이벤트) -> 다음 상태
# 매핑에 없는 조합은 "무시"로 처리되고, 동일 상태 매핑은 처리되지만 changed=False를 반환함
TRANSITIONS = {
    (State.SLEEP, Event.PIR_DETECTED): State.IDLE,
    (State.SLEEP, Event.CMD_WAKE): State.IDLE,

    (State.IDLE, Event.PIR_DETECTED): State.IDLE,
    (State.IDLE, Event.CMD_SLEEP): State.SLEEP,
    (State.IDLE, Event.CMD_START_PRACTICE): State.PRACTICE,


    (State.PRACTICE, Event.CMD_STOP_PRACTICE): State.IDLE,
    (State.PRACTICE, Event.PRACTICE_COMPLETE): State.IDLE,
    (State.PRACTICE, Event.PRACTICE_START_FAILED): State.IDLE,
    (State.PRACTICE, Event.PIR_DETECTED): State.PRACTICE,
}


class StateMachine:
    def __init__(self, initial_state=State.SLEEP):
        self.state = initial_state

    def handle(self, event):
        """
        이벤트 처리.
        반환: (현재 상태, changed: bool)
          - changed=True  -> 상태가 실제로 바뀜
          - changed=False -> 정의되지 않은 이벤트이거나 동일 상태로의 전이라 상태 변화 없음
        """
        next_state = TRANSITIONS.get((self.state, event))

        if next_state is None:
            return self.state, False

        changed = next_state != self.state
        self.state = next_state
        return self.state, changed
