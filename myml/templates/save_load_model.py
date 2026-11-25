# Description: Save and load a trained scikit-learn model using joblib
import joblib
joblib.dump(model, "model.joblib")
loaded_model = joblib.load("model.joblib")
print("Loaded model ready:", type(loaded_model).__name__)
