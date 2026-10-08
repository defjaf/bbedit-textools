#!/usr/bin/python3
# latexmk -gg: rebuild everything from scratch (also clears latexmk's memory of earlier failures).
import sys; from pathlib import Path
sys.path.insert(0, str(next(d / "Resources" for d in Path(__file__).resolve().parents
                            if (d / "Resources" / "texlib.py").exists())))
import texlib; texlib.cmd_typeset(force=True)
