#!/usr/bin/python3
# Open the root file's .log.
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Resources"))
import texlib; texlib.cmd_open_log()
