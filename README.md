# TeX Tools for BBEdit

A TextMate-LaTeX-bundle-style workflow for [BBEdit](https://www.barebones.com/products/bbedit/) 16, built from three parts:

| Part | Does |
|---|---|
| **[texlab](https://github.com/latex-lsp/texlab)** (language server, configured by `texlab.json`) | inline errors/warnings from the `.log`, chktex lint, completion of `\ref`/`\cite`/packages, go to definition, find references, formatting |
| **TeX Tools.bbpackage** (Scripts menu → TeX Tools) | typeset with latexmk in the background; parse `.log`/`.blg` into a clickable BBEdit results browser; whole-project outline; SyncTeX forward search to Skim; root-file handling; cleanup; word count |
| **[Skim](https://skim-app.sourceforge.io)** | PDF preview, auto-reload, inverse search (⌘⇧-click → BBEdit) |

## Requirements

- macOS (Apple Silicon or Intel) and **BBEdit 16** (earlier versions with LSP support probably work but are untested).
- BBEdit's **command-line tools** (`bbedit`, `bbresults`): *BBEdit → Install Command Line Tools…*.
- **MacTeX / TeX Live** with `latexmk` (standard in MacTeX). `texcount` for Word Count and `chktex` for lint are included in full installs.
- **[Skim](https://skim-app.sourceforge.io)** in `/Applications`.
- **[texlab](https://github.com/latex-lsp/texlab)**: `brew install texlab`, then select it as the TeX language server in BBEdit (see below).
- Python: the system `/usr/bin/python3` (installed with the Xcode Command Line Tools). No other dependencies.

## Install

Either download the latest release zip from the [Releases page](https://github.com/defjaf/bbedit-textools/releases), unzip it and run `./install` from Terminal in the unzipped folder, or:

```sh
git clone https://github.com/defjaf/bbedit-textools.git
cd bbedit-textools
./install
```

`install` copies the package into BBEdit's `Packages` folder and `texlab.json` into `Language Servers/Configuration` (the iCloud-synced support folder if you use one). To update, pull or download again and rerun `./install`. If you hack on it, edit in the repo and rerun `./install`; edits to the installed copy are overwritten.

Then, once:

1. **BBEdit → Settings → Languages → TeX → Server**: select texlab and set *Configuration* to `texlab.json`. Relaunch BBEdit.
2. **Skim → Settings → Sync**: tick *Check for file changes*; Preset **BBEdit**.
3. **BBEdit → Settings → Menus & Shortcuts → Scripts → TeX Tools**: assign keys (e.g. ⌘R Typeset single pass, ⇧⌘R Typeset, ⌥⌘R View PDF, ⇧⌘O Project Outline).

## Commands

| Command | |
|---|---|
| Typeset | Saves modified documents and runs `latexmk` on the root file **without blocking BBEdit**: it reruns until references settle and runs BibTeX/biber/makeindex as needed. Afterwards: a notification with error/warning counts; a results browser listing every error, warning, bad box and BibTeX/biber problem (double-click jumps to the file and line, including `\input` files and `.bib` entries); on success, Skim scrolls to the cursor position. |
| Typeset (single pass) | One run of the engine only, like TextMate's ⌘R: the fastest feedback for text edits. New references/citations need a full Typeset (or Run BibTeX or Biber + another pass). |
| View PDF at Cursor | SyncTeX forward search into Skim. |
| Show Errors & Warnings | Re-parse the existing log without compiling. |
| Project Outline | Every `\part`…`\paragraph` and `\label` across the root file and all `\input`/`\include`/`\import` files, in document order, with numbers and pages from the `.aux` (e.g. `§ 2.1  Methods  ⟨sec:methods⟩`, `Figure 3  ⟨fig:setup⟩  p.4 — caption…`), in a window titled *Outline — file.tex* that is replaced on each run. Understands your own macros that wrap `\section` or `\label`. Click to jump. Typeset first for numbers. (BBEdit labels every entry "Note"; that can't be changed.) |
| More Builds ▸ Typeset (force full rebuild) | `latexmk -gg`; also clears latexmk's memory of earlier failures. |
| More Builds ▸ Run BibTeX or Biber | Runs whichever the document uses (from the `.aux`/`.bcf`) once and reports `.blg` problems. |
| Clean ▸ Auxiliary Files | `latexmk -c`: keeps PDF, SyncTeX and `.bbl`. |
| Clean ▸ For Submission | Also removes `.synctex.gz`; keeps PDF and `.bbl` (arXiv and journals need the `.bbl`). |
| Clean ▸ Everything | `latexmk -C` plus `.bbl`: sources only. |
| Open ▸ Root File / Log File | |
| Word Count | `texcount -inc` over the whole document. |

Each clean shows one notification listing the file types removed.

### Root file and engine

Put these at the top of any file (same convention as TeXShop, TextMate and VS Code):

```latex
% !TEX root = ../thesis.tex
% !TEX program = lualatex      % pdflatex (default) | lualatex | xelatex | latex
```

Without a `root` line, a file lacking `\documentclass` is matched to a sibling/parent `.tex` that `\input`s or `\include`s it. Project `latexmkrc` files are respected.

### Settings

Defaults are at the top of `TeX Tools.bbpackage/Contents/Resources/texlib.py`. Override any of them in `~/.config/bbedit-textools/settings.json`, which survives reinstalls:

```json
{
  "EXTRA_TEXINPUTS": ["~/texmf-local/inputs//"],
  "DEFAULT_PROGRAM": "lualatex",
  "SHOW_BADBOXES": false,
  "FORWARD_SEARCH_AFTER_TYPESET": true,
  "ACTIVATE_SKIM_ON_TYPESET": false
}
```

`texlab.json` keeps `build.onSave` off, so saving doesn't race the Typeset command. Set `chktex.onOpenAndSave` to `false` if lint is too noisy.

## Things texlab already gives you in BBEdit

- **Citations**: typing `\cite{` completes keys and filters by author/title; **⌘-double-click a cite key** (or *Go → Go to Definition*) opens the `.bib` entry; *Search → Find References to Selected Symbol* lists every place a key is cited.
- **Labels**: `\ref{` completion shows each label's number and caption; ⌘-double-click goes to the `\label`; *Edit → Rename Selected Symbol* renames a label everywhere.
- **Symbols**: *Search → Find Symbol in Workspace* searches sections, labels, figures and bib entries across the project.
- *Text → Reformat Document* runs `latexindent`.

## Troubleshooting

- Background typesetting errors are logged to `$TMPDIR/bbedit-textools.log`.
- **biber: "extracting arm64 binary with lipo failed"** on macOS 27: biber ≤ 2.21 calls `lipo -extract_family`, which the macOS 27 developer tools removed ([plk/biber#510](https://github.com/plk/biber/issues/510)). Biber 2.22 fixes it; update biber together with the matching biblatex:
  ```sh
  sudo tlmgr update biber biblatex
  ```
- **Nothing happens / a command fails silently**: BBEdit records script output in *Window → Unix Script Output* (or `~/Library/Containers/com.barebones.bbedit/Data/Library/Logs/BBEdit/Unix Script Output.log`); please include it in bug reports.
- Menu items missing after installing: relaunch BBEdit.

## Licence

MIT. The `.log` parsing approach owes a debt to the TextMate LaTeX bundle and to Nathan Grigg's [Latex.bbpackage](https://github.com/nathangrigg/Latex.bbpackage).
