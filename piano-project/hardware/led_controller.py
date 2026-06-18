# hardware/led_controller.py

import time
import threading

import RPi.GPIO as GPIO
from core.state_machine import State
from hardware.enums import LED


# 상태 → 기본 점등 LED 매핑 (필요시 수정)
STATE_LED_MAP = {
    State.SLEEP: [],
    State.IDLE: [LED.REC_RED],          # 대기 상태 표시
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
        self._blink_thread = None
        self._blink_stop = threading.Event()
        self._blink_led = None
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

    def start_blink(self, led, interval=0.5):
        """지정 LED를 백그라운드 스레드에서 interval 초 간격으로 깜빡임."""
        if not self.stop_blink():
            raise RuntimeError("previous blink thread did not stop")
        self._blink_led = led
        self._blink_stop.clear()
        self._blink_thread = threading.Thread(
            target=self._blink_loop,
            args=(led, interval),
            daemon=True,
        )
        self._blink_thread.start()

    def _blink_loop(self, led, interval):
        on = False
        while not self._blink_stop.is_set():
            on = not on
            self._set(led, on)
            time.sleep(interval)
        self._set(led, False)

    def stop_blink(self, timeout=1):
        """백그라운드 LED 깜빡임을 중지."""
        if self._blink_thread and self._blink_thread.is_alive():
            self._blink_stop.set()
            self._blink_thread.join(timeout=timeout)

        if self._blink_thread and self._blink_thread.is_alive():
            return False

        self._blink_thread = None
        self._blink_led = None
        return True

    def blink_complete(self):
        """연습 완주 시 PRACTICE_GREEN LED를 0.3초 간격으로 3회 깜빡임."""
        self._set(LED.PRACTICE_BLUE, False)
        self._set(LED.PRACTICE_RED, False)
        for _ in range(3):
            self._set(LED.PRACTICE_GREEN, True)
            time.sleep(0.3)
            self._set(LED.PRACTICE_GREEN, False)
            time.sleep(0.3)

    def reset_practice_indicator(self):
        """피드백 표시 후 대기 상태(blue)로 복귀"""
        self._set(LED.PRACTICE_GREEN, False)
        self._set(LED.PRACTICE_RED, False)
        self._set(LED.PRACTICE_BLUE, True)

    def cleanup(self):
        self.stop_blink(timeout=None)
        self.all_off()
        GPIO.cleanup()
