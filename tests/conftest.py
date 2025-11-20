# tests/conftest.py
#
# Dzięki temu Python widzi pakiet am_nasa w katalogu src/
# bez ruszania struktury repo.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
