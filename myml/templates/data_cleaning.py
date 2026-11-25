# Description: Common pandas missing-value and duplicate cleaning steps
import pandas as pd
df = df.drop_duplicates().copy()
for column in df.select_dtypes(include="number"):
    df[column] = df[column].fillna(df[column].median())
for column in df.select_dtypes(exclude="number"):
    if df[column].isna().any():
        df[column] = df[column].fillna(df[column].mode().iloc[0])
print("Clean shape:", df.shape)
