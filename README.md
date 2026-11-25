# myml — verbatim notebook ML templates and code retrieval

myml provides seven reusable Python source templates and a full-block search engine for the personal ML/EDA code in myml/data/train.txt. Template imports read UTF-8 resources and insert their exact text into a fresh notebook cell; template code is never executed during import.

## Install

Git install:

~~~bash
pip install --upgrade git+https://github.com/DilipDC/npdrop.git
~~~

Windows ZIP install (PowerShell or Command Prompt):

~~~bash
py -m pip install --upgrade https://github.com/DilipDC/npdrop/archive/refs/heads/main.zip
~~~

Restart the notebook kernel after upgrading.

## Use the seven templates

Each import queues an untouched code block in the next editable cell in local Jupyter Notebook, JupyterLab, Notebook 7, and Google Colab.

~~~python
from myml import cluster
from myml import iqr
from myml import linear_regression
from myml import logistic_regression
from myml import model
from myml import tensorflow
from myml import token
~~~

Aliases are also supported:

~~~python
from myml import LinearRegression
from myml import LogisticRegression
from myml import tokenizer
~~~

Use myml.get_template("cluster").code to read source text without inserting a cell. Calling an import or accessing the template attribute again creates another cell.

Local Jupyter uses IPython's payload manager with source="set_next_input" and replace=False. Colab first tries google.colab._frontend.create_scratch_cell(code) and uses a one-click Copy card only if that API fails.

## Search complete code blocks with myml.sug()

The suggestion index is built exclusively from myml/data/train.txt using Python's standard library. Queries support identifier splitting, ML/EDA shorthand, generated acronyms, weighted BM25-style ranking, exact-phrase boosts, and typo-tolerant fuzzy matching.

~~~python
myml.sug()                        # print every parsed block with its number
myml.sug("km")                    # insert the best K-Means block
myml.sug("scatter plot")          # insert the matching scatter-plot block
myml.sug("hist")                  # histogram block
myml.sug("logistic regression")  # logistic-regression block
myml.sug("sactter plot")          # tolerate a typo
myml.sug("scatter plot", rank=2)  # insert the second-ranked match
~~~

A query returns the selected full multi-line source block and also queues that exact text into the next notebook cell. The function prints its selected rank and up to three alternative matches. myml.reload_index() rebuilds the index after train.txt is updated.

The training source is available only through myml.sug(); from myml import train is intentionally unsupported.

## Package contents

- myml/templates/: the seven verbatim import templates
- myml/data/train.txt: the separate EDA/ML suggestion source
- myml/__init__.pyi: static type declarations

The runtime package has no third-party dependencies. IPython is optional for notebook insertion; ML libraries referenced by inserted template code are needed only when those cells are executed.

## Tests

~~~bash
python -m pip install -e ".[test]"
python -m pytest -q
~~~
