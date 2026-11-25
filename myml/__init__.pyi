"""Generated template attribute declarations for editor completion."""
from typing import Any, List, Optional
from .core import Snippet

all_model: Snippet  # Decision tree and support vector machine classification examples
cluster: Snippet  # K-means clustering with WCSS elbow plot and cluster visualization
iqr: Snippet  # IQR and standard-deviation based outlier treatment examples
linear_regression: Snippet  # Linear regression training, evaluation, and regression-line visualization
logistic_regression: Snippet  # Logistic regression classification, evaluation, and sigmoid visualization
tensorflow: Snippet  # TensorFlow import, version check, and reproducible setup
token: Snippet  # Basic text tokenization with TensorFlow Keras
LinearRegression: Snippet  # Alias for linear_regression
LogisticRegression: Snippet  # Alias for logistic_regression
tokenizer: Snippet  # Alias for token

def suggest(prefix: str = '', previous_line: Optional[str] = None, limit: int = 15) -> List[str]: ...
def reload_index() -> Any: ...
