# midi_config.py

import json
import os

import config


STATE_FILE = config.MIDI_PORT_STATE_FILE


def load_selected_port():
    """Load the controller-owned persisted MIDI input port selection."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as fp:
            data = json.load(fp)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        return None

    port = data.get("port_name")
    return port if isinstance(port, str) and port else None


def save_selected_port(port_name):
    """Persist the selected MIDI input port for the controller process."""
    os.makedirs(STATE_FILE.parent, exist_ok=True)
    tmp_path = STATE_FILE.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as fp:
        json.dump({"port_name": port_name}, fp, ensure_ascii=False, indent=2)
        fp.write("\n")
    os.replace(tmp_path, STATE_FILE)
