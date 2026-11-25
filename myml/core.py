"""Template discovery, delivery, and fuzzy matching."""
from __future__ import annotations
import difflib, html, keyword, re, sys
from pathlib import Path
from importlib import resources

def _template_files():
    root = resources.files(__package__).joinpath("templates")
    return {p.name[:-3]: p for p in root.iterdir() if p.name.endswith(".py") and not p.name.startswith("_")}

def template_names():
    return sorted(_template_files())

def _read(name):
    files = _template_files()
    if name not in files:
        raise KeyError(name)
    return files[name].read_text(encoding="utf-8")

def _description(code):
    for line in code.splitlines()[:8]:
        line=line.strip()
        if line.startswith("# Description:"):
            return line.partition(":")[2].strip()
        if line.startswith('"""') or line.startswith("'''"):
            return line.strip("\"' ").splitlines()[0][:180]
    return "Python starter template"

class Snippet:
    """A source snippet; access .code to retrieve text without executing it."""
    def __init__(self, name, code):
        self.name, self.code, self.description = name, code, _description(code)
    def show(self):
        _deliver(self.name, self.code)
        return self
    def insert(self, replace=False):
        try:
            from IPython import get_ipython
            shell=get_ipython()
            if shell:
                shell.set_next_input(self.code, replace=replace)
                print(f"Inserted {self.name} into the next cell.")
                return self
        except Exception:
            pass
        print(self.code)
        return self
    def save(self, filename):
        Path(filename).write_text(self.code, encoding="utf-8")
        return Path(filename)
    def __repr__(self):
        return f"Snippet({self.name!r}: {self.description})"

def get_template(name):
    return Snippet(name, _read(name))

def _deliver(name, code):
    if "google.colab" in sys.modules:
        try:
            from IPython.display import display, HTML
            escaped=html.escape(code)
            card=f"""<div style="border:1px solid #d0d7de;border-radius:10px;padding:14px;margin:8px 0;font-family:system-ui">
<h3 style="margin:0 0 8px">myml · {html.escape(name)}</h3><button onclick="navigator.clipboard.writeText(this.nextElementSibling.innerText).then(()=>this.innerText='Copied!')">Copy Code</button>
<pre style="white-space:pre-wrap;overflow:auto;max-height:520px;background:#f6f8fa;padding:12px;border-radius:6px"><code>{escaped}</code></pre></div>"""
            display(HTML(card)); return
        except Exception:
            pass
    try:
        from IPython import get_ipython
        shell=get_ipython()
        if shell:
            shell.set_next_input(code, replace=False)
            print(f"myml: {name} — {get_template(name).description}. Methods: .code, .show(), .insert(), .save().")
            return
    except Exception:
        pass
    print(code)

def list_templates():
    rows=[(n,_description(_read(n))) for n in template_names()]
    try:
        from IPython.display import display, HTML
        body="".join(f"<tr><td><code>{html.escape(n)}</code></td><td>{html.escape(d)}</td></tr>" for n,d in rows)
        display(HTML("<table><thead><tr><th>Template</th><th>Description</th></tr></thead><tbody>"+body+"</tbody></table>"))
    except Exception:
        for n,d in rows: print(f"{n:26} {d}")
    return rows

def ask(query):
    query=query.strip().lower()
    if not query: return list_templates()
    words=set(re.findall(r"[a-z0-9_]+",query))
    scored=[]
    for name in template_names():
        code=_read(name); desc=_description(code).lower()
        hay=(name.replace("_"," ")+" "+desc+" "+code[:3000].lower())
        overlap=len(words & set(re.findall(r"[a-z0-9_]+",hay)))/max(len(words),1)
        ratio=difflib.SequenceMatcher(None,query,name.replace("_"," ")).ratio()
        score=0.65*overlap+0.35*ratio
        if score>0.08: scored.append((score,name))
    scored.sort(reverse=True)
    if not scored: print("No matching templates. Try myml.list_templates()."); return None
    if len(scored)>1 and scored[0][0]-scored[1][0]<0.12:
        print("Suggestions: "+", ".join(n for _,n in scored[:4]))
    return get_template(scored[0][1]).show()
