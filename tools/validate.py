#!/usr/bin/env python3
"""Validate the campaign folders of surf-etds-data.

    python tools/validate.py [REPOSITORY_ROOT]

Checks every folder under campaigns/: the campaign ID, the allowed entries and file names,
encoding and line endings, JSON syntax, the pseudonymised computerName of the ExacTrac
exports, runs.csv and its references, SHA256SUMS, the operator fields of the measurement
protocols (role codes only), forbidden patterns (e-mail addresses, home and cloud paths,
host names, earlier operator codes) in text files and PNG text chunks, and the file size.

Standard library only; runs on Python 3.9 and later.
Exit status: 0 valid, 1 problems found, 2 usage error.
"""

import csv
import datetime
import hashlib
import io
import json
import os
import re
import sys
import zlib
from pathlib import Path

MAX_SIZE = 50 * 1024 * 1024
CAMPAIGN_ID = re.compile(r"^(\d{4})-(\d{2})-(\d{2})_(L\d|LX|unknown)$")
CAMPAIGN_ENTRIES = {"phantom", "etd", "xray", "protocol.md", "runs.csv", "SHA256SUMS"}
PHANTOM_FILE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(\.csv|_log\.json|_log\.txt)$")
ETD_FILE = re.compile(r"^TrackingResult_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.(json|png)$")
XRAY_FILE = re.compile(r"^[a-z0-9][a-z0-9_]*\.csv$")
DATE_TOKEN = re.compile(r"(?<!\d)(20\d{2})(-?)(\d{2})\2(\d{2})(?!\d)")
TEXT_SUFFIXES = {".csv", ".json", ".txt", ".md"}

RUNS_HEADER = ["run_id", "csv_file", "etd_file", "group", "roi_area", "heatingpads", "title", "used_in_analysis",
               "note", "blueprint", "protocol_remark"]

# Operators are recorded as role codes (QMP1, Student1, ...), never as names. Same grammar as the
# validate workflow of surf-etds-phantom.
CODES = re.compile(r"\s*(QMP|RTT|Student)[1-9][0-9]?(\s*,\s*(QMP|RTT|Student)[1-9][0-9]?)*\s*")
MESSTEAM = re.compile(r"^Messteam\s*:\s*(.*)$", re.M)

# The exports name the workstation in their first field; published exports carry ETD-L<n> instead.
ETD_COMPUTER = re.compile(rb'^\{"computerName":"ETD-L(\d)",')
ORIGINAL_HOST = re.compile("ETD" + "LINAC", re.I)

