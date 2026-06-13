# hardware/pir_sensor.py

import RPi.GPIO as GPIO

class PIRSensor:
    def __init__(self, pin, bounce_ms=2000):
        """
        pin: PIR 센서 OUT이 연결된 GPIO 핀 번호 (BCM 기준)
        bounce_ms: 같은 감지가 연속으로 들어올 때 무시할 시간(ms)
        """
        self.pin = pin
        self.bounce_ms = bounce_ms
        self._callback = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)

    def on_motion(self, callback):
        """모션 감지 시 호출할 콜백 등록 (RISING edge 인터럽트 방식)"""
        self._callback = callback
        GPIO.add_event_detect(
            self.pin,
            GPIO.RISING,
            callback=self._handle_motion,
            bouncetime=self.bounce_ms,
        )

    def _handle_motion(self, channel):
        if self._callback:
            self._callback()

    def cleanup(self):
        GPIO.remove_event_detect(self.pin)