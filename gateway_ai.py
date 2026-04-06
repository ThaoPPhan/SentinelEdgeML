import pandas as pd
import joblib

MODEL_FILE = "sentineledge_rf_model.joblib"
INPUT_FILE = "smart_home_iot.csv"
OUTPUT_FILE = "gateway_ai_output.csv"

BAD_DOMAINS = ["evil-server.xyz", "malicious-drop.net", "unknown-remote.biz"]

bundle = joblib.load(MODEL_FILE)
model = bundle["model"]
encoders = bundle["encoders"]


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

    if row["temperature"] > 80 or row["temperature"] < -10:
        reasons.append("Sensor anomaly")

    return reasons


def preprocess_single_row(row_dict):
    row = pd.DataFrame([row_dict]).copy()

    row["timestamp"] = pd.to_datetime(row["timestamp"])
    row["hour"] = row["timestamp"].dt.hour
    row["minute"] = row["timestamp"].dt.minute
    row["second"] = row["timestamp"].dt.second

    # Safe transform for unseen values
    domain_encoder = encoders["domain_encoder"]
    device_encoder = encoders["device_encoder"]

    if row.loc[0, "target_domain"] in domain_encoder.classes_:
        row["target_domain_encoded"] = domain_encoder.transform(row["target_domain"])
    else:
        row["target_domain_encoded"] = -1

    if row.loc[0, "device_type"] in device_encoder.classes_:
        row["device_type_encoded"] = device_encoder.transform(row["device_type"])
    else:
        row["device_type_encoded"] = -1

    X = row[encoders["feature_columns"]]
    return X


def ai_prediction(row):
    X = preprocess_single_row(row.to_dict())
    pred = model.predict(X)[0]
    prob = model.predict_proba(X)[0][1]
    return pred, prob


def decision(row):
    rule_flags = rule_engine(row)
    ai_pred, ai_prob = ai_prediction(row)

    if rule_flags:
        return "BLOCK", rule_flags, ai_prob

    if ai_pred == 1 and ai_prob > 0.70:
        return "ALERT", ["AI detected anomaly"], ai_prob

    return "ALLOW", [], ai_prob


def process_data(file):
    df = pd.read_csv(file)
    results = []

    for _, row in df.iterrows():
        action, reasons, ai_score = decision(row)

        results.append({
            "device_id": row["device_id"],
            "device_type": row["device_type"],
            "timestamp": row["timestamp"],
            "action": action,
            "reasons": ", ".join(reasons),
            "ai_score": round(ai_score, 4),
            "true_label": row["label"]
        })

    return pd.DataFrame(results)


if __name__ == "__main__":
    result_df = process_data(INPUT_FILE)
    result_df.to_csv(OUTPUT_FILE, index=False)

    print("AI gateway processing done.")
    print(result_df["action"].value_counts())
    print(f"Saved to: {OUTPUT_FILE}")