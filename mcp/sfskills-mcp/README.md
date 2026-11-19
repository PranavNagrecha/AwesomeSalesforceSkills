# sfskills-mcp

Model Context Protocol server that hands any MCP-capable AI coding assistant
three things at once:

1. The full **SfSkills** library (1,040 Salesforce skills; a claims audit
   against the official guides is in progress and most packages have not been
   audited yet) — via `search_skill` and `get_skill`.
2. **Live metadata from your actual Salesforce org** — via `describe_org`,
   `list_custom_objects`, `list_flows_on_object`, `list_validation_rules`,
   `list_permission_sets`, `describe_permission_set`, `list_record_types`,
   `list_named_credentials`, `list_approval_processes`, `tooling_query`, and
   `validate_against_org`.
3. **Run-time agents** (70 active runtime agents across developer, admin,
   strategic, vertical/governance, and orchestration tiers, plus 15 build-time agents and
   14 deprecation stubs that redirect via `list_deprecated_redirects`) that
   compose the skill library + live-org tools into concrete deliverables —
   via `list_agents` and `get_agent`. 7 run-time agents are `stable`, 8 `beta`
   and 55 `experimental` (ungraded); see the agents section below.

> **Counts are live.** The numbers above reflect the registry at the time of
> writing; the server itself reads `registry/skills.json` and the AGENT.md
> frontmatter at startup, so what you see in your client always matches your
> checkout.

The net effect: the agent can answer "does this trigger framework already
exist in my org?" by itself instead of asking you — and if you say "refactor
this Apex class", it can pull the full `apex-refactorer` instruction set via
`get_agent` and execute it.

---

## Why this exists

Without live-org context, every Salesforce AI suggestion is a guess. The agent
doesn't know whether:

