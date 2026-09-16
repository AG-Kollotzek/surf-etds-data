"""A small, valid campaign folder for the tool tests (synthetic values only)."""

import csv
import hashlib
import io
import json
import zlib
from pathlib import Path

HEADER = ["run_id", "csv_file", "etd_file", "group", "roi_area", "heatingpads", "title", "used_in_analysis",
          "note", "blueprint", "protocol_remark"]
CSV_NAME = "ETsurface_easyQA_20260806_163851.csv"
QA_NAME = "ETsurface_easyQA_20260806_163851_QA.csv"
LOG_STEM = "ETsurface_easyQA_new_20260806_163703"
EXPORT = "TrackingResult_2026-08-06_16-43-56"


def png(chunks=()):
    def chunk(kind, body):
        return len(body).to_bytes(4, "big") + kind + body + zlib.crc32(kind + body).to_bytes(4, "big")
    ihdr = (1).to_bytes(4, "big") * 2 + bytes([8, 0, 0, 0, 0])
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + b"".join(chunk(k, b) for k, b in chunks)
            + chunk(b"IDAT", zlib.compress(b"\0\0")) + chunk(b"IEND", b""))


def export(computer="ETD-L3"):
    return ('{"computerName":"%s","startTime":"06.Aug..2026, 16:43:26","trackingResults":[]}' % computer).encode()


def runs_csv(rows):
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(rows)
    return buf.getvalue()


def write_sums(folder: Path):
    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.name != "SHA256SUMS")
    lines = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(folder).as_posix()}\n"
                    for p in files)
    (folder / "SHA256SUMS").write_bytes(lines.encode())


def make_campaign(root: Path, name="2026-08-06_L3") -> Path:
    folder = root / "campaigns" / name
    (folder / "phantom").mkdir(parents=True)
    (folder / "etd").mkdir()
    (folder / "phantom" / CSV_NAME).write_bytes(b"Time_Sec;Pos_H;Pos_V;Pos_R\n0.1;0.0;0.0;0.0\n")
    (folder / "phantom" / QA_NAME).write_bytes(b"Time_Sec;Point_ID\n")
    (folder / "phantom" / f"{LOG_STEM}_log.json").write_bytes(
        json.dumps({"personal": "Student1, QMP1", "csv_file": CSV_NAME, "linac": "3"}).encode())
    (folder / "phantom" / f"{LOG_STEM}_log.txt").write_bytes(b"Datum der Messung : 2026-08-06\n"
                                                             b"Messteam          : Student1, QMP1\n")
    (folder / "etd" / f"{EXPORT}.json").write_bytes(export())
    (folder / "etd" / f"{EXPORT}.png").write_bytes(png())
    (folder / "runs.csv").write_bytes(runs_csv([
        ["13", CSV_NAME, f"{EXPORT}.json", "single angle", "", "OFF", "deflection 1", "true", "", "", ""],
    ]).encode())
    (folder / "protocol.md").write_bytes("# Messprotokoll\n\nMessteam: Student1, QMP1\n".encode())
    write_sums(folder)
    return folder
