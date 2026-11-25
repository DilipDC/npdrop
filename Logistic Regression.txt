import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

df = pd.read_csv("data.csv")

X = df[["Hours"]]    
y = df["Passed"]   

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LogisticRegression()
model.fit(X_train, y_train)


y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred))

x_grid = np.linspace(X.iloc[:, 0].min(), X.iloc[:, 0].max(), 200).reshape(-1, 1)
prob_grid = model.predict_proba(x_grid)[:, 1]

plt.scatter(X, y, color="blue", label="Actual Class (0 / 1)")
plt.plot(x_grid, prob_grid, color="red", linewidth=2, label="Predicted Probability (Class 1)")
plt.axhline(0.5, color="gray", linestyle="--", label="Decision Threshold (0.5)")
plt.xlabel(X.columns[0])
plt.ylabel("Probability / Target Class")
plt.title("Logistic Regression Sigmoid Curve")
plt.legend()
plt.show()