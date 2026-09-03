"""Regression tests for external-source license classification."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.onboard_source import discover_repo


class SourceLicenseGateTests(unittest.TestCase):
    @staticmethod
    def _api_for(license_id: str):
        def fake(api_path: str):
            if api_path.startswith("repos/") and "/git/trees/" not in api_path:
                return {
                    "license": {"spdx_id": license_id},
                    "default_branch": "main",
                }
            if "/git/trees/" in api_path:
                return {
                    "truncated": False,
                    "tree": [
                        {
                            "path": "skills/example/SKILL.md",
                            "sha": "abc123",
                            "type": "blob",
                        }
                    ],
                }
            raise AssertionError(f"unexpected API path: {api_path}")

        return fake

    def test_known_conflicting_repo_is_forced_clean_room(self) -> None:
        with patch(
            "scripts.onboard_source.gh_json",
            side_effect=self._api_for("Apache-2.0"),
        ):
            report = discover_repo("https://github.com/forcedotcom/sf-skills")

        self.assertEqual(report["detected_license"], "Apache-2.0")
        self.assertEqual(report["license_class"], "clean-room")
        self.assertIn("CONFLICTING", report["license"])
        self.assertIn("topic discovery only", report["license_reason"])

    def test_normal_mit_repo_remains_permissive(self) -> None:
        with patch(
            "scripts.onboard_source.gh_json",
            side_effect=self._api_for("MIT"),
        ):
            report = discover_repo("https://github.com/example/permissive-skills")

        self.assertEqual(report["detected_license"], "MIT")
        self.assertEqual(report["license"], "MIT")
        self.assertEqual(report["license_class"], "permissive")
        self.assertNotIn("license_reason", report)


if __name__ == "__main__":
    unittest.main()
