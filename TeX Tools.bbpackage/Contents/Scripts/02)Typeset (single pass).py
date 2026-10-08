#!/usr/bin/python3
# One run of the engine only (like TextMate's Cmd-R): fastest feedback; references may need a full Typeset.
import sys; from pathlib import Path
sys.path.insert(0, str(next(d / "Resources" for d in Path(__file__).resolve().parents
                            if (d / "Resources" / "texlib.py").exists())))
import texlib; texlib.cmd_typeset_single()
