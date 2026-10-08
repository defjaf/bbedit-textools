#!/usr/bin/python3
# Open the root (master) .tex file.
import sys; from pathlib import Path
sys.path.insert(0, str(next(d / "Resources" for d in Path(__file__).resolve().parents
                            if (d / "Resources" / "texlib.py").exists())))
import texlib; texlib.cmd_open_root()
