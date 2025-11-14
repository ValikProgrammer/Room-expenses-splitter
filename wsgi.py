"""
WSGI wrapper for Gunicorn / Railway.
Tries common module names to locate a Flask `app` instance.
"""
from importlib import import_module

CANDIDATES = [
    "server",
    "app",
    "src.server",
    "src.app",
    "main",
    "project.server",
]

app = None
for mod_name in CANDIDATES:
    try:
        mod = import_module(mod_name)
    except ModuleNotFoundError:
        continue
    if hasattr(mod, "app"):
        app = getattr(mod, "app")
        break

if app is None:
    raise RuntimeError(
        "Could not find a Flask `app` instance. Ensure your app exports `app` from server.py or add its module name to wsgi.CANDIDATES."
    )