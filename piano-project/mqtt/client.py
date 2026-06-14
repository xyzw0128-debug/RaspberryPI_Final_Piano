# mqtt/client.py

import json
import paho.mqtt.client as mqtt


class MqttClient:
    def __init__(self, host, port=1883, client_id=None):
        self.host = host
        self.port = port
        self._client = mqtt.Client(client_id=client_id)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._subscriptions = {}  # topic -> callback
        self._connected = False

    def _on_connect(self, client, userdata, flags, rc):
        self._connected = (rc == 0)
        if not self._connected:
            return
        for topic in self._subscriptions:
            self._client.subscribe(topic)

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False

    def _on_message(self, client, userdata, msg):
        callback = self._subscriptions.get(msg.topic)
        if callback:
            try:
                payload = json.loads(msg.payload.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = msg.payload.decode(errors="ignore")
            callback(payload)

    def connect(self):
        self._client.connect(self.host, self.port)

    def loop_start(self):
        """백그라운드 스레드에서 송수신 루프 실행 (Flask/main 양쪽에서 사용)"""
        self._client.loop_start()

    def loop_stop(self):
        self._client.disconnect()
        self._client.loop_stop()

    def subscribe(self, topic, callback):
        """
        callback(payload: dict|str) 형태로 호출됨
        connect() 이전/이후 모두 호출 가능
        """
        self._subscriptions[topic] = callback
        if self._connected:
            self._client.subscribe(topic)

    def publish(self, topic, payload):
        """
        payload: dict면 자동으로 JSON 직렬화, str이면 그대로 전송
        """
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        self._client.publish(topic, payload)