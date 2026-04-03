# BACKLOG

Items here are real, tracked, and will be done — but are deferred until we have more content, a clear trigger, or a natural moment to tackle them without disrupting active skill building.

Each item has a **Why deferred** and a **Trigger** (what condition makes it the right time to pick it up).

---

## Infrastructure

### Git LFS for lexical.sqlite
**What:** Move `vector_index/lexical.sqlite` to Git LFS so large binary doesn't bloat the repo history.
**Why deferred:** Git LFS is not installed in the local environment. Workaround in place: `lexical.sqlite` is now in `.gitignore`; file is regenerated on each run.
**Trigger:** When the repo clone size starts causing CI slowdowns, or when a contributor reports the repo is slow to clone.
**Work needed:** `git lfs install`, `git lfs track "vector_index/lexical.sqlite"`, migrate history with `git lfs migrate import`.

---

### Embeddings (semantic search)
**What:** Enable vector embeddings in `config/retrieval-config.yaml` for semantic skill retrieval.
**Why deferred:** Threshold is set at 300 skills. Currently at ~90 skills. Lexical search is accurate enough below that threshold.
**Trigger:** When `find skills/ -name "SKILL.md" | wc -l` exceeds 300.
**Work needed:** Set `enabled: true` in retrieval-config.yaml, choose embedding provider (OpenAI text-embedding-3-small or local), add API key management.

---

### CI/CD Pipeline
**What:** GitHub Actions workflow that runs `validate_repo.py` on every PR and `skill_sync.py --all` on merge.
**Why deferred:** Repo is currently agent-driven with no human PRs. CI would be redundant until external contributors start submitting PRs.
**Trigger:** First external contributor opens a PR, or the repo goes into a "contributions welcome" phase.
**Work needed:** `.github/workflows/validate.yml`, badge in README.

---

## Content Quality

### Cross-skill contradiction detection
**What:** Automated check that scans overlapping skills for conflicting factual claims (e.g., two skills disagree on a governor limit).
**Why deferred:** Meaningful contradictions require enough content volume to detect patterns. With < 100 skills, manual review is faster.
**Trigger:** When the repo exceeds 150 skills across 3+ overlapping domains (e.g., apex + integration + admin all covering callout limits).
**Work needed:** Add a `scripts/check_contradictions.py` that runs `search_knowledge.py` against each skill's claims, flags divergence above a threshold. Add to Validator agent Gate 4.

---

### Source staleness monitoring (Currency Monitor)
**What:** Agent that checks `updated` frontmatter against Salesforce release notes and flags skills whose claims may be out of date.
**Why deferred:** Requires a stable release notes feed and enough content to make monitoring worthwhile.
**Trigger:** When the repo covers its first full Salesforce release cycle (Spring → Summer → Winter) with skills built before each release.
**Work needed:** `agents/currency-monitor/AGENT.md`, scheduled monthly run, `[STALE-RISK]` tag automation.

---

### Tier 4 source filtering in Validator
**What:** Automated detection of Reddit, LinkedIn, or non-MVP blog links in skill bodies.
**Why deferred:** All skills built so far use only T1/T2 sources. No actual violations to catch yet.
**Trigger:** When external contributors start submitting skills, or when agent-built skills start citing T4 sources (check with `grep -r "reddit.com\|linkedin.com" skills/`).
**Work needed:** Add URL pattern check to `_validate_checker_script_content` or a new `validate_source_tiers` function in `pipelines/validators.py`.

---

## Agent Architecture

### Multi-cloud skill builder specialization
**What:** Separate skill builder agents for specific clouds (Sales Cloud, Service Cloud, etc.) rather than one generic admin/dev builder.
**Why deferred:** Cloud-specific nuance becomes valuable once the core platform skills are complete. Building cloud-specific builders now would be premature.
**Trigger:** When Core Platform × all roles is complete (Phase 1 DONE), and Phase 2 (Sales Cloud) starts in earnest.
**Work needed:** `agents/sales-cloud-builder/AGENT.md`, `agents/service-cloud-builder/AGENT.md`, routing update in orchestrator.

---

### Skill update (UPDATE status) workflow
**What:** Full workflow for when an existing skill needs to be revised after a Salesforce release.
**Why deferred:** No UPDATE rows exist yet. The workflow is partially described in Orchestrator routing table but has no step-by-step procedure.
**Trigger:** When Currency Monitor (above) produces its first UPDATE row.
**Work needed:** Add `## UPDATE Workflow` section to `commands/run-queue.md`, define diff-based revision process.

---

## Content Expansion

### Phase 2+ cloud-specific skills
All non-Core-Platform skill rows in `MASTER_QUEUE.md` (Sales Cloud, Service Cloud, Experience Cloud, Marketing Cloud, Revenue Cloud, Data Cloud, Industries, MuleSoft, Tableau, Slack, Net Zero Cloud, Health Cloud, Financial Services Cloud, Education Cloud, Automotive Cloud).

**Why deferred:** Phase 1 (Core Platform) must be fully complete first. Cloud-specific skills depend on core concepts being solid.
**Trigger:** Phase 1 Progress Summary shows all TODO rows as DONE.

---

### Community contributions
**What:** CONTRIBUTING.md workflow, skill submission PR template, community issue template for skill gaps.
**Why deferred:** CONTRIBUTING.md exists. But no external contributors yet — no point building review tooling for a workflow that doesn't exist.
**Trigger:** First external contributor opens a GitHub issue or PR.

---

## Observability

### Skill usage analytics
**What:** Track which skills are retrieved most often, which queries return `has_coverage: false`, which fixtures fail.
**Why deferred:** No usage data yet — this is a local repo with agent-driven builds. Analytics become meaningful when external tools (Claude Code, Cursor, etc.) start querying the repo.
**Trigger:** When the repo is integrated into at least one external AI tool with measurable query volume.
**Work needed:** Logging wrapper around `search_knowledge.py`, `logs/` directory, weekly report agent.
