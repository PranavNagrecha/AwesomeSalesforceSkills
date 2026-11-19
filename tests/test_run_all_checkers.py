"""run_all_checkers.py must invoke each checker with the argument that checker
declares, and must never report a checker that failed to run as a finding."""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "run_all_checkers", ROOT / "scripts" / "run_all_checkers.py"
)
runner = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = runner
_spec.loader.exec_module(runner)


def _checker(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "check_demo.py"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def _argparse_checker(tmp_path: Path, argument: str, tail: str) -> Path:
    return _checker(
        tmp_path,
        f"""
        import argparse, sys
        p = argparse.ArgumentParser()
        p.add_argument({argument})
        a = p.parse_args()
        {tail}
        """,
    )


def test_manifest_dir_checker_is_called_with_manifest_dir(tmp_path):
    checker = _argparse_checker(
        tmp_path, '"--manifest-dir", required=True',
        'print("WARN: " + a.manifest_dir, file=sys.stderr); sys.exit(0)',
    )
    result = runner._run_one("demo/demo", checker, tmp_path, 30)
    assert result.error is None
    assert result.findings == [str(tmp_path)]
    assert result.had_findings


def test_positional_path_checker_gets_a_bare_path(tmp_path):
    checker = _argparse_checker(
        tmp_path, '"paths", nargs="*"',
        'print("HIGH " + a.paths[0]); sys.exit(1)',
    )
    result = runner._run_one("demo/demo", checker, tmp_path, 30)
    assert result.error is None
    assert result.findings == [f"HIGH: {tmp_path}"]


def test_document_only_checker_is_skipped_not_run(tmp_path):
    checker = _argparse_checker(tmp_path, '"--docs-dir", required=True', "sys.exit(1)")
    result = runner._run_one("demo/demo", checker, tmp_path, 30)
    assert result.skipped
    assert result.error is None
    assert not result.had_findings


def test_usage_error_is_an_error_not_a_finding(tmp_path):
    # Declares --root in a comment-free way the runner recognises, but argparse
    # also requires an option the runner cannot supply.
    checker = _checker(
        tmp_path,
        """
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument("--root", required=True)
        p.add_argument("--ticket", required=True)
        p.parse_args()
        """,
    )
    result = runner._run_one("demo/demo", checker, tmp_path, 30)
    assert result.exit_code == 2
    assert result.error and result.error.startswith("usage error")
    assert not result.had_findings


def test_traceback_exit_is_an_error_not_a_finding(tmp_path):
    checker = _argparse_checker(tmp_path, '"--manifest-dir"', 'raise RuntimeError("boom")')
    result = runner._run_one("demo/demo", checker, tmp_path, 30)
    assert result.error and "no parseable finding" in result.error
    assert not result.had_findings


def test_parse_findings_keeps_severity_and_ignores_info():
    out = "\n".join(
        [
            "WARN: a.cls: one",
            "[2] ISSUE: b.cls: two",
            "CRITICAL c.cls three",
            "[ERROR] d.cls four",
            "INFO: nothing to see",
            "3 finding(s): 0 ERROR, 0 WARN, 3 INFO",
        ]
    )
    assert runner._parse_findings(out, "") == [
        "a.cls: one",
        "ISSUE: b.cls: two",
        "CRITICAL: c.cls three",
        "ERROR: d.cls four",
    ]
