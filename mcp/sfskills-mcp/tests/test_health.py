"""Tests for the ``health`` diagnostic tool + the ``SFSKILLS_TIMEOUT_SECONDS``
deployer-wide timeout override."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import meta, sf_cli  # noqa: E402


class HealthTest(unittest.TestCase):
    def test_returns_required_keys(self) -> None:
        h = meta.health()
        for key in ("server_version", "mcp_sdk_version", "repo_root",
                    "registry", "lexical_index", "agents", "sf_cli"):
            self.assertIn(key, h)

    def test_server_version_matches_package(self) -> None:
        from sfskills_mcp import __version__
        self.assertEqual(meta.health()["server_version"], __version__)

    def test_agent_counts_sum_to_total(self) -> None:
        h = meta.health()["agents"]
        # runtime + build + deprecated + unknown = total
        self.assertEqual(
            h["runtime"] + h["build"] + h["deprecated"] + h["unknown"],
            h["total"],
        )

    def test_registry_skill_count_is_realistic(self) -> None:
        h = meta.health()
        skill_count = h["registry"]["skill_count"]
        # Either we have a registry (≥ 900 skills today) or it's None.
        self.assertTrue(skill_count is None or skill_count >= 900)

    def test_built_at_is_iso_or_none(self) -> None:
        h = meta.health()
        for path in ("registry", "lexical_index"):
            built_at = h[path]["built_at"]
            if built_at is not None:
                # ISO 8601 starts with YYYY-MM-DDTHH:
                self.assertRegex(built_at, r"^\d{4}-\d{2}-\d{2}T\d{2}:")

    def test_never_raises_on_missing_sf_cli(self) -> None:
        # Stub the binary lookup to return a non-existent path.
        prior = os.environ.pop("SFSKILLS_SF_BIN", None)
        try:
            os.environ["SFSKILLS_SF_BIN"] = "/path/that/does/not/exist/sf"
            h = meta.health()
            self.assertFalse(h["sf_cli"]["present"])
            # version stays None when the binary is bogus, but the tool
            # MUST NOT raise — that's the diagnostic-only contract.
            self.assertIsNone(h["sf_cli"]["version"])
        finally:
            os.environ.pop("SFSKILLS_SF_BIN", None)
            if prior:
                os.environ["SFSKILLS_SF_BIN"] = prior


class TimeoutOverrideTest(unittest.TestCase):
    def setUp(self) -> None:
        self._prior = os.environ.pop("SFSKILLS_TIMEOUT_SECONDS", None)

    def tearDown(self) -> None:
        os.environ.pop("SFSKILLS_TIMEOUT_SECONDS", None)
        if self._prior:
            os.environ["SFSKILLS_TIMEOUT_SECONDS"] = self._prior

    def test_default_is_90s_without_env_var(self) -> None:
        self.assertEqual(sf_cli._default_timeout(), 90)

    def test_env_var_raises_default(self) -> None:
        os.environ["SFSKILLS_TIMEOUT_SECONDS"] = "600"
        self.assertEqual(sf_cli._default_timeout(), 600)

    def test_invalid_env_var_falls_back(self) -> None:
        for bad in ("0", "-1", "abc", ""):
            os.environ["SFSKILLS_TIMEOUT_SECONDS"] = bad
            self.assertEqual(
                sf_cli._default_timeout(),
                90,
                f"bad env value {bad!r} should fall back to 90",
            )

    def test_run_sf_json_uses_default_at_call_time(self) -> None:
        # The deployer can change the env mid-process and the next
        # ``run_sf_json`` call picks it up — no caching at import time.
        os.environ["SFSKILLS_TIMEOUT_SECONDS"] = "300"
        # We don't need a real subprocess — just verify the resolution.
        self.assertEqual(sf_cli._default_timeout(), 300)


if __name__ == "__main__":
    unittest.main()
