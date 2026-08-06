#!/usr/bin/env python3
"""Startskript des Speichenrechners.

Laesst sich direkt aufrufen (``./speichenrechner.py``) und wird auch vom
Menueeintrag benutzt. Der Projektordner wird dabei selbst in den Suchpfad
gelegt, eine Installation per pip ist nicht noetig.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from speichenrechner.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
