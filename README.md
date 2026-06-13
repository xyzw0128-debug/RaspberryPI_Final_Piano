# Raspberry Pi Piano Assistant

Raspberry Pi 5 Ubuntu에서 동작하는 피아노 학습 보조 프로젝트입니다. Flask 웹 UI는 사용자 조작을 받고, 하드웨어 제어 프로세스는 MQTT를 통해 명령을 받아 PIR 센서, LED, USB-MIDI 입력, 녹음/연습 로직을 처리합니다.

## 구조

```text
piano-project/
├── main.py                  # 하드웨어 컨트롤러 실행
├── config.py                # GPIO, MQTT, 경로 설정
├── core/                    # 상태 머신과 컨트롤러
├── hardware/                # LED, PIR, MIDI 입력
├── mqtt/                    # MQTT wrapper
├── practice/                # 연습 세션과 곡 JSON
├── recording/               # MIDI 녹음 저장
└── web/                     # Flask 웹 UI
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
  → 브라우저 /api/status polling
```

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

다른 터미널에서 테스트 명령:

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

## 상태 규칙

- `SLEEP`: 절전 상태입니다. 웹 UI에서 녹음/연습 조작이 막히며, `Sleep 해제` 버튼 또는 PIR 감지로 `IDLE` 상태가 됩니다.
- `IDLE`: 대기 상태입니다. 녹음 또는 연습을 시작할 수 있습니다.
- `RECORDING`: MIDI 입력을 녹음합니다.
- `PRACTICE`: 현재 음을 순서대로 입력하면 LED로 정답/오답을 표시합니다.

녹음 파일은 최신 10개까지만 유지됩니다.
