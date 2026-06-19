# config.py

from hardware.enums import LED
from pathlib import Path


# ===== GPIO 핀 (BCM 기준) =====
PIR_PIN = 16

LED_PIN_MAP = {
    LED.IDLE_LED: 17,
    LED.SLEEP_LED: 27,
    LED.PRACTICE_CORRECT_LED: 22,
    LED.PRACTICE_READY_LED: 23,
    LED.PRACTICE_WRONG_LED: 24,
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

SONGS_DIR = BASE_DIR / "practice" / "songs"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "main.log"
MIDI_PORT_STATE_FILE = BASE_DIR / "state" / "midi_port.json"

# ===== MIDI =====
# One-time seed used only when no persisted MIDI port has been selected yet.
MIDI_PORT_NAME = None
