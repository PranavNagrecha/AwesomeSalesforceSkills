"""audit_sweep.py: leftover tokens after a correction, and UNVERIFIED markers on corpus-held claims."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_sweep  # noqa: E402


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    skill = repo / "skills" / "apex" / "demo"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Demo\n\nHeap is 6 MB synchronous.\nUse `Database.queryWithBinds` from API 55.0.\n")
    (skill / "references" / "gotchas.md").write_text("## Gotcha 1: Heap is 6 MB synchronous\n\nBody.\n")
    _git(repo, "init", "-q")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "base")
    return repo


def test_leftover_token_in_sibling_file_is_reported(tmp_path, capsys):
    repo = _repo(tmp_path)
    skill = repo / "skills" / "apex" / "demo"
    # writer corrects SKILL.md but forgets the gotcha heading
    (skill / "SKILL.md").write_text("# Demo\n\nHeap is 10 MB synchronous (apexdev 264 L19780).\nUse `Database.queryWithBinds` from API 57.0.\n")
    audit_sweep.main(["--base", "HEAD", "--skills", "skills/apex/demo", "--cwd", str(repo)])
    out = capsys.readouterr().out
    assert "LEFTOVER" in out and "gotchas.md:1" in out and "6 MB" in out
    assert out.strip().splitlines()[-1].startswith("SWEEP leftovers=1")


def test_marker_on_corpus_held_claim_is_flagged(tmp_path, capsys):
    repo = _repo(tmp_path)
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "guide.txt").write_text("Database.queryWithBinds is available in API version 57.0 and later.\n")
    skill = repo / "skills" / "apex" / "demo"
    (skill / "SKILL.md").write_text(
        "# Demo\n\nHeap is 6 MB synchronous.\n"
        "Use `Database.queryWithBinds` from API 57.0. UNVERIFIED (2026-10-20): queryWithBinds version not in corpus.\n"
    )
    audit_sweep.main(["--base", "HEAD", "--skills", "skills/apex/demo", "--cwd", str(repo), "--corpus", str(corpus)])
    out = capsys.readouterr().out
    assert "MARKER" in out and "guide.txt" in out
    assert "marker-hits=1" in out.strip().splitlines()[-1]


def test_cite_check_flags_blank_line(tmp_path, capsys):
    repo = _repo(tmp_path)
    corpus = tmp_path / "corpus264"
    corpus.mkdir()
    (corpus / "salesforce_apex_developer_guide.txt").write_text("line one\n\nTotal heap size 10 MB 25 MB\n")
    skill = repo / "skills" / "apex" / "demo"
    (skill / "SKILL.md").write_text("# Demo\n\nHeap is 10 MB (apexdev 264 L3). Old cite (apexdev 264 L2).\nUse `Database.queryWithBinds` from API 55.0.\n")
    audit_sweep.main(["--base", "HEAD", "--skills", "skills/apex/demo", "--cwd", str(repo), "--corpus", str(corpus)])
    out = capsys.readouterr().out
    assert "CITE     apexdev 264 L3: Total heap size" in out and "apexdev 264 L2: BLANK/TOC" in out
    assert "bad-cites=1" in out.strip().splitlines()[-1]


def test_clean_correction_reports_zero(tmp_path, capsys):
    repo = _repo(tmp_path)
    skill = repo / "skills" / "apex" / "demo"
    (skill / "SKILL.md").write_text("# Demo\n\nHeap is 10 MB synchronous.\nUse `Database.queryWithBinds` from API 55.0.\n")
    (skill / "references" / "gotchas.md").write_text("## Gotcha 1: Heap is 10 MB synchronous\n\nBody.\n")
    audit_sweep.main(["--base", "HEAD", "--skills", "skills/apex/demo", "--cwd", str(repo)])
    assert capsys.readouterr().out.strip().splitlines()[-1].startswith("SWEEP leftovers=0 marker-hits=0")


def test_restatement_without_marker_is_listed(tmp_path, capsys):
    repo = _repo(tmp_path)
    skill = repo / "skills" / "apex" / "demo"
    (skill / "references" / "gotchas.md").write_text(
        "## Gotcha 1: Heap is 6 MB synchronous\n\nBody.\n\n## Gotcha 2\n\nFlow_Limit_500 applies to every ScheduledFlow run.\n"
    )
    (skill / "SKILL.md").write_text(
        "# Demo\n\nHeap is 6 MB synchronous.\nUse `Database.queryWithBinds` from API 55.0.\n"
        "Flow_Limit_500 applies to every ScheduledFlow run. UNVERIFIED (2026-10-20): not in corpus.\n"
    )
    audit_sweep.main(["--base", "HEAD", "--skills", "skills/apex/demo", "--cwd", str(repo)])
    out = capsys.readouterr().out
    assert "RESTATEMENT" in out and "gotchas.md:7" in out
    assert out.strip().splitlines()[-1].endswith("restatements=1")

