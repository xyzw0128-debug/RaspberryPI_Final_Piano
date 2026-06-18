import importlib.util
import os
import unittest
from unittest.mock import patch

os.environ["FLASK_DEBUG"] = "1"

HAS_WEB_DEPS = (
    importlib.util.find_spec("flask") is not None
    and importlib.util.find_spec("paho.mqtt.client") is not None
)

if HAS_WEB_DEPS:
    from web.app import ALLOWED_ACTIONS, app


@unittest.skipUnless(HAS_WEB_DEPS, "Flask or paho-mqtt is not installed in this environment")
class WebAppPracticeOnlyTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_allowed_actions_are_practice_only(self):
        self.assertEqual(
            ALLOWED_ACTIONS,
            {"wake", "sleep", "start_practice", "stop_practice", "set_midi_port"},
        )
        self.assertNotIn("start_record", ALLOWED_ACTIONS)
        self.assertNotIn("stop_record", ALLOWED_ACTIONS)

    def test_legacy_pages_redirect_home(self):
        self.assertEqual(self.client.get("/practice").status_code, 302)
        self.assertEqual(self.client.get("/practice").headers["Location"], "/")
        self.assertEqual(self.client.get("/record").status_code, 302)
        self.assertEqual(self.client.get("/record").headers["Location"], "/")

    def test_rejects_recording_commands(self):
        response = self.client.post("/api/cmd", json={"action": "start_record"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"ok": False, "error": "invalid action"})

    def test_sends_practice_command(self):
        with patch("web.app.mqtt_client.send_cmd") as send_cmd:
            response = self.client.post(
                "/api/cmd",
                json={"action": "start_practice", "song_id": "twinkle"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"ok": True})
        send_cmd.assert_called_once_with({"action": "start_practice", "song_id": "twinkle"})


if __name__ == "__main__":
    unittest.main()
