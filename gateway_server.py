from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

MODEL_FILE = "sentineledge_rf_model.joblib"

bundle = joblib.load(MODEL_FILE)
model = bundle["model"]
encoders = bundle["encoders"]

BAD_DOMAINS = ["evil-server.xyz", "malicious-drop.net", "unknown-remote.biz"]
NORMAL_DOMAINS = ["api.home.local", "cloud.iot.safe", "telemetry.internal"]

DEVICES = [
    ("esp32_temp_1", "temperature"),
    ("esp32_motion_1", "motion"),
    ("smart_lock_1", "lock"),
    ("camera_1", "camera"),
    ("smart_light_1", "light")
]

logs = []
AI_THRESHOLD = 0.70


def validate_payload(data):
    required_fields = [
        "device_id",
        "device_type",
        "timestamp",
        "temperature",
        "humidity",
        "motion_detected",
        "packet_size",
        "send_interval",
        "failed_login_attempts",
        "target_domain"
    ]

    missing = [field for field in required_fields if field not in data]
    if missing:
        return False, f"Missing fields: {', '.join(missing)}"

    return True, None


def rule_engine(row):
    reasons = []

    if row["packet_size"] > 1500:
        reasons.append("Large packet")

    if row["send_interval"] < 0.2:
        reasons.append("High frequency")

    if row["failed_login_attempts"] > 5:
        reasons.append("Brute force")

    if row["target_domain"] in BAD_DOMAINS:
        reasons.append("Bad domain")

    if row["device_type"] == "temperature":
        if row["temperature"] > 80 or row["temperature"] < -10:
            reasons.append("Sensor anomaly")

    return reasons


def preprocess_single_row(row_dict):
    row = pd.DataFrame([row_dict]).copy()

    row["timestamp"] = pd.to_datetime(row["timestamp"])
    row["hour"] = row["timestamp"].dt.hour
    row["minute"] = row["timestamp"].dt.minute
    row["second"] = row["timestamp"].dt.second

    row["is_bad_domain"] = row["target_domain"].isin(BAD_DOMAINS).astype(int)

    domain_encoder = encoders["domain_encoder"]
    device_encoder = encoders["device_encoder"]

    target_domain = row.loc[0, "target_domain"]
    device_type = row.loc[0, "device_type"]

    def safe_transform(value, encoder):
        if value in encoder.classes_:
            return encoder.transform([value])[0]
        return -1

    row["target_domain_encoded"] = safe_transform(target_domain, domain_encoder)
    row["device_type_encoded"] = safe_transform(device_type, device_encoder)

    return row[encoders["feature_columns"]]


def ai_prediction(row):
    X = preprocess_single_row(row)
    pred = model.predict(X)[0]
    prob = model.predict_proba(X)[0][1]
    return int(pred), float(prob)


def decide_action(row):
    global AI_THRESHOLD

    rule_flags = rule_engine(row)
    ai_pred, ai_prob = ai_prediction(row)

    if rule_flags:
        return "BLOCK", rule_flags, ai_prob

    if ai_pred == 1 and ai_prob > AI_THRESHOLD:
        return "ALERT", ["AI detected anomaly"], ai_prob

    return "ALLOW", [], ai_prob


def save_log(data, action, reasons, ai_score):
    log = {
        "timestamp": datetime.now().isoformat(),
        "device_id": data["device_id"],
        "device_type": data["device_type"],
        "packet_size": data["packet_size"],
        "send_interval": data["send_interval"],
        "failed_login_attempts": data["failed_login_attempts"],
        "target_domain": data["target_domain"],
        "action": action,
        "reasons": reasons,
        "ai_score": round(ai_score, 4)
    }

    logs.append(log)

    if len(logs) > 300:
        logs.pop(0)

    return log


