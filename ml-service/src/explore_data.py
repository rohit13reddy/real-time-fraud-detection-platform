
from pathlib import Path
import pandas as pd

# Load the dataset
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "creditcard.csv"
df = pd.read_csv(DATA_PATH)

# 1. Basic information
print("\n===== DATASET OVERVIEW =====")
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())

# 2. Check missing values
print("\n===== MISSING VALUES =====")
print("Total missing values:", df.isnull().sum().sum())

# 3. Count legitimate vs fraudulent transactions
print("\n===== TRANSACTION COUNTS =====")
print(df["Class"].value_counts())

# 4. Percentage of each class
print("\n===== CLASS DISTRIBUTION (%) =====")
print((df["Class"].value_counts(normalize=True) * 100).round(4))

# 5. Compare transaction amounts
print("\n===== AMOUNT STATISTICS =====")
print(df.groupby("Class")["Amount"].describe())

# 6. Check duplicate rows
print("\n===== DUPLICATES =====")
print("Duplicate rows:", df.duplicated().sum())
