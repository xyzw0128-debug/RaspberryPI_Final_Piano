# hardware/led_controller.py

import time

import RPi.GPIO as GPIO
from core.state_machine import State
from hardware.enums import LED


# 상태 → 기본 점등 LED 매핑 (필요시 수정)
STATE_LED_MAP = {
    State.SLEEP: [LED.SLEEP_LED],           # 절전 상태 표시
    State.IDLE: [LED.IDLE_LED],            # 대기 상태 표시
    State.PRACTICE: [LED.PRACTICE_READY_LED],  # 입력 대기 표시
}


class LedController:
    def __init__(self, pin_map):
        """
        pin_map: {LED.IDLE_LED: 17, LED.SLEEP_LED: 27,
                  LED.PRACTICE_CORRECT_LED: 22, LED.PRACTICE_READY_LED: 23,
                  LED.PRACTICE_WRONG_LED: 24}
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

    def set_practice_feedback(self, correct):
        """
        연습 모드에서 음 입력 결과를 짧게 표시.
        correct=True  -> PRACTICE_CORRECT_LED 점등
        correct=False -> PRACTICE_WRONG_LED 점등
        controller의 타이머가 잠시 후 PRACTICE_READY_LED(대기)로 복귀시킵니다.
        """
        if correct:
            self._set(LED.PRACTICE_READY_LED, False)
            self._set(LED.PRACTICE_CORRECT_LED, True)
            self._set(LED.PRACTICE_WRONG_LED, False)
        else:
            self._set(LED.PRACTICE_READY_LED, False)
            self._set(LED.PRACTICE_CORRECT_LED, False)
            self._set(LED.PRACTICE_WRONG_LED, True)

    def blink_complete(self):
        """연습 완주 시 PRACTICE_CORRECT_LED를 0.3초 간격으로 3회 깜빡임."""
        self._set(LED.PRACTICE_READY_LED, False)
        self._set(LED.PRACTICE_WRONG_LED, False)
        for _ in range(3):
            self._set(LED.PRACTICE_CORRECT_LED, True)
            time.sleep(0.3)
            self._set(LED.PRACTICE_CORRECT_LED, False)
            time.sleep(0.3)

    def reset_practice_indicator(self):
        """피드백 표시 후 대기 상태(PRACTICE_READY_LED)로 복귀"""
        self._set(LED.PRACTICE_CORRECT_LED, False)
        self._set(LED.PRACTICE_WRONG_LED, False)
        self._set(LED.PRACTICE_READY_LED, True)

    def cleanup(self):
        self.all_off()
        GPIO.cleanup()
