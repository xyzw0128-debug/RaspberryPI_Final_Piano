# Raspberry Pi Piano Practice Assistant

Raspberry Pi 5 Ubuntu에서 동작하는 피아노 연습 보조 프로젝트입니다. Flask 웹 UI는 사용자의 조작을 받고, 하드웨어 컨트롤러는 MQTT 명령을 받아 PIR 센서, LED, USB-MIDI 입력, 연습 세션을 처리합니다.

## 핵심 기능

- PIR 센서 감지 또는 웹 버튼으로 SLEEP 상태를 해제합니다.
- Flask 단일 화면에서 현재 상태, MIDI 포트, 곡 선택, 연습 진행도, 오답 횟수, 완주 결과를 확인합니다.
- MQTT로 Flask 프로세스와 하드웨어 컨트롤러 프로세스를 분리해 통신합니다.
- MIDI 입력을 현재 곡의 기대 음과 비교해 정답/오답을 판정하고, 틀린 횟수를 연습 세션 단위로 누적합니다.
- LED로 대기, 정답, 오답, 완주 피드백을 표시합니다.

## 구조

```text
piano-project/
├── main.py                  # 하드웨어 컨트롤러 실행
├── config.py                # GPIO, MQTT, 경로 설정
├── midi_config.py           # MIDI 포트 선택 저장/불러오기
├── core/                    # 컨트롤러와 상태 머신
├── hardware/                # LED, PIR, MIDI 입력
├── mqtt/                    # MQTT wrapper
├── practice/                # 연습 세션과 곡 JSON
│   └── songs/               # 곡 JSON 파일 보관
├── state/                   # MIDI 포트 선택 영속화
├── logs/                    # 로그 파일
└── web/                     # Flask 단일 연습 UI
```

## MQTT 연동 방식

```text
브라우저
  → Flask /api/cmd
  → MQTT piano/cmd
  → main.py 하드웨어 컨트롤러
  → GPIO / MIDI / 연습 처리

main.py 하드웨어 컨트롤러
  → MQTT piano/status
  → Flask 상태 캐시
  → 브라우저 /api/status polling
```

### MQTT 커맨드 명세 (`piano/cmd`)

모든 커맨드는 JSON 형식으로 전송됩니다.

| action | 추가 파라미터 | 설명 |
|---|---|---|
| `wake` | 없음 | SLEEP → IDLE |
| `sleep` | 없음 | IDLE → SLEEP |
| `start_practice` | `song_id` 필수 | 연습 시작 |
| `stop_practice` | 없음 | 연습 종료 |
| `set_midi_port` | `port_name` 필수 | MIDI 입력 포트 전환 |

예시:

```bash
mosquitto_pub -h localhost -t piano/cmd -m '{"action":"start_practice","song_id":"twinkle"}'
```

### MQTT 상태 예시 (`piano/status`)

```json
{
  "state": "practice",
  "practice": {
    "title": "Twinkle Twinkle Little Star",
    "index": 3,
    "total": 42,
    "prev": "D4",
    "current": "E4",
    "next": "F4",
    "mistakes": 1
  },
  "midi_ports": ["USB MIDI Interface"],
  "midi_current_port": "USB MIDI Interface",
  "midi_saved_port": "USB MIDI Interface",
  "last_result": null
}
```

연습을 완주해 상태가 `idle`로 돌아가면 진행 중 연습 정보 대신 마지막 완주 결과가 `last_result`에 유지됩니다.

```json
{
  "state": "idle",
  "midi_ports": ["USB MIDI Interface"],
  "midi_current_port": "USB MIDI Interface",
  "midi_saved_port": "USB MIDI Interface",
  "last_result": {
    "title": "Twinkle Twinkle Little Star",
    "mistakes": 2,
    "completed_notes": 42,
    "total": 42
  }
}
```

## GPIO 핀 배치 (BCM 기준)

| 구분 | 핀 번호 | 설명 |
|---|---:|---|
| PIR 센서 | GPIO 16 | 움직임 감지 |
| IDLE_LED | GPIO 17 | IDLE 대기 상태 표시 |
| SLEEP_LED | GPIO 27 | SLEEP 절전 상태 표시 |
| PRACTICE_CORRECT_LED | GPIO 22 | 연습 정답/완주 표시 |
| PRACTICE_READY_LED | GPIO 23 | 연습 모드 대기 표시 |
| PRACTICE_WRONG_LED | GPIO 24 | 연습 오답 표시 |

