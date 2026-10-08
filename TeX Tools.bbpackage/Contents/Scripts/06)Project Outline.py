#!/usr/bin/python3
# Sections and labels across the whole project, in document order, with numbers from the .aux.
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Resources"))
import texlib; texlib.cmd_outline()
