#!/usr/bin/python3
"""Root-file detection tests. Run:  /usr/bin/python3 tests/test_find_root.py"""
import os, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "TeX Tools.bbpackage/Contents/Resources"))
import texlib

def write(root, rel, text=""):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return p

def main():
    t = Path(tempfile.mkdtemp()).resolve()
    # 1. ordinary root with \documentclass and an \input in a subfolder
    write(t, "a/main.tex", "\\documentclass{article}\\begin{document}\\input{ch/one}\\bibliography{refs}\\end{document}")
    write(t, "a/ch/one.tex", "Text.")
    write(t, "a/refs.bib", "@book{x, title={y}}")
    # 2. explicit % !TEX root wins over anything else
    write(t, "b/main.tex", "\\documentclass{article}\\begin{document}\\end{document}")
    write(t, "b/other.tex", "\\documentclass{article}\\begin{document}\\input{part}\\end{document}")
    write(t, "b/part.tex", "% !TEX root = main.tex\nText.")
    # 3. preamble in an \input file: root has only \end{document} (like the Information Theory notes)
    write(t, "c/macros.tex", "\\documentclass{article}\n\\begin{document}\n")
    write(t, "c/notes.tex", "\\input{macros.tex}\n\\input{sections/sec1.tex}\n\\end{document}\n")
    write(t, "c/sections/sec1.tex", "\\section{One}")
    # 4. several roots include the same file: prefer the one whose .fls lists it, else newest PDF
    write(t, "d/sections/s.tex", "Text.")
    for name in ("draft", "notes", "week1"):
        write(t, f"d/{name}.tex", "\\documentclass{article}\\begin{document}\\input{sections/s}\\end{document}")
    write(t, "d/week1.pdf", "x"); time.sleep(0.01); write(t, "d/draft.pdf", "x")
    write(t, "d/notes.fls", f"PWD {t}/d\nINPUT ./sections/s.tex\n")
    # 5. chain: root includes part/part.tex which includes part/sub.tex
    write(t, "e/book.tex", "\\documentclass{book}\\begin{document}\\include{part/part}\\end{document}")
    write(t, "e/part/part.tex", "\\input{part/sub}")
    write(t, "e/part/sub.tex", "Deep.")
    # 6. \import{dir}{file}
    write(t, "f/main.tex", "\\documentclass{article}\\usepackage{import}\\begin{document}\\import{figs/}{fig.tex}\\end{document}")
    write(t, "f/figs/fig.tex", "Fig.")
    # 7. stand-alone file with no root anywhere
    write(t, "g/lonely.tex", "Just text.")
    # 8. commented-out \input must not count
    write(t, "h/main.tex", "\\documentclass{article}\\begin{document}%\\input{x}\n\\end{document}")
    write(t, "h/x.tex", "Text.")

    cases = [("a/ch/one.tex", "a/main.tex"), ("a/refs.bib", "a/main.tex"), ("a/main.tex", "a/main.tex"),
             ("b/part.tex", "b/main.tex"), ("c/sections/sec1.tex", "c/notes.tex"), ("c/notes.tex", "c/notes.tex"),
             ("d/sections/s.tex", "d/notes.tex"), ("e/part/sub.tex", "e/book.tex"),
             ("f/figs/fig.tex", "f/main.tex"), ("g/lonely.tex", "g/lonely.tex"), ("h/x.tex", "h/x.tex")]
    failed = 0
    for src, want in cases:
        got = texlib.find_root(t / src)
        ok = got == (t / want).resolve()
        failed += not ok
        print(("ok  " if ok else "FAIL"), f"{src:22s} -> {got.relative_to(t)}" + ("" if ok else f"   (want {want})"))
    # 4b. without the .fls, the newest PDF wins
    (t / "d/notes.fls").unlink()
    got = texlib.find_root(t / "d/sections/s.tex"); ok = got.name == "draft.tex"; failed += not ok
    print(("ok  " if ok else "FAIL"), f"{'d/sections/s.tex (no .fls)':22s} -> {got.relative_to(t)}")
    print("all passed" if not failed else f"{failed} failed")
    return failed

if __name__ == "__main__":
    sys.exit(main())
