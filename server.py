from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from pathlib import Path
from datetime import datetime, timezone
import json, os

ROOT = Path(__file__).parent.resolve()
STATE_FILE = ROOT / "ecosystem.json"
LOG_FILE = ROOT / "divine_log.json"

app = Flask(__name__)
# Set FRONTEND_ORIGIN in Render to your GitHub Pages origin.
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5000")
socketio = SocketIO(app, cors_allowed_origins=[FRONTEND_ORIGIN], async_mode="threading")

ALLOWED_COMMANDS = {"START", "STOP", "ISOLATE", "ROLLBACK"}

def load_json(path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value
    except Exception:
        return default

def current_state():
    data = load_json(STATE_FILE, {})
    if not isinstance(data, dict):
        data = {}
    return {
        "water_level": data.get("water_level", 0),
        "chaos": data.get("chaos", 0),
        "temperature": data.get("temperature", 20),
        "generation": data.get("generation", 0)
    }

def recent_log(limit=50):
    data = load_json(LOG_FILE, [])
    if not isinstance(data, list):
        return []
    try:
        limit = min(max(int(limit), 1), 100)
    except (TypeError, ValueError):
        limit = 50
    return data[-limit:]

def host_event(event, data=""):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "data": str(data)[:500],
        "source": "Aquaduse Host V1.1"
    }
    existing = load_json(LOG_FILE, [])
    if not isinstance(existing, list):
        existing = []
    existing.append(entry)
    LOG_FILE.write_text(
        json.dumps(existing[-500:], indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    socketio.emit("host_event", entry)

@app.get("/api/health")
def health():
    return jsonify({
        "status": "ONLINE",
        "mode": "SAFE",
        "host": "Aquaduse Host",
        "version": "1.1.0"
    })

@app.get("/api/state")
def state():
    return jsonify(current_state())

@app.get("/api/log")
def log():
    return jsonify(recent_log(request.args.get("limit", 50)))

@app.post("/api/command")
def command():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("command", "")).upper()

    if name not in ALLOWED_COMMANDS:
        host_event("AUTHORIZATION_DENIED", f"Blocked command: {name}")
        return jsonify({
            "accepted": False,
            "status": "DENIED",
            "reason": "Command not allowed"
        }), 403

    # V1.1 records requests only. No OS/process action is executed.
    host_event(
        "MODULE_REQUEST",
        f"{name} | authorization=pending | execution=blocked"
    )
    return jsonify({
        "accepted": True,
        "status": "RECORDED",
        "command": name,
        "execution": "BLOCKED_IN_V1_1",
        "approval": "REQUIRED"
    })

def broadcaster():
    while True:
        socketio.emit("update", {
            "state": current_state(),
            "log": recent_log(10)
        })
        socketio.sleep(2)

if __name__ == "__main__":
    socketio.start_background_task(broadcaster)
    port = int(os.getenv("PORT", "10000"))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
