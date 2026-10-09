#!/usr/bin/python3
# Bind this to ⌘R (and remove ⌘R from #! → Run): typesets TeX documents,
# and chooses BBEdit's own #! → Run for everything else.
import sys; from pathlib import Path
sys.path.insert(0, str(next(d / "Resources" for d in Path(__file__).resolve().parents
                            if (d / "Resources" / "texlib.py").exists())))
import texlib; texlib.cmd_typeset_or_run()
