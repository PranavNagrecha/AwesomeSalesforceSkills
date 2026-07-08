# sfskills-mcp

Model Context Protocol server that hands any MCP-capable AI coding assistant
three things at once:

1. The full **SfSkills** library (1012 Salesforce skills, source-grounded,
   role-tagged, versioned) — via `search_skill` and `get_skill`.
2. **Live metadata from your actual Salesforce org** — via `describe_org`,
   `list_custom_objects`, `list_flows_on_object`, `list_validation_rules`,
   `list_permission_sets`, `describe_permission_set`, `list_record_types`,
   `list_named_credentials`, `list_approval_processes`, `tooling_query`, and
   `validate_against_org`.
3. **Run-time agents** (47 active runtime agents across developer, admin,
   strategic, and vertical/governance tiers, plus 14 build-time agents and
   14 deprecation stubs that redirect via `list_deprecated_redirects`) that
   compose the skill library + live-org tools into concrete deliverables —
   via `list_agents` and `get_agent`.

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
(so no secrets touch the server) and the SfSkills FTS5 index + fastembed
semantic embeddings for retrieval (no API keys required — both run locally).

### Retrieval quality (v0.4.2 benchmark, 2026-05-09)

Measured against three audits with different ground-truth shapes. The
secondary corpora (agents, templates, decision-trees) had no measured
baseline before v0.4.2; the slug-aware scorer rewrite added in this
release lifts them dramatically.

| Audit                                | Hit@1 | Hit@3 |
| ------------------------------------ | ----: | ----: |
| Author-curated triggers (1,285 Q)    |  98.6%|  100.0%|
| Synthetic NL skills (1,418 Q)        |  74.5%|   87.8%|
| Realistic-user smoke (71 Q)          |  81.7%|   94.4%|
| Agents NL (247 Q)                    |  95.5%|   98.0%|
| Templates NL (195 Q)                 |  88.7%|  100.0%|
| Decision-trees NL (34 Q)             |  82.4%|   97.1%|

The NL Hit@1 number on skills is dragged down by labeling artifacts in
the synthetic generator (multiple skills can legitimately answer one
fixture query). The realistic-user smoke — hand-crafted queries with
unambiguous expected answers — better reflects real-world quality at
81.7% Hit@1 / 94.4% Hit@3.

---

## Tools

| Tool                      | What it does                                                                                              |
| ------------------------- | --------------------------------------------------------------------------------------------------------- |
| `search_skill`            | Lexical search over the SfSkills corpus. Returns ranked skill ids + top chunks. Optional `domain` filter. |
| `get_skill`               | Full SKILL.md + registry metadata for a given skill id. Optional `include_references` for deep context.   |
| `describe_org`            | `sf org display` summary: org id, instance, edition, API version, sandbox/scratch flags.                  |
| `list_custom_objects`     | Custom (or standard) sObjects in the org. Substring filter via `name_filter`.                             |
| `list_flows_on_object`    | Flows whose `TriggerObjectOrEvent` matches the given sObject (Tooling API).                               |
| `validate_against_org`    | Category-aware probe: "does a skill's guidance already have analogs in the org?"                          |
| `list_agents`             | Enumerate SfSkills run-time + build-time agents with one-line summaries. Filter via `kind="runtime"`.     |
| `get_agent`               | Fetch an agent's full `AGENT.md` body so the caller's model can execute it (MCP does not execute agents). |
| `list_validation_rules`   | Validation rules for a given sObject with formula, active flag, error display.                            |
| `list_permission_sets`    | Permission sets + groups + muting permission sets, with license + assignment counts.                      |
| `describe_permission_set` | Full object / field / user permission matrix for a specific permission set.                               |
| `list_record_types`       | Record types, active flag, master-layout assignments, picklist value scoping.                             |
| `list_named_credentials`  | Named Credentials + External Credentials (read-only; never returns secrets).                              |
| `list_approval_processes` | Approval processes + steps + next approver rules for an sObject.                                          |
| `tooling_query`           | Generic read-only Tooling API SOQL with a DML/mutation blocklist (escape hatch for admin-land agents).    |
| `list_apex_classes`       | Apex class inventory + name filter + status filter. Primary consumer: apex-refactorer, code-reviewer.     |
| `get_apex_class`          | Single Apex class by name; optional body for header-only calls.                                           |
| `list_apex_triggers`      | Trigger inventory with per-event flags (BeforeInsert/AfterUpdate/etc.).                                   |
| `list_lwc_bundles`        | LightningComponentBundle inventory.                                                                       |
| `get_lwc_bundle`          | One bundle + every resource (js/html/css/meta-xml).                                                       |
| `list_custom_fields`      | Field metadata via EntityParticle. Custom-only by default; `include_standard=true` for standard fields.   |
| `describe_object_full`    | Composite read: fields + record types + validation rules + active flows in one call.                      |
| `list_orgs`               | Wraps `sf org list` — every authenticated org normalized into one shape.                                  |
| `search_agents`           | Rank agents by relevance to a natural-language query.                                                     |
| `search_templates`        | Rank canonical building blocks under `templates/`.                                                         |
| `search_decision_trees`   | Rank decision trees + return the best matching section per tree.                                          |
| `get_template`            | Read one template by relative path (e.g. `apex/TriggerHandler.cls`).                                       |
| `get_decision_tree`       | Read one decision tree by basename (e.g. `automation-selection`).                                          |
| `suggest_agent`           | Take a free-text task; return ranked candidate agents + decision-tree branches + a `next_step` pointer.    |

