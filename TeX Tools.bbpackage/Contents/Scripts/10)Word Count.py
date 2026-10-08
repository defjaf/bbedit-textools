#!/usr/bin/python3
# texcount over the root file and its includes.
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Resources"))
import texlib; texlib.cmd_word_count()
