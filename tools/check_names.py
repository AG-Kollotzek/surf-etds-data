#!/usr/bin/env python3
"""Check files for names of people before they are pushed.

    python tools/check_names.py PEOPLE_JSON [PATH ...] [--history]

PEOPLE_JSON is the private list of people kept by the lab (never commit it here). PATH are
files or folders to check (default: the repository root). With --history, every blob and
commit message on every ref of the git repository at the first PATH is checked as well.

Tokens come from the list: every word of a name, aliases, GitHub logins, e-mail addresses and
their local parts, and the "deny" entries. Matching ignores case and diacritics, repairs
double-encoded UTF-8, and treats "_", digits and camelCase as word boundaries. PDFs (via
pdftotext), ZIP members, gzip content and PNG text chunks are read too.

Consented public names ("public_name" with "public_name_consent": true) may appear outside
campaigns/, for example as authors. Inside campaigns/ no name may appear at all: operators
are recorded as role codes. Findings are printed masked (first letter and length).

Standard library only (pdftotext from poppler for PDFs); runs on Python 3.9 and later.
Exit status: 0 no names found, 1 names found, 2 usage error or invalid list, 3 read or tool error.

Expected list format (only these keys are read):
    {"people": [{"name": "...", "aliases": [], "github": [], "emails": [],
                 "public_name": null, "public_name_consent": false}],
     "deny": [], "commit_identities": {"allowed": []}}
"""

import gzip
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
import zlib
from pathlib import Path

MIN_LENGTH = 3
MAX_INFLATE = 50 * 1024 * 1024
INITIAL = re.compile(r"^[A-Z]\.$")
TRANSLITERATION = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"})


class ToolError(Exception):
    pass


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.replace("ß", "ss").replace("ẞ", "ss").casefold()


def allowed_parts(identities):
    """Whole name words, addresses, address local parts and logins of the allowed commit identities."""
    parts = set()
    for identity in identities:
        m = re.fullmatch(r"\s*(.*?)\s*<([^<>]*)>\s*", identity)
        name, mail = (m.group(1), m.group(2)) if m else (identity, "")
        parts.update(name.split())
        if mail:
            local = mail.split("@", 1)[0]
            parts.update((mail, local, local.split("+")[-1]))  # 123+login@users.noreply.github.com
    return parts


