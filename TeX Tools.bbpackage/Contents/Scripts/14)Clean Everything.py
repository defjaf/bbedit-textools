#!/usr/bin/python3
# latexmk -C and .bbl: leave only sources.
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Resources"))
import texlib; texlib.cmd_clean("all")
