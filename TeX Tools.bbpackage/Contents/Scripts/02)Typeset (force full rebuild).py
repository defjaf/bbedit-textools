#!/usr/bin/python3
# As Typeset, but latexmk -gg: rebuild everything from scratch.
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Resources"))
import texlib; texlib.cmd_typeset(force=True)
