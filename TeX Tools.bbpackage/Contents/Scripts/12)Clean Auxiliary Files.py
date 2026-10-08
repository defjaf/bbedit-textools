#!/usr/bin/python3
# latexmk -c: remove aux files; keep PDF, SyncTeX and .bbl.
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Resources"))
import texlib; texlib.cmd_clean("aux")
