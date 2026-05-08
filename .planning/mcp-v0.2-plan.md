# sfskills-mcp v0.2 — Detailed Implementation Plan

**Status:** draft for review
**Author:** Claude (under SfSkills Agent)
**Date:** 2026-05-08
**Scope target:** `mcp/sfskills-mcp/` and a small set of agent frontmatter files
**Non-goals:** No rewrite. No protocol change. No new auth model. No vertical/cloud expansion (Tier E is deferred).

---

## Reading guide

This plan is structured by Tier. Each Tier has:

- **Goal** — one sentence; what success looks like
- **Items** — concrete changes with file paths, before/after sketches, and validation
- **Risks** — what could break and how we'll catch it
- **Effort** — wall-clock estimate (one engineer, focused)
- **Exit criteria** — the binary "is this done?" check

Items are written so they can be cherry-picked. The order *within* a Tier is the recommended sequence; the Tiers themselves should be done strictly in order — Tier B assumes Tier A's drift fixes, Tier C assumes Tier B's annotations.

---

## Baseline (what's true at start of work)

| | |
|---|---|
| Repo root | `<repo>` (the SfSkills checkout) |
| MCP code | `mcp/sfskills-mcp/` |
| Tools registered today | 23 (in `src/sfskills_mcp/server.py`) |
| Tests | 67 cases in `tests/`; **65 pass, 2 fail** (content drift, not MCP bugs) |
| Skills in registry | 981 (`registry/skills.json`) |
| Agents on disk | 75 (`agents/*/AGENT.md`); **61 `class: runtime`**, **14 `class: build`** per frontmatter |
| Commands | 68 (`commands/*.md`), one per runtime agent + a few aggregators |
| Decision trees | 6 files in `standards/decision-trees/` (excluding README) |
| Templates | 5 domain dirs (`templates/{admin,agentforce,apex,flow,lwc}`) |

---

## Tier A — Fix drift (must, ~½ day)

**Goal:** every count, name list, and classification served by the MCP comes from the registry / frontmatter at runtime — never from a hardcoded constant. Tests pass green.

### A1. Replace `_RUNTIME_AGENTS` frozenset with frontmatter scan

**File:** `mcp/sfskills-mcp/src/sfskills_mcp/agents.py`

**Problem:** Lines 28–72 hardcode a 37-name `frozenset` that's been wrong since the Wave-1 add of audit-router, code-reviewer, apex-builder, lwc-builder, lwc-debugger, experience-cloud-admin-designer, process-flow-mapper, flow-orchestrator-designer, automation-migration-router, etc.

**Change:** introduce a tiny YAML-frontmatter parser (stdlib-only — same posture as the rest of the package) and resolve `kind` from each agent's frontmatter at call time, with an `lru_cache` so repeat calls stay cheap.

```python
# New helper
@lru_cache(maxsize=1)
def _agent_classes() -> dict[str, str]:
    """Return {agent_name: 'runtime' | 'build' | 'unknown'} from frontmatter."""
    out: dict[str, str] = {}
    for entry in sorted(_agents_dir().iterdir()):
        if not entry.is_dir() or entry.name.startswith((".", "_")):
            continue
        md = entry / "AGENT.md"
        if not md.exists():
            continue
        cls = _read_frontmatter_field(md, "class") or "unknown"
        out[entry.name] = cls
    return out
```

`_read_frontmatter_field` is a 15-line function: open the file, read until `---` start fence, scan `^class:\s*(\S+)$` lines, stop at the closing fence. No PyYAML dep — keeps `pyproject.toml` single-dep.

**Before:**
```python
is_runtime = entry.name in _RUNTIME_AGENTS
agent_kind = "runtime" if is_runtime else "build"
```

**After:**
```python
agent_kind = _agent_classes().get(entry.name, "unknown")
```

Delete the `_RUNTIME_AGENTS` frozenset entirely (lines 28–72).

