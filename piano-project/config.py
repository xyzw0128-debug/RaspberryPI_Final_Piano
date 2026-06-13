# config.py

from hardware.led_controller import LED
from pathlib import Path


# ===== GPIO 핀 (BCM 기준) =====
PIR_PIN = 16

LED_PIN_MAP = {
    LED.REC_GREEN: 17,
    LED.REC_RED: 27,
    LED.PRACTICE_GREEN: 22,
    LED.PRACTICE_BLUE: 23,
    LED.PRACTICE_RED: 24,
}

# ===== MQTT =====
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883

MQTT_TOPIC_CMD = "piano/cmd"
MQTT_TOPIC_STATUS = "piano/status"

# ===== 타이밍 =====
PIR_BOUNCE_MS = 2000
PRACTICE_FEEDBACK_SEC = 0.3

# ===== 경로 =====
BASE_DIR = Path(__file__).resolve().parent

RECORDINGS_DIR = BASE_DIR / "recordings"
SONGS_DIR = BASE_DIR / "practice" / "songs"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "main.log"

# ===== MIDI =====
MIDI_PORT_NAME = None  # None이면 자동으로 첫 번째 입력 포트 사용
