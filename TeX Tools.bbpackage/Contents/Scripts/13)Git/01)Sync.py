#!/usr/bin/python3
# Commit your changes, pull --rebase (e.g. Overleaf web edits), push. Conflicts go to a results window.
import sys; from pathlib import Path
sys.path.insert(0, str(next(d / "Resources" for d in Path(__file__).resolve().parents
                            if (d / "Resources" / "texlib.py").exists())))
import texlib; texlib.cmd_git("sync")
