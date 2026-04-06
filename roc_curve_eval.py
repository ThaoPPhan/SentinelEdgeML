import joblib
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

INPUT_FILE = "test_split.csv"
MODEL_FILE = "sentineledge_rf_model.joblib"


def safe_transform(value, encoder):
    if value in encoder.classes_:
        return encoder.transform([value])[0]
    return -1


def preprocess_for_roc(df: pd.DataFrame, encoders: dict):
    df = df.copy()

    domain_encoder = encoders["domain_encoder"]
    device_encoder = encoders["device_encoder"]

    df["target_domain_encoded"] = df["target_domain"].apply(
        lambda x: safe_transform(x, domain_encoder)
    )
    df["device_type_encoded"] = df["device_type"].apply(
        lambda x: safe_transform(x, device_encoder)
    )

    feature_columns = encoders["feature_columns"]
    X = df[feature_columns]
    y = df["label"]

    return X, y


def main():
    bundle = joblib.load(MODEL_FILE)
    model = bundle["model"]
    encoders = bundle["encoders"]

    df = pd.read_csv(INPUT_FILE)
    X, y = preprocess_for_roc(df, encoders)

    y_prob = model.predict_proba(X)[:, 1]

    fpr, tpr, _ = roc_curve(y, y_prob)
    roc_auc = auc(fpr, tpr)

    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.4f}", linewidth=2)
    plt.plot([0, 1], [0, 1], linestyle="--", linewidth=1)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve (Held-Out Test Set)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig("roc_curve.png", dpi=300)
    plt.show()

    print(f"ROC AUC = {roc_auc:.4f}")
    print("Saved figure: roc_curve.png")


if __name__ == "__main__":
    main()