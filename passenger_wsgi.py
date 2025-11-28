import os
import sys

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
paths = [
    APP_ROOT,
    os.path.join(APP_ROOT, "app"),
    "/home/qircuitc/repositories/QircuitLearn",
    "/home/qircuitc/repositories/QircuitLearn/app",
    "/home/qircuitc/qircuitapp",
    "/home/qircuitc/qircuitapp/app",
]
for p in paths:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

from app import create_app

application = create_app()
