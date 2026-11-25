"""Optional IPython %myml magic and completion."""
def enable_magic():
    try:
        from IPython import get_ipython
        shell=get_ipython()
        if shell is None: return
        try: shell.Completer.greedy=True
        except Exception: pass
        if getattr(shell,"_myml_magic_registered",False): return
        from IPython.core.magic import register_line_magic
        from .core import ask, template_names
        @register_line_magic
        def myml(line):
            name=line.strip()
            if name: return ask(name)
            from .core import list_templates
            return list_templates()
        try:
            completer=shell.Completer
            def complete(text, line, cursor_pos):
                return [n for n in template_names() if n.startswith(text)]
            completer.custom_matchers.append(lambda context: [])
            shell.set_hook("complete_command", complete, str_key="%myml")
        except Exception:
            pass
        shell._myml_magic_registered=True
    except Exception:
        return
