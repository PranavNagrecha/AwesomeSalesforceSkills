"""Live-tree version-consistency gate."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "scripts"))
import check_release_versions as crv  # noqa: E402


class ReleaseVersionConsistencyTests(unittest.TestCase):
    def test_plugin_and_mcp_sources_agree(self) -> None:
        issues = crv.collect_issues()
        self.assertEqual(issues, [], msg="\n".join(issues))

    def test_required_keys_present(self) -> None:
        versions = crv.collect_versions()
        self.assertTrue(versions["plugin_source"])
        self.assertTrue(versions["mcp_pyproject"])
        self.assertTrue(versions["mcp_dunder"])


if __name__ == "__main__":
    unittest.main()
