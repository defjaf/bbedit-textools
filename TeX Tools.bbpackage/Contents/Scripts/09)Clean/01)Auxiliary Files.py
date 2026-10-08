#!/usr/bin/python3
# latexmk -c: remove aux files; keep PDF, SyncTeX and .bbl.
import sys; from pathlib import Path
sys.path.insert(0, str(next(d / "Resources" for d in Path(__file__).resolve().parents
                            if (d / "Resources" / "texlib.py").exists())))
import texlib; texlib.cmd_clean("aux")
