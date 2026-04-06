import time
import random
import requests
from datetime import datetime

URL = "http://127.0.0.1:5000/ingest"

DEVICES = [
    ("esp32_temp_1", "temperature"),
    ("esp32_motion_1", "motion"),
    ("smart_lock_1", "lock"),
    ("camera_1", "camera"),
    ("smart_light_1", "light")
]

NORMAL_DOMAINS = ["api.home.local", "cloud.iot.safe", "telemetry.internal"]
BAD_DOMAINS = ["evil-server.xyz", "malicious-drop.net", "unknown-remote.biz"]

def generate_normal(device_id, device_type):
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

def generate_attack(device_id, device_type):
    row = generate_normal(device_id, device_type)
    attack = random.choice(["ddos", "bruteforce", "exfiltration", "spoof"])

    if attack == "ddos":
        row["send_interval"] = round(random.uniform(0.01, 0.15), 3)

    elif attack == "bruteforce":
        row["failed_login_attempts"] = random.randint(6, 20)

    elif attack == "exfiltration":
        row["packet_size"] = random.randint(1800, 5000)
        row["target_domain"] = random.choice(BAD_DOMAINS)

    elif attack == "spoof":
        row["temperature"] = round(random.uniform(-20, 120), 2)

    return row

def main():
    print("Streaming fake IoT data to gateway... Press Ctrl+C to stop.")

    while True:
        device_id, device_type = random.choice(DEVICES)

        if random.random() < 0.18:
            payload = generate_attack(device_id, device_type)
        else:
            payload = generate_normal(device_id, device_type)

        try:
            response = requests.post(URL, json=payload, timeout=3)
            print(f"{payload['device_id']} -> {response.json()}")
        except Exception as e:
            print("Gateway not reachable:", e)

        time.sleep(1)

if __name__ == "__main__":
    main()