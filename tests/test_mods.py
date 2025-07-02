import unittest
from pathlib import Path
import json

import mods


class ModTestBasic(unittest.TestCase):
    def test_mod_version(self):
        subs = {"128.35.58": "128.35.58", "1": "1.0.0"}
        for given, expect in subs.items():
            with self.subTest("sub", given=given, expect=expect) as sub:
                self.assertEqual(str(mods.ModVersion(given)), expect)

    def test_parse_all_deps(self):
        for mod in self.data["results"]:
            with self.subTest("mod", mod_name=mod["name"]):
                for release in mod["releases"]:
                    self.assertIsNotNone(release["info_json"].get("dependencies"))
                    dep_arr = release["info_json"].get("dependencies", [])
                    if not dep_arr:
                        continue
                    if release["info_json"]["factorio_version"] != "2.0":
                        continue
                    with self.subTest(
                        "release",
                        v=release["version"],
                        fv=release["info_json"]["factorio_version"],
                    ):
                        deps = mods.Dependencies(dep_arr)

    @classmethod
    def setUpClass(cls) -> None:
        with (Path(__file__).parent / "mod_test_data.json").open(encoding="utf8") as fp:
            cls.data = json.load(fp)
        return super().setUpClass()
