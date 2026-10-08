#!/usr/bin/python3
# Parse the existing .log/.blg into a BBEdit results browser.
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Resources"))
import texlib; texlib.cmd_show_issues()
