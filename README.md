# myml — ML Code Templates for Jupyter

A lightweight Python snippet library: import a template, and myml delivers its source code into your notebook. Templates are never executed during lookup.

## Install

```bash
pip install git+https://github.com/DilipDC/npdrop.git
```

Restart/import in your notebook:
```python
from myml import tensorflow
```
In local Jupyter this queues an editable cell. In Google Colab it displays a copyable code card. Also use `%myml tensorflow`, `myml.ask("linear model")`, `myml.list_templates()`, or `snippet.code`.

## Add templates
Place any `.py` file in `myml/templates/`; its first comment should be `# Description: ...`. Discovery and magic completion update dynamically. Regenerate static IDE hints with `python scripts/generate_stubs.py`.

## Requirements
Python 3.9+, standard library; IPython is optional and used when available. Templates may require their respective ML libraries.
