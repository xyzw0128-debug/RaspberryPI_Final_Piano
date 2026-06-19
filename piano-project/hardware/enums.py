# hardware/enums.py

from enum import Enum


class LED(Enum):
    IDLE_LED = "idle_led"
    SLEEP_LED = "sleep_led"
    PRACTICE_CORRECT_LED = "practice_correct_led"
    PRACTICE_READY_LED = "practice_ready_led"
    PRACTICE_WRONG_LED = "practice_wrong_led"
