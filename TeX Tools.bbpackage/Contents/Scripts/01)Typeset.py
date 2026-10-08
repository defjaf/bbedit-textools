#!/usr/bin/python3
# latexmk on the root file in the background: reruns until references settle, runs BibTeX/biber as needed.
import sys; from pathlib import Path
sys.path.insert(0, str(next(d / "Resources" for d in Path(__file__).resolve().parents
                            if (d / "Resources" / "texlib.py").exists())))
import texlib; texlib.cmd_typeset()
