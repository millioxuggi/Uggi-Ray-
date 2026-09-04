from __future__ import annotations

import json
import os
import time
from pathlib import Path
from threading import Lock

from flask import Flask, jsonify, request
from flask_socketio import SocketIO

APP_ROOT = Path(__file__).resolve().parent
STATE_FILE = APP_ROOT / "ecosystem.json"
LOG_FILE = APP_ROOT / "divine_log.json"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("HOST_SECRET_KEY", "development-only-change-me")

# Socket.IO is used for dashboard updates. The browser dashboard is not given
# direct operating-system command authority.
socketio = SocketIO(
    app,
    cors_allowed_origins=os.getenv("CORS_ORIGINS", "*"),
    async_mode="threading",
)

_state_lock = Lock()
_runtime = {
    "status": "SAFE",
    "host": "Aquaduse Host",
    "generation": 0,
    "last_command": None,
    "last_command_time": None,
}


def _read_json(path: Path, fallback):
    try:
        if path.exists():
            value = json.loads(path.read_text(encoding="utf-8"))
            return value
    except Exception:
        pass
    return fallback


def load_state():
    state = _read_json(
        STATE_FILE,
        {"water_level": 0, "chaos": 0, "temperature": 20, "generation": 0},
    )
    if not isinstance(state, dict):
        state = {"water_level": 0, "chaos": 0, "temperature": 20, "generation": 0}

    state.setdefault("water_level", 0)
    state.setdefault("chaos", 0)
    state.setdefault("temperature", 20)
    state.setdefault("generation", _runtime["generation"])
    return state


def load_log():
    log = _read_json(LOG_FILE, [])
    return log[-20:] if isinstance(log, list) else []


def safe_event(event: str, data: str = ""):
    """Append a bounded, non-secret dashboard event."""
    entry = {
        "timestamp": time.time(),
        "event": str(event),
        "data": str(data)[:500],
        "source": "AQUADUSE_HOST",
    }
    with _state_lock:
        current = load_log()
        current.append(entry)
        try:
            LOG_FILE.write_text(
                json.dumps(current[-500:], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            # The API must remain available even if logging storage fails.
            pass


@app.get("/")
def dashboard_info():
    return jsonify({
        "system": "UGGI-RAY",
        "service": "Aquaduse Host Backend",
        "version": "1.2.0",
        "status": "ONLINE",
        "mode": "SAFE",
        "message": "Host backend API is running.",
    })


@app.get("/api/health")
def health():
    return jsonify({
        "ok": True,
        "service": "Aquaduse Host Backend",
        "version": "1.2.0",
        "mode": "SAFE",
    })


@app.get("/api/state")
def api_state():
    state = load_state()
    state["host_status"] = _runtime["status"]
    state["last_command"] = _runtime["last_command"]
    state["last_command_time"] = _runtime["last_command_time"]
    return jsonify(state)


@app.get("/api/log")
def api_log():
    return jsonify(load_log())


@app.get("/api/modules")
def api_modules():
    return jsonify({
        "modules": [
            {"name": "AI Brain", "status": "ADVISORY", "authority": "PREDICTION_ONLY"},
            {"name": "Water Spirit", "status": "CONTROLLED", "authority": "ORCHESTRATION_REQUEST"},
            {"name": "Ecosystem", "status": "REGISTERED", "forms": 14, "execution": "SANDBOX_ONLY"},
            {"name": "Code Lab", "status": "REGISTERED", "execution": "SANDBOX_ONLY"},
            {"name": "Eternal Flame", "status": "REGISTERED", "execution": "SOURCE_ARTIFACT_ONLY"},
        ]
    })


@app.post("/api/command")
def api_command():
    payload = request.get_json(silent=True) or {}
    command = str(payload.get("command", "")).upper().strip()
    allowed = {"START", "STOP", "ISOLATE", "ROLLBACK"}

    if command not in allowed:
        safe_event("AUTHORIZATION_DENIED", f"Unknown command: {command[:100]}")
        return jsonify({
            "ok": False,
            "authorized": False,
            "executed": False,
            "message": "Command not recognized by Host Gate.",
        }), 400

    # V1.2 deliberately records requests only. No shell/OS command is executed.
    _runtime["last_command"] = command
    _runtime["last_command_time"] = time.time()
    safe_event("MODULE_REQUEST", command)

    socketio.emit("host_event", {
        "event": "COMMAND_REQUESTED",
        "command": command,
        "authorized": False,
        "executed": False,
    })

    return jsonify({
        "ok": True,
        "authorized": False,
        "executed": False,
        "command": command,
        "message": "Request recorded. Approval/execution is disabled in Host Backend V1.2.",
    })


def broadcast_updates():
    while True:
        try:
            socketio.emit("update", {
                "state": load_state(),
                "log": load_log(),
            })
        except Exception:
            pass
        socketio.sleep(2)


@socketio.on("connect")
def on_connect():
    safe_event("HOST_DASHBOARD_CONNECTED")
    socketio.emit("update", {"state": load_state(), "log": load_log()})


@socketio.on("disconnect")
def on_disconnect():
    safe_event("HOST_DASHBOARD_DISCONNECTED")


socketio.start_background_task(broadcast_updates)


if __name__ == "__main__":
    # Local development only. Render uses Gunicorn via the Start Command.
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False,
    )
