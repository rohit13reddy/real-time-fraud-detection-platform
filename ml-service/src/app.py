
from pathlib import Path
import json

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Locate the model files relative to this script.
BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "fraud_model.joblib"
THRESHOLD_PATH = BASE_DIR / "models" / "threshold.json"

# Load the model and threshold once when the API starts.
model = joblib.load(MODEL_PATH)

with open(THRESHOLD_PATH, "r") as file:
    threshold = json.load(file)["threshold"]

app = FastAPI(
    title="Real-Time Fraud Detection API",
    description="Predicts whether a transaction may be fraudulent.",
    version="1.0.0",
)

# Input features expected by the trained model.
FEATURE_NAMES = [
    "Time",
    *[f"V{i}" for i in range(1, 29)],
    "Amount",
]


class Transaction(BaseModel):
    Time: float = Field(ge=0)
    V1: float
    V2: float
    V3: float
    V4: float
    V5: float
    V6: float
    V7: float
    V8: float
    V9: float
    V10: float
    V11: float
    V12: float
    V13: float
    V14: float
    V15: float
    V16: float
    V17: float
    V18: float
    V19: float
    V20: float
    V21: float
    V22: float
    V23: float
    V24: float
    V25: float
    V26: float
    V27: float
    V28: float
    Amount: float = Field(ge=0)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(transaction: Transaction):
    # Convert the request into the exact feature order used in training.
    transaction_data = transaction.model_dump()
    features = pd.DataFrame(
        [[transaction_data[name] for name in FEATURE_NAMES]],
        columns=FEATURE_NAMES,
    )

    score = float(model.predict_proba(features)[0, 1])
    prediction = int(score >= threshold)

    return {
        "prediction": "fraud" if prediction == 1 else "legitimate",
        "fraud_score": round(score, 6),
        "threshold": round(threshold, 4),
    }
