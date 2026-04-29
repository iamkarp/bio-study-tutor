"""Package shim. Connect/shinyapps imports `app` (the package) and looks for
an `app` attribute. Load the actual Shiny app from app/app.py and expose it.
"""
from __future__ import annotations

import importlib.util as _u
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

_spec = _u.spec_from_file_location("_bio_app_main", _DIR / "app.py")
_mod = _u.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

app = _mod.app
