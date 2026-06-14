// web/static/app.js

function sendCmd(payload) {
  return fetch("/api/cmd", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  }).then(res => res.json());
}

function stateLabel(state) {
  const labels = {
    sleep: "SLEEP (절전)",
    idle: "IDLE (대기)",
    recording: "RECORDING (녹음 중)",
    practice: "PRACTICE (연습 중)",
  };
  return labels[state] || state || "-";
}

function pollStatus(callback) {
  function tick() {
    fetch("/api/status")
      .then(res => res.json())
      .then(callback)
      .catch(() => {
        document.getElementById("state").textContent = "연결 끊김";
        });
  }
  tick();
  setInterval(tick, 200);
}
