# Test .csv data file
import pandas as pd

FILE_NAME = "smart_home_iot.csv"

df = pd.read_csv(FILE_NAME)

print("=== FIRST 5 ROWS ===")
print(df.head())

print("\n=== SHAPE ===")
print(df.shape)

print("\n=== COLUMN NAMES ===")
print(df.columns.tolist())

print("\n=== LABEL COUNTS ===")
print(df["label"].value_counts())

print("\n=== DEVICE TYPES ===")
print(df["device_type"].value_counts())

print("\n=== MISSING VALUES ===")
print(df.isnull().sum())