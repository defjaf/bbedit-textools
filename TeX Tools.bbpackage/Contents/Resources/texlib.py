"""Shared machinery for the TeX Tools BBEdit package.

Every menu script is a thin stub that calls one of the `cmd_*` functions
below.  Long-running work (latexmk) is detached from BBEdit so the editor
never blocks; results come back as a notification, a BBEdit results
browser (via bbresults), and a SyncTeX jump in Skim.

Requires only the macOS system python3 (3.9+).
"""

import fcntl
import hashlib
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# --------------------------------------------------------------------------
# User settings — edit to taste.
# --------------------------------------------------------------------------

# Extra directories searched for .sty/.cls/.bst etc. (a trailing // means
# "and all subdirectories").  The empty entry keeps the system defaults.
EXTRA_TEXINPUTS = ["~/home/tex/inputs//"]

# Default engine when the root file has no "% !TEX program = ..." line.
DEFAULT_PROGRAM = "pdflatex"

# Show over/underfull box messages in the results browser?
SHOW_BADBOXES = True

# After a successful typeset, jump Skim to the cursor position.
FORWARD_SEARCH_AFTER_TYPESET = True

# Bring Skim to the front on typeset (False keeps BBEdit focused).
ACTIVATE_SKIM_ON_TYPESET = False

TEXBIN = "/Library/TeX/texbin"
DISPLAYLINE = "/Applications/Skim.app/Contents/SharedSupport/displayline"
BBRESULTS = "/usr/local/bin/bbresults"
BBEDIT = "/usr/local/bin/bbedit"

LATEXMK_ENGINE_FLAG = {
    "pdflatex": "-pdf",
    "lualatex": "-lualatex",
    "xelatex": "-xelatex",
    "latex": "-pdfdvi",
}

TEX_SUFFIXES = {".tex", ".ltx", ".latex"}

# --------------------------------------------------------------------------
# Talking to BBEdit
# --------------------------------------------------------------------------


