import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)

INPUT_FILE = "test_split.csv"
MODEL_FILE = "sentineledge_rf_model.joblib"


def safe_transform(value, encoder):
    if value in encoder.classes_:
        return encoder.transform([value])[0]
    return -1


def preprocess_for_evaluation(df: pd.DataFrame, encoders: dict):
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


def plot_confusion_matrix(cm):
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Pred Normal", "Pred Attack"],
        yticklabels=["Actual Normal", "Actual Attack"]
    )
    plt.title("Confusion Matrix (Held-Out Test Set)")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig("confusion_matrix.png", dpi=300)
    plt.show()


def plot_feature_importance(model, feature_names):
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]

    sorted_features = [feature_names[i] for i in indices]
    sorted_importances = importances[indices]

    plt.figure(figsize=(10, 6))
    plt.bar(range(len(sorted_importances)), sorted_importances)
    plt.xticks(range(len(sorted_features)), sorted_features, rotation=45, ha="right")
    plt.title("Feature Importance")
    plt.ylabel("Importance Score")
    plt.tight_layout()
    plt.savefig("feature_importance.png", dpi=300)
    plt.show()


def main():
    bundle = joblib.load(MODEL_FILE)
    model = bundle["model"]
    encoders = bundle["encoders"]

    df = pd.read_csv(INPUT_FILE)

    X, y = preprocess_for_evaluation(df, encoders)

    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]

    print("=== HELD-OUT TEST EVALUATION ===")
    print("Accuracy :", round(accuracy_score(y, y_pred), 4))
    print("Precision:", round(precision_score(y, y_pred), 4))
    print("Recall   :", round(recall_score(y, y_pred), 4))
    print("F1-score :", round(f1_score(y, y_pred), 4))
    print("ROC AUC  :", round(roc_auc_score(y, y_prob), 4))

    cm = confusion_matrix(y, y_pred)
    print("\n=== CONFUSION MATRIX ===")
    print(cm)

    print("\n=== CLASSIFICATION REPORT ===")
    print(classification_report(y, y_pred, digits=4))

    plot_confusion_matrix(cm)
    plot_feature_importance(model, encoders["feature_columns"])

    print("\nSaved figures:")
    print("- confusion_matrix.png")
    print("- feature_importance.png")


if __name__ == "__main__":
    main()