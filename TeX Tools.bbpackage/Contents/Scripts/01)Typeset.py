#!/usr/bin/python3
# Save, run latexmk on the root file in the background, report errors, sync Skim.
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Resources"))
import texlib; texlib.cmd_typeset()
