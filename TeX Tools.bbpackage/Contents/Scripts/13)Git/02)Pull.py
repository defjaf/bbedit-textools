#!/usr/bin/python3
# Pull --rebase --autostash only: bring in others' edits without committing yours.
import sys; from pathlib import Path
sys.path.insert(0, str(next(d / "Resources" for d in Path(__file__).resolve().parents
                            if (d / "Resources" / "texlib.py").exists())))
import texlib; texlib.cmd_git("pull")
