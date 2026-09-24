from configparser import ConfigParser
from pathlib import Path
import tomllib
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
APP_ID = "io.github.scientifica007.TroikaD"


class BrandingTests(unittest.TestCase):
    def test_python_project_exposes_troika_d_command(self):
        with (ROOT / "pyproject.toml").open("rb") as handle:
            project = tomllib.load(handle)
        self.assertEqual(project["project"]["name"], "troika-d")
        self.assertEqual(
            project["project"]["scripts"]["troika-d"],
            "ubuntu_screen_recorder.app:main",
        )

    def test_desktop_launcher_identity_is_consistent(self):
        parser = ConfigParser(interpolation=None)
        parser.optionxform = str
        parser.read(
            ROOT / "data" / f"{APP_ID}.desktop",
            encoding="utf-8",
        )
        desktop = parser["Desktop Entry"]
        self.assertEqual(desktop["Name"], "Troika D")
        self.assertEqual(desktop["Exec"], "troika-d")
        self.assertEqual(desktop["Icon"], APP_ID)

    def test_appstream_identity_is_consistent(self):
        root = ET.parse(
            ROOT / "data" / f"{APP_ID}.metainfo.xml"
        ).getroot()
        self.assertEqual(root.findtext("id"), APP_ID)
        self.assertEqual(root.findtext("name"), "Troika D")
        self.assertEqual(
            root.findtext("project_license"),
            "GPL-3.0-or-later",
        )
        self.assertEqual(
            root.findtext("launchable"),
            f"{APP_ID}.desktop",
        )

    def test_repository_declares_gpl3_or_later(self):
        license_file = ROOT / "LICENSE"
        self.assertTrue(license_file.is_file())
        text = license_file.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("GNU GENERAL PUBLIC LICENSE"))
        self.assertIn("Version 3, 29 June 2007", text)

        with (ROOT / "pyproject.toml").open("rb") as handle:
            project = tomllib.load(handle)
        self.assertIn(
            "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
            project["project"]["classifiers"],
        )

        self.assertTrue((ROOT / "RESPONSIBLE_USE.md").is_file())
        self.assertTrue((ROOT / "TRADEMARKS.md").is_file())

    def test_scalable_icon_exists_with_product_title(self):
        icon = (
            ROOT
            / "data"
            / "icons"
            / "hicolor"
            / "scalable"
            / "apps"
            / f"{APP_ID}.svg"
        )
        self.assertTrue(icon.is_file())
        root = ET.parse(icon).getroot()
        ns = {"svg": "http://www.w3.org/2000/svg"}
        self.assertEqual(
            root.findtext("svg:title", namespaces=ns),
            "Troika D",
        )


if __name__ == "__main__":
    unittest.main()
