"""Tests for the no-regression depth gate (``validate_depth_gate``) and the
depth scorer (``scripts/score_skill_depth.py``).

Skills are built in ``tmp_path``; "HEAD" is a throwaway git repo created there,
so the NEW-vs-EXISTING decision runs against real ``git ls-tree`` / ``git show``.
Only ``config/skill-frontmatter.schema.json`` is read from the real repository.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from pipelines import validators as V  # noqa: E402
from scripts.score_skill_depth import SIGNALS, score_skill  # noqa: E402

DOMAIN, NAME = "admin", "sample-skill"

FRONT = """---
name: {name}
description: "Sample skill. NOT for anything else."
category: {domain}
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
tags:
  - sample
triggers:
  - "how do I configure the sample thing"
  - "sample thing is not working"
  - "why does the sample thing fail"
  - "set up the sample thing"
  - "audit the sample thing"
inputs:
  - "context"
outputs:
  - "guidance"
dependencies: []
version: {version}
author: Pranav Nagrecha
updated: {updated}
---
"""

QUESTIONS = """
## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which region?" | Decides the calendar | The calendar list |
"""

BODY = """
# Sample

## Recommended Workflow

1. Read the requirement.
2. Build the metadata.

## Metadata

```xml
<CustomObject/>
```
"""

GOTCHAS = "# Gotchas\n\n" + "\n".join(f"## Gotcha {i}: thing\n\nDetail.\n" for i in range(1, 6))
ANTIPAT = "# Anti\n\n" + "\n".join(f"## Anti-Pattern {i}\n\nDetail.\n" for i in range(1, 6))
WAF = "# WAF\n\n## Official Sources Used\n\n" + "\n".join(f"- https://example.com/{i}" for i in range(4)) + "\n"
EXAMPLES = "# Examples\n\n```apex\nSystem.debug(1);\n```\n"
CHECKER = "#!/usr/bin/env python3\nprint('real check')\n"
EXTRA = "# Extra\n\n" + "A real reference paragraph. " * 40 + "\n"


def build_skill(root: Path, *, version="2.0.0", updated="2026-01-01", questions=True,
                extra=EXTRA, checker=CHECKER, xml=True, gotchas=GOTCHAS) -> Path:
    d = root / "skills" / DOMAIN / NAME
    (d / "references").mkdir(parents=True, exist_ok=True)
    (d / "scripts").mkdir(exist_ok=True)
    (d / "templates").mkdir(exist_ok=True)
    body = BODY if xml else BODY.replace("```xml\n<CustomObject/>\n```", "no fence")
    (d / "SKILL.md").write_text(
        FRONT.format(name=NAME, domain=DOMAIN, version=version, updated=updated)
        + (QUESTIONS if questions else "") + body, encoding="utf-8")
    refs = {"gotchas.md": gotchas, "llm-anti-patterns.md": ANTIPAT,
            "well-architected.md": WAF, "examples.md": EXAMPLES}
    for fname, text in refs.items():
        (d / "references" / fname).write_text(text, encoding="utf-8")
    if extra is not None:
        (d / "references" / "extra.md").write_text(extra, encoding="utf-8")
    (d / "scripts" / "check_sample.py").write_text(checker, encoding="utf-8")
    (d / "templates" / "t.txt").write_text("t\n", encoding="utf-8")
    return d


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                    "-c", "core.hooksPath=/dev/null", *args],
                   cwd=root, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    V._head_files.cache_clear()
    git(tmp_path, "init", "-q")
    (tmp_path / "README.md").write_text("x\n", encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "init")
    yield tmp_path
    V._head_files.cache_clear()


def commit(root: Path) -> None:
    V._head_files.cache_clear()
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "skill")
    V._head_files.cache_clear()


def errors(issues):
    return [i for i in issues if i.level == "ERROR"]


# ---------------------------------------------------------------- scorer


def test_built_skill_scores_twelve(tmp_path):
    assert score_skill(build_skill(tmp_path))["score"] == len(SIGNALS)


def test_todos_ignore_scripts_and_templates(tmp_path):
    d = build_skill(tmp_path, checker="# TODO: Implement real checks\nprint(1)\n")
    (d / "templates" / "t.txt").write_text("TODO fill me\n", encoding="utf-8")
    row = score_skill(d)
    assert row["todos"] is True and row["todo_n"] == 0


def test_todos_count_in_prose(tmp_path):
    d = build_skill(tmp_path)
    with (d / "references" / "examples.md").open("a", encoding="utf-8") as fh:
        fh.write("\nTODO later\n")
    assert score_skill(d)["todos"] is False
    d2 = build_skill(tmp_path / "b")
    with (d2 / "SKILL.md").open("a", encoding="utf-8") as fh:
        fh.write("\nTODO: write this\n")
    assert score_skill(d2)["todos"] is False


@pytest.mark.parametrize("size,expected", [(0, False), (499, False), (500, True)])
def test_extras_needs_500_bytes(tmp_path, size, expected):
    d = build_skill(tmp_path, extra="x" * size)
    assert score_skill(d)["extras"] is expected


def test_extras_absent(tmp_path):
    assert score_skill(build_skill(tmp_path, extra=None))["extras"] is False


def test_unverified_n_counts_skill_and_references(tmp_path):
    d = build_skill(tmp_path)
    with (d / "SKILL.md").open("a", encoding="utf-8") as fh:
        fh.write("\n<!-- UNVERIFIED -->\n")
    with (d / "references" / "gotchas.md").open("a", encoding="utf-8") as fh:
        fh.write("\nUNVERIFIED claim. UNVERIFIED again.\n")
    row = score_skill(d)
    assert row["unverified_n"] == 3
    assert row["score"] == len(SIGNALS)  # informational only
    assert "unverified_n" not in SIGNALS


# ---------------------------------------------------------------- gate: new skills


def test_new_skill_at_bar_passes(repo):
    d = build_skill(repo)  # untracked => absent from HEAD => new
    assert errors(V.validate_depth_gate(repo, d)) == []


def test_new_skill_below_bar_errors_and_lists_signals(repo):
    d = build_skill(repo, extra=None, checker="# TODO: Implement real checks\n", xml=False)
    errs = errors(V.validate_depth_gate(repo, d))
    msg = " | ".join(e.message for e in errs)
    assert errs and "extras" in msg and "checker" in msg and "xml" in msg


def test_new_skill_padding_does_not_reach_bar(repo):
    d = build_skill(repo, extra="", checker="# TODO: Implement real checks\n", questions=False, xml=False,
                    gotchas="# G\n\n" + "\n".join(f"## H{i}\n" for i in range(5)))
    row = score_skill(d)
    assert row["extras"] is False and row["score"] < 10
    assert errors(V.validate_depth_gate(repo, d))


def test_new_skill_without_questions_heading_errors(repo):
    d = build_skill(repo, questions=False)
    msg = " | ".join(e.message for e in errors(V.validate_depth_gate(repo, d)))
    assert "Questions to Ask Before Configuring" in msg


@pytest.mark.parametrize("header", [
    "| Question | Why | Adds |",
    "| Ask | Why it matters |",
])
def test_new_skill_with_wrong_questions_header_errors(repo, header):
    d = build_skill(repo)
    p = d / "SKILL.md"
    p.write_text(p.read_text(encoding="utf-8").replace("| Ask | Why it matters | What a good answer adds |", header),
                 encoding="utf-8")
    assert errors(V.validate_depth_gate(repo, d))


def test_questions_header_is_case_insensitive(repo):
    d = build_skill(repo)
    p = d / "SKILL.md"
    p.write_text(p.read_text(encoding="utf-8").replace("| Ask | Why it matters | What a good answer adds |",
                                                       "| ASK | why it matters | What A Good Answer Adds |"),
                 encoding="utf-8")
    assert errors(V.validate_depth_gate(repo, d)) == []


def test_committed_1_0_0_updated_today_is_still_new(repo):
    d = build_skill(repo, version="1.0.0", updated="2026-10-19", questions=False)
    commit(repo)
    assert errors(V.validate_depth_gate(repo, d))


def test_committed_1_0_0_updated_before_cutoff_is_existing(repo):
    d = build_skill(repo, version="1.0.0", updated="2026-10-18", extra=None, questions=False)
    commit(repo)
    assert V.validate_depth_gate(repo, d) == []
    assert V.validate_depth_gate(repo, d, changed_only=True) == []


# ---------------------------------------------------------------- gate: existing skills


def test_existing_untouched_old_skill_gets_no_issue(repo):
    d = build_skill(repo, extra=None, questions=False, xml=False)  # low score, but old
    commit(repo)
    assert V.validate_depth_gate(repo, d) == []
    assert V.validate_depth_gate(repo, d, changed_only=True) == []


def test_existing_regression_errors_in_changed_only(repo):
    d = build_skill(repo)
    commit(repo)
    (d / "references" / "extra.md").unlink()
    errs = errors(V.validate_depth_gate(repo, d, changed_only=True))
    assert errs and "regress" in errs[0].message.lower()
    # full sweep does not judge untouched-or-edited old skills
    assert V.validate_depth_gate(repo, d) == []


def test_existing_without_regression_is_clean(repo):
    d = build_skill(repo, extra=None)
    commit(repo)
    (d / "references" / "extra.md").write_text(EXTRA, encoding="utf-8")  # improves
    assert V.validate_depth_gate(repo, d, changed_only=True) == []
    (d / "SKILL.md").write_text((d / "SKILL.md").read_text(encoding="utf-8") + "\nmore prose\n", encoding="utf-8")
    assert V.validate_depth_gate(repo, d, changed_only=True) == []


# ---------------------------------------------------------------- schema pattern


def _pattern():
    schema = json.loads((REPO_ROOT / "config" / "skill-frontmatter.schema.json").read_text(encoding="utf-8"))
    return schema["properties"]["salesforce-version"]["pattern"]


@pytest.mark.parametrize("value", [
    "Spring '25+",
    "Summer '26+ (API 67.0+, GA)",
    "Spring '25+; verified against Apex Developer Guide v67.0, Summer '26",
    "Winter '26+",
])
def test_version_pattern_accepts(value):
    assert re.search(_pattern(), value)


@pytest.mark.parametrize("value", ["Spring '25+'", "TODO", "Fall '25+", "Spring 25+", "Spring '25"])
def test_version_pattern_rejects(value):
    assert not re.search(_pattern(), value)


def test_repo_skills_all_match_version_pattern():
    pat = _pattern()
    bad = []
    for p in (REPO_ROOT / "skills").glob("*/*/SKILL.md"):
        m = re.search(r'^salesforce-version:\s*"(.*)"\s*$', p.read_text(encoding="utf-8"), re.M)
        if not m or not re.search(pat, m.group(1)):
            bad.append(str(p))
    assert bad == []
