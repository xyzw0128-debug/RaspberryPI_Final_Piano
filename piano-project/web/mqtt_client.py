# web/mqtt_client.py

import threading
from mqtt.client import MqttClient
import config

DEFAULT_STATUS = {
    "state": "sleep",
    "practice": None,
    "midi_ports": [],
    "midi_current_port": None,
    "midi_saved_port": None,
}
status_cache = dict(DEFAULT_STATUS)
_lock = threading.Lock()
_start_lock = threading.Lock()
_started = False


def _on_status(payload):
    if isinstance(payload, dict):
        with _lock:
            status_cache.clear()
            status_cache.update(DEFAULT_STATUS)
            status_cache.update(payload)


mqtt = MqttClient(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT, client_id="flask")
mqtt.subscribe(config.MQTT_TOPIC_STATUS, _on_status)


def start():
    global _started
    with _start_lock:
        if _started:
            return
        mqtt.connect()
        mqtt.loop_start()
        _started = True


def get_status():
    with _lock:
        return dict(status_cache)


def send_cmd(payload):
    mqtt.publish(config.MQTT_TOPIC_CMD, payload)