def generate_normal_event():
    device_id, device_type = random.choice(DEVICES)

    return {
        "device_id": device_id,
        "device_type": device_type,
        "timestamp": datetime.now().isoformat(),
        "temperature": round(random.uniform(20, 30), 2) if device_type == "temperature" else 0,
        "humidity": round(random.uniform(30, 60), 2) if device_type == "temperature" else 0,
        "motion_detected": random.choice([0, 1]) if device_type == "motion" else 0,
        "packet_size": random.randint(60, 500),
        "send_interval": round(random.uniform(1.0, 10.0), 2),
        "failed_login_attempts": 0,
        "target_domain": random.choice(NORMAL_DOMAINS)
    }


def generate_attack_event():
    device_id, device_type = random.choice(DEVICES)

    row = {
        "device_id": device_id,
        "device_type": device_type,
        "timestamp": datetime.now().isoformat(),
        "temperature": round(random.uniform(20, 30), 2) if device_type == "temperature" else 0,
        "humidity": round(random.uniform(30, 60), 2) if device_type == "temperature" else 0,
        "motion_detected": random.choice([0, 1]) if device_type == "motion" else 0,
        "packet_size": random.randint(60, 500),
        "send_interval": round(random.uniform(1.0, 10.0), 2),
        "failed_login_attempts": 0,
        "target_domain": random.choice(NORMAL_DOMAINS)
    }

    attack = random.choice(["ddos", "bruteforce", "exfiltration", "spoof"])

    if attack == "ddos":
        row["send_interval"] = round(random.uniform(0.01, 0.15), 3)
    elif attack == "bruteforce":
        row["failed_login_attempts"] = random.randint(6, 20)
    elif attack == "exfiltration":
        row["packet_size"] = random.randint(1800, 5000)
        row["target_domain"] = random.choice(BAD_DOMAINS)
    elif attack == "spoof":
        if row["device_type"] == "temperature":
            row["temperature"] = round(random.uniform(-20, 120), 2)
        else:
            row["packet_size"] = random.randint(1200, 2200)

    return row


@app.route("/ingest", methods=["POST"])
def ingest():
    data = request.json or {}

    ok, error_message = validate_payload(data)
    if not ok:
        return jsonify({"error": error_message}), 400

    try:
        action, reasons, ai_score = decide_action(data)
        log = save_log(data, action, reasons, ai_score)
        return jsonify(log)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/inject-normal", methods=["POST"])
def inject_normal():
    data = generate_normal_event()
    action, reasons, ai_score = decide_action(data)
    log = save_log(data, action, reasons, ai_score)
    return jsonify(log)


@app.route("/inject-attack", methods=["POST"])
def inject_attack():
    data = generate_attack_event()
    action, reasons, ai_score = decide_action(data)
    log = save_log(data, action, reasons, ai_score)
    return jsonify(log)


@app.route("/logs", methods=["GET"])
def get_logs():
    return jsonify(logs[-50:])


@app.route("/stats", methods=["GET"])
def get_stats():
    recent_logs = logs[-50:]

    allow_count = sum(1 for log in recent_logs if log["action"] == "ALLOW")
    block_count = sum(1 for log in recent_logs if log["action"] == "BLOCK")
    alert_count = sum(1 for log in recent_logs if log["action"] == "ALERT")

    avg_ai_score = round(
        sum(log["ai_score"] for log in recent_logs) / len(recent_logs), 4
    ) if recent_logs else 0.0

    top_suspicious = max(recent_logs, key=lambda x: x["ai_score"], default=None)

    return jsonify({
        "total_logs": len(logs),
        "recent_allow": allow_count,
        "recent_block": block_count,
        "recent_alert": alert_count,
        "avg_ai_score": avg_ai_score,
        "ai_threshold": AI_THRESHOLD,
        "top_suspicious": top_suspicious
    })


@app.route("/threshold", methods=["GET", "POST"])
def threshold():
    global AI_THRESHOLD

    if request.method == "POST":
        data = request.json or {}
        new_threshold = float(data.get("threshold", 0.70))
        AI_THRESHOLD = max(0.0, min(1.0, new_threshold))
        return jsonify({"ai_threshold": AI_THRESHOLD})

    return jsonify({"ai_threshold": AI_THRESHOLD})


@app.route("/reset-logs", methods=["POST"])
def reset_logs():
    logs.clear()
    return jsonify({"message": "Logs cleared"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)