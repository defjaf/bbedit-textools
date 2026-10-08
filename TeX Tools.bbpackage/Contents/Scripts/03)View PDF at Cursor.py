#!/usr/bin/python3
# SyncTeX forward search: show the cursor position in Skim.
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Resources"))
import texlib; texlib.cmd_view()
