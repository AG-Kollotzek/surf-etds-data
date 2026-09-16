import json
import shutil
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import validate  # noqa: E402
from tests.campaign import CSV_NAME, EXPORT, LOG_STEM, export, make_campaign, png, runs_csv, write_sums  # noqa: E402


class ValidateTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.folder = make_campaign(self.root)

    def tearDown(self):
        shutil.rmtree(self.root)

    def problems(self, resum=True):
        if resum:
            write_sums(self.folder)
        return [f"{path}: {message}" for path, message in validate.validate(self.root)]

    def assertProblem(self, text, resum=True):
        problems = self.problems(resum)
        self.assertTrue(any(text in p for p in problems), problems)

    def test_valid_campaign(self):
        self.assertEqual(self.problems(), [])

    def test_campaign_id(self):
        self.folder = self.folder.rename(self.folder.with_name("2026-08-06_Linac3"))
        self.assertProblem("campaign folder must be named")

    def test_invalid_date(self):
        self.folder = self.folder.rename(self.folder.with_name("2026-02-30_L3"))
        self.assertProblem("campaign folder must be named")

    def test_unexpected_entry(self):
        (self.folder / "notes.txt").write_text("x")
        self.assertProblem("unexpected entry")

    def test_crlf(self):
        (self.folder / "phantom" / CSV_NAME).write_bytes(b"Time_Sec;Pos_H\r\n0.1;0.0\r\n")
        self.assertProblem("carriage return")

    def test_bom(self):
        (self.folder / "protocol.md").write_bytes(b"\xef\xbb\xbf# Messprotokoll\n")
        self.assertProblem("byte order mark")

    def test_invalid_json(self):
        (self.folder / "phantom" / f"{LOG_STEM}_log.json").write_text('{"personal": ')
        self.assertProblem("invalid JSON")

    def test_original_workstation_name(self):
        (self.folder / "etd" / f"{EXPORT}.json").write_bytes(export("ETD" + "LINAC3"))
        self.assertProblem("computerName must be the first field")

    def test_computer_name_linac_mismatch(self):
        (self.folder / "etd" / f"{EXPORT}.json").write_bytes(export("ETD-L4"))
        self.assertProblem("does not match campaign linac L3")

    def test_export_in_campaign_without_linac(self):
        self.folder = self.folder.rename(self.folder.with_name("2026-08-06_LX"))
        self.assertProblem("without a linac number")

    def test_operator_name_in_json(self):
        (self.folder / "phantom" / f"{LOG_STEM}_log.json").write_text(json.dumps({"personal": "Erika, QMP1"}))
        self.assertProblem("operator field is not a role code list")

    def test_operator_name_in_txt(self):
        (self.folder / "phantom" / f"{LOG_STEM}_log.txt").write_text("Messteam : Erika\n")
        self.assertProblem("operator field is not a role code list")

    def test_json_and_txt_differ(self):
        (self.folder / "phantom" / f"{LOG_STEM}_log.txt").write_text("Messteam : Student1\n")
        self.assertProblem("differ")

    def test_log_pair_missing(self):
        (self.folder / "phantom" / f"{LOG_STEM}_log.txt").unlink()
        self.assertProblem("needs both")

    def test_email(self):
        (self.folder / "protocol.md").write_text("Kontakt: erika.mustermann@example.org\n")
        self.assertProblem("e-mail address")

    def test_home_path(self):
        (self.folder / "protocol.md").write_text("Datei: C:\\Users\\erika\\Desktop\\x.csv\n")
        self.assertProblem("home path")

    def test_cloud_path(self):
        (self.folder / "protocol.md").write_text("Datei: OneDrive/Messung/x.csv\n")
        self.assertProblem("cloud or volume path")

    def test_host_name(self):
        (self.folder / "protocol.md").write_text("Rechner DESKTOP-4F7K2Q9\n")
        self.assertProblem("host name")

    def test_earlier_operator_code(self):
        (self.folder / "protocol.md").write_text("Messteam: Operator B\n")
        self.assertProblem("earlier operator code")

    def test_png_text_chunk(self):
        (self.folder / "etd" / f"{EXPORT}.png").write_bytes(png([(b"zTXt", b"Author\0\0" + zlib.compress(b"erika@example.org"))]))
        self.assertProblem("in a PNG text chunk")

    def test_date_token(self):
        (self.folder / "phantom" / CSV_NAME).rename(self.folder / "phantom" / "ETsurface_easyQA_20260807_163851.csv")
        self.assertProblem("does not match the campaign")

    def test_runs_header(self):
        (self.folder / "runs.csv").write_text("run,csv\n")
        self.assertProblem("header must be")

    def test_runs_missing_reference(self):
        (self.folder / "runs.csv").write_text(runs_csv([["13", "missing.csv", "", "", "", "", "", "true", "", "", ""]]))
        self.assertProblem("is not in phantom/")

    def test_runs_unlisted_export(self):
        (self.folder / "runs.csv").write_text(runs_csv([["", CSV_NAME, "", "", "", "", "", "false", "", "", ""]]))
        self.assertProblem("is not listed")

    def test_sums_wrong_checksum(self):
        write_sums(self.folder)
        (self.folder / "protocol.md").write_text("# changed\n")
        self.assertProblem("checksum of protocol.md does not match", resum=False)

    def test_sums_missing_file(self):
        write_sums(self.folder)
        (self.folder / "xray").mkdir()
        (self.folder / "xray" / "readouts.csv").write_text("point\n1\n")
        self.assertProblem("does not list exactly the campaign files", resum=False)

    def test_sums_unsorted(self):
        write_sums(self.folder)
        path = self.folder / "SHA256SUMS"
        path.write_text("".join(reversed(path.read_text().splitlines(keepends=True))))
        self.assertProblem("not sorted", resum=False)

    def test_symlink(self):
        (self.folder / "phantom" / "link.csv").symlink_to(self.folder / "phantom" / CSV_NAME)
        self.assertProblem("symbolic links are not allowed")

    def test_sums_path_outside_campaign(self):
        write_sums(self.folder)
        with open(self.folder / "SHA256SUMS", "a") as fh:
            fh.write("0" * 64 + "  ../../outside.txt\n")
        self.assertProblem("path must stay inside the campaign folder", resum=False)

    def test_bom_is_reported_once(self):
        path = self.folder / "phantom" / f"{LOG_STEM}_log.json"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        problems = self.problems()
        self.assertTrue(any("byte order mark" in p for p in problems), problems)
        self.assertFalse(any("invalid JSON" in p for p in problems), problems)

    def test_file_too_large(self):
        old = validate.MAX_SIZE
        validate.MAX_SIZE = 10
        try:
            self.assertProblem("larger than")
        finally:
            validate.MAX_SIZE = old

    def test_repository_data_are_valid(self):
        root = Path(__file__).resolve().parents[2]
        if (root / "campaigns").is_dir():
            self.assertEqual(validate.validate(root), [])


if __name__ == "__main__":
    unittest.main()
