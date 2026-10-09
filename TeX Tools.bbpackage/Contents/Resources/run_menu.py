#!/usr/bin/python3
# Called (in the background) by the "#!•Run" menu attachment script when ⌘R
# is used on a TeX document. Not a menu item itself.
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import texlib; texlib.cmd_run_menu()
