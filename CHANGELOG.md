# Changelog

## 0.1.0 — 2026-10-20

First public release.

- Typeset (latexmk, in the background) and Typeset (single pass), with errors, warnings, bad boxes and BibTeX/biber problems in a clickable BBEdit results browser.
- Run BibTeX or Biber; Typeset (force full rebuild).
- SyncTeX forward search to Skim; inverse search via Skim's BBEdit preset.
- Project Outline across `\input`/`\include`/`\import` files, with numbers from the `.aux`, support for user macros that wrap `\section`/`\label`, and labelled items that weren't typeset marked *(not in PDF)*.
- Root-file and engine detection via `% !TEX root` / `% !TEX program`, or automatically: roots whose preamble is in an `\input` file, chains of includes, and several candidate roots (preferring the one last built from the file).
- Three cleanup levels with a summary notification; word count.
- texlab configuration for inline diagnostics, completion and navigation.
- Git ▸ Sync and Git ▸ Pull for Overleaf and other shared remotes: commit, pull --rebase, push, with conflicts in a clickable results window.
- Personal settings in `~/.config/bbedit-textools/settings.json`.
