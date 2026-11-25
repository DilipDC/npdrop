# Description: Reusable train-test evaluation helpers for sklearn estimators
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
def train_evaluate(estimator, X, y, test_size=0.2, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    estimator.fit(X_train, y_train)
    predictions = estimator.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, predictions))
    print(classification_report(y_test, predictions))
    return estimator