### LED 동작 요약

| 상태/상황 | LED 동작 |
|---|---|
| SLEEP | SLEEP_LED 점등 |
| IDLE | IDLE_LED 점등 |
| PRACTICE 대기 | PRACTICE_READY_LED 점등 |
| PRACTICE 정답 | PRACTICE_CORRECT_LED 점등 후 PRACTICE_READY_LED 복귀 |
| PRACTICE 오답 | PRACTICE_WRONG_LED 점등 후 PRACTICE_READY_LED 복귀 |
| PRACTICE 완주 | PRACTICE_CORRECT_LED 3회 점멸 |

## 상태 전이표

| 현재 상태 | 이벤트 | 다음 상태 |
|---|---|---|
| SLEEP | PIR 감지 / `wake` 커맨드 | IDLE |
| IDLE | `sleep` 커맨드 | SLEEP |
| IDLE | `start_practice` 커맨드 | PRACTICE |
| PRACTICE | `stop_practice` 커맨드 | IDLE |
| PRACTICE | 곡 완주 | IDLE |
| PRACTICE | 연습 시작 실패 | IDLE |

## 웹 UI

| 경로 | 설명 |
|---|---|
| `/` | 상태 표시, SLEEP 전환, MIDI 포트 선택, 연습 결과, 곡 선택, 연습 시작/종료, 진행도 표시 |

홈 화면은 다음 순서로 구성됩니다.

1. **장치 준비**: SLEEP 해제 또는 SLEEP 전환 버튼을 제공합니다.
2. **MIDI 입력 선택**: 현재 MIDI 포트와 선택 가능한 MIDI 입력 포트를 보여주고 적용할 수 있습니다.
3. **연습 결과**: 직전 연습을 완주한 뒤 곡 제목, 틀린 횟수, 완주한 음 수를 표시합니다. 연습 중이거나 결과가 없으면 숨겨집니다.
4. **곡 선택 후 연습 시작**: 연습할 곡을 선택하고 시작합니다.
5. **연습 중 화면**: 이전 음, 현재 누를 음, 다음 음, 진행률, 현재까지의 오답 횟수를 보여줍니다.


## Raspberry Pi 5 Ubuntu 설치

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
sudo apt install -y mosquitto mosquitto-clients
sudo apt install -y libasound2-dev
```

## MQTT broker 실행

```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
sudo systemctl status mosquitto
```

MQTT 상태 구독:

```bash
mosquitto_sub -h localhost -t piano/status
```

테스트 커맨드:

```bash
mosquitto_pub -h localhost -t piano/cmd -m '{"action":"wake"}'
```

## Python 환경 구성

```bash
cd ~/RaspberryPI_Final_Piano/piano-project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

USB-MIDI 장치 확인:

```bash
python -c "import mido; print(mido.get_input_names())"
```

## 실행

터미널 1에서 하드웨어 컨트롤러 실행:

```bash
cd ~/RaspberryPI_Final_Piano/piano-project
source .venv/bin/activate
python main.py
```

GPIO 권한 문제가 있으면 시연용으로 다음처럼 실행할 수 있습니다.

```bash
sudo .venv/bin/python main.py
```

터미널 2에서 Flask 웹 서버 실행:

```bash
cd ~/RaspberryPI_Final_Piano/piano-project
source .venv/bin/activate
python -m web.app
```

브라우저에서 접속:

```text
http://라즈베리파이IP:5000
```

## 곡 파일 추가

`practice/songs/` 디렉토리에 JSON 파일을 추가해 곡을 늘릴 수 있습니다.

```json
{
  "title": "곡 이름",
  "notes": [60, 62, 64, 65, 67]
}
```

`notes`는 MIDI 노트 번호 배열입니다. 예를 들어 C4는 60입니다. 파일명에서 `.json`을 제외한 값이 `song_id`로 사용됩니다.

## 로그

실행 중 오류 및 이벤트는 `logs/main.log`에 기록됩니다.

```bash
tail -f logs/main.log
```