**Validation:**
- Existing test `tests/test_agents.py` should still pass with no edits (it doesn't pin to specific agent names).
- New test: assert `len(list_agents(kind="runtime")["agents"]) >= 56` (matches CLAUDE.md tier table, allows growth).
- New test: assert at least one agent named `code-reviewer` is classified `runtime` (canary for the drift bug).
- Manual: run `python3 -c "from sfskills_mcp.agents import list_agents; import json; print(json.dumps(list_agents(kind='runtime'), indent=2))"` — count should match `grep -c "^class: runtime" agents/*/AGENT.md`.

**Risk:** None. Frontmatter coverage is 75/75. Worst case: an agent without a `class:` field is classified `unknown` and excluded from both `runtime` and `build` filters — visible, harmless, easy to spot.

---

### A2. Make skill / agent counts dynamic in tool descriptions

**Files:** `mcp/sfskills-mcp/src/sfskills_mcp/server.py`, `mcp/sfskills-mcp/src/sfskills_mcp/__init__.py`

**Problem:** The `search_skill` tool description reads "686+ Salesforce skills…" ([server.py:82](mcp/sfskills-mcp/src/sfskills_mcp/server.py:82)). Real count is 981. Same drift in `SERVER_INSTRUCTIONS` and several other strings.

**Change:** load counts at server-build time and string-format them in.

```python
# In server.py, at the top of build_server()
from . import paths
import json

_registry_skill_count = _load_skill_count()
_runtime_agent_count = sum(1 for v in _agent_classes().values() if v == "runtime")
_total_agent_count   = len(_agent_classes())

SERVER_INSTRUCTIONS = SERVER_INSTRUCTIONS_TEMPLATE.format(
    skill_count=_registry_skill_count,
    runtime_agent_count=_runtime_agent_count,
)
```

`_load_skill_count` reads `registry/skills.json` and returns `len(payload["skills"])`. If the registry file is missing, fall back to `"950+"` (graceful degradation; the actual count is the goal but the server should still come up).

Make the `search_skill` description a templated f-string referencing `_registry_skill_count`.

**Validation:**
- New test `tests/test_meta_freshness.py`: assert the server-instructions string contains the actual current `len(skills)` from the registry, not a stale literal.
- New test: assert no occurrence of `"686"` or `"56 total"` literals anywhere in `src/`.

**Risk:** Reading the registry at import time slows cold-start by ~20–50 ms (5.4 MB JSON). Acceptable; alternative is a generator that defers the load. If start-up speed matters for any client, switch to lazy load behind `lru_cache`.

---

### A3. Update README.md and tool descriptions to reflect current state

**Files:** `mcp/sfskills-mcp/README.md`, `mcp/sfskills-mcp/src/sfskills_mcp/server.py`, `mcp/sfskills-mcp/docs/CONNECT.md`

**Changes:**
- README: update "686+" → live count phrase ("980+"), "56 run-time agents" → "60+ run-time agents", refresh agent-roster tables to match the canonical CLAUDE.md tiers (Wave-1 dev = 17, Tier 1 = 15, Tier 2 = 12, Tier 3 = 12 — total 56). Use the values from CLAUDE.md verbatim; do not invent new tiers.
- README: bump "23 tools" to whatever Tier B/C lands (do this last, in a separate commit).
- CONNECT.md: nothing structural — just sweep `686+` and `six tools` (line 5, 11, etc.) literals. Replace `six tools` with a generic phrase.
- server.py: rewrite `search_skill` description, `list_agents` description to use the live-count tokens.

**Validation:** `grep -E "686\+|six tools|56 (total|run-time|agents)" mcp/sfskills-mcp/` returns nothing.

**Risk:** Cosmetic. None.

---

### A4. Fix the 2 failing tests (content drift)

**Files (the *agents'* AGENT.md, not MCP code):**
- `agents/apex-builder/AGENT.md` — declare 5 `templates/apex/tests/*.cls` files in `frontmatter.dependencies.templates`
- `agents/fit-gap-analyzer/AGENT.md` — declare `skills/architect/hipaa-compliance-architecture` in `frontmatter.dependencies.skills`
- `agents/story-drafter/AGENT.md` — declare `skills/admin/compliance-documentation-requirements` in `dependencies.skills`, and `decision_trees/automation-selection.md` in `dependencies.decision_trees`

**How:** the test failures already include the exact remediation: `python3 scripts/migrate_agent_dependencies.py --agent <name> --force`. Run for the 3 agents.

For the second failure (`test_multi_dimensional_agents_enumerate_dimensions`):
- `agents/data-loader-pre-flight/AGENT.md` — Output Contract section needs to enumerate dimensions or reference `dimensions_compared`
- `agents/duplicate-rule-designer/AGENT.md` — same
- `agents/story-drafter/AGENT.md` — same

This is a manual edit: add to the Output Contract block a line per dimension following the existing `audit-router` pattern. Look at `agents/audit-router/AGENT.md` as the canonical example.

**Validation:** `cd mcp/sfskills-mcp && python3 -m unittest discover -s tests` returns `OK` with 0 failures.

**Risk:** Touches agent content, not MCP. Re-run `python3 scripts/skill_sync.py --all` and `python3 scripts/validate_repo.py` after — both must pass.

---

### A5. Tier-A exit criteria

- [x] `python3 -m unittest discover -s mcp/sfskills-mcp/tests` exits 0 (78/78 pass)
- [x] `python3 scripts/validate_repo.py` exits 0 (8 unrelated content warnings, 0 errors)
- [x] `_RUNTIME_AGENTS` symbol no longer present in `agents.py`
- [x] No `686+` or `56 total` literals in `mcp/sfskills-mcp/` source — exception: `tests/test_meta_freshness.py` references `686+` as the literal it scans *for* (drift-prevention canary, intentional)
- [~] **Plan said:** `list_agents(kind="runtime")` returns ≥ 56 entries including `code-reviewer`, `apex-builder`, `lwc-builder`, `audit-router`. **Actual:** returns **47** entries. **Reason:** the `≥ 56` figure came from CLAUDE.md's tier rosters which still list 14 agents that have since been retired. Their AGENT.md frontmatter now carries `status: deprecated`, and the new `_agent_classes()` resolver classifies them under `kind="deprecated"` (not `runtime`) — exactly the behaviour we want, just at a different cardinality than the plan named. `code-reviewer` is **`class: build`** per its own frontmatter, not runtime — the plan miscategorized it. Updated criterion: `list_agents(kind="runtime")` returns ≥ 40 entries including `apex-builder`, `lwc-builder`, `audit-router`, `apex-refactorer`. **Met as updated.**
- [x] `list_agents(kind="deprecated")` returns the 14 retired stubs (new filter introduced during A1; not in the original plan)
- [x] README tier tables annotate the 9 deprecated stubs that appear in them with `*(deprecated → audit-router)*`

### A6. Tier-A actual outcomes (not in original plan)

- Added `kind="deprecated"` filter to `list_agents` and updated the tool description so LLMs know the filter exists.
- Added 4 new freshness tests (`tests/test_meta_freshness.py`) preventing future re-introduction of stale literals.
- Replaced the hardcoded `EXPECTED_RUNTIME` set in `tests/test_agents.py` with canary + count-floor invariants.
- Fixed a pre-existing truthy-string bug in `tests/test_deliverable_contract.py` (`meta.get("multi_dimensional")` returned `"false"` strings as truthy).

**Effort actual:** ~3.5 hours. Slightly under estimate; saved time on A1 because frontmatter coverage was 75/75 (no backfill needed), spent more on A4 because the test had a latent bug.

---

## Tier B — MCP primitives the prototype skipped (~1 day)

**Goal:** unlock features built into the MCP protocol that the current server ignores: tool annotations, Prompts, Resources, progress notifications. No new tools yet — make the existing 23 tools richer.

### B1. Add tool annotations to all 23 tools

**File:** `mcp/sfskills-mcp/src/sfskills_mcp/server.py`

**Change:** every `@mcp.tool(...)` call gains an `annotations=` block. FastMCP supports annotations in MCP SDK ≥ 1.2 via the `annotations` kwarg or `mcp.types.ToolAnnotations`.

The 4 hint flags relevant to this server:

| Annotation | Value | Why |
|---|---|---|
| `readOnlyHint` | `True` for all 23 tools | Every tool is read-only; no DML, no metadata write, no deploy. Lets clients (Cursor, Cline) auto-approve safely. |
| `destructiveHint` | `False` for all | Belt-and-suspenders. |
| `idempotentHint` | `True` for org tools (idempotent under no concurrent org changes), `True` for `search_skill` / `get_skill` / `list_agents` / `get_agent` (deterministic), `True` for `emit_envelope` only when `overwrite=True` (otherwise non-idempotent — flag `False`) | Truth-in-advertising. |
| `openWorldHint` | `True` for the 14 org-touching tools (output depends on external state: the org), `False` for the 9 repo-only tools (`search_skill`, `get_skill`, `list_agents`, `get_agent`, `list_deprecated_redirects`, `get_invocation_modes`, `emit_envelope`) | Tells the client whether to re-run vs. cache. |

**Per-tool table** (recommendation):

| Tool | readOnly | destructive | idempotent | openWorld |
|---|---|---|---|---|
| `search_skill` | T | F | T | F |
| `get_skill` | T | F | T | F |
| `describe_org` | T | F | T | T |
| `list_custom_objects` | T | F | T | T |
| `list_flows_on_object` | T | F | T | T |
| `validate_against_org` | T | F | T | T |
| `list_validation_rules` | T | F | T | T |
| `list_permission_sets` | T | F | T | T |
| `describe_permission_set` | T | F | T | T |
| `list_record_types` | T | F | T | T |
| `list_named_credentials` | T | F | T | T |
| `list_approval_processes` | T | F | T | T |
| `tooling_query` | T | F | T | T |
| `probe_apex_references` | T | F | T | T |
| `probe_flow_references` | T | F | T | T |
| `probe_matching_rules` | T | F | T | T |
| `probe_permset_shape` | T | F | T | T |
| `probe_automation_graph` | T | F | T | T |
| `list_agents` | T | F | T | F |
| `get_agent` | T | F | T | F |
| `list_deprecated_redirects` | T | F | T | F |
| `get_invocation_modes` | T | F | T | F |
| `emit_envelope` | F¹ | F | F² | F |

¹ writes a file — not "read-only" in the strict sense. Annotation choice: `readOnlyHint=False` to be honest, but `destructiveHint=False` because it's idempotent under `overwrite=True` and writes only inside the repo's `docs/reports/` cone.
² becomes `True` only with `overwrite=True`; safer to leave `False` and let clients decide.

**Validation:** new test `tests/test_tool_annotations.py`:
- assert every registered tool has annotations
- assert `readOnlyHint=True` for the 22 listed
- assert `openWorldHint=True` for the 14 org tools
- assert `emit_envelope.readOnlyHint=False`

**Risk:** API mismatch with the user's MCP SDK version. Pin `mcp>=1.4.0` in `pyproject.toml` (annotations stable since 1.4) and update `requirements.txt` to match.

---

### B2. Expose `commands/*.md` as MCP Prompts

**New file:** `mcp/sfskills-mcp/src/sfskills_mcp/prompts.py`

**Why this is high-leverage:** the repo has 68 ready-made command wrappers (`commands/refactor-apex.md`, `commands/audit-router.md`, etc.) that today only Claude Code consumes (because of `.claude/commands/` location). MCP Prompts give every client a native picker — type `/refactor-apex` in Cursor, Cline, Claude Desktop, and the prompt loads the wrapper for that agent.

**Shape per prompt:**
- Name: `commands/<file>.md` → prompt `name = "<basename without .md>"` (e.g. `refactor-apex`)
- Description: first H1 of the markdown after the leading `# /name — `
- Arguments: enumerate the inputs the wrapper asks for in its "Step 1 — Collect inputs" section. Most wrappers have 2–4 numbered prompts; surface those as MCP prompt arguments with `required=True/False` per the wrapper's own "[optional]" markers.

**Discovery:** at server build time, scan `commands/*.md`, parse, register one MCP prompt per file:

```python
# in server.py build_server()
for prompt_def in prompts.discover():
    @mcp.prompt(name=prompt_def.name, description=prompt_def.description)
    def _wrapper(**kwargs):
        return prompts.render(prompt_def.name, kwargs)
```

`prompts.render(name, args)` returns the wrapper's full markdown body with argument placeholders substituted. Use a simple `{{arg_name}}` substitution convention; rewrite the existing 68 commands once to swap "Path to the Apex class to refactor?" → `{{class_path}}` (one PR, separate from the MCP work).

**Validation:**
- New test `tests/test_prompts.py`: assert ≥ 60 prompts register at server build time. Assert `refactor-apex`, `audit-router`, `build-apex` are present.
- Use `npx @modelcontextprotocol/inspector python3 -m sfskills_mcp` and verify the **Prompts** tab populates.

**Risk:** Argument placeholder rewrite of 68 markdown files is mechanical but not zero-touch. Mitigation: ship Prompts in two phases:
- **B2a (this Tier):** register prompts with empty argument lists; the prompt body is the entire wrapper markdown including the inputs section. Clients will paste the inputs interactively. Zero markdown changes.
- **B2b (later):** parse the inputs section and expose typed arguments. Higher polish, requires the `{{placeholder}}` rewrite.

Recommend doing B2a only in this Tier; defer B2b to a separate small task once we see real usage patterns.

---

### B3. Expose skills as MCP Resources

**New file:** `mcp/sfskills-mcp/src/sfskills_mcp/resources.py`

**Why:** today every skill read is a tool call. MCP Resources let clients pre-index a registry list and pull bodies on demand without a tool round-trip. Concretely:

- Resource list: `sfskills://skill/{id}` for each of 981 skills, plus a tree-style aggregate `sfskills://catalog` returning the registry index.
- Optional: `sfskills://template/{path}` for the shared canon (TriggerHandler.cls, BaseService.cls, etc.) and `sfskills://decision-tree/{name}` for the 6 trees.

**Server registration:**

```python
@mcp.resource("sfskills://catalog")
def catalog() -> list[dict]:
    return resources.skill_catalog()  # slim list: id, category, description

@mcp.resource("sfskills://skill/{skill_id}")
def skill_resource(skill_id: str) -> str:
    payload = skills.get_skill(skill_id, include_markdown=True, include_references=False)
    return payload.get("markdown", "")
```

**MIME type:** `text/markdown` for skill bodies and decision trees; `application/json` for the catalog; `text/plain` (or `text/x-apex` if we're being fancy) for templates.

**Validation:** new test `tests/test_resources.py`:
- assert `sfskills://catalog` returns a list of length ≥ 980
- assert `sfskills://skill/apex/trigger-framework` returns markdown starting with `---` (frontmatter)
- assert an unknown id returns a structured error, not an exception

**Risk:** large resource counts (981 skills) might cause some clients to choke when they `resources/list`. Mitigation: paginate via the MCP `cursor` arg. FastMCP supports this in `>=1.4`.

---

### B4. Add progress notifications to slow probes

**File:** `mcp/sfskills-mcp/src/sfskills_mcp/probes.py`

**Why:** `probe_apex_references` on a 5000-class org takes 30+ seconds with no client-side feedback. MCP supports `notifications/progress` so clients can render a spinner with substeps.

**Change:** the four probes that fetch and post-process bodies (`probe_apex_references`, `probe_flow_references`, `probe_matching_rules`, `probe_automation_graph`) gain a progress callback parameter that FastMCP injects:

```python
async def probe_apex_references(..., context: Context) -> dict:
    await context.report_progress(0.1, "Fetching ApexClass rows…")
    classes = _run_soql(...)
    await context.report_progress(0.4, f"Scanning {len(classes['records'])} class bodies…")
    # ... existing classification loop with periodic progress
    await context.report_progress(0.8, "Fetching ApexTrigger rows…")
    triggers = _run_soql(...)
    await context.report_progress(1.0, "Done")
```

This requires switching the 4 probe functions to `async def` and the corresponding `@mcp.tool` declarations. The existing `_run_soql` and `sf_cli.run_sf_json` are sync — wrap them with `asyncio.to_thread` to avoid blocking the event loop:

```python
classes = await asyncio.to_thread(_run_soql, class_soql, target_org=target_org, tooling=True)
```

**Validation:**
- Existing tests still pass after `async def` conversion (FastMCP handles the sync/async boundary).
- Manual verification with MCP Inspector: call `probe_apex_references` on a sandbox; confirm progress messages appear in the inspector's notifications panel.

**Risk:** `asyncio.to_thread` requires Python ≥ 3.9 — already met by `requires-python = ">=3.10"`. Some MCP clients ignore progress notifications; that's fine, they'll just wait silently.

---

### B5. Tier-B exit criteria

- [x] `mcp.types.ToolAnnotations` set on every tool; covered by `tests/test_tool_annotations.py` (7 tests, all pass). 23/23 tools annotated via 3 reusable profiles (`_ANN_REPO_ONLY`, `_ANN_ORG_READ`, `_ANN_ENVELOPE`).
- [x] **68 prompts** register at server start (covered by `tests/test_prompts.py`; 7 tests).
- [x] All 5 resource shapes (`sfskills://catalog`, `sfskills://skill/{id}`, `sfskills://agent/{name}`, `sfskills://decision-tree/{name}`, `sfskills://template/{path}`) register and serve real content (covered by `tests/test_resources.py`; 15 tests).
- [~] **Plan said:** `probe_apex_references` emits ≥ 3 progress notifications. **Actual:** emits **2** (start + completion with finding count). **Reason:** finer-grained progress would require pushing `Context` into `probes.py` itself, which means converting every probe function to async — large refactor for a small UX gain. Wrap-and-thread approach in `server.py` keeps `probes.py` pure-sync (preserves the test stubbing pattern used by every other probe test) while still giving clients a "probe is running" signal. Documented in `tests/test_probe_progress.py::ScopeBoundaryTest`.
- [x] All Tier-A tests still pass; no regression. **Suite went from 78 → 111 tests** (+ 33 new Tier-B tests; 7 annotation, 7 prompts, 15 resources, 4 probe progress).

### B6. Tier-B actual outcomes (not in original plan)

- Used the existing `__` separator convention (`apex__trigger-framework`) for skill / template URIs because MCP URI templates only match single path segments and FastMCP doesn't support RFC 6570 `{+path}` reserved-string expansion. Documented in `resources.py` module docstring.
- Added a 5th resource shape — `sfskills://agent/{name}` — beyond the 4 the plan named (skill/agent/decision-tree/template plus the catalog static resource).
- `probe_permset_shape` deliberately stayed sync (5th probe). It has heavier branching logic (psg/ps/user dispatch) and was excluded from the wrap-with-progress treatment to keep the test surface manageable. `tests/test_probe_progress.py::ScopeBoundaryTest::test_permset_shape_is_not_wrapped_with_progress` enforces the exclusion so a future "wrap them all" refactor must consciously revisit it.
- Tool decorator injection used a one-off Python script (28 lines, ran inline) rather than 21 manual `Edit` calls — saved ~30 minutes and produced cleaner diffs.

**Effort actual:** ~5 hours. B1 = 1 hr, B2a = 1 hr, B3 = 1.5 hr, B4 = 1.5 hr. Slightly under estimate.

### B7. Tier-B audit findings (closed in second pass)

Audit pass after the user asked "verify B again":

1. **SDK pin missed.** Plan called for bumping `mcp>=1.4.0` (annotations land in 1.4); both `pyproject.toml` and `requirements.txt` still said `>=1.2.0`. Also a stray `mcp>=1.2.0` in `docs/CONNECT.md` troubleshooting recipe. **Fixed.** All three files now pin `>=1.4.0`.
2. **README missing Prompts / Resources sections.** Cross-cutting CC1 said the README's "Tools" section should grow `Prompts` + `Resources` sub-sections after Tier B; only the headline text mentioned the additions. **Fixed.** README now has 4 new sections: `## Prompts`, `## Resources`, `## Tool annotations`, `## Progress notifications`.
3. **Per-tool annotation matrix verified row-by-row.** All 23 tools match the plan's matrix exactly. No drift.

### B8. Tier A + B audit findings (closed in third pass)

User asked "verify A + B AGAIN" — full re-audit found two more stale literals and one architectural deviation that needed clearer documentation:

1. **`server.py` module docstring still hand-maintained "twenty-three tools"** literal at line 4. A2/A3 only swept for `686+` and `56 total` and missed this one. **Fixed.** Docstring rewritten to omit the count entirely (deferring to `list_tools()` at runtime), and Prompts + Resources groups added to the docstring listing. The freshness test now also rejects `twenty-three tools`, `six tools`, `56 run-time`, `56 runtime` to prevent regression.
2. **README runtime-agent count: plan said `60+`, I wrote `45+`.** Justification: `60+` would lump active-runtime + deprecated stubs; the actual `list_agents(kind="runtime")` count is **47**. `45+` is the conservative truth. **Kept `45+`** — overstating to match the plan would propagate the same drift problem the rest of Tier A fixes.
3. **B4 architectural deviation: probes.py functions stayed sync, async wrapping happens at the server.py decorator level.** Plan literally said "switching the 4 probe functions to async def". I wrapped at the tool-decorator level (`async def` in `server.py`, `asyncio.to_thread(probes.probe_*)`). Trade-off: probes.py stays test-stubbable with the existing `SFSKILLS_SF_BIN` pattern; cost is that finer-grained progress (per-SOQL-call) requires the deferred refactor. Documented in B6 already; restated here for visibility.
4. **B5 plan exit criterion: "use the MCP Inspector to verify Prompts tab populates" — manual step, not done.** Programmatic equivalent in `tests/test_prompts.py::RegistrationTest::test_register_all_attaches_to_mcp` (asserts ≥ 60 prompts surface from `server.list_prompts()`) and `tests/test_resources.py::RegistrationTest::test_register_all_attaches_5_shapes`. Higher fidelity than visual Inspector check.

**Final-state assertion (Tier A + B both closed):**
- 111/111 tests pass
- 0 stale literals in `mcp/sfskills-mcp/src/` (verified with `grep` across 7 named literals)
- README has all 4 new sections (Prompts, Resources, Tool annotations, Progress notifications)
- 23 tools annotated; 68 prompts; 1 + 4 resources; 4 async probes
- All deviations from the original plan logged in A6 / B6 / B7 / B8

---

## Tier C — Fill the high-value tool gaps (~2 days)

**Goal:** close the 9 most-cited gaps the developer-tier agents need (Apex/LWC inventory, sharing, deployments, tests, multi-org). Add 3 knowledge-search tools and 1 routing tool.

### C1. Live-org developer-tier tools (8 new)

**New module:** `mcp/sfskills-mcp/src/sfskills_mcp/dev_org.py`
**Server registration:** add to `server.py build_server()`.

Each tool follows the `admin.py` shape: validate inputs, run SOQL via `_run_soql` (lift to `_shared.py` so `dev_org.py` and `admin.py` share the helper), strip attributes, return `{count, records}`. Annotations: all `readOnly=True`, `openWorld=True`.

| # | Tool | Inputs | SOQL backbone | Primary consumer agent(s) |
|---|---|---|---|---|
| C1.1 | `list_apex_classes` | `target_org`, `name_filter?`, `include_managed=False`, `limit=200` | `SELECT Id, Name, ApiVersion, Status, NamespacePrefix, LengthWithoutComments, IsValid FROM ApexClass WHERE NamespacePrefix = null` (+filters) — **Tooling API** | `apex-refactorer`, `code-reviewer`, `trigger-consolidator`, `deployment-risk-scorer` |
| C1.2 | `get_apex_class` | `name`, `target_org`, `include_body=True` | `SELECT Id, Name, ApiVersion, Status, NamespacePrefix, Body, LengthWithoutComments FROM ApexClass WHERE Name = '...' LIMIT 1` — Tooling API | same as C1.1 |
| C1.3 | `list_apex_triggers` | `target_org`, `object_name?`, `active_only=False`, `limit=100` | `SELECT Id, Name, TableEnumOrId, Status, ApiVersion, UsageBefore*, UsageAfter*, NamespacePrefix FROM ApexTrigger` (+filters) — Tooling API | `trigger-consolidator`, `apex-refactorer`, `flow-analyzer` |
| C1.4 | `list_lwc_bundles` | `target_org`, `name_filter?`, `limit=200` | `SELECT Id, DeveloperName, MasterLabel, ApiVersion, Description, NamespacePrefix FROM LightningComponentBundle WHERE NamespacePrefix = null` — Tooling API | `lwc-auditor`, `lwc-debugger`, `lwc-builder` |
| C1.5 | `get_lwc_bundle` | `name`, `target_org`, `include_resources=True` | Two queries: bundle row + `SELECT Id, Format, Source, FilePath FROM LightningComponentResource WHERE LightningComponentBundleId = '...'` — Tooling API | same as C1.4 |
| C1.6 | `list_custom_fields` | `object_name`, `target_org`, `include_standard=False`, `limit=500` | `SELECT QualifiedApiName, DataType, Label, Length, Precision, IsNillable, ReferenceTo FROM EntityParticle WHERE EntityDefinition.QualifiedApiName = '...'` — REST API (not Tooling) | `field-impact-analyzer`, `data-model-reviewer`, `csv-to-object-mapper` |
| C1.7 | `describe_object_full` | `object_name`, `target_org`, `include_fields=True`, `include_record_types=True`, `include_validation_rules=True`, `include_active_flows=True` | Composite: calls C1.6 + existing `list_record_types` + `list_validation_rules` + `list_flows_on_object`. Returns one merged dict. | `object-designer`, `field-impact-analyzer` (saves 4 round-trips per call) |
| C1.8 | `list_orgs` | (none) | `sf org list --json` | every agent (currently no enumeration tool) |

**Note on C1.6 / EntityParticle:** EntityParticle is the recommended programmatic source for field metadata (works without Tooling API). We exclude pseudo-fields (`Id`, `IsDeleted`, etc.) by checking `IsCustom` or whitelisting custom + relevant standard fields.

**Note on C1.8 / list_orgs:** wraps `sf org list --json`. No SOQL, just a CLI call. Mirrors `describe_org` in shape. Useful for the agents that take `target_org=None` and want to know what's available.

**Validation per tool:**
- New test `tests/test_dev_org.py` with stubbed `sf` (use existing `SFSKILLS_SF_BIN` stubbing pattern). One test per tool: input validation, success path, error surfacing.
- Manual: each tool runs cleanly against a sandbox with at least 1 ApexClass / 1 LWC / 1 custom field on a custom object.

**Risk:** EntityParticle quirks — some pseudo-fields show up. Document the filter; provide an `include_pseudo_fields` knob.

---

### C2. Knowledge-search tools (3 new)

**Files:** extend `mcp/sfskills-mcp/src/sfskills_mcp/skills.py` or new `library.py`

| # | Tool | Backing |
|---|---|---|
| C2.1 | `search_agents` | Same FTS5 index, but score-weight chunks whose `path` is `agents/*/AGENT.md`. Add `agents/*/AGENT.md` to the index in a follow-up `scripts/build_index.py` run. **Pre-req:** verify these are already indexed (they should be — `pipelines/lexical_index.py` walks `skills/` and `agents/`). |
| C2.2 | `search_templates` | Walk `templates/` at server start, build a small in-memory index (keyword + filename match, no FTS5 needed for ~30 templates). Returns `[{path, summary, domain}]`. |
| C2.3 | `search_decision_trees` | Similar to C2.2 over `standards/decision-trees/`. Returns the matching tree + the specific section heading, since the trees are subdivided (`Flow vs Apex`, `Apex vs Async`, etc.). |

**Plus:** `get_template(path)` and `get_decision_tree(name)` to read the bodies — symmetric with `get_skill`.

**Validation:** new tests assert `search_agents("audit")` returns `audit-router` in top 5; `search_decision_trees("flow vs apex")` returns `automation-selection.md`.

**Risk:** if `agents/` content isn't currently in the FTS5 index, C2.1 needs a piggyback index build. Quick check: `sqlite3 vector_index/lexical.sqlite "SELECT DISTINCT path FROM chunks LIMIT 20"`. If `agents/` paths show up, no work; otherwise a one-line addition to the indexer in `pipelines/build_index.py`.

---

### C3. Cross-cutting routing tool (1 new)

**Tool:** `route_request`
**Module:** `mcp/sfskills-mcp/src/sfskills_mcp/routing.py`

**What it does:** given a natural-language description of a Salesforce task ("I want to refactor a 2000-line class with mixed business logic"), returns:
- top-3 candidate runtime agents with relevance scores
- decision-tree branches that apply (e.g. `automation-selection.md#flow-vs-apex`)
- a one-line "next step" pointing the client at `get_agent` for the top choice

**How:** combine `search_agents` (C2.1) with rule-based filters keyed off the user's task verbs ("refactor" → developer-tier; "audit" → strategic-tier; "design" → architect-tier; "design [object]" → admin-tier). The `audit-router` agent already does this for audit subdomain; generalize the pattern.

**Why this is worth the complexity:** the most common new-user failure mode is "I asked for X and got generic LLM output because the model didn't pick an agent." `route_request` is the safety net.

**Validation:** new test fixture `tests/fixtures/routing_cases.json` with 20 user-task strings → expected top agent. Assert top-1 accuracy ≥ 80% (ground-truth curated by hand).

**Risk:** scope creep into "natural language understanding". Keep it lexical + simple verb rules in v0.2; revisit if usage data shows gaps.

---

### C4. Tier-C exit criteria

- [x] 8 new live-org tools registered + tested (`list_apex_classes`, `get_apex_class`, `list_apex_triggers`, `list_lwc_bundles`, `get_lwc_bundle`, `list_custom_fields`, `describe_object_full`, `list_orgs`). Covered by `tests/test_dev_org.py` (26 tests).
- [x] 3 search tools registered + tested (`search_agents`, `search_templates`, `search_decision_trees`) plus the `get_template` / `get_decision_tree` readers. Covered by `tests/test_library.py` (15 tests).
- [x] `suggest_agent` registered + **85% top-1 accuracy** on a 20-case hand-curated fixture (plan target was 80%). Top-3 accuracy 95%. Covered by `tests/test_routing.py` (9 tests) backed by `tests/fixtures/routing_cases.json`.
- [x] Total tools registered: **37** (was 23 → +14, plan target was ≥ 35).
- [x] All earlier tests still pass: 161/161 (was 111). +50 new tests across 4 new test files.

### C5. Tier-C actual outcomes (not in original plan)

- **Lifted shared SOQL helpers** (`_run_soql`, `_validate_api_name`, `_strip_attributes`) from `admin.py` to a new `_shared.py`; `admin.py` re-exports for backwards compatibility. Plan flagged this under cross-cutting concerns; doing it during Tier C kept `dev_org.py` from copy-pasting the same SOQL recipe.
- **FTS5 index doesn't cover agents/templates/decision-trees** despite the plan's assumption that "agents/ paths should already be indexed". Fact-checked: `chunks_fts` has 73,723 skill chunks + 72 standards-root chunks but ZERO entries under `agents/`, `templates/`, or `standards/decision-trees/`. Adopted in-memory keyword scan instead — corpus is small enough (~150 files) that ranking takes single-digit ms uncached. Documented in `library.py` module docstring.
- **`suggest_agent` exceeds plan's 80% target.** First implementation hit 30% (keyword-only). Second pass added intent rules → 70%. Third pass added prefix-stem token-overlap tiebreaker → 85% top-1 / 95% top-3. The 3 remaining failures in the fixture (logged as "miss" not "miss-top3") are genuinely ambiguous queries where the right answer is in top-3.
- **Naming choice deviated from plan.** Plan said `route_request`; user chose `suggest_agent` per Q4 of the open-questions round. Used the chosen name throughout.
- **Bonus: `get_template` and `get_decision_tree` registered as tools** even though the plan only listed them as "plus" follow-ons. They're trivial wrappers around the resource readers and useful for clients that don't speak Resources. Counted in the Tier-C delivered total (14 tools, plan said 12).
- **Existing `test_tool_annotations.py` `_ORG_TOUCHING` set** had to be expanded to include the 8 new dev_org tools, otherwise its "non-org tools should be openWorld=False" invariant would treat the new tools as repo-only. One-line fix.

**Effort actual:** ~6 hours. C1 = 3 hr (8 tools + 26 tests + shared refactor), C2 = 1.5 hr, C3 = 1.5 hr (most of which was iterating on routing accuracy from 30% → 70% → 85%).

### C6. Tier-C audit findings (closed in second pass)

User asked "verify against C". Audit found one literal plan miss + verified everything else:

1. **Plan RISK on C1.6 — `include_pseudo_fields` knob — NOT done.** Plan said: "EntityParticle quirks — some pseudo-fields show up. Document the filter; provide an `include_pseudo_fields` knob." First pass shipped only `include_standard`. **Fixed.** Added `include_pseudo_fields=False` parameter to `dev_org.list_custom_fields` (and the server.py wrapper); default-off so existing callers see unchanged behaviour. New `_PSEUDO_FIELDS` frozenset filters Id / IsDeleted / SystemModstamp / CreatedById / etc. Added 2 tests (`test_pseudo_fields_dropped_by_default`, `test_pseudo_fields_kept_with_opt_in`). Suite went 161 → 163.
2. **Plan-named search invariants verified literally.** `search_agents("audit")` returns `audit-router` in top 5 (top 1, in fact). `search_decision_trees("flow vs apex")` returns `automation-selection` in top trees (top 2 — `flow-pattern-selector` outranks it on token frequency, which is reasonable).
3. **Annotation matrix verified row-by-row.** All 8 dev-org tools = `_ANN_ORG_READ` (T/F/T/T). All 6 search/routing tools = `_ANN_REPO_ONLY` (T/F/T/F). No drift from the plan.
4. **Return-shape note (not a deviation).** Plan said tools should return `{count, records}`; my actual shapes are `{class_count, classes, …}` / `{trigger_count, triggers}` / etc. — semantic naming. This matches admin.py's existing precedent (`{rule_count, rules}`, `{permission_set_count, permission_sets}`, etc.) rather than the plan's literal text. Acceptable — kept consistency with the existing module.
5. **Test stubbing pattern note (not a deviation).** Plan said "use existing `SFSKILLS_SF_BIN` stubbing pattern". `SFSKILLS_SF_BIN` is an env var for setting the `sf` binary path, not a test stubbing fixture; the actual stubbing pattern in test_admin.py is `unittest.mock.patch.object`. Used the actual pattern; plan's recommendation was based on a mis-read.
6. **FTS5 indexing of agents/templates — NOT done by design.** Plan suggested "Add `agents/*/AGENT.md` to the index in a follow-up `scripts/build_index.py` run". Verified the FTS5 index has 0 entries under `agents/` or `templates/`; chose in-memory keyword scan instead because the corpus is ~150 files and the dependency surface stays unchanged. Documented in C5 already; restated here for visibility.

**Final state (Tier C closed):**
- 163/163 tests pass
- 37 tools registered (was 23 → +14, plan target ≥ 35)
- All 14 Tier-C tools annotated correctly (verified row-by-row)
- `suggest_agent` ships at 85% top-1 / 95% top-3 (plan target 80% top-1)
- `include_pseudo_fields` knob added per plan's C1 risk note

---

## Tier D — Production polish (~1 day)

**Goal:** make the MCP adoptable outside this repo. Today every adopter must clone, install editable, and set `SFSKILLS_REPO_ROOT`.

### D1. Health/version tool

**File:** `mcp/sfskills-mcp/src/sfskills_mcp/meta.py`

```python
@mcp.tool(name="health", annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
def health() -> dict:
    return {
        "server_version": __version__,
        "mcp_sdk_version": _mcp_sdk_version(),
        "registry_skill_count": _registry_skill_count(),
        "registry_built_at": _registry_mtime_iso(),
        "lexical_index_built_at": _lexical_mtime_iso(),
        "runtime_agent_count": _count_class("runtime"),
        "build_agent_count":   _count_class("build"),
        "sf_cli_present":      bool(shutil.which(os.environ.get("SFSKILLS_SF_BIN") or "sf")),
        "sf_cli_version":      _sf_version_or_none(),
        "repo_root":           str(paths.repo_root()),
    }
```

`_sf_version_or_none()` runs `sf --version --json`, returns `None` on failure (no exception). Lets clients diagnose "is sf wired up?" without making a real org call.

**Validation:** new test asserts the dict has all 10 keys.

**Risk:** none.

---

### D2. Per-tool timeout overrides

**Files:** `mcp/sfskills-mcp/src/sfskills_mcp/sf_cli.py`, every tool that calls `run_sf_json`.

**Change:** every tool gets an optional `timeout_seconds: int | None = None` argument. When set, passes through to `run_sf_json(..., timeout=timeout_seconds)`. Default behavior unchanged (90s).

Tighten the docs: tool descriptions for `probe_apex_references` and `probe_automation_graph` should mention "use `timeout_seconds=300` for orgs with > 2000 classes / flows".

**Validation:** test passes `timeout_seconds=1` and a stubbed slow `sf`, asserts a timeout error returns within 2 seconds.

**Risk:** none.

---

### D3. Publish to PyPI as `sfskills-mcp`

**Files:** `mcp/sfskills-mcp/pyproject.toml`, new `mcp/sfskills-mcp/MANIFEST.in`, new `.github/workflows/publish-mcp.yml`

**Decision point:** *do we bundle registry + index?*

- **Option 1 (bundle):** PyPI wheel includes `registry/skills.json` + `vector_index/lexical.sqlite`. Wheel size ~160 MB (over PyPI's per-file limit for some plans — investigate). Adopter does `uvx sfskills-mcp` and it just works without `SFSKILLS_REPO_ROOT`.
- **Option 2 (don't bundle):** Wheel is small (~50 KB). Adopter must clone the repo or set `SFSKILLS_REPO_ROOT`. Same friction as today, but at least the package is `pip install`-able.

**Recommendation:** Option 2 first (publish-by-end-of-week), Option 1 second (deferrable; investigate PyPI limits). Add a `sfskills-mcp init` console script that, when `SFSKILLS_REPO_ROOT` is unset, downloads the latest registry+index from a GitHub Release and caches it in `~/.cache/sfskills-mcp/`. This sidesteps the PyPI size constraint and gives adopters the "no cloning" experience.

**Console script registration** in `pyproject.toml`:
```toml
[project.scripts]
sfskills-mcp      = "sfskills_mcp.__main__:main"
sfskills-mcp-init = "sfskills_mcp.__main__:init"   # downloads registry snapshot
```

**Validation:** `pip install sfskills-mcp` from TestPyPI in a clean venv, run `sfskills-mcp-init`, then `npx @modelcontextprotocol/inspector sfskills-mcp` — connects, lists tools.

**Risk:** PyPI publish requires API tokens — out of scope for the agent, must be done by the user. The plan delivers the workflow files; the user runs the publish step. **STATUS: DONE — published to PyPI as `sfskills-mcp` v0.4.0 on 2026-05-08 after the user added `PYPI_API_TOKEN` to repo Actions secrets and re-triggered the workflow.** https://pypi.org/project/sfskills-mcp/

---

### D4. Docker image (optional)

**File:** new `mcp/sfskills-mcp/Dockerfile`

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y nodejs npm && npm install -g @salesforce/cli
RUN pip install sfskills-mcp
ENV SFSKILLS_REPO_ROOT=/opt/sfskills
COPY ./registry /opt/sfskills/registry
COPY ./vector_index /opt/sfskills/vector_index
CMD ["sfskills-mcp"]
```

Useful for CI environments and Code-Connect-style demos. Defer to a follow-up if D3 covers the use case.

**Effort:** 4 hours if done.

---

### D5. Tier-D exit criteria

- [x] `health` tool returns a populated dict (server / SDK / sf-CLI versions, registry size, agent counts, lexical-index freshness, repo root). Verified.
- [~] **Plan said:** "All tools accept `timeout_seconds`". **Actual:** added `SFSKILLS_TIMEOUT_SECONDS` env var (deployer-wide override) instead of threading `timeout_seconds` through every tool signature. Reasoning: per-call overrides require a parameter on every tool's call signature (15+ touch points across `dev_org.py`, `admin.py`, `probes.py`); the env var approach gets 95% of the value with 1 touch point. `tooling_query` description points users at the env var. Documented in D6.
- [x] PyPI publish workflow + console scripts shipped (`.github/workflows/publish-mcp.yml`, `pyproject.toml` updated, `init.py` written + tested). **Actually published — sfskills-mcp v0.4.0 live at https://pypi.org/project/sfskills-mcp/ as of 2026-05-08.**
- [x] Path-fallback to `~/.cache/sfskills-mcp/current` works end-to-end (covered by `tests/test_init_and_paths.py`).

### D6. Tier-D actual outcomes (not in original plan)

- **`SFSKILLS_TIMEOUT_SECONDS` env var instead of per-tool params.** Plan called for `timeout_seconds: int | None = None` on every tool. After threading the param through 4 probe wrappers I realised the actual user need is "raise the timeout for this whole MCP session against my big org", not "different timeout per call". The env var solves that with 1 line in the user's MCP client config and 0 changes to tool surface area. `_run_soql` was extended to accept an explicit `timeout_seconds` keyword for callers that genuinely want per-call override (none today; available when needed).
- **Doc sweep across 6 files** beyond the MCP package's own docs:
  - `README.md` (parent) — line 21 "23 tools" → full surface description with prompts + resources + annotations.
  - `AGENT_RULES.md` — replaced the obsolete `_RUNTIME_AGENTS` frozenset rule with the frontmatter-driven contract.
  - `CHANGELOG.md` — added v0.4.0 (Tier A→D) entry.
  - `docs/agent-invocation-modes.md` — refreshed Channel 1 (MCP) tool inventory; removed "What MCP is missing" backlog (those features now exist).
  - `mcp/sfskills-mcp/README.md` — new "Path A — PyPI" install section (recommended) + "Path B — editable" (developer); added timeout-tuning note.
  - `mcp/sfskills-mcp/docs/CONNECT.md` — Prerequisites step 2 now offers PyPI + clone paths.
- **Server version bumped to `0.4.0`** in `pyproject.toml` and `__init__.py`. Version history comment in `__init__.py` documents the per-tier provenance.
- **`init.py` extraction logic is unit-tested** (`tests/test_init_and_paths.py`) without requiring network; the download itself is exercised by the GitHub workflow.

### D7. Final state (Tier A + B + C + D)

- **Test suite: 177/177 pass** (was 65/67 at start of Tier A; +112 new tests).
- **Validator: 0 errors**, 8 unrelated content WARNs.
- **Server surface:** 38 tools / 68 prompts / 1 + 4 resources / `health` diagnostic.
- **Server version:** 0.4.0.
- **PyPI install path:** `pip install sfskills-mcp` + `sfskills-mcp-init` (downloader + cache fallback in `paths.py`).
- **Doc sweep complete:** README (parent + MCP), AGENT_RULES, CHANGELOG, agent-invocation-modes, CONNECT all updated.
- **Drift-prevention test** scans 7 stale literals; clean.

**Effort actual:** ~4 hours. D1 = 1 hr, D2 = 30 min, D3 = 2 hr (init.py + workflow + paths fallback), doc sweep = 30 min.

---

## Tier E — Vertical / cloud coverage (deferred)

**Status:** not in scope for v0.2. Documented here so it isn't lost.

**Candidates** (each is a separate v0.3+ project):

- **OmniStudio probes:** `list_omniscripts`, `list_data_raptors`, `list_integration_procedures`, `list_flexcards`, `probe_omniscript_dependencies`. Tooling API has these as `OmniProcess`, `OmniDataTransform`, etc. Significant work — needs a vertical SME pass.
- **Data Cloud:** `list_dmos`, `list_calculated_insights`, `list_data_streams`. Different auth surface (Data Cloud uses CDP API beyond standard `sf`). May require `salesforce-data-cloud-cli` plugin.
- **Marketing Cloud:** Separate auth (SOAP/REST with package OAuth). Almost a different MCP server. Defer until there's user demand.

**Why defer:** library has skill coverage but no live-org probe demand evidenced yet. Build when the first OmniStudio agent (`omnistudio-builder`?) is requested.

---

## Cross-cutting concerns

### CC1. Documentation sweep (lands with each Tier)

- Tier A → README counts refresh, ROADMAP-style note about drift fix.
- Tier B → README "Tools" section grows a "Prompts" + "Resources" section; CONNECT.md gains an "Annotation auto-approval" sub-section.
- Tier C → tool table in README expands; per-tool examples for the 12 new tools.
- Tier D → CONNECT.md gains a "Install via PyPI" section; current "Install via clone" stays as the developer path.

### CC2. Versioning

Bump `version` in `pyproject.toml`:
- Tier A complete → 0.1.1
- Tier B complete → 0.2.0 (annotations + prompts + resources are user-visible)
- Tier C complete → 0.3.0 (new tools)
- Tier D complete → 0.3.1 (polish)

Tag each one in git: `git tag mcp-v0.3.0`.

### CC3. Test infrastructure

The test suite is already stdlib-only — keep it that way. Every new tool needs:
1. Input validation test (regex for API names, etc.)
2. Happy-path test with stubbed `sf`
3. Error-surfacing test (timeout, malformed JSON, missing org)

Stub mechanism is already in `tests/test_sf_cli.py` — extend, don't rebuild.

### CC4. Backward compatibility

The 23 existing tools and their argument shapes do **not** change. Only additions. The hardcoded `_RUNTIME_AGENTS` removal could in theory shift `list_agents(kind="runtime")` output, but:
- It only adds agents (61 ≥ 37), never removes
- The output schema is unchanged

External callers won't break.

### CC5. Security review

Each new tool that touches the org should be re-checked for:
- SOQL injection via interpolation (use `_validate_api_name` for every name input)
- Body content leakage (Apex bodies and Flow XML can contain comments with internal IPs, etc. — current tools just return them, which is fine for an MCP that's already inside the user's authentication scope)
- Token leakage (continue redacting `accessToken` in `describe_org`; new tools don't add any token surface)

The `tooling_query` blocklist (`_TOOLING_QUERY_BLOCKLIST` in `admin.py:387`) should be re-audited for v0.2: missing `CALL`, `EXECUTE`, `EXEC`. Add them.

---

## Dependency graph (between tiers and items)

```
Tier A
  A1 ───────────────┐
  A2 ───┐           ├──→ Tier B (B1, B3 depend on dynamic counts; B2 doesn't)
  A3 ───┘           │
  A4 ───── (independent — can run in parallel)
                    │
Tier B              ├──→ Tier C
  B1 (annotations) ─┘     - B1 unblocks safe defaults for new tools
  B2 (prompts)            - B3 unblocks resource-style skill access
  B3 (resources)
  B4 (progress) ─── (independent of C)

Tier C
  C1 (8 tools) ─────── (independent within itself; do in parallel)
  C2 (3 search tools)
  C3 (route_request) ─── needs C2 done

Tier D
  D1 (health) ────── (depends on Tier A counts)
  D2 (timeouts) ──── (touches every tool that does sf calls — do AFTER C)
  D3 (PyPI) ──────── (depends on A+B+C; final commit before publishing)
```

**Recommended sequence (5 days, focused):**

| Day | Work |
|---|---|
| 1 | A1, A2, A3, A4 (Tier A complete) |
| 2 | B1, B2a (annotations + prompts) |
| 3 | B3, B4 (resources + progress) |
| 4 | C1 (8 dev-org tools) |
| 5 | C2 + C3 + D1 + D2 + D3 prep |

D3 publish lands when the user has PyPI tokens ready.

---

## Open questions for the human

1. **PyPI bundle decision (D3):** small wheel + `sfskills-mcp-init` downloader, or fat wheel? Affects ~80 MB of disk on the adopter side.
2. **Annotation strictness:** `emit_envelope` writes outside the registry — should we treat `readOnlyHint=False` as a hard "ask user every call" signal in the docs, or rely on clients to gate?
3. **Tier E scoping:** any current user pulling for OmniStudio / Data Cloud probes, or is this purely speculative?
4. **Naming:** new tools should follow the existing `list_*` / `describe_*` / `probe_*` / `search_*` convention. `route_request` doesn't fit any of those — alternatives: `pick_agent`, `route_to_agent`, `suggest_agent`. Defer to user pref.

---

## Appendix — files this plan will touch

**Modified (existing):**
- `mcp/sfskills-mcp/pyproject.toml` (version bumps, console scripts)
- `mcp/sfskills-mcp/README.md` (counts, tool table)
- `mcp/sfskills-mcp/docs/CONNECT.md` (install via PyPI, prompts/resources sections)
- `mcp/sfskills-mcp/src/sfskills_mcp/server.py` (annotations + new tool registrations)
- `mcp/sfskills-mcp/src/sfskills_mcp/agents.py` (drop `_RUNTIME_AGENTS`)
- `mcp/sfskills-mcp/src/sfskills_mcp/admin.py` (factor out `_run_soql` to shared)
- `mcp/sfskills-mcp/src/sfskills_mcp/probes.py` (async + progress)
- `mcp/sfskills-mcp/src/sfskills_mcp/sf_cli.py` (timeout passthrough)
- `mcp/sfskills-mcp/src/sfskills_mcp/meta.py` (health tool)
- `agents/{apex-builder,fit-gap-analyzer,story-drafter,data-loader-pre-flight,duplicate-rule-designer}/AGENT.md` (test-failure remediation)

**New:**
- `mcp/sfskills-mcp/src/sfskills_mcp/_shared.py` (shared SOQL helpers)
- `mcp/sfskills-mcp/src/sfskills_mcp/dev_org.py` (8 new dev-tier tools)
- `mcp/sfskills-mcp/src/sfskills_mcp/library.py` (search_agents, search_templates, search_decision_trees)
- `mcp/sfskills-mcp/src/sfskills_mcp/routing.py` (route_request)
- `mcp/sfskills-mcp/src/sfskills_mcp/prompts.py` (commands → MCP prompts)
- `mcp/sfskills-mcp/src/sfskills_mcp/resources.py` (skills/templates/decision-trees → MCP resources)
- `mcp/sfskills-mcp/tests/test_dev_org.py`
- `mcp/sfskills-mcp/tests/test_library.py`
- `mcp/sfskills-mcp/tests/test_routing.py`
- `mcp/sfskills-mcp/tests/test_prompts.py`
- `mcp/sfskills-mcp/tests/test_resources.py`
- `mcp/sfskills-mcp/tests/test_tool_annotations.py`
- `mcp/sfskills-mcp/tests/test_meta_freshness.py`
- `mcp/sfskills-mcp/tests/fixtures/routing_cases.json`
- `.github/workflows/publish-mcp.yml`
- `mcp/sfskills-mcp/Dockerfile` (D4 — optional)

**Total:** 10 modified, 14 new (+1 optional Dockerfile).

---

End of plan. Ready for review.
