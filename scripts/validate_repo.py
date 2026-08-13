#!/usr/bin/env python3
"""Validate skills, agents, manifests, and generated retrieval artifacts.

Wave-1 rewrite: sharded + changed-only + in-process fixture validation.

The three flags that matter:
  --changed-only   Only validate skills/agents touched by the current git diff
                   (HEAD + staged). Always runs the generated-artifact drift
                   check. Used by the pre-commit hook — < 5 s on a 1-file change.
  --shard N/M      Partition skills by stable hash(skill_id) % M and validate
                   only the N-th bucket (0-indexed). Used by CI matrix jobs.
  --domain X       Restrict to skills under skills/X/. Used for local work.

These three are composable. Without any of them, the full repo is validated.

Fixture validation used to spawn 744+ subprocesses calling search_knowledge.py
(one per fixture). We now import ``build_search_context`` + ``run_search``
from it and loop in-process — same correctness, 60x faster.

Per-skill script ``--help`` checks still need subprocesses (they're arbitrary
user-authored entrypoints) but we run them in a bounded ThreadPoolExecutor so
N skills * ~100 ms becomes ~N/8 * ~100 ms wall clock.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import py_compile
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines.registry_builder import discover_skill_dirs
from pipelines.sync_engine import build_state, diff_state
from pipelines.validators import (
    ValidationIssue,
    validate_frontmatter,
    validate_knowledge_source,
    validate_official_sources_uniqueness,
    validate_skill_authoring_style,
    validate_skill_registry_record,
    validate_skill_similarity,
    validate_skill_structure,
)
from pipelines.knowledge_builder import load_sources_manifest
from pipelines.agent_validators import validate_agents
from pipelines.frontmatter import parse_markdown_with_frontmatter
from scripts.search_knowledge import build_search_context, run_search
from scripts.check_doc_counts import collect_doc_count_issues
from scripts.check_decision_trees import collect_decision_tree_issues
from scripts.check_agent_citation_parity import collect_citation_parity_issues
# Single source of truth for "this description restates the slug". Imported,
# never reimplemented: the writer (patch_agent_skill.py) rejects echo stubs at
# creation time and this gate rejects them at review time, and the two must not
# be able to drift apart.
from scripts.patch_agent_skill import is_echo_description


# Thread pool size for parallel subprocess fan-out on skill-local scripts.
# os.cpu_count() is often 8-12 on dev machines and 2-4 on CI runners; capping
# at 8 keeps CI runners from oversubscribing while still giving local dev the
# full win.
MAX_WORKERS = min(os.cpu_count() or 4, 8)


def print_issue(issue: ValidationIssue) -> None:
    print(f"{issue.level} {issue.path}: {issue.message}")


# ---------------------------------------------------------------------------
# Per-skill validator (pure, safe to fan out)
# ---------------------------------------------------------------------------

@dataclass
class SkillRecord:
    skill_id: str
    name: str
    path: Path
    issues: list[ValidationIssue]


def _check_skill_local_script(script_path: Path, cwd: Path) -> list[ValidationIssue]:
    """py_compile + ``--help`` smoke for a single skill-local helper script.

    Returns a list so the caller can extend() without special-casing empty.
    Runs the ``--help`` subprocess — this is the IO-bound step we parallelize.
    """
    issues: list[ValidationIssue] = []
    try:
        py_compile.compile(str(script_path), doraise=True)
    except py_compile.PyCompileError as exc:
        issues.append(
            ValidationIssue("ERROR", str(script_path), f"py_compile failed: {exc.msg}")
        )
        return issues  # no point running --help on an uncompilable script
    help_run = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if help_run.returncode != 0:
        issues.append(ValidationIssue("ERROR", str(script_path), "--help exited non-zero"))
    return issues


def validate_one_skill(skill_dir: Path, root: Path) -> SkillRecord:
    """Validate a single skill's structure + frontmatter. Does NOT run the
    script ``--help`` check (that's parallelized separately). Returns a
    SkillRecord that includes the skill_id / name so the driver can detect
    duplicates across the whole set."""
    skill_path = skill_dir / "SKILL.md"
    issues: list[ValidationIssue] = []
    issues.extend(validate_skill_structure(skill_dir))
    issues.extend(validate_frontmatter(root, skill_path))
    issues.extend(validate_skill_authoring_style(skill_dir))

    skill_id = ""
    name = ""
    try:
        parsed = parse_markdown_with_frontmatter(skill_path)
        metadata = parsed.metadata
        name = metadata["name"]
        skill_id = f"{metadata['category']}/{name}"
    except Exception as exc:
        issues.append(
            ValidationIssue("ERROR", str(skill_path), f"unable to parse frontmatter: {exc}")
        )
    return SkillRecord(skill_id=skill_id, name=name, path=skill_path, issues=issues)


# ---------------------------------------------------------------------------
# Partitioning: --shard, --domain, --changed-only
# ---------------------------------------------------------------------------

def _stable_shard(skill_id: str, total_shards: int) -> int:
    """Hash-based shard assignment. MD5 is used not for security but because
    it's available in stdlib and has good distribution. Value mod total_shards
    is deterministic across machines and Python versions."""
    digest = hashlib.md5(skill_id.encode("utf-8")).hexdigest()
    return int(digest, 16) % total_shards


def _parse_shard_spec(spec: str) -> tuple[int, int]:
    """Parse ``N/M`` into ``(n, m)`` with bounds checking."""
    try:
        n_str, m_str = spec.split("/", 1)
        n, m = int(n_str), int(m_str)
    except (ValueError, AttributeError) as exc:
        raise argparse.ArgumentTypeError(
            f"--shard must be N/M with integers, got {spec!r}"
        ) from exc
    if m <= 0 or n < 0 or n >= m:
        raise argparse.ArgumentTypeError(
            f"--shard {spec!r}: need 0 <= N < M and M > 0"
        )
    return n, m


def _git_changed_files(root: Path) -> set[Path] | None:
    """Return paths the user is preparing to commit, relative to ``root``.

    Scope is **staged-only** when there are staged paths (the pre-commit
    hook's natural scope). Falls back to staged + unstaged + untracked
    when nothing is staged — that's the interactive "what does my working
    tree look like" use case.

    Returns None if we're not in a git repo or git fails — the caller
    should fall back to full validation in that case.

    Pre-commit semantics matter here: the hook is gating "what is about
    to land in HEAD", not "everything I have on disk". A pre-existing
    untracked WIP skill scaffold (e.g. someone left
    skills/devops/foo/SKILL.md half-filled in) would otherwise block any
    unrelated commit (infra, docs, evals) from going through.
    """
    try:
        staged = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            cwd=root, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        if any(p.strip() for p in staged):
            return {Path(p) for p in staged if p.strip()}
        # Nothing staged — interactive use. Include unstaged + untracked.
        unstaged = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=root, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=root, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return {Path(p) for p in (unstaged + untracked) if p.strip()}


def _changed_skill_dirs(root: Path, all_skill_dirs: list[Path]) -> set[Path] | None:
    """Of the discovered skill dirs, which ones have at least one file
    touched in the current git diff? Returns None if git info unavailable."""
    changed = _git_changed_files(root)
    if changed is None:
        return None
    hits: set[Path] = set()
    for skill_dir in all_skill_dirs:
        rel = skill_dir.relative_to(root)
        for p in changed:
            try:
                p.relative_to(rel)
            except ValueError:
                continue
            hits.add(skill_dir)
            break
        else:
            # also match if the skill_dir itself is a prefix of the path
            for p in changed:
                if str(p).startswith(f"{rel}/") or Path(p) == rel / "SKILL.md":
                    hits.add(skill_dir)
                    break
    return hits


def _filter_skill_dirs(
    all_skill_dirs: list[Path],
    domain: str | None,
    shard: tuple[int, int] | None,
    changed_only: bool,
    root: Path,
) -> list[Path]:
    """Apply --domain, --shard, --changed-only to the discovered skill set.
    Filters compose: --domain narrows, --shard partitions the narrowed list,
    --changed-only intersects the partitioned list with git-touched skills."""
    pool = list(all_skill_dirs)
    if domain:
        pool = [p for p in pool if p.relative_to(root).parts[1] == domain]
    if shard:
        n, m = shard
        pool = [
            p for p in pool
            if _stable_shard(
                f"{p.relative_to(root).parts[1]}/{p.name}", m
            ) == n
        ]
    if changed_only:
        touched = _changed_skill_dirs(root, pool)
        if touched is None:
            # git unavailable — conservatively run the full pool
            print(
                "WARN: --changed-only could not query git; running full filtered set",
                file=sys.stderr,
            )
        else:
            pool = [p for p in pool if p in touched]
    return pool


# ---------------------------------------------------------------------------
# Skill validation (orchestrator)
# ---------------------------------------------------------------------------

def run_skill_validation(
    *,
    domain: str | None = None,
    shard: tuple[int, int] | None = None,
    changed_only: bool = False,
    skip_drift: bool = False,
    skip_fixture_retrieval: bool = False,
    skip_similarity: bool = False,
) -> tuple[list[ValidationIssue], int]:
    """Validate skills with optional partitioning. Returns (issues, count).

    Partitioning (--domain, --shard, --changed-only) narrows the set of
    SKILLS validated. Cross-repo steps (sources manifest, registry records,
    generated-artifact drift check, query fixtures) always run unless
    ``skip_drift`` is set — drift is the #1 thing that rots silently across
    sharded CI jobs, so we want EVERY shard to fail loudly on drift.

    Fixture validation: we only check fixtures that target skills in the
    filtered set (plus we cross-check that every skill in the filtered set
    has a fixture).
    """
    all_skill_dirs = list(discover_skill_dirs(ROOT))
    filtered_dirs = _filter_skill_dirs(
        all_skill_dirs,
        domain=domain,
        shard=shard,
        changed_only=changed_only,
        root=ROOT,
    )

    issues: list[ValidationIssue] = []
    seen_ids: dict[str, str] = {}
    seen_names: dict[str, str] = {}

    # Step 1 — frontmatter + structure for filtered skills (in-process, fast).
    records: list[SkillRecord] = [validate_one_skill(p, ROOT) for p in filtered_dirs]
    for rec in records:
        issues.extend(rec.issues)
        if rec.skill_id:
            if rec.skill_id in seen_ids:
                issues.append(
                    ValidationIssue(
                        "ERROR", str(rec.path),
                        f"duplicate skill id `{rec.skill_id}` also seen in {seen_ids[rec.skill_id]}",
                    )
                )
            else:
                seen_ids[rec.skill_id] = str(rec.path)
            if rec.name in seen_names:
                issues.append(
                    ValidationIssue(
                        "ERROR", str(rec.path),
                        f"duplicate skill name `{rec.name}` also seen in {seen_names[rec.name]}",
                    )
                )
            else:
                seen_names[rec.name] = str(rec.path)

    # Step 2 — cross-repo manifest validation (always runs).
    for source in load_sources_manifest(ROOT):
        issues.extend(validate_knowledge_source(ROOT, source))

    # Step 3 — registry records (full repo; cheap in-memory).
    # Skip embeddings rebuild during validation: it's the slow part and
    # registry-record validation only inspects skill metadata, not vectors.
    state = build_state(ROOT, skip_embeddings=True)
    for record in state.registry_records:
        issues.extend(validate_skill_registry_record(ROOT, record))

    # Step 4 — skill-local scripts (subprocess fan-out via thread pool).
    script_paths: list[Path] = []
    if filtered_dirs == all_skill_dirs:
        script_paths = sorted(ROOT.glob("skills/*/*/scripts/*.py"))
    else:
        for skill_dir in filtered_dirs:
            script_paths.extend(sorted(skill_dir.glob("scripts/*.py")))

    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for script_issues in pool.map(
            lambda p: _check_skill_local_script(p, ROOT), script_paths
        ):
            issues.extend(script_issues)

    # Step 5 — query fixtures (in-process via SearchContext; no subprocesses).
    fixtures_path = ROOT / "vector_index" / "query-fixtures.json"
    if fixtures_path.exists():
        fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
        covered_skills = {f["expected_skill"] for f in fixtures.get("queries", [])}
        # Every filtered skill must have a fixture.
        for skill_id in seen_ids:
            if skill_id not in covered_skills:
                issues.append(
                    ValidationIssue(
                        "ERROR", "vector_index/query-fixtures.json",
                        f"skill `{skill_id}` has no query fixture — add at least one entry",
                    )
                )
        # Only run fixture queries whose expected_skill is in the filtered set
        # (in full-repo mode that's every fixture; in --changed-only mode that's
        # a handful).
        fixtures_to_run = [
            f for f in fixtures.get("queries", [])
            if f["expected_skill"] in seen_ids
        ]
        if fixtures_to_run and not skip_fixture_retrieval:
            ctx = build_search_context(ROOT)
            for fixture in fixtures_to_run:
                payload = run_search(fixture["query"], ctx, domain=fixture.get("domain"))
                top_k = fixture.get("top_k", 3)
                top_skill_ids = [s["id"] for s in payload.get("skills", [])[:top_k]]
                if fixture["expected_skill"] not in top_skill_ids:
                    issues.append(
                        ValidationIssue(
                            "ERROR", "vector_index/query-fixtures.json",
                            f"query `{fixture['query']}` did not return `{fixture['expected_skill']}` in top {top_k}",
                        )
                    )

    # Step 6 — generated-artifact drift check (always, unless explicitly skipped).
    if not skip_drift:
        drift = diff_state(ROOT, state)
        for path in drift:
            issues.append(
                ValidationIssue("ERROR", path, "generated artifact is stale; run `python3 scripts/skill_sync.py --all`")
            )

    # Step 7 — orphan-skill check: WARN if a skill is not cited by any agent.
    # Skills can opt out by setting `runtime_orphan: true` in frontmatter.
    issues.extend(_check_orphan_skills(filtered_dirs))

    # Step 8 — semantic-duplicate check (WARN). Compares each skill in the
    # filtered set against the FULL corpus (not just the filtered set) so a
    # newly added skill near-duplicating an existing one gets flagged in
    # --changed-only mode. Threshold + weights from config/retrieval-config.yaml.
    # Skipped by validate_repo_bench (synthetic skills share tags + triggers,
    # which defeats the prefilter and doubles the orchestration runtime
    # without testing the gate's actual correctness).
    if not skip_similarity:
        skill_md_paths = [p / "SKILL.md" for p in filtered_dirs]
        issues.extend(validate_skill_similarity(ROOT, skill_md_paths))

    # Step 9 — shared `## Official Sources Used` block check (WARN). Same
    # corpus-level shape as Step 8: the fingerprint map is built over the FULL
    # corpus so a pair whose members land in different shards is still caught,
    # but only skills in the filtered set are reported.
    issues.extend(
        validate_official_sources_uniqueness(
            ROOT, [p / "SKILL.md" for p in filtered_dirs]
        )
    )

    return issues, len(filtered_dirs)


def _check_orphan_skills(filtered_dirs: list[Path]) -> list[ValidationIssue]:
    """Emit a WARN for each filtered skill no run-time agent cites (advisory).

    Coverage is a signal, not a contract. This gate used to be an ERROR whose
    message handed the reader a ready-to-paste command that added a citation,
    which made mass-citation the cheapest route to a green build — and produced
    555 machine-generated citations whose description was just the slug
    title-cased. Uncited-ness is now advisory; what carries ERROR severity is
    citation QUALITY (see ``_check_agent_citation_quality``), because a
    citation an agent will not read is worse than no citation at all.

    A skill can still record the decision explicitly with ``runtime_orphan:
    true`` in its frontmatter (plus ``runtime_orphan_reason``), which silences
    the advisory. Doing that in bulk to quiet the WARN is the same gaming
    pattern under a different label — the WARN is cheap to leave standing.

    Implementation: scans ``agents/*/AGENT.md`` YAML frontmatter for
    ``dependencies.skills:`` entries and treats the union as the cited set.
    """
    cited: set[str] = set()
    skill_block_re = re.compile(
        r"^dependencies:\s*\n(?:[ \t]+\S.*\n)*?[ \t]+skills:\s*\n((?:[ \t]+-\s+\S.*\n)+)",
        re.MULTILINE,
    )
    skill_item_re = re.compile(r"^[ \t]+-\s+(\S+)\s*$", re.MULTILINE)
    for agent_md in (ROOT / "agents").glob("*/AGENT.md"):
        try:
            text = agent_md.read_text(encoding="utf-8")
        except OSError:
            continue
        m = skill_block_re.search(text)
        if not m:
            continue
        for it in skill_item_re.finditer(m.group(1)):
            cited.add(it.group(1))

    out: list[ValidationIssue] = []
    for skill_dir in filtered_dirs:
        skill_md = skill_dir / "SKILL.md"
        try:
            parsed = parse_markdown_with_frontmatter(skill_md)
            meta = parsed.metadata
        except Exception:
            continue
        if meta.get("runtime_orphan") is True:
            continue
        skill_id = f"{meta.get('category')}/{meta.get('name')}"
        if skill_id not in cited:
            out.append(
                ValidationIssue(
                    "WARN", str(skill_md),
                    f"skill `{skill_id}` is cited by no run-time agent (advisory). "
                    f"Wire it only if some agent's output would be wrong without it — "
                    f"a citation an agent will not actually read inflates coverage while "
                    f"diluting that agent's reading list. Otherwise leave it uncited, or "
                    f"record the decision in frontmatter with `runtime_orphan: true` plus "
                    f"`runtime_orphan_reason: <why no agent owns this topic>`.",
                )
            )
    return out


# A numbered Mandatory Reads entry pointing at a skill, with its optional
# em-dash / en-dash / hyphen justification: "3. `skills/apex/foo` — why".
_AGENT_READ_RE = re.compile(
    r"^\s*\d+\.\s+`?skills/([a-z0-9\-]+/[a-z0-9\-]+)`?\s*(?:[—–-]\s*(.*))?$"
)
# "Analytics/reporting: " — a bucketing label some agents prefix onto the
# description. Bounded length so it cannot swallow a real sentence.
_AGENT_READ_LABEL_RE = re.compile(r"^[A-Z][^:]{0,40}:\s+")
# Per-agent reading-list ceiling, counting numbered `skills/...` entries
# anywhere in the AGENT.md (see the scoping note in the loop below).
# Measured gap in the corpus: 45/44/44/42 then a drop to 36, so 40 separates
# the four outliers from the body of the distribution without arbitrariness.
# Shared-contract and harness reads are deliberately excluded from the count —
# charging an agent for reading its own contract inverts the signal.
MAX_AGENT_SKILL_READS = 40


def _check_agent_citation_quality(
    agents_root: Path = ROOT / "agents",
) -> list[ValidationIssue]:
    """Gate the quality and size of each run-time agent's reading list.

    This is the ERROR side of the inversion that ``_check_orphan_skills``
    gives up. Uncited-ness is advisory; a citation that carries no reason to
    read it is a defect, because it spends the agent's context and buys no
    accuracy. Four defect classes, three severities of aggregation:

    * ERROR, per line — the description is present but merely echoes the slug
      ("fsl-mobile-app-setup" -> "Fsl mobile app setup"). Zero hits on the
      corpus today; this is a regression guard against the stub wave
      recurring, and per-line so an offender is precisely locatable. The
      predicate is an exact match after normalisation, so it catches a
      re-run of the machine-generated wave and nothing subtler: one appended
      word ("... setup guidance") clears it. That is deliberate — hardening
      an echo detector into a filler detector is an arms race, and the
      incentive to mass-cite is gone now that coverage is advisory.
    * WARN, one per agent — reads with no description at all (133 lines
      across 23 agents today). Same underlying defect, an order of magnitude
      more of it, and writing 133 real justifications is content work.
    * WARN, one per agent — reads that echo the slug once a bucketing label
      prefix is stripped. Staged; see the comment on that branch.
    * WARN, one per agent — more than ``MAX_AGENT_SKILL_READS`` numbered
      skill reads anywhere in the file.

    The description-quality branches read only the ``## Mandatory Reads*``
    section, which is where the contract promises a justification. The
    ceiling counts the whole file, because a read is a read whichever
    heading it sits under.

    The WARN classes are aggregated per agent per class rather than emitted
    per line on purpose: 162 per-line WARNs would fire on every run including
    the pre-commit hook, and a warning stream nobody reads is the same
    Goodhart failure this gate exists to undo.

    Known hazard: this runs unconditionally over every ``agents/*/AGENT.md``,
    not over the changed set, so the per-line ERROR branch can red a build
    for a file the contributor never touched — including under the
    ``--changed-only`` pre-commit hook, where the failure would look
    unrelated to the commit. Harmless while the branch has zero corpus hits,
    but that shape is how gates end up disabled wholesale; if a real hit ever
    lands here, scope the ERROR branch to changed agents before the next
    contributor hits it cold.

    ``agents_root`` is a parameter so the gate can be exercised against a
    fixture without writing a deliberately-bad AGENT.md into ``agents/``.
    """
    issues: list[ValidationIssue] = []
    for agent_md in sorted(agents_root.glob("*/AGENT.md")):
        try:
            lines = agent_md.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        agent_id = agent_md.parent.name
        agent_path = f"agents/{agent_id}"

        # Two counts, deliberately different in scope.
        #   `reads`      — numbered skill entries INSIDE `## Mandatory Reads*`.
        #                  The description-quality branches below apply only
        #                  here, because only this section promises a reason.
        #   `total_reads`— numbered skill entries ANYWHERE in the file. The
        #                  ceiling is a budget on what the agent will actually
        #                  open, and a read is a read whichever heading it sits
        #                  under. Scoping the ceiling to one section made it
        #                  evadable by moving lines verbatim under a new
        #                  heading (`## Situational Reads`, etc.):
        #                  `pipelines/agent_validators.py` enforces only the
        #                  presence and relative order of required sections, so
        #                  an extra heading is legal and the same 45 files stay
        #                  in the agent's path. Counting the whole file changes
        #                  no current output — no agent carries a numbered
        #                  skill read outside Mandatory Reads today.
        reads: list[tuple[str, str]] = []
        total_reads = 0
        in_section = False
        for line in lines:
            match = _AGENT_READ_RE.match(line)
            if match:
                total_reads += 1
            if re.match(r"^##\s+Mandatory Reads", line):
                in_section = True
                continue
            if in_section and re.match(r"^##\s+", line):
                in_section = False
            if in_section and match:
                reads.append((match.group(1), (match.group(2) or "").strip()))

        if not total_reads:
            continue

        undescribed: list[str] = []
        label_echoes: list[str] = []
        for skill_id, description in reads:
            if not description:
                undescribed.append(skill_id)
            elif is_echo_description(skill_id, description):
                issues.append(ValidationIssue(
                    "ERROR", str(agent_md),
                    f"Mandatory Reads entry for `skills/{skill_id}` is an echo stub — its "
                    f"description ({description!r}) restates the slug and tells the agent "
                    f"nothing the path did not already say. Write why THIS agent's output "
                    f"would be wrong without the skill, or delete the citation.",
                ))
            elif is_echo_description(skill_id, _AGENT_READ_LABEL_RE.sub("", description)):
                # Staged rollout. Identical defect to the ERROR branch above,
                # just wearing a bucketing label ("Analytics/reporting:
                # Analytics dashboard json"). All 25 current hits are in
                # agents/audit-router/AGENT.md, which this change does not own,
                # so shipping it at ERROR would red the tree for a file its
                # author cannot touch. PROMOTE THIS BRANCH TO ERROR, merged
                # into the exact-match branch above, once audit-router's reads
                # carry real justifications.
                label_echoes.append(skill_id)

        def _sample(ids: list[str]) -> str:
            shown = ", ".join(f"`{i}`" for i in ids[:5])
            return shown + (f", +{len(ids) - 5} more" if len(ids) > 5 else "")

        if undescribed:
            issues.append(ValidationIssue(
                "WARN", agent_path,
                f"{len(undescribed)} Mandatory Reads entr(ies) carry no justification at "
                f"all: {_sample(undescribed)}. A bare path tells the agent what to open "
                f"but not why, so it cannot decide to skip — add one clause per entry "
                f"naming what this agent gets wrong without it.",
            ))

        if label_echoes:
            issues.append(ValidationIssue(
                "WARN", agent_path,
                f"{len(label_echoes)} Mandatory Reads entr(ies) restate the slug behind a "
                f"bucketing label: {_sample(label_echoes)}. Stripping the label leaves a "
                f"description identical to the skill name. Keep the label if it helps "
                f"navigation, but follow it with a real reason to read.",
            ))

        if total_reads > MAX_AGENT_SKILL_READS:
            issues.append(ValidationIssue(
                "WARN", agent_path,
                f"{total_reads} numbered skill reads in this AGENT.md, over the advisory "
                f"ceiling of {MAX_AGENT_SKILL_READS}. Past that, the list stops being a "
                f"reading list and becomes a coverage claim. Drop the entries this agent "
                f"does not actually need, or split it into two agents with narrower "
                f"scopes. Note that the count covers the whole file, not just the "
                f"Mandatory Reads section: relocating entries under another heading "
                f"leaves the same skills in the agent's path and does not clear this.",
            ))

    return issues


def run_agent_validation() -> list[ValidationIssue]:
    return validate_agents(ROOT)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the repository skill framework, agents, and generated artifacts.",
    )
    parser.add_argument(
        "--agents", action="store_true",
        help="Run only the AGENT.md structural + citation gate.",
    )
    parser.add_argument(
        "--skills-only", action="store_true",
        help="Run only the existing skill validation (default if neither flag set).",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run both skill and agent validation.",
    )
    parser.add_argument(
        "--changed-only", action="store_true",
        help="Validate only skills/agents touched by the current git diff "
             "(staged + unstaged + untracked). Drift check still runs.",
    )
    parser.add_argument(
        "--shard", type=_parse_shard_spec, default=None, metavar="N/M",
        help="Only validate the N-th bucket of skills partitioned by "
             "stable hash mod M (0-indexed). For CI matrix jobs.",
    )
    parser.add_argument(
        "--domain", type=str, default=None,
        help="Restrict to skills under skills/<domain>/. "
             "Composable with --shard and --changed-only.",
    )
    parser.add_argument(
        "--skip-drift", action="store_true",
        help="Skip the generated-artifact drift check. "
             "Use only when sync_engine is deliberately in an inconsistent state.",
    )
    parser.add_argument(
        "--skip-fixture-retrieval", action="store_true",
        help="Skip the per-fixture retrieval-quality assertion (every fixture "
             "must still exist). Used by the bench and when the lexical index "
             "is intentionally absent. Coverage check — every skill has a "
             "fixture — still runs.",
    )
    parser.add_argument(
        "--skip-similarity", action="store_true",
        help="Skip the semantic-duplicate WARN gate. Used by the orchestration "
             "bench (synthetic skills share tags + triggers, which defeats "
             "the prefilter and inflates wall-clock without testing the gate). "
             "Real-corpus runs should leave this enabled.",
    )
    args = parser.parse_args()

    # Default behavior (no flags) preserves pre-existing CI: run skill validation only.
    run_skills = (
        args.skills_only or args.all
        or (not args.agents and not args.skills_only and not args.all)
    )
    run_agents = args.agents or args.all

    issues: list[ValidationIssue] = []
    skill_count = 0

    if run_skills:
        skill_issues, skill_count = run_skill_validation(
            domain=args.domain,
            shard=args.shard,
            changed_only=args.changed_only,
            skip_drift=args.skip_drift,
            skip_fixture_retrieval=args.skip_fixture_retrieval,
            skip_similarity=args.skip_similarity,
        )
        issues.extend(skill_issues)

    agent_count = 0
    if run_agents:
        agent_issues = run_agent_validation()
        issues.extend(agent_issues)
        agent_count = sum(1 for _ in (ROOT / "agents").glob("*/AGENT.md"))

    # Repo-level doc-count consistency gate (README / MCP README / CLAUDE.md /
    # AGENT_RULES.md / RUNTIME_VS_BUILD.md vs registry + agent frontmatter).
    # Cheap and order-independent, so it runs on every invocation.
    issues.extend(
        ValidationIssue(level, path, message)
        for level, path, message in collect_doc_count_issues(ROOT)
    )

    # Repo-level agent citation-QUALITY gate (echo stubs, undescribed reads,
    # oversized reading lists). Same rationale as the doc-count gate above:
    # cheap (76 small file reads) and order-independent, so it runs on every
    # invocation rather than only under --agents. It is deliberately not inside
    # run_agent_validation(): the defect it guards is what the skill-side
    # orphan gate stopped ERRORing on, so a --skills-only run must still see it.
    issues.extend(_check_agent_citation_quality())

    # Repo-level decision-tree gate. Runs on EVERY invocation, never under
    # --changed-only gating, because a tree breaks without the tree file
    # changing: `standards/decision-trees/README.md` tells run-time agents to
    # consult a tree BEFORE activating any skill, so renaming or deleting a
    # skill silently turns a live branch into a citation the agent cannot
    # resolve. Seven small files; the cost is nil.
    issues.extend(
        ValidationIssue(level, path, message)
        for level, path, message in collect_decision_tree_issues(ROOT)
    )

    # Repo-level AGENT_CONTRACT rule 5 gate: dependencies.skills: and the prose
    # must agree. Runs on every invocation for the same reason as the two above
    # — it is cheap and order-independent — and it closes the one asymmetry the
    # rest of the citation gates cannot see: the coverage check reads the YAML
    # block ONLY, so a skill listed there and never written into the body is
    # counted as cited while being invisible to review and unread by the agent.
    issues.extend(
        ValidationIssue(level, path, message)
        for level, path, message in collect_citation_parity_issues(ROOT)
    )

    for issue in issues:
        print_issue(issue)

    error_count = sum(1 for issue in issues if issue.level == "ERROR")
    warn_count = sum(1 for issue in issues if issue.level == "WARN")
    summary_parts = []
    if run_skills:
        summary_parts.append(f"{skill_count} skill(s)")
    if run_agents:
        summary_parts.append(f"{agent_count} agent(s)")
    summary = " + ".join(summary_parts) if summary_parts else "nothing"
    mode_tags = []
    if args.changed_only:
        mode_tags.append("changed-only")
    if args.shard:
        mode_tags.append(f"shard={args.shard[0]}/{args.shard[1]}")
    if args.domain:
        mode_tags.append(f"domain={args.domain}")
    mode_str = f" [{', '.join(mode_tags)}]" if mode_tags else ""
    print(f"Validated {summary}{mode_str}; {error_count} error(s), {warn_count} warning(s).")
    return 1 if error_count else 0


if __name__ == "__main__":
    sys.exit(main())
