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

function updateMidiPortSelect(status) {
  const select = document.getElementById("midiPortSelect");
  if (!select) {
    return;
  }

  const current = document.getElementById("midiCurrentPort");
  if (current) {
    current.textContent = status.midi_current_port || "-";
  }

  const ports = status.midi_ports || [];
  const appliedPort = status.midi_port_applied;
  const portsKey = JSON.stringify(ports);
  const hasFocus = document.activeElement === select;

  if (hasFocus && select.dataset.populated) {
    return;
  }

  if (select.dataset.ports !== portsKey) {
    select.innerHTML = "";
    ports.forEach(port => {
      const option = document.createElement("option");
      option.value = port;
      option.textContent = port;
      select.appendChild(option);
    });
    select.dataset.ports = portsKey;
  }

  if (!select.dataset.populated || appliedPort) {
    select.value = appliedPort || status.midi_current_port || status.midi_saved_port || "";
  }

  select.disabled = ports.length === 0;
  select.dataset.populated = "true";
}

function applyMidiPort() {
  const select = document.getElementById("midiPortSelect");
  if (!select || !select.value) {
    return;
  }
  sendCmd({action: "set_midi_port", port_name: select.value});
}
