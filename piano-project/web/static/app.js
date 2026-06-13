// web/static/app.js

function sendCmd(payload) {
  fetch("/api/cmd", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
}

function pollStatus(callback) {
  function tick() {
    fetch("/api/status")
      .then(res => res.json())
      .then(callback)
      .catch(() => {});
  }
  tick();
  setInterval(tick, 1000);
}