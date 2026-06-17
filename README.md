코드 전체 다시 꼼꼼히 읽을게.전체 다 읽었어. 이제 작성할게.이제 전부 파악했어. README 업데이트할게.

```markdown
# Raspberry Pi Piano Assistant

Raspberry Pi 5 Ubuntu에서 동작하는 피아노 학습 보조 프로젝트입니다. Flask 웹 UI는 사용자 조작을 받고, 하드웨어 제어 프로세스는 MQTT를 통해 명령을 받아 PIR 센서, LED, USB-MIDI 입력, 녹음/연습 로직을 처리합니다.

## 구조

```text
piano-project/
├── main.py                  # 하드웨어 컨트롤러 실행
├── config.py                # GPIO, MQTT, 경로 설정
├── midi_config.py           # MIDI 포트 선택 저장/불러오기
├── core/                    # 상태 머신과 컨트롤러
├── hardware/                # LED, PIR, MIDI 입력
├── mqtt/                    # MQTT wrapper
├── practice/                # 연습 세션과 곡 JSON
│   └── songs/               # 곡 JSON 파일 보관 (예: twinkle.json)
├── recording/               # MIDI 녹음 저장 (recordings/*.mid)
├── state/                   # MIDI 포트 선택 영속화 (midi_port.json)
├── logs/                    # 로그 파일 (main.log)
└── web/                     # Flask 웹 UI
    ├── mqtt_client.py       # Flask 전용 MQTT 상태 캐시
    └── ...
```

## MQTT 연동 방식

이 프로젝트의 MQTT는 외부 서버 통신용이 아니라, 같은 Raspberry Pi 내부에서 실행되는 두 프로세스 사이의 통신용입니다.

```text
브라우저
  → Flask /api/cmd
  → MQTT piano/cmd
  → main.py 하드웨어 컨트롤러
  → GPIO / MIDI / 녹음 / 연습 처리

main.py 하드웨어 컨트롤러
  → MQTT piano/status
  → Flask 상태 캐시
  → 브라우저 /api/status polling (200ms 간격)
```

### MQTT 커맨드 명세 (`piano/cmd`)

모든 커맨드는 JSON 형식으로 전송됩니다.

| action | 추가 파라미터 | 설명 |
|---|---|---|
| `wake` | 없음 | SLEEP → IDLE |
| `sleep` | 없음 | IDLE → SLEEP |
| `start_record` | 없음 | 녹음 시작 |
| `stop_record` | `filename` (선택) | 녹음 종료. 생략 시 날짜/시간으로 자동 설정 |
| `start_practice` | `song_id` (필수) | 연습 시작 |
| `stop_practice` | 없음 | 연습 종료 |
| `set_midi_port` | `port_name` (필수) | MIDI 입력 포트 전환 |

예시:

```bash
mosquitto_pub -h localhost -t piano/cmd -m '{"action":"start_practice","song_id":"twinkle"}'
```

## GPIO 핀 배치 (BCM 기준)

| 구분 | 핀 번호 | 설명 |
|---|---|---|
| PIR 센서 | GPIO 16 | 움직임 감지 (RISING edge, 바운스 2000ms) |
| LED_REC_GREEN | GPIO 17 | 녹음 중 점멸 |
| LED_REC_RED | GPIO 27 | IDLE 대기 상태 표시 |
| LED_PRACTICE_GREEN | GPIO 22 | 연습 정답 표시 |
| LED_PRACTICE_BLUE | GPIO 23 | 연습 모드 대기 표시 |
| LED_PRACTICE_RED | GPIO 24 | 연습 오답 표시 |

### LED 동작 요약

| 상태 | LED 동작 |
|---|---|
| SLEEP | 전체 소등 |
| IDLE | REC_RED 점등 |
| RECORDING | REC_GREEN 점멸 (0.5초 간격) |
| PRACTICE (대기) | PRACTICE_BLUE 점등 |
| PRACTICE (정답) | PRACTICE_GREEN 점등 → 0.3초 후 BLUE 복귀 |
| PRACTICE (오답) | PRACTICE_RED 점등 → 0.3초 후 BLUE 복귀 |
| PRACTICE (완주) | PRACTICE_GREEN 3회 점멸 |

## 상태 전이표

| 현재 상태 | 이벤트 | 다음 상태 |
|---|---|---|
| SLEEP | PIR 감지 / `wake` 커맨드 | IDLE |
| IDLE | `sleep` 커맨드 | SLEEP |
| IDLE | `start_record` 커맨드 | RECORDING |
| IDLE | `start_practice` 커맨드 | PRACTICE |
| RECORDING | `stop_record` 커맨드 | IDLE |
| PRACTICE | `stop_practice` 커맨드 | IDLE |
| PRACTICE | 곡 완주 | IDLE |
| PRACTICE | 연습 시작 실패 | IDLE |

RECORDING / PRACTICE 상태 중 다른 커맨드를 보내면 `{"error": "busy"}` 응답이 반환되고 상태는 유지됩니다.

## 웹 UI 페이지

| 경로 | 설명 |
|---|---|
| `/` | 메인: 상태 표시, SLEEP ↔ IDLE 전환, MIDI 포트 선택 |
| `/record` | 녹음 시작/종료, 녹음 파일 목록 확인 |
| `/practice` | 곡 선택 후 연습 시작, 이전/현재/다음 음 표시 |

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

MQTT 동작 확인:

```bash
mosquitto_sub -h localhost -t piano/status
```

다른 터미널에서 테스트 커맨드:

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

의존 패키지 (`requirements.txt`):

```
flask
paho-mqtt<2.0
mido
python-rtmidi
rpi-lgpio
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

`notes`는 MIDI 노트 번호 배열입니다 (C4=60, D4=62, E4=64, F4=65, G4=67 ...). 파일명(`.json` 제외)이 `song_id`로 사용됩니다. 기본 제공: `twinkle.json` (Twinkle Twinkle Little Star, 42음).

## 로그

실행 중 오류 및 이벤트는 `logs/main.log`에 기록됩니다.

```bash
tail -f logs/main.log
```

## 상태 규칙

- `SLEEP`: 절전 상태입니다. 웹 UI에서 녹음/연습 조작이 막히며, `Sleep 해제` 버튼 또는 PIR 감지로 `IDLE` 상태가 됩니다.
- `IDLE`: 대기 상태입니다. 녹음 또는 연습을 시작할 수 있습니다.
- `RECORDING`: MIDI 입력을 녹음합니다.
- `PRACTICE`: 현재 음을 순서대로 입력하면 LED로 정답/오답을 표시합니다.

녹음 파일은 최신 10개까지만 유지됩니다. MIDI 포트 선택은 `state/midi_port.json`에 저장되어 재시작 시 자동 복원됩니다.

---

## 알려진 이슈

- **MQTT 레이스 컨디션** (`mqtt/client.py`): `_on_connect` 콜백이 `_subscriptions` dict를 순회하는 도중 메인 스레드에서 `subscribe()`가 호출되면 락 없이 dict가 동시에 수정될 수 있습니다. 현재 구조상 모든 구독 등록이 `connect()` 호출 이전에 완료되므로 실제 문제가 발생하는 경우는 드물지만, 잠재적 버그로 남아 있습니다.

- **연습 모드 묵시적 IDLE 롤백** (`core/controller.py`): `practice/songs/`가 비어있거나 존재하지 않는 `song_id`가 전달된 경우, 예외 발생 후 상태가 조용히 IDLE로 롤백됩니다. 에러는 `piano/status`의 `error` 필드로 게시되지만 웹 UI 상단에 별도 알림이 없어 사용자가 인지하기 어렵습니다.
```

