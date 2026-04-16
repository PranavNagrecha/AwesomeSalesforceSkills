"""Smoke tests for the sf CLI wrapper.

The wrapper is tested without requiring the real ``sf`` binary by pointing
``SFSKILLS_SF_BIN`` at a stubbed script we generate into a tmp dir. This keeps
tests hermetic and lets CI run without Salesforce CLI installed.
"""

from __future__ import annotations

import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import sf_cli  # noqa: E402


def _write_stub(path: Path, *, exit_code: int, stdout: str, stderr: str = "") -> None:
    body = (
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"sys.stdout.write({stdout!r})\n"
        f"sys.stderr.write({stderr!r})\n"
        f"sys.exit({exit_code})\n"
    )
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


class SfCliWrapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.stub = Path(self.tmp.name) / "sf"
        os.environ["SFSKILLS_SF_BIN"] = str(self.stub)

    def tearDown(self) -> None:
        os.environ.pop("SFSKILLS_SF_BIN", None)

    def test_successful_json_is_parsed(self) -> None:
        _write_stub(self.stub, exit_code=0, stdout='{"status": 0, "result": {"ok": true}}')
        payload = sf_cli.run_sf_json(["org", "display"])
        self.assertEqual(payload["status"], 0)
        self.assertEqual(payload["result"], {"ok": True})

    def test_nonzero_exit_surfaces_error(self) -> None:
        _write_stub(
            self.stub,
            exit_code=1,
            stdout='{"status": 1, "message": "No target org set"}',
            stderr="auth error",
        )
        payload = sf_cli.run_sf_json(["org", "display"])
        self.assertIn("error", payload)
        self.assertEqual(payload["status"], 1)
        self.assertIn("No target org set", payload["error"])

    def test_invalid_json_is_handled(self) -> None:
        _write_stub(self.stub, exit_code=0, stdout="not-json")
        payload = sf_cli.run_sf_json(["org", "display"])
        self.assertIn("error", payload)
        self.assertIn("did not return valid JSON", payload["error"])

    def test_missing_binary_returns_actionable_error(self) -> None:
        os.environ["SFSKILLS_SF_BIN"] = str(Path(self.tmp.name) / "does-not-exist")
        payload = sf_cli.run_sf_json(["org", "display"])
        self.assertIn("error", payload)
        self.assertGreaterEqual(payload["status"], 126)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
