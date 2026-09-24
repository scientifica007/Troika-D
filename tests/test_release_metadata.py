from pathlib import Path
import re
import tomllib
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

PYTHON_VERSION = "0.1.0b1"
PUBLIC_VERSION = "0.1.0-beta.1"


class ReleaseMetadataTests(unittest.TestCase):
    def test_python_versions_match(self):
        with (ROOT / "pyproject.toml").open("rb") as handle:
            project = tomllib.load(handle)
        self.assertEqual(project["project"]["version"], PYTHON_VERSION)

        init_text = (
            ROOT / "src" / "ubuntu_screen_recorder" / "__init__.py"
        ).read_text(encoding="utf-8")
        match = re.search(
            r'^__version__\s*=\s*"([^"]+)"',
            init_text,
            re.MULTILINE,
        )
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), PYTHON_VERSION)

    def test_appstream_public_release_version_matches(self):
        appstream = ET.parse(
            ROOT
            / "data"
            / "io.github.scientifica007.TroikaD.metainfo.xml"
        ).getroot()
        release = appstream.find("./releases/release")
        self.assertIsNotNone(release)
        self.assertEqual(release.attrib["version"], PUBLIC_VERSION)
        self.assertEqual(release.attrib["date"], "2026-09-24")

    def test_changelog_and_release_notes_cover_public_version(self):
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        notes = (
            ROOT / "docs" / f"RELEASE-NOTES-{PUBLIC_VERSION}.md"
        ).read_text(encoding="utf-8")
        self.assertIn(f"[{PUBLIC_VERSION}]", changelog)
        self.assertIn(f"v{PUBLIC_VERSION}", notes)


if __name__ == "__main__":
    unittest.main()
