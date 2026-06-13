# hardware/led_controller.py

import RPi.GPIO as GPIO
from enum import Enum
from core.state_machine import State


class LED(Enum):
    REC_GREEN = "rec_green"
    REC_RED = "rec_red"
    PRACTICE_GREEN = "practice_green"
    PRACTICE_BLUE = "practice_blue"
    PRACTICE_RED = "practice_red"


# 상태 → 기본 점등 LED 매핑 (필요시 수정)
STATE_LED_MAP = {
    State.SLEEP: [],
    State.IDLE: [LED.REC_RED],          # 녹음 대기 표시
    State.RECORDING: [LED.REC_GREEN],
    State.PRACTICE: [LED.PRACTICE_BLUE],  # 입력 대기 표시
}


class LedController:
    def __init__(self, pin_map):
        """
        pin_map: {LED.REC_GREEN: 17, LED.REC_RED: 27,
                  LED.PRACTICE_GREEN: 22, LED.PRACTICE_BLUE: 23,
                  LED.PRACTICE_RED: 24}
        """
        self.pin_map = pin_map
        GPIO.setmode(GPIO.BCM)
        for pin in self.pin_map.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def _set(self, led, on):
        GPIO.output(self.pin_map[led], GPIO.HIGH if on else GPIO.LOW)

    def all_off(self):
        for led in self.pin_map:
            self._set(led, False)

    def set_state(self, state):
        """controller가 상태 전이 시 호출. 이전 LED는 모두 끄고 새 상태에 맞게 점등."""
        self.all_off()
        for led in STATE_LED_MAP.get(state, []):
            self._set(led, True)

    def set_practice_feedback(self, correct, hold_seconds=0.3):
        """
        연습 모드에서 음 입력 결과를 짧게 표시.
        correct=True  -> 초록 점등
        correct=False -> 빨강 점등
        표시 후 다시 PRACTICE_BLUE(대기)로 복귀.
        주의: time.sleep을 쓰면 MIDI 콜백 스레드가 블로킹되므로
              실제로는 controller에서 별도 타이머/스레드로 처리 권장.
        """
        if correct:
            self._set(LED.PRACTICE_BLUE, False)
            self._set(LED.PRACTICE_GREEN, True)
            self._set(LED.PRACTICE_RED, False)
        else:
            self._set(LED.PRACTICE_BLUE, False)
            self._set(LED.PRACTICE_GREEN, False)
            self._set(LED.PRACTICE_RED, True)

    def reset_practice_indicator(self):
        """피드백 표시 후 대기 상태(blue)로 복귀"""
        self._set(LED.PRACTICE_GREEN, False)
        self._set(LED.PRACTICE_RED, False)
        self._set(LED.PRACTICE_BLUE, True)

    def cleanup(self):
        self.all_off()
        GPIO.cleanup()