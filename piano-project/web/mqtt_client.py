# web/mqtt_client.py

import threading
from mqtt.client import MqttClient
import config

status_cache = {"state": "sleep", "recordings": [], "practice": None}
_lock = threading.Lock()


def _on_status(payload):
    if isinstance(payload, dict):
        with _lock:
            status_cache.update(payload)


mqtt = MqttClient(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT, client_id="flask")
mqtt.subscribe(config.MQTT_TOPIC_STATUS, _on_status)


def start():
    mqtt.connect()
    mqtt.loop_start()


def get_status():
    with _lock:
        return dict(status_cache)


def send_cmd(payload):
    mqtt.publish(config.MQTT_TOPIC_CMD, payload)