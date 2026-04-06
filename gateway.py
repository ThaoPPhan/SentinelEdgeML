import pandas as pd

BAD_DOMAINS = ["evil-server.xyz", "malicious-drop.net", "unknown-remote.biz"]


# ---------------- RULE ENGINE ----------------
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


# ---------------- AI PLACEHOLDER ----------------
def ai_model_score(row):
    score = 0

    if row["packet_size"] > 2000:
        score += 0.3
    if row["send_interval"] < 0.1:
        score += 0.3
    if row["failed_login_attempts"] > 10:
        score += 0.3
    if row["target_domain"] in BAD_DOMAINS:
        score += 0.2

    return min(score, 1.0)


# ---------------- DECISION ENGINE ----------------
def decision(row):
    rule_flags = rule_engine(row)
    ai_score = ai_model_score(row)

    if rule_flags:
        return "BLOCK", rule_flags, ai_score

    if ai_score > 0.6:
        return "ALERT", ["AI anomaly"], ai_score

    return "ALLOW", [], ai_score


# ---------------- MAIN PIPELINE ----------------
def process_data(file):
    df = pd.read_csv(file)

    results = []

    for _, row in df.iterrows():
        action, reasons, score = decision(row)

        results.append({
            "device_id": row["device_id"],
            "action": action,
            "reasons": ", ".join(reasons),
            "ai_score": score
        })

    return pd.DataFrame(results)


if __name__ == "__main__":
    result_df = process_data("smart_home_iot.csv")
    result_df.to_csv("gateway_output.csv", index=False)

    print("Gateway processing done.")
    print(result_df["action"].value_counts())