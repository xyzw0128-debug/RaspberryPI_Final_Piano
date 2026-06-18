# Practice Mode Simplification Plan

This project will be simplified around the required MQTT, LED, sensor, and Flask flow while removing recording features.

## Target scope

- Keep MQTT as the command/status bridge between Flask and the hardware controller.
- Keep PIR sensor wake-up from sleep mode.
- Keep LED feedback for idle, practice, correct notes, wrong notes, and completion.
- Keep Flask as the web interface for status, MIDI port selection, and practice controls.
- Remove MIDI recording routes, state transitions, storage, and UI.

## Proposed structure

```text
piano-project/
├── main.py
├── config.py
├── midi_config.py
├── core/
│   ├── controller.py
│   └── state_machine.py
├── hardware/
│   ├── enums.py
│   ├── led_controller.py
│   ├── midi_io.py
│   └── pir_sensor.py
├── mqtt/
│   └── client.py
├── practice/
│   ├── session.py
│   └── songs/
└── web/
    ├── app.py
    ├── mqtt_client.py
    ├── static/
    └── templates/
```

## Removal checklist

- Remove the `recording` package.
- Remove `/record` from Flask.
- Remove `RECORDING` from the state machine.
- Remove `start_record` and `stop_record` MQTT commands.
- Remove recording lists from status payloads and web UI.
- Update the README around the practice-only workflow.
