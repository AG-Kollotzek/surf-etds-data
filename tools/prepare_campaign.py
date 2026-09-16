#!/usr/bin/env python3
"""Prepare a new campaign folder for a pull request.

    python tools/prepare_campaign.py campaigns/<YYYY-MM-DD>_<Linac> [--check]

1. Text files (.csv, .json, .txt, .md) get LF line endings and lose a UTF-8 byte order mark;
   the measurement terminal on Windows writes CRLF.
2. ExacTrac exports in etd/ get the pseudonymised workstation name ETD-L<n>. The linac number
   must match the campaign folder; only the first field of the export changes, byte for byte.
3. SHA256SUMS is written for every file of the campaign, sorted by path.

With --check nothing is written; the exit status is 1 if anything would change.
Run tools/validate.py and tools/check_names.py afterwards.

Standard library only; runs on Python 3.9 and later.
Exit status: 0 done (or nothing to change), 1 changes needed (--check), 2 usage or data error.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

CAMPAIGN_ID = re.compile(r"^(\d{4})-(\d{2})-(\d{2})_(L\d|LX|unknown)$")
TEXT_SUFFIXES = {".csv", ".json", ".txt", ".md"}
# First field of an export as written by the tracking workstation, and its published form.
WORKSTATION = re.compile(rb'^\{"computerName":"ETD' + b"LINAC" + rb'(\d)",')
PSEUDONYM = re.compile(rb'^\{"computerName":"ETD-L(\d)",')


class DataError(Exception):
    pass


def normalise_text(data: bytes) -> bytes:
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.replace(b"\r\n", b"\n")


def pseudonymise_export(data: bytes, linac: str, name: str) -> bytes:
    if PSEUDONYM.match(data):
        n = PSEUDONYM.match(data).group(1).decode()
    else:
        m = WORKSTATION.match(data)
        if not m:
            raise DataError(f"{name}: the export does not start with a computerName field")
        n = m.group(1).decode()
        data = b'{"computerName":"ETD-L' + m.group(1) + b'",' + data[m.end():]
    if linac != f"L{n}":
        raise DataError(f"{name}: the export names linac {n}, the campaign folder says {linac}")
    try:
        json.loads(data)
    except ValueError as exc:
        raise DataError(f"{name}: not valid JSON after preparation ({exc})") from None
    return data


def prepare(campaign: Path, check: bool) -> list:
    m = CAMPAIGN_ID.match(campaign.name)
    if not campaign.is_dir() or not m:
        raise DataError(f"{campaign} is not a campaign folder named <YYYY-MM-DD>_<L0-L9|LX|unknown>")
    linac = m.group(4)
    changes = []
    links = [p for p in campaign.rglob("*") if p.is_symlink()]
    if links:
        raise DataError(f"symbolic links are not allowed: {links[0]}")
    files = sorted(p for p in campaign.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    contents = {}
    for path in files:
        rel = path.relative_to(campaign).as_posix()
        data = path.read_bytes()
        new = data
        if path.suffix in TEXT_SUFFIXES:
            new = normalise_text(new)
        if rel.startswith("etd/") and path.suffix == ".json":
            new = pseudonymise_export(new, linac, rel)
        if new != data:
            changes.append(rel)
            if not check:
                path.write_bytes(new)
        contents[rel] = new
    sums = "".join(f"{hashlib.sha256(contents[rel]).hexdigest()}  {rel}\n" for rel in sorted(contents))
    sums_path = campaign / "SHA256SUMS"
    if not sums_path.is_file() or sums_path.read_text(encoding="utf-8") != sums:
        changes.append("SHA256SUMS")
        if not check:
            sums_path.write_bytes(sums.encode("utf-8"))
    return changes


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    check = "--check" in args
    args = [a for a in args if a != "--check"]
    if len(args) != 1 or args[0].startswith("-"):
        print(__doc__)
        return 2
    try:
        changes = prepare(Path(args[0]), check)
    except DataError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    verb = "would change" if check else "changed"
    for rel in changes:
        print(f"{verb}: {rel}")
    print(f"{len(changes)} file(s) {verb}.")
    return 1 if check and changes else 0


if __name__ == "__main__":
    sys.exit(main())
