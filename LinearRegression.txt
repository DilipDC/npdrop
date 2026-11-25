import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

#
df = pd.read_csv("data.csv")

df.dropna()
df.drop_duplicates()

df=pd.get_dummies(df,drop_first=True,dtype=int)

X = df.drop('Score',axis=1)
y = df["Score"]     

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LinearRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("Slope (m):", model.coef_[0])
print("Intercept (c):", model.intercept_)
print("MSE:", mean_squared_error(y_test, y_pred))
print("R2 Score:", r2_score(y_test, y_pred))

plt.scatter(X, y, color="blue", label="Actual Data")
plt.plot(X, model.predict(X), color="red", linewidth=2, label="Regression Line")
plt.xlabel(X.columns[0])
plt.ylabel(y.name)
plt.title("Linear Regression Fit")
plt.legend()
plt.show()

