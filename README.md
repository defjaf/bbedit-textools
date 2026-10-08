# TeX Tools for BBEdit

A TextMate-LaTeX-bundle-style workflow for [BBEdit](https://www.barebones.com/products/bbedit/) 16, built from three parts:

| Part | Does |
|---|---|
| **[texlab](https://github.com/latex-lsp/texlab)** (language server, configured by `texlab.json`) | inline errors/warnings from the `.log`, chktex lint, completion of `\ref`/`\cite`/packages, go to definition, find references, formatting |
| **TeX Tools.bbpackage** (Scripts menu → TeX Tools) | typeset with latexmk in the background; parse `.log`/`.blg` into a clickable BBEdit results browser; whole-project outline; SyncTeX forward search to Skim; root-file handling; cleanup; word count |
| **[Skim](https://skim-app.sourceforge.io)** | PDF preview, auto-reload, inverse search (⌘⇧-click → BBEdit) |

Requirements: macOS, BBEdit 16 (with its `bbedit`/`bbresults` command-line tools installed), MacTeX/TeX Live (latexmk), Skim, texlab (`brew install texlab`). Everything else uses the system `/usr/bin/python3`.

## Install

```sh
git clone https://github.com/defjaf/bbedit-textools.git
cd bbedit-textools
./install
```

`install` copies the package into BBEdit's `Packages` folder and `texlab.json` into `Language Servers/Configuration` (the iCloud-synced support folder if you use one). Edit files here in the repo, then rerun `./install`.

Then, once:

1. **BBEdit → Settings → Languages → TeX → Server**: select texlab and set *Configuration* to `texlab.json`. Relaunch BBEdit.
2. **Skim → Settings → Sync**: tick *Check for file changes*; Preset **BBEdit**.
3. **BBEdit → Settings → Menus & Shortcuts → Scripts → TeX Tools**: assign keys (e.g. ⌘R Typeset, ⌥⌘R View PDF, ⇧⌘O Project Outline).

## Commands

| Command | |
|---|---|
| Typeset | Saves modified documents and runs `latexmk` on the root file **without blocking BBEdit**. Afterwards: a notification with error/warning counts; a results browser listing every error, warning, bad box and BibTeX/biber problem (double-click jumps to the file and line, including `\input` files and `.bib` entries); on success, Skim scrolls to the cursor position. |
| Typeset (force full rebuild) | Same, with `latexmk -gg`. |
| View PDF at Cursor | SyncTeX forward search into Skim. |
| Show Errors & Warnings | Re-parse the existing log without compiling. |
| Project Outline | Every `\part`…`\paragraph` and `\label` across the root file and all `\input`/`\include`/`\import` files, in document order, with numbers and pages from the `.aux` (e.g. `2.1 Methods`, `⟨fig:setup⟩ Figure 3 p.4 — caption…`). Click to jump. Typeset first for numbers. |
| Open Log File / Open Root File | |
| Word Count | `texcount -inc` over the whole document. |
| Clean Auxiliary Files | `latexmk -c`: keeps PDF, SyncTeX and `.bbl`. |
| Clean for Submission | Also removes `.synctex.gz`; keeps PDF and `.bbl` (arXiv and journals need the `.bbl`). |
| Clean Everything | `latexmk -C` plus `.bbl`: sources only. |

Each clean shows one notification listing the file types removed.

### Root file and engine

Put these at the top of any file (same convention as TeXShop, TextMate and VS Code):

```latex
% !TEX root = ../thesis.tex
% !TEX program = lualatex      % pdflatex (default) | lualatex | xelatex | latex
```

Without a `root` line, a file lacking `\documentclass` is matched to a sibling/parent `.tex` that `\input`s or `\include`s it. Project `latexmkrc` files are respected.

### Settings

At the top of `TeX Tools.bbpackage/Contents/Resources/texlib.py`: extra `TEXINPUTS` directories, default engine, whether to list bad boxes, whether Typeset syncs/activates Skim.

`texlab.json` keeps `build.onSave` off, so saving doesn't race the Typeset command. Set `chktex.onOpenAndSave` to `false` if lint is too noisy.

## Things texlab already gives you in BBEdit

- **Citations**: typing `\cite{` completes keys and filters by author/title; **⌘-double-click a cite key** (or *Go → Go to Definition*) opens the `.bib` entry; *Search → Find References to Selected Symbol* lists every place a key is cited.
- **Labels**: `\ref{` completion shows each label's number and caption; ⌘-double-click goes to the `\label`; *Edit → Rename Selected Symbol* renames a label everywhere.
- **Symbols**: *Search → Find Symbol in Workspace* searches sections, labels, figures and bib entries across the project.
- *Text → Reformat Document* runs `latexindent`.

## Troubleshooting

- Background typesetting errors are logged to `$TMPDIR/bbedit-textools.log`.
- **biber: "extracting arm64 binary with lipo failed"** (seen with TeX Live 2026 on recent macOS): the universal biber can't detect the architecture. Replace it with its arm64 slice:
  ```sh
  cd /usr/local/texlive/2026/bin/universal-darwin
  sudo cp biber biber.universal-backup && sudo lipo biber.universal-backup -thin arm64 -output biber
  ```
  A `tlmgr update` of biber may undo this.

## Licence

MIT. The `.log` parsing approach owes a debt to the TextMate LaTeX bundle and to Nathan Grigg's [Latex.bbpackage](https://github.com/nathangrigg/Latex.bbpackage).
