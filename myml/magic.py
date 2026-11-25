"""Optional IPython %myml line magic and completion integration."""


def enable_magic():
    try:
        from IPython import get_ipython
        shell = get_ipython()
        if shell is None:
            return False
        try:
            shell.Completer.greedy = True
        except Exception:
            pass

        try:
            from .suggester import install_matcher
            install_matcher(shell)
        except Exception:
            pass

        if getattr(shell, "_myml_magic_registered", False):
            return True

        from IPython.core.magic import register_line_magic
        from .core import ask, list_templates

        @register_line_magic
        def myml(line):
            text = line.strip()
            if text:
                return ask(text)
            return list_templates()

        shell._myml_magic_registered = True
        return True
    except Exception:
        return False
