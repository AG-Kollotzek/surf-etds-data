import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import prepare_campaign  # noqa: E402
import validate  # noqa: E402
from tests.campaign import CSV_NAME, EXPORT, export, make_campaign  # noqa: E402


class PrepareTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.folder = make_campaign(self.root)

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_prepared_campaign_needs_no_change(self):
        self.assertEqual(prepare_campaign.prepare(self.folder, check=True), [])

    def test_fixes_line_endings_workstation_name_and_sums(self):
        (self.folder / "phantom" / CSV_NAME).write_bytes(b"\xef\xbb\xbfTime_Sec;Pos_H\r\n0.1;0.0\r\n")
        (self.folder / "etd" / f"{EXPORT}.json").write_bytes(export("ETD" + "LINAC3"))
        self.assertEqual(prepare_campaign.main([str(self.folder), "--check"]), 1)
        changes = prepare_campaign.prepare(self.folder, check=False)
        self.assertEqual(sorted(changes), sorted([f"phantom/{CSV_NAME}", f"etd/{EXPORT}.json", "SHA256SUMS"]))
        self.assertEqual((self.folder / "phantom" / CSV_NAME).read_bytes(), b"Time_Sec;Pos_H\n0.1;0.0\n")
        self.assertEqual((self.folder / "etd" / f"{EXPORT}.json").read_bytes(), export("ETD-L3"))
        self.assertEqual(validate.validate(self.root), [])

    def test_workstation_name_must_match_campaign(self):
        (self.folder / "etd" / f"{EXPORT}.json").write_bytes(export("ETD" + "LINAC4"))
        with self.assertRaises(prepare_campaign.DataError):
            prepare_campaign.prepare(self.folder, check=False)
        self.assertEqual((self.folder / "etd" / f"{EXPORT}.json").read_bytes(), export("ETD" + "LINAC4"))

    def test_rejects_other_folders(self):
        self.assertEqual(prepare_campaign.main([str(self.root)]), 2)


if __name__ == "__main__":
    unittest.main()
