# myml — notebook ML source templates

myml is a lightweight, pip-installable package for inserting reusable machine-learning code into Jupyter Notebook, JupyterLab, Notebook 7, and Google Colab. Template files are read as text through importlib.resources; importing a template never executes the template's ML code.

## Install or upgrade

~~~bash
pip install --upgrade --force-reinstall git+https://github.com/DilipDC/npdrop.git
~~~

Restart the notebook kernel after upgrading. In a notebook, importing a template creates a new editable code cell containing the source:

~~~python
from myml import all_model
from myml import iqr, cluster  # queues one next-cell payload per template
~~~

In local Jupyter, myml uses IPython's payload manager with single=False. In Colab, it first requests a scratch cell and uses a one-click copy card only when that API is unavailable.

## Included templates

| Import | Description |
|---|---|
| from myml import all_model | Decision tree and support vector machine examples |
| from myml import cluster | K-means clustering, WCSS plot, and cluster scatter plot |
| from myml import iqr | IQR and standard-deviation outlier-treatment code |
| from myml import linear_regression | Linear regression training, metrics, and plot |
| from myml import LinearRegression | Alias for linear_regression |
| from myml import logistic_regression | Logistic regression classification and sigmoid plot |
| from myml import LogisticRegression | Alias for logistic_regression |
| from myml import tensorflow | TensorFlow import, version, and seed setup |
| from myml import token | Keras text tokenizer example |
| from myml import tokenizer | Alias for token |

Access the code without triggering cell insertion with myml.get_template("cluster").code.

## Base-code completion

The standard-library suggestion index is built from every myml/templates/*.py file at import time. It indexes template names and aliases, AST identifiers and dotted calls, meaningful source lines, and immediate next-line transitions. It registers an IPython v2 matcher without suppressing Jedi or built-in completion.

~~~python
myml.suggest("pd.read")
myml.suggest("from myml import ")
myml.suggest("model.", previous_line="model = LinearRegression()")
myml.reload_index()  # refresh after adding/editing template files
~~~

The %myml line magic also supports template names and Tab completion.

## Add a template

Add a .py file under myml/templates/. Put a short description in its first line:

~~~python
# Description: What this code snippet demonstrates
~~~

Call myml.reload_index() to rebuild suggestions in the current kernel, and regenerate static IDE declarations with:

~~~bash
python scripts/generate_stubs.py
~~~

## Requirements

Python 3.9+. Runtime code uses only the Python standard library. IPython is optional and is needed for notebook cell delivery and live Tab integration. Templates may require their respective machine-learning dependencies when you execute the inserted code.
