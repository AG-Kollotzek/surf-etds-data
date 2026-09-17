import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_names  # noqa: E402
from tests.campaign import png  # noqa: E402

# Synthetic people only. "Erika Mustermann" gave consent to be named, "Jürgen Weiß" did not.
PEOPLE = {
    "people": [
        {"name": "Erika Mustermann", "public_name": "E. Mustermann", "public_name_consent": True,
         "aliases": ["Riki"], "github": ["emuster"], "emails": ["erika.mustermann@example.org",
                                                               "123+emuster@users.noreply.github.com"]},
        {"name": "Jürgen Weiß", "public_name": None, "public_name_consent": False, "aliases": [],
         "github": ["jweiss-lab"], "emails": ["jw@example.org"]},
    ],
    "deny": ["Hansi"],
    "commit_identities": {"allowed": ["E. Mustermann <123+emuster@users.noreply.github.com>"]},
}


class CheckNamesTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.people = self.root.parent / f"{self.root.name}-people.json"
        self.people.write_text(json.dumps(PEOPLE), encoding="utf-8")
        (self.root / "campaigns" / "2026-08-06_L3").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.root)
        self.people.unlink()

    def run_check(self, *extra, people=PEOPLE):
        checker = check_names.Checker(check_names.Names(people))
        check_names.check_paths(checker, [self.root], self.root)
        if "--history" in extra:
            check_names.check_history(checker, self.root)
        return checker.findings

    def write(self, rel, data):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))

    def test_clean(self):
        self.write("README.md", "Maintained by E. Mustermann. Operators: QMP1, Student2.\n")
        self.assertEqual(self.run_check(), [])

    def test_public_name_allowed_outside_campaigns_only(self):
        self.write("CITATION.cff", "family-names: Mustermann\n")
        self.assertEqual(self.run_check(), [])
        self.write("campaigns/2026-08-06_L3/protocol.md", "Messteam: Mustermann\n")
        findings = self.run_check()
        self.assertEqual(len(findings), 1)
        self.assertIn("public name inside campaigns/ m********* (10)", findings[0])

    def test_private_given_name_of_consented_person(self):
        self.write("docs/notes.md", "Thanks to Erika and Riki\n")
        self.assertEqual(len(self.run_check()), 2)

    def test_diacritics_and_sharp_s(self):
        for text in ("Juergen", "Jurgen Weiss", "JÜRGEN WEISS", "Weiß"):
            self.write("docs/a.txt", text + "\n")
            self.assertTrue(self.run_check(), text)

    def test_double_encoded_utf8(self):
        self.write("docs/a.txt", "Messteam: Jürgen".encode("utf-8").decode("latin-1").encode("utf-8"))
        self.assertTrue(self.run_check())

    def test_camel_case_and_underscore(self):
        for name in ("docs/firstTryHansi.csv", "docs/run_hansi.csv", "docs/IDHansi.csv"):
            self.write(name, "x\n")
            self.assertTrue(any(name in f for f in self.run_check()), name)
            (self.root / name).unlink()

    def test_login_and_email(self):
        self.write("docs/a.txt", "see jweiss-lab and jw@example.org\n")
        self.assertEqual(len(self.run_check()), 1 + 1)

    def test_allowed_identity_is_public(self):
        self.write("docs/a.txt", "Co-authored: E. Mustermann <123+emuster@users.noreply.github.com>\n")
        self.assertEqual(self.run_check(), [])

    def test_author_only_name_only_in_citation_files(self):
        people = json.loads(json.dumps(PEOPLE))
        people["people"].append({"name": "Lotte Beispielautorin", "public_name": "L. Beispielautorin",
                                 "public_name_consent": True, "public_name_scope": "authors"})
        self.write("CITATION.cff", "authors:\n  - given-names: L.\n    family-names: Beispielautorin\n")
        self.assertEqual(self.run_check(people=people), [])
        self.write("README.md", "Reviewed by L. Beispielautorin.\n")
        findings = self.run_check(people=people)
        self.assertEqual(len(findings), 1)
        self.assertIn("author name outside CITATION.cff", findings[0])
        self.write("README.md", "Reviewed by Lotte.\n")
        self.assertIn(": name ", self.run_check(people=people)[0])
        self.write("README.md", "clean\n")
        self.write("campaigns/2026-08-06_L3/protocol.md", "Messteam: Beispielautorin\n")
        self.assertIn("public name inside campaigns/", self.run_check(people=people)[0])

    def test_part_of_an_allowed_identity_is_not_enough(self):
        people = json.loads(json.dumps(PEOPLE))
        people["people"][0]["aliases"].append("emu")  # a nickname inside the allowed login "emuster"
        names = check_names.Names(people)
        self.assertIn(("emu", "private"), names.find("signed emu"))
        self.assertIn(("emuster", "public"), names.find("login emuster"))

    def test_zip_member_gzip_and_png(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("notes/Hansi.txt", "x")
        self.write("docs/a.zip", buf.getvalue())
        self.write("docs/b.txt.gz", gzip.compress(b"by Hansi\n"))
        self.write("docs/c.png", png([(b"zTXt", b"Author\0\0" + zlib.compress(b"Hansi"))]))
        self.write("docs/d.png", png([(b"eXIf", b"II*\0\x08\0\0\0Artist Hansi\0")]))
        findings = self.run_check()
        for name in ("a.zip!notes/Hansi.txt", "b.txt.gz (gunzipped)", "c.png (PNG text)", "d.png (PNG text)"):
            self.assertTrue(any(name in f for f in findings), (name, findings))

    def test_utf16(self):
        self.write("docs/a.txt", "Hansi".encode("utf-16-le"))
        self.assertTrue(self.run_check())

    @unittest.skipUnless(shutil.which("git"), "git is needed")
    def test_history(self):
        env = {**os.environ, "GIT_AUTHOR_NAME": "E. Mustermann", "GIT_AUTHOR_EMAIL": "123+emuster@users.noreply.github.com",
               "GIT_COMMITTER_NAME": "E. Mustermann", "GIT_COMMITTER_EMAIL": "123+emuster@users.noreply.github.com",
               "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

        def git(*args):
            subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True, env=env)
        git("init", "-q")
        self.write("docs/a.txt", "Hansi\n")
        git("add", "-A")
        git("commit", "-q", "-m", "add")
        (self.root / "docs" / "a.txt").write_text("clean\n")
        git("commit", "-q", "-am", "thanks Riki")
        findings = self.run_check("--history")
        self.assertTrue(any("history" in f and "docs/a.txt" in f for f in findings), findings)
        self.assertTrue(any(f.startswith("commit ") for f in findings), findings)

    def test_exit_codes(self):
        self.assertEqual(check_names.main([str(self.people), str(self.root)]), 0)
        self.write("docs/a.txt", "Hansi\n")
        self.assertEqual(check_names.main([str(self.people), str(self.root)]), 1)
        self.assertEqual(check_names.main([]), 2)
        bad = self.root.parent / f"{self.root.name}-bad.json"
        bad.write_text("{}")
        try:
            self.assertEqual(check_names.main([str(bad), str(self.root)]), 2)
        finally:
            bad.unlink()

    def test_pdf_needs_pdftotext(self):
        self.write("docs/a.pdf", b"%PDF-1.4\n%%EOF\n")
        old = check_names.shutil.which
        check_names.shutil.which = lambda name: None
        try:
            self.assertEqual(check_names.main([str(self.people), str(self.root)]), 3)
        finally:
            check_names.shutil.which = old


if __name__ == "__main__":
    unittest.main()