class Names:
    def __init__(self, data):
        if not isinstance(data, dict) or not isinstance(data.get("people"), list):
            raise ValueError("the list needs a 'people' array")
        allowed = allowed_parts((data.get("commit_identities") or {}).get("allowed") or [])
        self.kind = {}
        for person in data["people"]:
            if not isinstance(person, dict) or not isinstance(person.get("name"), str):
                raise ValueError("every person needs a 'name'")
            consent = person.get("public_name_consent") is True and bool(person.get("public_name"))
            public = {w for w in (person.get("public_name") or "").split() if not INITIAL.match(w)} if consent else set()
            words = set(person["name"].split())
            words.update(person.get("aliases") or [])
            logins = set(person.get("github") or [])
            for mail in person.get("emails") or []:
                words.update((mail, mail.split("@", 1)[0]))
            for token in words | logins:
                if len(token) < MIN_LENGTH or INITIAL.match(token):
                    continue
                # consented names, and logins or addresses that are part of an allowed commit identity
                is_public = token in public or (consent and token in allowed)
                self._add(token, "public" if is_public else "private")
        for token in data.get("deny") or []:
            if not isinstance(token, str) or not token.strip():
                raise ValueError("deny entries must be non-empty strings")
            self._add(token, "private")
        if not self.kind:
            raise ValueError("the list contains no names")
        alternation = "|".join(re.escape(t) for t in sorted(self.kind, key=len, reverse=True))
        self.regex = re.compile(r"(?<![a-z])(?:" + alternation + r")(?![a-z])")

    def _add(self, token, kind):
        for key in {fold(token), fold(token.translate(TRANSLITERATION))}:  # Jürgen, Jurgen, Juergen
            if self.kind.get(key) != "private":  # private wins over public
                self.kind[key] = kind

    def find(self, text: str):
        """(token, kind) for every name in the text, in any of the normalised forms."""
        variants = {text, re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", text)}
        try:
            variants.add(text.encode("latin-1").decode("utf-8"))
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        found = {}
        for variant in variants:
            for m in self.regex.finditer(fold(variant)):
                found[m.group(0)] = self.kind[m.group(0)]
        return sorted(found.items())


def mask(token: str) -> str:
    return f"{token[0]}{'*' * (len(token) - 1)} ({len(token)})"


class Checker:
    def __init__(self, names: Names):
        self.names = names
        self.findings = []
        self.errors = []

    def report(self, where: str, line, text: str, inside_campaigns: bool):
        for token, kind in self.names.find(text):
            if kind == "public" and not inside_campaigns:
                continue
            label = "name" if kind == "private" else "public name inside campaigns/"
            location = f"{where}:{line}" if line else where
            self.findings.append(f"{location}: {label} {mask(token)}")

    def text(self, where: str, text: str, inside_campaigns: bool):
        for number, line in enumerate(text.splitlines(), start=1):
            self.report(where, number, line, inside_campaigns)

    def blob(self, where: str, data: bytes, inside_campaigns: bool, depth: int = 0):
        if depth > 4:
            self.errors.append(f"{where}: nested too deeply to check")
            return
        try:
            if data.startswith(b"%PDF-"):
                self.text(where, self.pdf_text(data), inside_campaigns)
            elif data.startswith((b"PK\x03\x04", b"PK\x05\x06")):
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    for info in zf.infolist():
                        member = f"{where}!{info.filename}"
                        self.report(member, None, info.filename, inside_campaigns)
                        if not info.is_dir():
                            if info.file_size > MAX_INFLATE:
                                self.errors.append(f"{member}: too large to check")
                                continue
                            self.blob(member, zf.read(info), inside_campaigns, depth + 1)
            elif data.startswith(b"\x1f\x8b"):
                with gzip.GzipFile(fileobj=io.BytesIO(data)) as fh:
                    self.blob(f"{where} (gunzipped)", fh.read(MAX_INFLATE), inside_campaigns, depth + 1)
            elif data.startswith(b"\x89PNG\r\n\x1a\n"):
                self.text(f"{where} (PNG text)", png_text(data), inside_campaigns)
            elif data.startswith((b"\xff\xfe", b"\xfe\xff")):
                self.text(where, data.decode("utf-16", "replace"), inside_campaigns)
            elif b"\0" in data:
                for encoding in ("utf-16-le", "utf-16-be"):
                    for offset in (0, 1):
                        self.text(f"{where} ({encoding})", data[offset:].decode(encoding, "replace"), inside_campaigns)
                self.text(f"{where} (bytes)", data.decode("latin-1"), inside_campaigns)
            else:
                try:
                    self.text(where, data.decode("utf-8"), inside_campaigns)
                except UnicodeDecodeError:
                    self.text(where, data.decode("latin-1"), inside_campaigns)
        except (zipfile.BadZipFile, OSError, EOFError, zlib.error, ValueError, RuntimeError) as exc:
            self.errors.append(f"{where}: cannot be read ({exc})")

    @staticmethod
    def pdf_text(data: bytes) -> str:
        tool = shutil.which("pdftotext")
        if not tool:
            raise ToolError("pdftotext (poppler) is needed to check PDF files")
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.pdf"
            src.write_bytes(data)
            proc = subprocess.run([tool, "-q", "-enc", "UTF-8", str(src), "-"], capture_output=True)
            if proc.returncode:
                raise ValueError(f"pdftotext failed with exit status {proc.returncode}")
            info = subprocess.run([shutil.which("pdfinfo") or "pdfinfo", str(src)], capture_output=True)
            return proc.stdout.decode("utf-8", "replace") + "\n" + info.stdout.decode("utf-8", "replace")


def png_text(data: bytes) -> str:
    out, pos = [], 8
    while pos + 8 <= len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + length]
        if len(body) != length:
            raise ValueError("truncated PNG chunk")
        if kind == b"tEXt":
            out.append(body.replace(b"\0", b" "))
        elif kind == b"zTXt":
            key, _, rest = body.partition(b"\0")
            out.append(key + b" " + zlib.decompress(rest[1:]))
        elif kind == b"iTXt":
            key, _, rest = body.partition(b"\0")
            flag, rest = rest[0], rest[2:]
            _, _, rest = rest.partition(b"\0")
            _, _, text = rest.partition(b"\0")
            out.append(key + b" " + (zlib.decompress(text) if flag else text))
        elif kind == b"eXIf":
            out.append(body)
        elif kind == b"IEND":
            break
        pos += 12 + length
    return b"\n".join(out).decode("utf-8", "replace")