### Run-time agents reachable via `get_agent`

Tier sizes below count the 47 active runtime agents. Fourteen single-mode
auditors/governors were retired in Wave 3b and now redirect via
`list_deprecated_redirects` (`audit-router` absorbs them); `list_agents(kind="runtime")`
returns the active set shown here.

Developer + architecture tier (16):

| Agent name                 | What it returns |
| -------------------------- | --------------- |
| `apex-refactorer`          | Refactor an Apex class onto canonical `templates/apex/` patterns + a test class |
| `trigger-consolidator`     | Collapse N triggers on one sObject into the `TriggerHandler` framework |
| `test-class-generator`     | Bulk-safe ≥85% coverage test class using `TestDataFactory` + `BulkTestPattern` |
| `soql-optimizer`           | Ranked SOQL findings with before/after fixes |
| `security-scanner`         | CRUD/FLS + sharing + hardcoded-secret audit |
| `flow-analyzer`            | Flow-vs-Apex routing + bulkification review |
| `bulk-migration-planner`   | Bulk API 2.0 / PE / Pub-Sub / REST / Connect plan from volume + latency |
| `lwc-auditor`              | A11y + performance + security audit of an LWC bundle |
| `deployment-risk-scorer`   | HIGH/MEDIUM/LOW risk score + breaking-change list |
| `agentforce-builder`       | Full Agentforce action scaffold: Apex + topic + test + eval || `lwc-builder`              | Full LWC bundle (js/html/css/meta/tests) + optional Apex controller |
| `lwc-debugger`             | Ranked hypotheses + diagnostic probes + proposed fix for a live LWC failure |
| `apex-builder`             | Apex class(es) built from requirements + test class |
| `changeset-builder`        | Change set manifest + deployment checklist |
| `flow-orchestrator-designer` | Flow Orchestrator design + stage / step map |
| `automation-migration-router` | WFR/PB automation inventory → Flow migration plan |

Admin accelerators — Tier 1 (14):

| Agent name                   | What it returns |
| ---------------------------- | --------------- |
| `field-impact-analyzer`      | Blast-radius report before renaming / deleting a field |
| `object-designer`            | Setup-ready sObject design from a business concept |
| `permission-set-architect`   | Profile-less PS / PSG / Muting design per persona |
| `flow-builder`               | Flow design from requirements + automation-tree routing || `data-loader-pre-flight`     | Go/no-go checklist for a Data Loader / Bulk API load |
| `duplicate-rule-designer`    | Matching + Duplicate Rules + post-load hygiene |
| `assignment-and-auto-response-rules-designer` | Assignment rule + auto-response rule design |
| `business-hours-and-holidays-configurator` | Business hours + holiday set configuration plan |
| `config-workbook-author`     | Configuration workbook (object / field / automation inventory) |
| `custom-metadata-and-settings-designer` | CMDT / Custom Settings design + Apex usage patterns |
| `entitlement-and-milestone-designer` | Entitlement process + milestone design |
| `experience-cloud-admin-designer` | Experience Cloud site design (member, guest, CMS) |
| `path-designer`              | Path + guidance + key fields design per object / stage |
| `process-flow-mapper`        | Business process → Salesforce automation map |

Strategic — Tier 2 (7):

| Agent name                                 | What it returns |
| ------------------------------------------ | --------------- || `data-model-reviewer`                      | Data-model domain review (rollups, XID, growth) |
| `integration-catalog-builder`              | Integration catalog + posture scorecard || `csv-to-object-mapper`                     | CSV → sObject mapping + VR collision report |
| `email-template-modernizer`                | Template classification + migration plan |
| `audit-router`                             | Routes to appropriate single-mode auditor or runs multi-mode audit |
| `fit-gap-analyzer`                         | Fit / gap analysis: requirements vs org configuration |
| `story-drafter`                            | User stories with Given/When/Then acceptance criteria |

Vertical + governance — Tier 3 (10):