FORBIDDEN = [
    ("e-mail address", re.compile(r"[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    ("home path", re.compile(r"(?i:/Users/|/home/|[A-Za-z]:[\\/]{1,2}Users[\\/]{1,2})[\w.-]+")),
    ("cloud or volume path", re.compile(r"(?i:iCloud[ _]?Drive|Mobile Documents|com~apple~CloudDocs|OneDrive)"
                                        r"|(?<![\w.~-])/Volumes/[^/\s\"'<>]+")),
    ("host name", re.compile(r"(?i)\b(?:DESKTOP|LAPTOP)-[A-Z0-9]{4,}\b|[\w-]+\.local(?![\w.])")),
    ("original workstation name", ORIGINAL_HOST),
    ("earlier operator code", re.compile(r"(?i)\boperators?[ \t_-]*[A-D]\b"
                                         r"|operators?\s+A\s*(?:-|\u2013|\u2026|to|bis)\s*D")),
]


class Report:
    def __init__(self, root: Path):
        self.root = root
        self.problems = []

    def error(self, path, message):
        rel = os.path.relpath(path, self.root) if isinstance(path, Path) else path
        self.problems.append((rel, message))


def is_date(y, m, d):
    try:
        datetime.date(int(y), int(m), int(d))
        return True
    except ValueError:
        return False


def png_text(data: bytes) -> str:
    """Text of tEXt, zTXt and iTXt chunks; raises ValueError on a malformed file."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG file")
    out, pos = [], 8
    while pos + 8 <= len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + length]
        if len(body) != length:
            raise ValueError("truncated chunk")
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


def check_forbidden(report, path, text, label=""):
    for name, rx in FORBIDDEN:
        m = rx.search(text)
        if m:
            report.error(path, f"{name}{label}: {m.group(0)!r}")


def read_text(report, path: Path):
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        report.error(path, "UTF-8 byte order mark")
        data = data[3:]
    if b"\r" in data:
        report.error(path, "carriage return (CRLF line endings); run tools/prepare_campaign.py")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        report.error(path, f"not UTF-8: {exc}")
        return None


def check_operator_value(report, path, value):
    if value in (None, "", "-"):
        return
    if not isinstance(value, str) or not CODES.fullmatch(value):
        report.error(path, "operator field is not a role code list (expected e.g. 'QMP1, Student1')")


def check_runs(report, campaign: Path, texts: dict):
    path = campaign / "runs.csv"
    text = texts.get("runs.csv")
    if text is None:
        return
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or rows[0] != RUNS_HEADER:
        report.error(path, f"header must be {','.join(RUNS_HEADER)}")
        return
    phantom = {p.name for p in (campaign / "phantom").glob("*")} if (campaign / "phantom").is_dir() else set()
    etd = {p.name for p in (campaign / "etd").glob("*")} if (campaign / "etd").is_dir() else set()
    listed_csv, listed_etd = set(), set()
    for number, row in enumerate(rows[1:], start=2):
        where = f"{os.path.relpath(path, report.root)}:{number}"
        if len(row) != len(RUNS_HEADER):
            report.error(where, f"{len(row)} fields, expected {len(RUNS_HEADER)}")
            continue
        r = dict(zip(RUNS_HEADER, row))
        if r["run_id"] and not r["run_id"].isdigit():
            report.error(where, "run_id must be empty or a number")
        if r["used_in_analysis"] not in ("true", "false"):
            report.error(where, "used_in_analysis must be true or false")
        if r["heatingpads"] not in ("", "OFF") and not r["heatingpads"].isdigit():
            report.error(where, "heatingpads must be empty, OFF or a temperature in degC")
        if r["blueprint"] and not re.fullmatch(r"[A-Za-z0-9._-]+\.json", r["blueprint"]):
            report.error(where, "blueprint must be a blueprint file name")
        if r["csv_file"]:
            listed_csv.add(r["csv_file"])
            if r["csv_file"] not in phantom:
                report.error(where, f"csv_file {r['csv_file']} is not in phantom/")
        if r["etd_file"]:
            listed_etd.add(r["etd_file"])
            if not r["etd_file"].endswith(".json") or r["etd_file"] not in etd:
                report.error(where, f"etd_file {r['etd_file']} is not an export in etd/")
        if not (r["csv_file"] or r["etd_file"] or r["note"]):
            report.error(where, "row names neither a file nor a note")
    for name in sorted(phantom):
        if name.endswith("_QA.csv"):
            if name not in listed_csv and name[:-7] + ".csv" not in listed_csv:
                report.error(path, f"{name} and its raw CSV are not listed")
        elif name.endswith(".csv") and name not in listed_csv:
            report.error(path, f"phantom/{name} is not listed")
    for name in sorted(etd):
        if name.endswith(".json") and name not in listed_etd:
            report.error(path, f"etd/{name} is not listed")


def check_sums(report, campaign: Path, files: list):
    path = campaign / "SHA256SUMS"
    if not path.is_file():
        report.error(path, "missing")
        return
    text = read_text(report, path)
    if text is None:
        return
    entries = []
    for number, line in enumerate(text.splitlines(), start=1):
        m = re.fullmatch(r"([0-9a-f]{64})  (\S(?:.*\S)?)", line)
        if not m:
            report.error(f"{os.path.relpath(path, report.root)}:{number}", "not '<sha256>  <path>'")
            continue
        if m.group(2).startswith("/") or "\\" in m.group(2) or ".." in m.group(2).split("/"):
            report.error(f"{os.path.relpath(path, report.root)}:{number}", "path must stay inside the campaign folder")
            continue
        entries.append((m.group(2), m.group(1)))
    names = [e[0] for e in entries]
    if names != sorted(names):
        report.error(path, "entries are not sorted by path")
    expected = sorted(str(f.relative_to(campaign)).replace(os.sep, "/") for f in files if f.name != "SHA256SUMS"
                      or f.parent != campaign)
    if sorted(set(names)) != expected or len(names) != len(set(names)):
        missing = sorted(set(expected) - set(names))
        extra = sorted(set(names) - set(expected))
        report.error(path, f"does not list exactly the campaign files (missing {missing[:3]}, extra {extra[:3]})")
    for name, digest in entries:
        target = campaign / name
        if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            report.error(path, f"checksum of {name} does not match")


def check_campaign(report, campaign: Path):
    m = CAMPAIGN_ID.match(campaign.name)
    if not m or not is_date(*m.groups()[:3]):
        report.error(campaign, "campaign folder must be named <YYYY-MM-DD>_<L0-L9|LX|unknown>")
        return
    year, month, day, linac = m.groups()
    date_compact = f"{year}{month}{day}"
    for entry in sorted(campaign.iterdir()):
        if entry.name not in CAMPAIGN_ENTRIES:
            report.error(entry, "unexpected entry (allowed: phantom/, etd/, xray/, protocol.md, runs.csv, SHA256SUMS)")
        elif entry.name in ("phantom", "etd", "xray") and not entry.is_dir():
            report.error(entry, "must be a directory")
    for required in ("runs.csv", "SHA256SUMS"):
        if not (campaign / required).is_file():
            report.error(campaign / required, "missing")

    links = sorted(p for p in campaign.rglob("*") if p.is_symlink())
    for link in links:
        report.error(link, "symbolic links are not allowed")
    files = sorted(p for p in campaign.rglob("*") if p.is_file() and not p.is_symlink())
    texts, logs = {}, {}
    for path in files:
        rel = path.relative_to(campaign)
        parts = rel.parts
        if any(part.startswith(".") for part in parts):
            report.error(path, "hidden file or folder")
            continue
        if len(parts) > 2:
            report.error(path, "nested folders are not allowed")
            continue
        if path.stat().st_size > MAX_SIZE:
            report.error(path, f"larger than {MAX_SIZE // (1024 * 1024)} MB")
        name = path.name
        folder = parts[0] if len(parts) == 2 else ""
        if folder == "phantom" and not PHANTOM_FILE.match(name):
            report.error(path, "unexpected file name in phantom/")
        if folder == "etd" and not ETD_FILE.match(name):
            report.error(path, "unexpected file name in etd/ (TrackingResult_<date>_<time>.json|png)")
        if folder == "xray" and not XRAY_FILE.match(name):
            report.error(path, "unexpected file name in xray/")
        for token in DATE_TOKEN.finditer(name):
            if token.group(1) + token.group(3) + token.group(4) != date_compact:
                report.error(path, f"date {token.group(0)} in the file name does not match the campaign")

        if path.suffix == ".png":
            data = path.read_bytes()
            try:
                check_forbidden(report, path, png_text(data), " in a PNG text chunk")
            except (ValueError, zlib.error) as exc:
                report.error(path, f"invalid PNG: {exc}")
            continue
        if path.suffix not in TEXT_SUFFIXES:
            if name != "SHA256SUMS":
                report.error(path, "unexpected file type")
            continue
        text = read_text(report, path)
        if text is None:
            continue
        texts[str(rel).replace(os.sep, "/")] = text
        check_forbidden(report, path, text)
        if path.suffix == ".json":
            try:
                value = json.loads(text)
            except ValueError as exc:
                report.error(path, f"invalid JSON: {exc}")
                continue
            if folder == "etd":
                em = ETD_COMPUTER.match(path.read_bytes())
                if not em:
                    report.error(path, "computerName must be the first field and read ETD-L<n>")
                elif linac != f"L{em.group(1).decode()}":
                    report.error(path, f"computerName ETD-L{em.group(1).decode()} does not match campaign linac {linac}")
            if name.endswith("_log.json"):
                if not isinstance(value, dict):
                    report.error(path, "measurement protocol must be a JSON object")
                    continue
                check_operator_value(report, path, value.get("personal"))
                logs.setdefault(name[:-len("_log.json")], {})["json"] = (path, value)
        elif name.endswith("_log.txt"):
            values = MESSTEAM.findall(text)
            for v in values:
                check_operator_value(report, path, v.strip())
            logs.setdefault(name[:-len("_log.txt")], {})["txt"] = (path, values)

    for stem, pair in sorted(logs.items()):
        if set(pair) != {"json", "txt"}:
            report.error(campaign / "phantom" / f"{stem}_log.*", "protocol needs both _log.json and _log.txt")
            continue
        json_path, value = pair["json"]
        personal = value.get("personal")
        messteam = [v.strip() for v in pair["txt"][1]]
        normal = "-" if personal in (None, "") else personal.strip() if isinstance(personal, str) else personal
        if messteam != [normal]:
            report.error(json_path, "personal in _log.json and Messteam in _log.txt differ")
        csv_file = value.get("csv_file")
        if csv_file and not (campaign / "phantom" / csv_file).is_file():
            report.error(json_path, f"csv_file {csv_file} is not in phantom/")
    etd_pngs = {p.stem for p in files if p.parent.name == "etd" and p.suffix == ".png"}
    etd_jsons = {p.stem for p in files if p.parent.name == "etd" and p.suffix == ".json"}
    for stem in sorted(etd_pngs - etd_jsons):
        report.error(campaign / "etd" / f"{stem}.png", "image without its export")
    if etd_jsons and not re.fullmatch(r"L\d", linac):
        report.error(campaign / "etd", "ExacTrac exports in a campaign without a linac number")
    check_runs(report, campaign, texts)
    check_sums(report, campaign, files)


def validate(root: Path) -> list:
    report = Report(root)
    campaigns = root / "campaigns"
    if not campaigns.is_dir():
        report.error(campaigns, "missing campaigns/ folder")
        return report.problems
    for entry in sorted(campaigns.iterdir()):
        if entry.name.startswith(".") or not entry.is_dir():
            report.error(entry, "only campaign folders are allowed in campaigns/")
            continue
        check_campaign(report, entry)
    return report.problems


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) > 1 or (argv and argv[0] in ("-h", "--help")):
        print(__doc__)
        return 2
    root = Path(argv[0] if argv else Path(__file__).resolve().parents[1]).resolve()
    problems = validate(root)
    github = os.environ.get("GITHUB_ACTIONS") == "true"
    for path, message in problems:
        print(f"::error file={path}::{message}" if github else f"{path}: {message}")
    count = len(list((root / "campaigns").glob("*"))) if (root / "campaigns").is_dir() else 0
    print(f"{'FAILED' if problems else 'OK'}: {count} campaign folder(s), {len(problems)} problem(s).")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
