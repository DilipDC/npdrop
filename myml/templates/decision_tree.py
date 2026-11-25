# Description: Decision tree classification starter example
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = DecisionTreeClassifier(max_depth=5, random_state=42).fit(X_train, y_train)
print("Accuracy:", accuracy_score(y_test, model.predict(X_test)))
