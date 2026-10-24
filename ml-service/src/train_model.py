
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "creditcard.csv"
MODEL_PATH = BASE_DIR / "models" / "fraud_model.joblib"
THRESHOLD_PATH = BASE_DIR / "models" / "threshold.json"

# ---------- 1. Load and order data ----------
print("Loading dataset...")
df = pd.read_csv(DATA_PATH)
df = df.sort_values("Time").reset_index(drop=True)

# Chronological split: 70% train, 15% validation, 15% test
n = len(df)
train_end = int(n * 0.70)
validation_end = int(n * 0.85)

train_df = df.iloc[:train_end]
validation_df = df.iloc[train_end:validation_end]
test_df = df.iloc[validation_end:]

X_train = train_df.drop(columns=["Class"])
y_train = train_df["Class"]

X_val = validation_df.drop(columns=["Class"])
y_val = validation_df["Class"]

X_test = test_df.drop(columns=["Class"])
y_test = test_df["Class"]

print("\nDataset split")
print("Training rows:", len(train_df))
print("Validation rows:", len(validation_df))
print("Test rows:", len(test_df))
print("Training frauds:", int(y_train.sum()))
print("Validation frauds:", int(y_val.sum()))
print("Test frauds:", int(y_test.sum()))

# ---------- 2. Train model ----------

model = Pipeline([
    ("classifier", HistGradientBoostingClassifier(
        learning_rate=0.1,
        max_iter=100,
        max_leaf_nodes=31,
        class_weight="balanced",
        random_state=42
    )),
])


if not np.isfinite(X_train.to_numpy()).all():
    raise ValueError("Training data contains NaN or infinite values.")

if not np.isfinite(X_val.to_numpy()).all():
    raise ValueError("Validation data contains NaN or infinite values.")

if not np.isfinite(X_test.to_numpy()).all():
    raise ValueError("Test data contains NaN or infinite values.")

print("\nTraining model...")
model.fit(X_train, y_train)

# ---------- 3. Select threshold using validation data ----------
# print("\nSelecting threshold on validation data...")
# val_scores = model.predict_proba(X_val)[:, 1]


print("\nChecking numerical stability...")

print(
    "Training data finite:",
    np.isfinite(X_train.to_numpy()).all()
)
print(
    "Validation data finite:",
    np.isfinite(X_val.to_numpy()).all()
)
print(
    "Test data finite:",
    np.isfinite(X_test.to_numpy()).all()
)

print("\nSelecting threshold on validation data...")
val_scores = model.predict_proba(X_val)[:, 1]

print(
    "Validation scores finite:",
    np.isfinite(val_scores).all()
)
print(
    "Validation score range:",
    val_scores.min(),
    "to",
    val_scores.max()
)


# Test a range of thresholds and choose the one with best validation F1.
thresholds = np.arange(0.05, 0.951, 0.01)
best_threshold = 0.5
best_f1 = -1.0

for threshold in thresholds:
    val_pred = (val_scores >= threshold).astype(int)
    score = f1_score(y_val, val_pred, zero_division=0)

    if score > best_f1:
        best_f1 = score
        best_threshold = float(threshold)

print(f"Selected threshold: {best_threshold:.2f}")
print(f"Validation F1-score: {best_f1:.4f}")

# ---------- 4. Final evaluation on untouched test data ----------
print("\nEvaluating on final test set...")
test_scores = model.predict_proba(X_test)[:, 1]
test_pred = (test_scores >= best_threshold).astype(int)

print("\n===== TEST CONFUSION MATRIX =====")
print(confusion_matrix(y_test, test_pred, labels=[0, 1]))

print("\n===== TEST CLASSIFICATION REPORT =====")
print(classification_report(
    y_test,
    test_pred,
    labels=[0, 1],
    target_names=["Legitimate", "Fraud"],
    zero_division=0,
))

print("Test average precision:",
      round(average_precision_score(y_test, test_scores), 4))
print("Test precision:", round(
    precision_score(y_test, test_pred, zero_division=0), 4
))
print("Test recall:", round(
    recall_score(y_test, test_pred, zero_division=0), 4
))
print("Test F1-score:", round(
    f1_score(y_test, test_pred, zero_division=0), 4
))

# ---------- 5. Save model and selected threshold ----------
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(model, MODEL_PATH)

with open(THRESHOLD_PATH, "w") as file:
    json.dump({"threshold": best_threshold}, file, indent=2)

print("\nModel saved to:", MODEL_PATH)
print("Threshold saved to:", THRESHOLD_PATH)
print("Training and evaluation complete!")
