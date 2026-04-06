import csv
import random
from datetime import datetime, timedelta

OUTPUT_FILE = "smart_home_iot.csv"

DEVICES = [
    ("esp32_temp_1", "temperature"),
    ("esp32_motion_1", "motion"),
    ("smart_lock_1", "lock"),
    ("camera_1", "camera"),
    ("smart_light_1", "light")
]

NORMAL_DOMAINS = ["api.home.local", "cloud.iot.safe", "telemetry.internal"]
BAD_DOMAINS = ["evil-server.xyz", "malicious-drop.net", "unknown-remote.biz"]


def generate_normal(device_id, device_type, t):
    return {
        "device_id": device_id,
        "device_type": device_type,
        "timestamp": t.isoformat(),
        "temperature": round(random.uniform(20, 30), 2) if device_type == "temperature" else 0,
        "humidity": round(random.uniform(30, 60), 2) if device_type == "temperature" else 0,
        "motion_detected": random.choice([0, 1]) if device_type == "motion" else 0,
        "packet_size": random.randint(60, 500),
        "send_interval": round(random.uniform(1, 10), 2),
        "failed_login_attempts": 0,
        "target_domain": random.choice(NORMAL_DOMAINS),
        "label": 0
    }


def generate_anomaly(device_id, device_type, t):
    row = generate_normal(device_id, device_type, t)
    row["label"] = 1

    attack = random.choice(["ddos", "bruteforce", "data_exfil", "spoof"])

    if attack == "ddos":
        row["send_interval"] = round(random.uniform(0.01, 0.2), 3)

    elif attack == "bruteforce":
        row["failed_login_attempts"] = random.randint(5, 20)

    elif attack == "data_exfil":
        row["packet_size"] = random.randint(1500, 5000)
        row["target_domain"] = random.choice(BAD_DOMAINS)

    elif attack == "spoof":
        row["temperature"] = random.uniform(-20, 120)

    return row


def generate_data(n=1000, anomaly_ratio=0.15):
    data = []
    t = datetime.now()

    for _ in range(n):
        device_id, device_type = random.choice(DEVICES)

        if random.random() < anomaly_ratio:
            row = generate_anomaly(device_id, device_type, t)
        else:
            row = generate_normal(device_id, device_type, t)

        data.append(row)
        t += timedelta(seconds=random.randint(1, 5))

    return data


def save_csv(data):
    keys = data[0].keys()
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    dataset = generate_data(1000)
    save_csv(dataset)
    print("CSV created:", OUTPUT_FILE)