- `AccountTriggerHandler` already exists (and you're about to create a second one).
- There are three record-triggered flows on `Opportunity` that will run before
  your new Apex trigger.
- Your org is a sandbox with a namespace that changes field API names.
- The SfSkills library already has a `trigger-framework` skill that covers
  exactly what you're about to ask the agent to invent.

This MCP server closes both gaps using the Salesforce CLI for org access
(so no secrets touch the server) and the SfSkills lexical FTS5 index for
retrieval (no API keys; runs locally). The PyPI data bundle is lexical-only;
embeddings exist only in a checkout with `fastembed` installed and enabled.

Held-out lexical retrieval (154 queries, 2026-10-20): Hit@1 0.41, Hit@3
0.50. That is the number for `search_skill` on queries the index was not
tuned on.

---

## Tools

All 50 tools, listed from the `@mcp.tool` registrations in `server.py`: 23 run offline against the library and local files, 26 read from an org through the `sf` CLI, and `emit_envelope` is the only one that writes (to `docs/reports/`). Scope is the tool's annotation set; see "Tool annotations" below.

| Tool | Scope | What it does |
|---|---|---|
| `search_skill` | repo | Lexical search over the SfSkills library (1,040 Salesforce skills spanning admin, apex, flow, lwc, integration, security, data, architect, devops, omnistudio, agentforce) |
| `get_skill` | repo | Fetch a skill by id (e.g. 'apex/trigger-framework'). |
| `describe_org` | org (read) | Describe the user's target Salesforce org via 'sf org display' — org id, instance URL, edition, API version, sandbox/scratch status. |
| `list_custom_objects` | org (read) | List custom sObjects in the target org. Set include_standard=true to include standard objects. |
| `list_flows_on_object` | org (read) | List Flows (record-triggered, scheduled-triggered, or platform-event-triggered) targeting the given sObject, via the Tooling API. |
| `validate_against_org` | org (read) | Category-aware probe that checks whether a skill's guidance already has analogs in the org. E.g. |
| `list_validation_rules` | org (read) | List Validation Rules on an sObject via the Tooling API. Returns rule name, active state, error message, error display field, and id. |
| `list_permission_sets` | org (read) | List Permission Sets in the org. By default excludes the profile-owned shadow PSes Salesforce creates per profile. |
| `describe_permission_set` | org (read) | Describe a single Permission Set by API name — header metadata, ObjectPermissions, and (optionally) FieldPermissions. |
| `list_record_types` | org (read) | List Record Types on an sObject — developer name, label, active flag, and description. Use this in record-type-and-layout-auditor and object-designer. |
| `list_named_credentials` | org (read) | List Named Credentials in the org. Includes endpoint and principal type. |
| `list_approval_processes` | org (read) | List Approval ProcessDefinitions, optionally filtered by object. By default returns only active approvals. |
| `tooling_query` | org (read) | Escape-hatch read-only SOQL against the Tooling or REST API. Refuses any statement that is not a SELECT or that contains DML keywords / semicolons. |
| `probe_apex_references` | org (read) | Enumerate Apex classes and triggers referencing an <object>.<field>. Uses word-boundary regex on fetched bodies to filter substring false positives. |
| `probe_flow_references` | org (read) | Enumerate active Flow versions whose metadata XML references <object>.<field>. |
| `probe_matching_rules` | org (read) | List MatchingRule + DuplicateRule records on an sObject with their field items. |
| `probe_permset_shape` | org (read) | Summarize a Permission Set / Permission Set Group / user scope. scope argument is psg:<DeveloperName>, ps:<Name>, or user:<username>. |
| `list_agents` | repo | List SfSkills agents available to the caller. |
| `get_agent` | repo | Fetch the full AGENT.md body for a named agent (e.g. 'apex-refactorer', 'security-scanner', 'deployment-risk-scorer'). |
| `health` | repo | Server diagnostic snapshot — server / SDK / sf-CLI versions, registry skill count + build timestamp, lexical-index freshness + size, agent counts by class (runtime / buil |
| `get_deployment_result` | org (read) | Read-only: retrieve an EXISTING Salesforce deployment job via `sf project deploy report --job-id --json`. job_id is required (15/18-char 0Af…). |
| `get_apex_test_run` | org (read) | Read-only: retrieve an EXISTING Apex test run via `sf apex get test --test-run-id --json`. test_run_id is required (15/18-char 707…). |
| `get_user_access_evidence` | repo | Read-only P03 access-path evidence from a captured JSON fixture (result_path). Bounded to 32 KiB. |
| `get_component_dependency_evidence` | repo | Read-only P04 component-dependency evidence from a captured JSON fixture (result_path). Bounded to 32 KiB. |
| `get_automation_inventory` | repo | Read-only P05 automation inventory from a captured JSON fixture (result_path). Bounded to 32 KiB. |
| `get_flow_test_result` | repo | Read-only P06 flow-test / release-readiness evidence from a captured JSON fixture (result_path). Bounded to 32 KiB. |
| `get_code_analysis_result` | repo | Read-only P07 code-analysis / security-posture evidence from a captured JSON fixture (result_path). Bounded to 32 KiB. |
| `get_integration_config_summary` | repo | Read-only P08 integration-config evidence from a captured JSON fixture (result_path). Bounded to 32 KiB. |
| `get_data_load_result` | repo | Read-only P09 data-load result evidence from a captured JSON fixture (result_path). Bounded to 32 KiB. |
| `get_org_snapshot_manifest` | repo | Read-only P10 org-snapshot manifest from a captured JSON fixture (result_path). Bounded to 32 KiB. |
| `get_agentforce_test_result` | repo | Read-only P11 Agentforce test evidence from a captured JSON fixture (result_path). Bounded to 32 KiB. |
| `compare_org_snapshots` | repo | Read-only P12 org-snapshot comparison from a captured JSON fixture (result_path). Bounded to 32 KiB. |
| `list_deprecated_redirects` | repo | Return the map of retired agent ids → canonical router + flag. Call this once per session; before get_agent, check whether the requested id is in this map and redirect. |
| `get_invocation_modes` | repo | Return docs/agent-invocation-modes.md — the 15 channels this library can be consumed through (MCP, slash commands, bundle export, informal chat, CI harness, subagents, et |
| `emit_envelope` | writes docs/reports | Atomically write an agent's output envelope JSON + paired markdown report to docs/reports/<agent>/<run_id>.… per docs/consumer-responsibilities.md. |
| `probe_automation_graph` | org (read) | Enumerate every active automation on a given sObject: record-triggered flows (grouped by trigger context), legacy Process Builders, active Apex triggers (with event usage |
| `list_apex_classes` | org (read) | List Apex classes in the org via the Tooling API. Excludes managed-package classes by default (NamespacePrefix = null). |
| `get_apex_class` | org (read) | Fetch one ApexClass by name. include_body defaults True; pass False for a header-only call when the class is large or you only need metadata. |
| `list_apex_triggers` | org (read) | List ApexTrigger rows. object_name scopes to one sObject. |
| `list_lwc_bundles` | org (read) | List Lightning Web Component bundles via the Tooling API. Excludes managed-package bundles by default. |
| `get_lwc_bundle` | org (read) | Fetch one LightningComponentBundle by DeveloperName + (by default) every resource in the bundle (js, html, css, meta-xml). |
| `list_custom_fields` | org (read) | List fields on an sObject via EntityParticle (REST API). |
| `describe_object_full` | org (read) | Composite read: fields + record types + validation rules + active flows for one sObject in a single call. |
| `list_orgs` | org (read) | List every Salesforce org the user is authenticated to. Wraps 'sf org list'. |
| `search_agents` | repo | Rank SfSkills agents by relevance to a natural-language query. Useful when you know what you want to do (e.g. |
| `search_templates` | repo | Rank canonical building blocks under templates/ by relevance (TriggerHandler, ApplicationLogger, BaseService, TestDataFactory, LWC skeleton, Flow fault-path, etc.). |
| `search_decision_trees` | repo | Rank standards/decision-trees/ by relevance and return the best matching section per tree (e.g. 'flow vs apex' → automation-selection.md → '## Flow vs Apex'). |
| `get_template` | repo | Fetch one canonical template by relative path under templates/ (e.g. 'apex/TriggerHandler.cls'). |
| `get_decision_tree` | repo | Fetch one decision tree by basename without .md (e.g. 'automation-selection'). |
| `suggest_agent` | repo | Take a free-text task description ('I want to refactor a 2000-line Apex class', 'audit my picklists', 'design a permission set for the marketing team') and return ranked  |

### Run-time agents reachable via `get_agent`

`list_agents(kind="runtime")` returns the 70 active run-time agents. By tier:
Developer + architecture (28), Admin accelerators — Tier 1 (14),
Strategic — Tier 2 (9), Vertical + governance — Tier 3 (11), and
Orchestration — Tier 4 (8), the requirement-to-build loop in
`standards/build-orchestration.md`.

By status: 7 are `stable` (each graded once on one real input, with mixed
grades), 8 are `beta` (the Tier-4 loop, exercised by five maintainer-run
example builds), and 55 are `experimental` (ungraded). Treat an experimental
agent's output as a draft. The roster with each agent's status is
[`agents/_shared/RUNTIME_VS_BUILD.md`](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/blob/main/agents/_shared/RUNTIME_VS_BUILD.md).
Fourteen retired agents redirect via `list_deprecated_redirects` to
`audit-router`. No agent deploys or approves a gate.

### `validate_against_org` routing

| Skill category               | Probes run                                                                             |
| ---------------------------- | -------------------------------------------------------------------------------------- |
| `apex`, `devops`             | `*TriggerHandler*` / `*Handler` ApexClass rows                                         |
| `flow`, `agentforce`         | Flows targeting `object_name`                                                          |
| `integration`                | `NamedCredential` + `RemoteProxy` rows                                                 |
| `security`                   | `PermissionSet` rows (excluding profile-owned)                                         |
| `data`, `architect`, `admin` | `sobject describe` on `object_name` + (for architect) handler class scan               |
| `lwc`                        | `LightningComponentBundle` rows                                                        |
| `omnistudio`                 | Handler class scan                                                                     |

Any probe that needs `object_name` and doesn't receive one returns
`{"skipped": ...}` instead of failing, so the agent can still read the
rest of the response.

---

## Prompts

Every wrapper file in [`commands/`](../../commands/) is exposed as an MCP
Prompt. Type `/refactor-apex`,
`/audit-router`, `/build-apex`, etc. in any MCP-capable client and the
wrapper loads — Claude Code, Cursor, Cline, Claude Desktop all support this.

Each prompt body is the wrapper's own markdown; it walks the user through
input collection → agent execution → output. The MCP server registers them;
the client's model executes them.

## Resources

Five resource shapes, addressable from any MCP client without a tool call:

| URI | What |
| --- | --- |
| `sfskills://catalog` | Slim JSON list of every registered skill (id, category, description, tags) |
| `sfskills://skill/{id}` | Full `SKILL.md` markdown. Use the `domain__name` form: `apex__trigger-framework` |
| `sfskills://agent/{name}` | Full `AGENT.md` body for a named agent: `apex-refactorer`, `audit-router`, … |
| `sfskills://decision-tree/{name}` | A routing tree from `standards/decision-trees/` (basename, no `.md`): `automation-selection` |
| `sfskills://template/{path}` | Canonical building block under `templates/`. Same `__` convention: `apex__TriggerHandler.cls` |

> **Why `__`:** MCP URI templates only match a single path segment, so we
> use `__` as the on-the-wire separator and decode it server-side. The
> registry already supports the same form (`apex/foo` and `apex__foo` are
> equivalent everywhere).

## Tool annotations

Every tool registers with [`ToolAnnotations`](https://modelcontextprotocol.io/specification/2025-03-26/server/tools#tool-annotations) so MCP-aware clients can auto-approve safely:

- **`readOnlyHint`** — `True` for every tool except `emit_envelope` (the only tool that writes to disk; output goes to `docs/reports/<agent>/<run_id>.{json,md}`).
- **`destructiveHint`** — `False` for all tools.
- **`openWorldHint`** — `True` for the 26 org-touching tools (output depends on external state); `False` for the 24 repo-only tools (deterministic, cacheable).
- **`idempotentHint`** — `True` for read tools; `False` for `emit_envelope` (overwrite-protected by default; re-runs of the same `run_id` reject without `overwrite=True`).

Honest annotations let Cursor's `autoApprove`, Cline's per-tool gating, and
Claude Desktop's trust prompts make safe defaults without the user having
to opt-in per tool.

## Progress notifications

Four probes — `probe_apex_references`, `probe_flow_references`,
`probe_matching_rules`, `probe_automation_graph` — emit `notifications/progress`
at start and completion. On orgs with thousands of Apex classes or Flow
versions a probe can take 30+ seconds; the progress signal stops the client
from looking frozen.

`probe_permset_shape` deliberately stayed sync (more conditional branches,
faster typical case); finer-grained progress inside any probe requires a
follow-up that pushes `Context` into [probes.py](src/sfskills_mcp/probes.py).

---

## Install

Two paths:

### Path A — PyPI (recommended for end users)

```bash
pip install sfskills-mcp           # wheel of about 100 KB
sfskills-mcp-init                  # one-time data download (about 116 MB compressed for mcp-v0.5.1) → ~/.cache/sfskills-mcp/
sfskills-mcp                       # serves stdio
```

The data download fetches the registry, lexical index, agent corpus,
templates, and decision trees from the latest GitHub Release into
`~/.cache/sfskills-mcp/`. Override the cache location with
`SFSKILLS_CACHE_DIR=/some/path` if your home directory is read-only.

Pin a release: `sfskills-mcp-init --release mcp-v0.5.1`. Re-download:
`sfskills-mcp-init --force`.

### Path B — Editable install from a checkout (developer / contributor)

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills
python3 -m pip install -e mcp/sfskills-mcp
```

The package auto-detects the repo root via `registry/skills.json`; no
init step needed.

Python 3.10+ required for both paths.

### Salesforce CLI

You also need the **Salesforce CLI** (`sf`) on PATH, authenticated to at
least one org:

```bash
# Install: https://developer.salesforce.com/tools/salesforcecli
sf org login web --alias my-dev
sf config set target-org=my-dev
```

The server never sees org credentials — it shells out to `sf`, which uses
its own keyring-backed auth store.

**Supported `sf` versions:**

| | Version | Notes |
|---|---|---|
| **Minimum** | `2.0.0` | The unified `sf` CLI (post-`sfdx` rename). Earlier `sfdx`-prefixed builds will not work — the server invokes `sf data query` and `sf data query --use-tooling-api`. |
| **Recommended** | latest stable | Keep `sf` current — Salesforce ships frequent bug-fix releases. Run `sf update` periodically. |

Check your version: `sf --version`

### Tuning timeouts

Default `sf` subprocess timeout is 90s. Raise it for orgs with thousands
of Apex classes / Flow versions:

```bash
export SFSKILLS_TIMEOUT_SECONDS=600
```

Verify the install with the `health` tool — it returns versions, registry
size, sf-CLI presence, and agent counts without making a real org call.

---

## Run

```bash
# stdio transport (default; used by every MCP client)
python3 -m sfskills_mcp

# or, after install
sfskills-mcp
```

### Environment

| Variable             | Purpose                                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `SFSKILLS_REPO_ROOT` | Absolute path to the SfSkills checkout. Auto-detected when the server is installed inside the repo; set it whenever you wire the server into an AI client. |
| `SFSKILLS_SF_BIN`    | Absolute path to the `sf` binary. Defaults to whatever `sf` is on PATH. Set this for macOS GUI clients (Claude Desktop, Cursor, VS Code) that don't inherit your shell PATH. |

---

## Connect it to your AI client

Claude Code, after a PyPI install:

```bash
claude mcp add sfskills -- sfskills-mcp
```

From a checkout:

```bash
claude mcp add sfskills \
  --env SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills \
  -- python3 -m sfskills_mcp
```

Every other client (Cursor, Windsurf, VS Code, Claude Desktop, Zed, Cline,
Continue, Codex CLI, Gemini CLI, Goose and the generic stdio transport), with
per-client pitfalls and troubleshooting, is in [docs/CONNECT.md](./docs/CONNECT.md).

---

## Example agent prompts

```
"Before I write an Account trigger handler, check whether my org already has one."
→ search_skill("trigger framework", domain="apex")
→ get_skill("apex/trigger-framework")
→ validate_against_org(skill_id="apex/trigger-framework", target_org="my-dev")
```

```
"What record-triggered flows run on Opportunity today?"
→ list_flows_on_object(object_name="Opportunity", active_only=true)
```

```
"List every custom object with 'Claim' in the name and tell me which have flows."
→ list_custom_objects(name_filter="Claim")
→ list_flows_on_object(object_name="<each>") for each hit
```

---

## Verify your setup

Fastest way — run the official MCP Inspector against the server:

```bash
npx -y @modelcontextprotocol/inspector python3 -m sfskills_mcp
```

Open the URL it prints, click **Connect**, switch to **Tools**, call
`search_skill` with `{"query": "trigger recursion"}`. You should see ranked
skill ids come back. See [docs/CONNECT.md → Verifying the connection](./docs/CONNECT.md#verifying-the-connection)
for more options.

---

## Development

```bash
cd mcp/sfskills-mcp

# Run tests (stdlib-only; MCP SDK not required for these)
python3 -m unittest discover -s tests -v

# Install dev extras
python3 -m pip install -e '.[dev]'
```

The `sf` CLI is stubbed in tests via `SFSKILLS_SF_BIN`, so CI runs hermetically
without Salesforce CLI installed.

---

## Design notes

- **No secrets in-process.** Every org call routes through `sf`; the server
  inherits the CLI's keyring-backed auth. Access tokens, refresh tokens, and
  other credentials in `describe_org` / `list_orgs` / `list_named_credentials`
  output are **fully masked** — the `access_token_preview` field renders as
  `"***"`.
- **Read-only.** Every org call is a read through `sf` (describes, SOQL and
  Tooling queries, `org display` / `org list`, and reports on existing deploy
  jobs and Apex test runs); no tool performs DML, deploys, or runs Apex.
- **Failures are data, not exceptions.** Every tool returns
  `{"error": ..., ...}` rather than raising when the CLI or registry
  misbehaves, so MCP clients can surface actionable messages to the user
  without the server crashing mid-conversation.
- **Retrieval uses the repo's own FTS5 index** (`vector_index/lexical.sqlite`)
  through a separate implementation of the `scripts/search_knowledge.py`
  pipeline. On a checkout, CI checks that both return the same skills for 154
  held-out queries (`evals/measurement/check_cli_mcp_parity.py --heldout`); a
  PyPI install is lexical-only and is not covered by that check.
- **Namespace-tolerant skill ids.** `apex/trigger-framework` and
  `apex__trigger-framework` both resolve; the latter matches the on-disk
  filename convention.

---

## License

Same as the parent repository: PolyForm Small Business License 1.0.0
(source-available, not open source).
