#!/usr/bin/python3
# As Clean Auxiliary Files, and also remove .synctex.gz (keeps PDF and .bbl).
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Resources"))
import texlib; texlib.cmd_clean("submission")
