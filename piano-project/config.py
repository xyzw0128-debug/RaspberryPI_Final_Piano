# config.py

from hardware.led_controller import LED

# ===== GPIO 핀 (BCM 기준) =====
PIR_PIN = 4

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
IDLE_TIMEOUT_SEC = 60
PRACTICE_FEEDBACK_SEC = 0.3

# ===== 경로 =====
RECORDINGS_DIR = "recordings"
SONGS_DIR = "practice/songs"
LOGS_DIR = "logs"
LOG_FILE = f"{LOGS_DIR}/main.log"

# ===== MIDI =====
MIDI_PORT_NAME = None  # None이면 자동으로 첫 번째 입력 포트 사용