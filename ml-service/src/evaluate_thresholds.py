
from pathlib import Path

import joblib
import pandas as pd

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    average_precision_score,
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "creditcard.csv"
MODEL_PATH = BASE_DIR / "models" / "fraud_model.joblib"

# Load the trained model and data
model = joblib.load(MODEL_PATH)
df = pd.read_csv(DATA_PATH)

# Keep the same chronological test split used in train_model.py
df = df.sort_values("Time").reset_index(drop=True)
split_index = int(len(df) * 0.80)
test_df = df.iloc[split_index:]

X_test = test_df.drop(columns=["Class"])
y_test = test_df["Class"]

# Obtain fraud scores (probabilities)
y_scores = model.predict_proba(X_test)[:, 1]

print("Average precision:", round(
    average_precision_score(y_test, y_scores), 4
))

# Evaluate different thresholds
thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

print("\nThreshold comparison")
print("-" * 90)
print(
    f"{'Threshold':>10} {'Precision':>10} {'Recall':>10} "
    f"{'F1':>10} {'False alarms':>14} {'Frauds caught':>14}"
)

for threshold in thresholds:
    y_pred = (y_scores >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_test, y_pred, labels=[0, 1]
    ).ravel()

    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    print(
        f"{threshold:>10.1f} {precision:>10.3f} {recall:>10.3f} "
        f"{f1:>10.3f} {fp:>14} {tp:>14}"
    )