| Agent name                            | What it returns |
| ------------------------------------- | --------------- |
| `omni-channel-routing-designer`       | Queue + routing + presence design with capacity math |
| `knowledge-article-taxonomy-agent`    | Data categories + article types + channel-audience plan |
| `sales-stage-designer`                | Opportunity stage ladder + forecast + VR gates |
| `lead-routing-rules-designer`         | Source × geo × product routing matrix + SLAs || `sandbox-strategy-designer`           | Environment ladder + pools + refresh calendar |
| `release-train-planner`               | Package + branching + CI/CD + release calendar |
| `waf-assessor`                        | Well-Architected scorecard + remediation backlog |
| `agentforce-action-reviewer`          | Per-action A–F scorecard + guardrails gap list || `profile-to-permset-migrator`         | Profile → Permission Set migration plan + PS / PSG design |
| `user-access-diff`                    | Side-by-side access comparison report between users |

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
Prompt (~68 prompts as of this writing). Type `/refactor-apex`,
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
- **`openWorldHint`** — `True` for the 16 org-touching tools (output depends on external state); `False` for the 7 repo-only tools (deterministic, cacheable).
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
pip install sfskills-mcp           # ~50 KB wheel
sfskills-mcp-init                  # one-time data download (~160 MB → ~/.cache/sfskills-mcp/)
sfskills-mcp                       # serves stdio
```

The data download fetches the registry, lexical index, agent corpus,
templates, and decision trees from the latest GitHub Release into
`~/.cache/sfskills-mcp/`. Override the cache location with
`SFSKILLS_CACHE_DIR=/some/path` if your home directory is read-only.

Pin a release: `sfskills-mcp-init --release mcp-v0.4.0`. Re-download:
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
| **Tested floor (v0.4.4 QA)** | `2.103.7` | Pre-prod regression suite passes against this version on a real Education-Cloud sandbox. |
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

Quick recipe for the most common clients below. **Every other client we
support — Claude Desktop, Zed, Cline, Continue, Cody, Codex CLI, Gemini CLI,
Goose, LibreChat, Open WebUI, JetBrains AI Assistant, 5ire, and the generic
stdio transport — is covered in [docs/CONNECT.md](./docs/CONNECT.md)**, along
with troubleshooting and the security model.

### Cursor

`~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project-scoped):

```json
{
  "mcpServers": {
    "sfskills": {
      "command": "python3",
      "args": ["-m", "sfskills_mcp"],
      "env": {
        "SFSKILLS_REPO_ROOT": "/absolute/path/to/AwesomeSalesforceSkills"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add sfskills \
  --env SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills \
  -- python3 -m sfskills_mcp
```

### Windsurf

`~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "sfskills": {
      "command": "python3",
      "args": ["-m", "sfskills_mcp"],
      "env": { "SFSKILLS_REPO_ROOT": "/absolute/path/to/AwesomeSalesforceSkills" }
    }
  }
}
```

### VS Code (GitHub Copilot Agent)

`.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "sfskills": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "sfskills_mcp"],
      "env": { "SFSKILLS_REPO_ROOT": "/absolute/path/to/AwesomeSalesforceSkills" }
    }
  }
}
```

**For the full recipe matrix (15+ clients), per-client pitfalls, and
troubleshooting, read [docs/CONNECT.md](./docs/CONNECT.md).**

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

### Layout

```
mcp/sfskills-mcp/
├── pyproject.toml
├── requirements.txt
├── README.md
├── docs/
│   └── CONNECT.md       # per-client setup for every MCP-capable AI tool
├── src/sfskills_mcp/
│   ├── __init__.py
│   ├── __main__.py      # python -m sfskills_mcp entrypoint
│   ├── server.py        # FastMCP wiring
│   ├── paths.py         # repo-root resolution
│   ├── skills.py        # search_skill, get_skill
│   ├── sf_cli.py        # sf subprocess wrapper
│   └── org.py           # describe_org, list_custom_objects, list_flows_on_object, validate_against_org
└── tests/
    ├── test_skills.py
    └── test_sf_cli.py
```

---

## Design notes

- **No secrets in-process.** Every org call routes through `sf`; the server
  inherits the CLI's keyring-backed auth. Access tokens, refresh tokens, and
  other credentials in `describe_org` / `list_orgs` / `list_named_credentials`
  output are **fully masked** — the `access_token_preview` field renders as
  `"***"`. (Earlier docs claimed a prefix/suffix preview; the implementation
  was hardened in v0.4.3 to drop all token bytes after a live-test leak.)
- **Read-only.** No tool performs DML, deploys metadata, or runs apex. The
  full operation surface is `sobject describe`, `sobject list`, `data query`,
  `org display`, and `org list`.
- **Failures are data, not exceptions.** Every tool returns
  `{"error": ..., ...}` rather than raising when the CLI or registry
  misbehaves, so MCP clients can surface actionable messages to the user
  without the server crashing mid-conversation.
- **Retrieval reuses the repo's own FTS5 index** (`vector_index/lexical.sqlite`)
  and the ranking logic in `pipelines/ranking.py`, so MCP search results match
  `scripts/search_knowledge.py` exactly.
- **Namespace-tolerant skill ids.** `apex/trigger-framework` and
  `apex__trigger-framework` both resolve; the latter matches the on-disk
  filename convention.

---

## License

Same as the parent repository.