def inside(rel: str) -> bool:
    return rel.replace("\\", "/").startswith("campaigns/")


SKIP_DIRS = {".git", "__pycache__", ".venv", ".ruff_cache", ".pytest_cache"}


def list_files(folder: Path):
    """The files git would push (tracked, and untracked but not ignored); every file outside a git work tree."""
    proc = subprocess.run(["git", "-C", str(folder), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                          capture_output=True) if shutil.which("git") else None
    if proc is not None and proc.returncode == 0:
        return sorted(folder / p for p in proc.stdout.decode("utf-8").split("\0") if p and (folder / p).is_file())
    return sorted(p for p in folder.rglob("*") if p.is_file() and not SKIP_DIRS & set(p.relative_to(folder).parts))


def check_paths(checker: Checker, paths, root: Path):
    root = root.resolve()  # macOS temporary folders resolve through /private
    for path in paths:
        files = [path] if path.is_file() else list_files(path)
        for f in files:
            if f.is_symlink():
                checker.errors.append(f"{f}: symbolic link, not checked")
                continue
            try:
                rel = str(f.resolve().relative_to(root))
            except ValueError:
                rel = str(f)
            if ".git" in Path(rel).parts:
                continue
            checker.report(rel, None, rel, inside(rel))
            checker.blob(rel, f.read_bytes(), inside(rel))


def check_history(checker: Checker, repo: Path):
    def git(*args):
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
        if proc.returncode:
            raise ToolError(f"git {' '.join(args)} failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
        return proc.stdout

    log = git("log", "--all", "--format=%H%x00%an <%ae>%x00%cn <%ce>%x00%B%x1e").decode("utf-8", "replace")
    for record in filter(None, (r.strip("\n") for r in log.split("\x1e"))):
        sha, author, committer, message = (record.split("\x00") + ["", "", ""])[:4]
        checker.text(f"commit {sha[:7]}", "\n".join((author, committer, message)), False)
    objects = git("rev-list", "--all", "--objects").decode("utf-8", "replace").splitlines()
    with subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE) as proc:
        for line in objects:
            sha, _, path = line.partition(" ")
            proc.stdin.write(sha.encode() + b"\n")
            proc.stdin.flush()
            header = proc.stdout.readline().split()
            data = proc.stdout.read(int(header[2]))
            proc.stdout.read(1)
            if header[1] != b"blob":
                if path:
                    checker.report(f"history {sha[:7]}:{path}", None, path, inside(path))
                continue
            where = f"history {sha[:7]}:{path}"
            checker.report(where, None, path, inside(path))
            checker.blob(where, data, inside(path))
        proc.stdin.close()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    history = "--history" in args
    args = [a for a in args if a != "--history"]
    if not args or args[0] in ("-h", "--help") or any(a.startswith("-") for a in args):
        print(__doc__)
        return 2
    try:
        names = Names(json.loads(Path(args[0]).read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        print(f"invalid list of people: {exc}", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parents[1]
    paths = [Path(p).resolve() for p in args[1:]] or [root]
    if len(paths) == 1 and paths[0].is_dir():
        root = paths[0]
    checker = Checker(names)
    try:
        check_paths(checker, paths, root)
        if history:
            check_history(checker, paths[0] if paths[0].is_dir() else root)
    except ToolError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    for finding in checker.findings:
        print(finding)
    for error in checker.errors:
        print(f"error: {error}", file=sys.stderr)
    print(f"{len(checker.findings)} finding(s), {len(checker.errors)} read error(s).")
    if checker.errors:
        return 3
    return 1 if checker.findings else 0


if __name__ == "__main__":
    sys.exit(main())