def osascript(script):
    r = subprocess.run(["/usr/bin/osascript", "-e", script],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.rstrip("\n")


def notify(message, title="TeX Tools", sound=None):
    esc = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')
    script = f'display notification "{esc(message)}" with title "{esc(title)}"'
    if sound:
        script += f' sound name "{sound}"'
    try:
        osascript(script)
    except RuntimeError:
        pass


def front_document(save=True):
    """Save modified on-disk documents; return (path, line) of the front one."""
    save_part = """
        repeat with d in (every text document whose modified is true)
            try
                if on disk of d then save d
            end try
        end repeat
    """ if save else ""
    script = f"""
    tell application "BBEdit"
        {save_part}
        set d to active document of text window 1
        set p to POSIX path of ((file of d) as alias)
        set l to startLine of selection of text window 1
        return p & linefeed & (l as text)
    end tell
    """
    out = osascript(script)
    path, line = out.split("\n")
    return Path(path), int(line)


def open_in_bbedit(path, line=None):
    args = [BBEDIT]
    if line:
        args.append(f"+{line}")
    args.append(str(path))
    subprocess.run(args)


def show_results(lines):
    """Send gcc-style "file:line: kind: message" lines to a BBEdit results window."""
    if not lines:
        return
    subprocess.run([BBRESULTS, "-p", "gcc", "-n"],
                   input="\n".join(lines) + "\n", text=True)


# --------------------------------------------------------------------------
# Finding the root file and engine
# --------------------------------------------------------------------------

MAGIC_RE = re.compile(r"^\s*%\s*!\s*TEX\s+(\w+)\s*=\s*(.+?)\s*$", re.I)


def magic_comments(path, max_lines=30):
    """Read "% !TEX key = value" lines from the head of a file."""
    out = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for _, line in zip(range(max_lines), f):
                m = MAGIC_RE.match(line)
                if m:
                    out[m.group(1).lower()] = m.group(2)
    except OSError:
        pass
    return out


def has_documentclass(path):
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return re.search(r"^[^%\n]*\\documentclass", text, re.M) is not None


def find_root(path):
    """Resolve the root .tex file for `path`.

    Order: "% !TEX root" (TeXShop/TextMate/VS Code convention) →
    the file itself if it has \\documentclass → a sibling or parent .tex
    with \\documentclass that mentions this file's name → the file itself.
    """
    path = Path(path).resolve()
    seen = set()
    while path not in seen:
        seen.add(path)
        root = magic_comments(path).get("root")
        if not root:
            break
        path = (path.parent / root).resolve()
    if path.suffix == ".bib" or not has_documentclass(path):
        stem = path.stem
        for d in (path.parent, path.parent.parent):
            for cand in sorted(d.glob("*.tex")):
                if cand == path or not has_documentclass(cand):
                    continue
                try:
                    text = cand.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if re.search(r"\\(input|include|subfile|bibliography|addbibresource)\{[^}]*"
                             + re.escape(stem), text):
                    return cand
    return path


def program_for(root):
    prog = magic_comments(root).get("program", DEFAULT_PROGRAM).lower()
    return prog if prog in LATEXMK_ENGINE_FLAG else DEFAULT_PROGRAM


def tex_env():
    env = dict(os.environ)
    env["PATH"] = f"{TEXBIN}:/usr/local/bin:/opt/homebrew/bin:{env.get('PATH', '/usr/bin:/bin')}"
    extra = ":".join(os.path.expanduser(p) for p in EXTRA_TEXINPUTS)
    env["TEXINPUTS"] = f"{extra}:{env.get('TEXINPUTS', '')}"
    env["max_print_line"] = "10000"   # stop TeX wrapping log lines at 79 cols
    env["error_line"] = "254"
    env["half_error_line"] = "238"
    return env


# --------------------------------------------------------------------------
# Log parsing
# --------------------------------------------------------------------------

FILE_LINE_ERROR_RE = re.compile(r"^(\.{0,2}/?[^:\s][^:]*\.\w+):(\d+): (.*)$")
BANG_ERROR_RE = re.compile(r"^! (.*)$")
CONTEXT_LINE_RE = re.compile(r"^l\.(\d+) ?(.*)$")
WARNING_RE = re.compile(
    r"^(?:(?:LaTeX|pdfTeX|LuaTeX|XeTeX)|(?:Package|Class|Module)\s+(\S+))\s*(?:Font\s+)?Warning:\s*(.*)$")
INPUT_LINE_RE = re.compile(r"on input line (\d+)")
BADBOX_RE = re.compile(r"^((?:Over|Under)full \\[hv]box .*?) (?:in paragraph|in alignment|detected) at lines? (\d+)")
CONTINUATION_RE = re.compile(r"^\(([\w.@-]+)\)\s+(.*)$")
FILE_TOKEN_RE = re.compile(r'\(("[^"]+"|[^\s()]+)|\(|\)')


class LogParser:
    """A pragmatic TeX log parser.

    Tracks the file stack from the "(file ... )" nesting so warnings can be
    attributed to the right source file, and reads -file-line-error style
    errors directly.
    """

    def __init__(self, root):
        self.root = Path(root)
        self.dir = self.root.parent
        self.stack = []
        self.issues = []   # (path, line, kind, message)

    def current_file(self):
        for f in reversed(self.stack):
            if f is not None:
                return f
        return self.root

    def _scan_parens(self, line):
        for m in FILE_TOKEN_RE.finditer(line):
            tok = m.group(0)
            if tok == ")":
                if self.stack:
                    self.stack.pop()
                continue
            name = m.group(1)
            if name:
                name = name.strip('"')
                p = Path(name) if name.startswith("/") else self.dir / name
                if re.search(r"\.\w+$", name) and p.exists():
                    self.stack.append(p.resolve())
                    continue
            self.stack.append(None)

    def _resolve(self, name):
        p = Path(name)
        return (p if p.is_absolute() else self.dir / p).resolve()

    def add(self, path, line, kind, message):
        msg = re.sub(r"\s+", " ", message).strip()
        key = (str(path), line, kind, msg)
        if key not in {(str(a), b, c, d) for a, b, c, d in self.issues}:
            self.issues.append((path, line, kind, msg))

    def parse(self, text):
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]

            m = FILE_LINE_ERROR_RE.match(line)
            if m and Path(m.group(1)).suffix in TEX_SUFFIXES | {".sty", ".cls", ".bbl", ".aux", ".cfg", ".def", ".clo"}:
                msg, ctx, j = m.group(3), "", i + 1
                while j < len(lines) and j < i + 12:
                    c = CONTEXT_LINE_RE.match(lines[j])
                    if c:
                        ctx = c.group(2).strip()
                        break
                    j += 1
                if ctx:
                    msg += f"  [at: {ctx}]"
                self.add(self._resolve(m.group(1)), int(m.group(2)), "error", msg)
                i += 1
                continue

            m = BANG_ERROR_RE.match(line)
            if m:
                msg, lineno, j = m.group(1), 1, i + 1
                while j < len(lines) and j < i + 12:
                    c = CONTEXT_LINE_RE.match(lines[j])
                    if c:
                        lineno = int(c.group(1))
                        msg += f"  [at: {c.group(2).strip()}]"
                        break
                    j += 1
                self.add(self.current_file(), lineno, "error", msg)
                i += 1
                continue

            m = WARNING_RE.match(line)
            if m:
                pkg = m.group(1)
                msg = m.group(2)
                j = i + 1
                # Gather continuation lines: "(pkg)   more text" or indented text.
                while j < len(lines) and lines[j].strip():
                    c = CONTINUATION_RE.match(lines[j])
                    if c:
                        msg += " " + c.group(2)
                    elif lines[j].startswith(" ") and not pkg:
                        msg += " " + lines[j].strip()
                    else:
                        break
                    j += 1
                lm = INPUT_LINE_RE.search(msg)
                lineno = int(lm.group(1)) if lm else 1
                kind = "warning"
                if "Rerun" in msg or "Label(s) may have changed" in msg:
                    kind = "note"
                prefix = f"[{pkg}] " if pkg else ""
                self.add(self.current_file(), lineno, kind, prefix + msg)
                i = j
                continue

            m = BADBOX_RE.match(line)
            if m:
                if SHOW_BADBOXES:
                    self.add(self.current_file(), int(m.group(2)), "note", m.group(1))
                i += 1
                continue

            if not CONTINUATION_RE.match(line):
                self._scan_parens(line)
            i += 1
        return self.issues


