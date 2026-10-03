"""
cPanel entry point. Phusion Passenger imports `application` from this file.

- Environment variables come from cPanel > Setup Python App (settings.py does not read .env).
- Restart after deploying: touch tmp/restart.txt (or "Restart" in the cPanel UI).
- Passenger is WSGI-only: WebSockets (asgi.py / Channels) are not served here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")

from course_recomeder_backend.wsgi import application


# import importlib.machinery
# import importlib.util
# import os
# import sys


# sys.path.insert(0, os.path.dirname(__file__))

# def load_source(modname, filename):
#     loader = importlib.machinery.SourceFileLoader(modname, filename)
#     spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
#     module = importlib.util.module_from_spec(spec)
#     loader.exec_module(module)
#     return module

# wsgi = load_source('wsgi', 'passenger_wsgi.py')
# application = wsgi.application
