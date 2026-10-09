# Changelog

## 0.1.0 — 2026-10-08

First public release.

- Typeset (latexmk, in the background) and Typeset (single pass), with errors, warnings, bad boxes and BibTeX/biber problems in a clickable BBEdit results browser.
- Run BibTeX or Biber; Typeset (force full rebuild).
- SyncTeX forward search to Skim; inverse search via Skim's BBEdit preset.
- Project Outline across `\input`/`\include`/`\import` files, with numbers from the `.aux` and support for user macros that wrap `\section`/`\label`.
- Root-file and engine detection via `% !TEX root` / `% !TEX program`.
- Three cleanup levels with a summary notification; word count.
- texlab configuration for inline diagnostics, completion and navigation.
- Personal settings in `~/.config/bbedit-textools/settings.json`.