def parse_blg(blg_path):
    """Pick warnings/errors out of a bibtex or biber .blg file."""
    issues = []
    try:
        lines = Path(blg_path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return issues
    blg_dir = Path(blg_path).parent
    bibs = [blg_dir / m.group(1) for l in lines
            for m in [re.match(r"^Database file #\d+: (.+)$", l)] if m]

    def locate_entry(key):
        """Find the .bib file and line where entry `key` is defined."""
        pat = re.compile(r"^\s*@\w+\s*[{(]\s*" + re.escape(key) + r"\s*,")
        for bib in bibs:
            try:
                for n, l in enumerate(bib.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if pat.match(l):
                        return bib, n
            except OSError:
                pass
        return None

    for i, line in enumerate(lines):
        # bibtex
        m = re.match(r"^Warning--(.*)$", line)
        if m:
            path, lineno = blg_path, i + 1
            km = re.search(r" in (\S+)$", m.group(1))
            hit = km and locate_entry(km.group(1))
            if hit:
                path, lineno = hit
            if i + 1 < len(lines):
                l2 = re.match(r"^--line (\d+) of file (.+)$", lines[i + 1])
                if l2:
                    lineno, path = int(l2.group(1)), Path(blg_path).parent / l2.group(2)
            issues.append((Path(path), lineno, "warning", "BibTeX: " + m.group(1)))
            continue
        m = re.match(r"^(.*)---line (\d+) of file (.+)$", line)
        if m:
            issues.append((Path(blg_path).parent / m.group(3), int(m.group(2)), "error", "BibTeX: " + m.group(1)))
            continue
        m = re.match(r"^I (couldn't open|found no) (.*)$", line)
        if m:
            issues.append((Path(blg_path), i + 1, "error", "BibTeX: " + line))
            continue
        # biber
        m = re.match(r"^\[\d+\] .*?> (WARN|ERROR) - (.*)$", line)
        if m:
            msg = m.group(2)
            path, lineno = Path(blg_path), i + 1
            bm = re.search(r"(?:file|datasource) '([^']+\.bib)'.*?line (\d+)", msg)
            if bm:
                path, lineno = Path(bm.group(1)), int(bm.group(2))
            issues.append((path, lineno, "error" if m.group(1) == "ERROR" else "warning", "Biber: " + msg))
    return issues


def collect_issues(root):
    root = Path(root)
    issues = []
    log = root.with_suffix(".log")
    if log.exists():
        text = log.read_text(encoding="utf-8", errors="replace")
        issues += LogParser(root).parse(text)
    blg = root.with_suffix(".blg")
    if blg.exists() and (not log.exists() or blg.stat().st_mtime >= log.stat().st_mtime - 600):
        issues += parse_blg(blg)
    return issues


def format_issues(issues):
    order = {"error": 0, "warning": 1, "note": 2}
    issues = sorted(issues, key=lambda t: (order[t[2]], str(t[0]), t[1]))
    return [f"{p}:{n}: {k}: {m}" for p, n, k, m in issues]


# --------------------------------------------------------------------------
# Actions
# --------------------------------------------------------------------------


def forward_search(pdf, tex, line, activate):
    if not Path(DISPLAYLINE).exists():
        notify("Skim is not installed (needed for PDF preview).")
        return
    args = [DISPLAYLINE, "-r", "-b"]
    if not activate:
        args.append("-g")
    args += [str(line), str(pdf), str(tex)]
    subprocess.run(args)


def detach(func_name, *args):
    """Re-run this module in a background process so BBEdit is not blocked."""
    here = Path(__file__).resolve().parent
    code = (f"import sys; sys.path.insert(0, {str(here)!r}); import texlib; "
            f"texlib.{func_name}(*{list(map(str, args))!r})")
    log = open(os.path.join(os.environ.get("TMPDIR", "/tmp"), "bbedit-textools.log"), "a")
    subprocess.Popen([sys.executable, "-c", code], stdout=log, stderr=log,
                     stdin=subprocess.DEVNULL, start_new_session=True)


def _typeset_worker(root, source, line, force="0"):
    root, source, line = Path(root), Path(source), int(line)
    lockpath = Path(os.environ.get("TMPDIR", "/tmp")) / ("textools-" + hashlib.md5(str(root).encode()).hexdigest()[:12] + ".lock")
    with open(lockpath, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            notify(f"{root.name} is already being typeset.")
            return
        prog = program_for(root)
        cmd = ["latexmk", LATEXMK_ENGINE_FLAG[prog], "-interaction=nonstopmode",
               "-file-line-error", "-synctex=1", "-silent"]
        if force == "1":
            cmd.append("-gg")
        cmd.append(root.name)
        notify(f"Typesetting {root.name} ({prog})…")
        t0 = time.time()
        r = subprocess.run(cmd, cwd=root.parent, env=tex_env(),
                           capture_output=True, text=True)
        dt = time.time() - t0

    issues = collect_issues(root)
    n_err = sum(1 for i in issues if i[2] == "error")
    n_warn = sum(1 for i in issues if i[2] == "warning")
    if r.returncode != 0 and n_err == 0:
        # latexmk failed for a reason the log doesn't explain — show its output.
        out = (r.stdout + "\n" + r.stderr).splitlines()
        summary = []
        if any("Collected error summary" in l for l in out):
            k = next(i for i, l in enumerate(out) if "Collected error summary" in l)
            for l in out[k + 1:]:
                if not l.startswith("  "):
                    break
                summary.append(l.strip())
        summary = summary or [l for l in out if l.strip()][-1:] or ["(no output)"]
        for msg in summary:
            issues.append((root, 1, "error", "latexmk: " + msg))
        n_err = len(summary)

    pdf = root.with_suffix(".pdf")
    if n_err:
        notify(f"{n_err} error(s), {n_warn} warning(s) — {root.name}", sound="Basso")
    else:
        notify(f"OK in {dt:.1f}s — {n_warn} warning(s)", title=f"TeX Tools: {root.name}")
        if FORWARD_SEARCH_AFTER_TYPESET and pdf.exists():
            forward_search(pdf, source, line, ACTIVATE_SKIM_ON_TYPESET)
    if n_err or n_warn:
        show_results(format_issues(issues))


def cmd_typeset(force=False):
    path, line = front_document(save=True)
    root = find_root(path)
    detach("_typeset_worker", root, path, line, "1" if force else "0")


def cmd_view():
    path, line = front_document(save=False)
    root = find_root(path)
    pdf = root.with_suffix(".pdf")
    if not pdf.exists():
        notify(f"No PDF yet for {root.name} — typeset first.")
        return
    forward_search(pdf, path, line, activate=True)


def cmd_show_issues():
    path, _ = front_document(save=False)
    root = find_root(path)
    issues = collect_issues(root)
    if not issues:
        notify(f"No errors or warnings in {root.with_suffix('.log').name}.")
        return
    show_results(format_issues(issues))


def cmd_open_root():
    path, _ = front_document(save=False)
    open_in_bbedit(find_root(path))


def cmd_open_log():
    path, _ = front_document(save=False)
    log = find_root(path).with_suffix(".log")
    if log.exists():
        open_in_bbedit(log)
    else:
        notify(f"No log file {log.name}.")


def _snapshot(d):
    files = set()
    for dirpath, dirnames, filenames in os.walk(d):
        dirnames[:] = [n for n in dirnames if not n.startswith(".")]
        files.update(Path(dirpath) / f for f in filenames)
    return files


def cmd_clean(level="aux"):
    """Remove generated files and report what went.

    aux        — latexmk -c: keeps PDF, SyncTeX and .bbl
    submission — as aux, and also removes .synctex.gz (keeps PDF and .bbl,
                 which arXiv and journals need)
    all        — latexmk -C plus .bbl: back to sources only
    """
    path, _ = front_document(save=False)
    root = find_root(path)
    before = _snapshot(root.parent)
    flag = "-C" if level == "all" else "-c"
    subprocess.run(["latexmk", flag, root.name], cwd=root.parent, env=tex_env(),
                   capture_output=True)
    extra = []
    if level in ("submission", "all"):
        extra.append(root.with_suffix(".synctex.gz"))
        extra.append(root.with_suffix(".synctex"))
    if level == "all":
        extra.append(root.with_suffix(".bbl"))
    for f in extra:
        try:
            f.unlink()
        except FileNotFoundError:
            pass
    removed = sorted(before - _snapshot(root.parent))
    if not removed:
        notify(f"Nothing to clean for {root.name}.")
        return
    exts = sorted({"".join(f.suffixes[-2:]) if f.name.endswith(".synctex.gz") else f.suffix
                   for f in removed})
    notify(f"Removed {len(removed)} file(s): {' '.join(exts)}",
           title=f"Cleaned {root.name}")


def cmd_word_count():
    path, _ = front_document(save=True)
    root = find_root(path)
    r = subprocess.run(["texcount", "-inc", "-total", "-sum", "-brief", root.name],
                       cwd=root.parent, env=tex_env(), capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    notify(out.splitlines()[-1] if out else "texcount produced no output",
           title=f"Word count: {root.name}")


# --------------------------------------------------------------------------
# Project outline
# --------------------------------------------------------------------------

SECTION_LEVELS = {"part": 0, "chapter": 1, "section": 2, "subsection": 3,
                  "subsubsection": 4, "paragraph": 5}
LABEL_KINDS = {"figure": "Figure", "table": "Table", "equation": "Eq.", "AMS": "Eq.",
               "align": "Eq.", "gather": "Eq.", "multline": "Eq.", "eqnarray": "Eq.",
               "part": "Part", "chapter": "Chapter", "section": "§", "subsection": "§",
               "subsubsection": "§", "paragraph": "§", "appendix": "Appendix",
               "Item": "Item", "theorem": "Theorem", "lemma": "Lemma",
               "proposition": "Proposition", "corollary": "Corollary",
               "definition": "Definition", "listing": "Listing", "lstlisting": "Listing"}

OUTLINE_RE = re.compile(
    r"\\(?P<sec>part|chapter|section|subsection|subsubsection|paragraph)(?P<star>\*?)\s*(?:\[[^\]]*\])?\s*\{"
    r"|\\label\s*\{(?P<label>[^}]*)\}"
    r"|\\(?P<inc>input|include|subfile)\s*\{(?P<incfile>[^}]*)\}"
    r"|\\(?:sub)?import\*?\s*\{(?P<impdir>[^}]*)\}\s*\{(?P<impfile>[^}]*)\}"
    r"|\\begin\s*\{(?P<begin>[^}]*)\}"
    r"|\\end\s*\{(?P<end>[^}]*)\}"
    r"|\\caption\s*(?:\[[^\]]*\])?\s*\{(?P<caption>)")


def _braced(text, pos):
    """Return the contents of a {...} group whose opening brace is just before pos."""
    depth, i = 1, pos
    while i < len(text) and depth:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        depth += (c == "{") - (c == "}")
        i += 1
    return text[pos:i - 1]


def _strip_comments(text):
    return re.sub(r"(?<!\\)%.*", "", text)


def _plain(tex, labels=None):
    """Rough TeX → plain text for display; inline maths is kept verbatim.

    With `labels` (from the .aux), \ref/\eqref become their numbers.
    """
    if labels:
        tex = re.sub(r"\\(eq)?ref\s*\{([^}]*)\}",
                     lambda m: ("({})" if m.group(1) else "{}").format(
                         labels.get(m.group(2), ["?"])[0]), tex)
    parts = re.split(r"(\$[^$]*\$)", tex)
    return re.sub(r"\s+", " ", "".join(
        p if p.startswith("$") else _plain_text(p) for p in parts)).strip()


def _plain_text(tex):
    s = re.sub(r"\\(?:emph|textbf|textit|textsc|texttt|mathrm|mathbf|text)\s*\{([^{}]*)\}", r"\1", tex)
    s = re.sub(r"\\(?:label|cite\w*|ref|eqref|footnote)\s*\{[^{}]*\}", "", s)
    s = re.sub(r"\\[a-zA-Z@]+\*?", "", s)
    return re.sub(r"[{}~]", lambda m: " " if m.group() == "~" else "", s)


def _norm(s):
    return re.sub(r"[^0-9a-z]", "", _plain(s).lower())


def _read_aux(aux, labels, toc, seen):
    """Collect \\newlabel data and the table of contents from aux files."""
    if aux in seen or not aux.exists():
        return
    seen.add(aux)
    text = aux.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"\\newlabel\{([^}]*)\}\{", text):
        body = _braced(text, m.end())
        fields, pos = [], 0
        while True:
            j = body.find("{", pos)
            if j < 0:
                break
            f = _braced(body, j + 1)
            fields.append(f)
            pos = j + 1 + len(f) + 1
        if fields:
            labels[m.group(1)] = fields
    for m in re.finditer(r"\\contentsline\s*\{(\w+)\}\{", text):
        body = _braced(text, m.end())
        nm = re.match(r"\s*\\numberline\s*\{([^}]*)\}(.*)", body, re.S)
        if nm:
            toc.append((m.group(1), nm.group(1), _norm(nm.group(2))))
    for m in re.finditer(r"\\@input\{([^}]*)\}", text):
        _read_aux(aux.parent / m.group(1), labels, toc, seen)


def build_outline(root):
    root = Path(root)
    labels, toc = {}, []
    _read_aux(root.with_suffix(".aux"), labels, toc, set())
    toc_pos = 0
    entries = []          # (path, line, level, text)
    visited = set()
    state = {"level": 0}

    def section_number(kind, title):
        nonlocal toc_pos
        want = _norm(title)
        for k in range(toc_pos, min(toc_pos + 25, len(toc))):
            lvl, num, t = toc[k]
            if lvl == kind and (t == want or (want and t.startswith(want[:30]))):
                toc_pos = k + 1
                return num
        return None

    def resolve(name, base):
        p = Path(name.strip())
        p = p if p.is_absolute() else base / p
        if p.suffix != ".tex" and not p.exists():
            p = p.with_name(p.name + ".tex")
        return p.resolve()

    def walk(path, import_dir):
        if path in visited or not path.exists():
            return
        visited.add(path)
        text = _strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        envs, captions = [], []
        for m in OUTLINE_RE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            if m.group("sec"):
                kind = m.group("sec")
                title = _braced(text, m.end())
                lvl = SECTION_LEVELS[kind]
                state["level"] = lvl
                num = None if m.group("star") else section_number(kind, title)
                head = f"{num}  " if num else ("" if m.group("star") else "")
                entries.append((path, line, lvl, f"{head}{_plain(title, labels)}"))
                state["last_section"] = (len(entries) - 1, num, line)
            elif m.group("label") is not None:
                key = m.group("label")
                info = labels.get(key, [])
                num = info[0] if info else "?"
                page = info[1] if len(info) > 1 else None
                anchor = info[3] if len(info) > 3 else ""
                kind = anchor.split(".")[0] if anchor else (envs[-1].rstrip("*") if envs else "")
                kind_name = LABEL_KINDS.get(kind, kind.capitalize() if kind else "")
                if kind_name == "Eq.":
                    ref = f"Eq. ({num})"
                elif kind_name:
                    ref = f"{kind_name} {num}"
                else:
                    ref = num
                desc = f"⟨{key}⟩  {ref}"
                if page:
                    desc += f"  p.{page}"
                if captions and envs and envs[-1].rstrip("*") in ("figure", "table", "wrapfigure", "sidewaysfigure", "sidewaystable"):
                    cap = captions[-1]
                    desc += "  — " + (cap[:70] + "…" if len(cap) > 70 else cap)
                last = state.get("last_section")
                if (kind_name in ("§", "Chapter", "Part", "Appendix")
                        or (last and last[1] == num and 0 <= line - last[2] <= 3)):
                    if last:   # the heading's own label: show the key on the heading
                        p_, n_, l_, t_ = entries[last[0]]
                        entries[last[0]] = (p_, n_, l_, f"{t_}  ⟨{key}⟩")
                    continue
                entries.append((path, line, state["level"] + 1, desc))
            elif m.group("inc"):
                walk(resolve(m.group("incfile"), import_dir), import_dir)
            elif m.group("impfile") is not None:
                d = (path.parent / m.group("impdir")).resolve()
                walk(resolve(m.group("impfile"), d), d)
            elif m.group("begin"):
                envs.append(m.group("begin"))
                if m.group("begin").rstrip("*") in ("figure", "table"):
                    captions.clear()
            elif m.group("end"):
                if envs and envs[-1] == m.group("end"):
                    envs.pop()
            elif m.group("caption") is not None:
                captions.append(_plain(_braced(text, m.end()), labels))

    walk(root.resolve(), root.parent)
    return entries


def cmd_outline():
    path, _ = front_document(save=True)
    root = find_root(path)
    entries = build_outline(root)
    if not entries:
        notify(f"No sections or labels found in {root.name}.")
        return
    top = min(e[2] for e in entries)
    indent = "\u2003\u2003"   # em spaces survive the results browser's trimming
    show_results([f"{p}:{n}: note: {indent * (lvl - top)}{t}" for p, n, lvl, t in entries])
