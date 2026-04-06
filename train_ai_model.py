import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    accuracy_score,
    roc_auc_score
)
from sklearn.preprocessing import LabelEncoder
import joblib

INPUT_FILE = "smart_home_iot.csv"
MODEL_FILE = "sentineledge_rf_model.joblib"
TEST_SPLIT_FILE = "test_split.csv"

BAD_DOMAINS = ["evil-server.xyz", "malicious-drop.net", "unknown-remote.biz"]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["minute"] = df["timestamp"].dt.minute
    df["second"] = df["timestamp"].dt.second

    df["is_bad_domain"] = df["target_domain"].isin(BAD_DOMAINS).astype(int)

    return df


def fit_encoders(train_df: pd.DataFrame):
    domain_encoder = LabelEncoder()
    device_encoder = LabelEncoder()

    domain_encoder.fit(train_df["target_domain"])
    device_encoder.fit(train_df["device_type"])

    return {
        "domain_encoder": domain_encoder,
        "device_encoder": device_encoder,
    }


def safe_transform(value, encoder):
    if value in encoder.classes_:
        return encoder.transform([value])[0]
    return -1


def transform_with_encoders(df: pd.DataFrame, encoders: dict):
    df = df.copy()

    domain_encoder = encoders["domain_encoder"]
    device_encoder = encoders["device_encoder"]

    df["target_domain_encoded"] = df["target_domain"].apply(
        lambda x: safe_transform(x, domain_encoder)
    )
    df["device_type_encoded"] = df["device_type"].apply(
        lambda x: safe_transform(x, device_encoder)
    )

    feature_columns = [
        "temperature",
        "humidity",
        "motion_detected",
        "packet_size",
        "send_interval",
        "failed_login_attempts",
        "is_bad_domain",
        "target_domain_encoded",
        "device_type_encoded",
        "hour",
        "minute",
        "second"
    ]

    X = df[feature_columns]
    y = df["label"]

    return X, y, feature_columns


def train_model():
    df = pd.read_csv(INPUT_FILE)
    df = add_features(df)

    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["label"]
    )

    encoders = fit_encoders(train_df)

    X_train, y_train, feature_columns = transform_with_encoders(train_df, encoders)
    X_test, y_test, _ = transform_with_encoders(test_df, encoders)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("=== MODEL EVALUATION ===")
    print("Accuracy :", round(accuracy_score(y_test, y_pred), 4))
    print("Precision:", round(precision_score(y_test, y_pred), 4))
    print("Recall   :", round(recall_score(y_test, y_pred), 4))
    print("F1-score :", round(f1_score(y_test, y_pred), 4))
    print("ROC AUC  :", round(roc_auc_score(y_test, y_prob), 4))

    print("\n=== CONFUSION MATRIX ===")
    print(confusion_matrix(y_test, y_pred))

    print("\n=== CLASSIFICATION REPORT ===")
    print(classification_report(y_test, y_pred, digits=4))

    feature_importance = pd.DataFrame({
        "feature": feature_columns,
        "importance": model.feature_importances_
    }).sort_values(by="importance", ascending=False)

    print("\n=== FEATURE IMPORTANCE ===")
    print(feature_importance)

    joblib.dump({
        "model": model,
        "encoders": {
            **encoders,
            "feature_columns": feature_columns
        }
    }, MODEL_FILE)

    # Save held-out test split for later evaluation plots
    test_df.to_csv(TEST_SPLIT_FILE, index=False)

    print(f"\nModel saved to: {MODEL_FILE}")
    print(f"Test split saved to: {TEST_SPLIT_FILE}")


if __name__ == "__main__":
    train_model()