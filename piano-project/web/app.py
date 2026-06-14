# web/app.py

from flask import Flask, render_template, request, jsonify

from practice.session import PracticeSession
from web import mqtt_client
import config

app = Flask(__name__)
song_catalog = PracticeSession(config.SONGS_DIR)
ALLOWED_ACTIONS = {
    "wake",
    "sleep",
    "start_record",
    "stop_record",
    "start_practice",
    "stop_practice",
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/record")
def record_page():
    return render_template("record.html")


@app.route("/practice")
def practice_page():
    songs = song_catalog.list_songs()
    return render_template("practice.html", songs=songs)


@app.route("/api/status")
def api_status():
    return jsonify(mqtt_client.get_status())


@app.route("/api/cmd", methods=["POST"])
def api_cmd():
    data = request.get_json(silent=True) or {}
    if data.get("action") not in ALLOWED_ACTIONS:
        return jsonify({"ok": False, "error": "invalid action"}), 400
    mqtt_client.send_cmd(data)
    return jsonify({"ok": True})


mqtt_client.start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
