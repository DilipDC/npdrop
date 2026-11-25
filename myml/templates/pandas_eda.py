# Description: Quick exploratory data analysis with pandas
import pandas as pd
df = pd.read_csv("data.csv")
display(df.head())
print(df.shape, df.info())
display(df.describe(include="all").T)
print("Missing values:\n", df.isna().sum().sort_values(ascending=False))
