"""Unit tests for scripts.bootstrap.classify_verify exit-code matrix."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts import bootstrap  # noqa: E402


def test_classify_verify_ok_in_sync() -> None:
    code, headline, detail = bootstrap.classify_verify(True, 90, 90, True)
    assert code == 0
    assert headline == ""
    assert detail == ""


def test_classify_verify_ok_commands_stale() -> None:
    code, headline, detail = bootstrap.classify_verify(True, 67, 90, True)
    assert code == 2
    assert "RETRIEVAL OK" in headline
    assert "install_local_commands.py" in headline
    assert "BOOTSTRAP FAILED" not in headline
    assert detail == "FAIL  67 slash commands installed, 90 in commands/"


def test_classify_verify_retrieval_broken_in_sync() -> None:
    code, headline, detail = bootstrap.classify_verify(False, 90, 90, True)
    assert code == 1
    assert headline.startswith("BOOTSTRAP FAILED")
    assert detail == ""


def test_classify_verify_ok_skip_commands() -> None:
    code, headline, detail = bootstrap.classify_verify(True, None, None, False)
    assert code == 0
    assert headline == ""
    assert detail == ""
