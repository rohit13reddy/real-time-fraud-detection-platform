import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "creditcard.csv"

df = pd.read_csv(DATA_PATH)

print("Dataset shape:", df.shape)
print("\nFirst five rows:")
print(df.head())

print("\nClass distribution:")
print(df["Class"].value_counts())

print("\nMissing values:")
print(df.isnull().sum().sum())