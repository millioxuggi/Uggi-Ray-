const HOST_API = "https://uggi-ray-aquaduse-host.onrender.com";

const stream = document.getElementById("stream");

function addEvent(message) {
  if (!stream) return;

  const e = document.createElement("div");
  e.className = "event";
  e.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  stream.prepend(e);
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

async function loadHealth() {
  try {
    const r = await fetch(`${HOST_API}/api/health`, {
      cache: "no-store"
    });

    const data = await r.json();

    setText(
      "hostStatus",
      `${data.status || "UNKNOWN"} | ${data.mode || "SAFE"}`
    );

    addEvent(
      `HOST HEALTH | ${data.status} | SECURITY: ${data.security || "ENABLED"}`
    );
  } catch (err) {
    setText("hostStatus", "OFFLINE / UNREACHABLE");
    addEvent("HOST HEALTH ERROR | Backend unreachable");
  }
}

async function loadSecurity() {
  try {
    const r = await fetch(`${HOST_API}/api/security`, {
      cache: "no-store"
    });

    const data = await r.json();

    addEvent(
      `SECURITY | AUTH=${data.authentication} | ` +
      `AUTHZ=${data.authorization} | ` +
      `AUDIT=${data.audit_logging} | ` +
      `OS_EXEC=${data.os_execution}`
    );
  } catch (err) {
    addEvent("SECURITY CHECK ERROR | Unable to read security status");
  }
}

async function loadState() {
  try {
    const r = await fetch(`${HOST_API}/api/state`, {
      cache: "no-store"
    });

    const data = await r.json();

    setText("water", Number(data.water_level ?? 0).toFixed(2));
    setText("chaos", Number(data.chaos ?? 0).toFixed(2));
    setText(
      "temp",
      `${Number(data.temperature ?? 20).toFixed(2)}°C`
    );
    setText("gen", data.generation ?? 0);
  } catch (err) {
    addEvent("STATE ERROR | Unable to read ecosystem state");
  }
}

async function sendHostRequest(command) {
  addEvent(
    `HOST_REQUEST | ${command} | AUTHORIZATION REQUIRED | ` +
    `EXECUTION BLOCKED UNTIL SECURE ADMIN AUTHORIZATION`
  );

  try {
    const r = await fetch(`${HOST_API}/api/command`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        command: command
      })
    });

    const data = await r.json();

    if (r.status === 401) {
      addEvent(
        `🔒 SECURITY | ${command} DENIED | ` +
        `Valid Host Admin authorization required`
      );
      return;
    }

    if (!r.ok) {
      addEvent(
        `SECURITY | ${command} DENIED | ` +
        `${data.reason || "Request rejected"}`
      );
      return;
    }

    addEvent(
      `HOST_RESPONSE | ${command} | ${data.status} | ` +
      `${data.execution} | APPROVAL=${data.approval}`
    );
  } catch (err) {
    addEvent(
      `HOST_REQUEST ERROR | ${command} | Backend unreachable`
    );
  }
}

document.querySelectorAll("[data-a]").forEach((button) => {
  button.addEventListener("click", () => {
    const command = String(button.dataset.a || "").toUpperCase();

    if (command) {
      sendHostRequest(command);
    }
  });
});

addEvent(
  "HOST DASHBOARD READY | AQUADUSE HOST | SECURITY V1"
);

addEvent(
  "COMMAND GATE ACTIVE | DENY-BY-DEFAULT | " +
  "NO ADMIN KEY STORED IN FRONTEND"
);

loadHealth();
loadSecurity();
loadState();

setInterval(loadState, 5000);
setInterval(loadHealth, 30000);
