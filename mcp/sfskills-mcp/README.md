# sfskills-mcp

Model Context Protocol server that hands any MCP-capable AI coding assistant
two things at once:

1. The full **SfSkills** library (686+ Salesforce skills, source-grounded,
   role-tagged, versioned) — via `search_skill` and `get_skill`.
2. **Live metadata from your actual Salesforce org** — via `describe_org`,
   `list_custom_objects`, `list_flows_on_object`, and `validate_against_org`.

The net effect: the agent can answer "does this trigger framework already
exist in my org?" by itself instead of asking you.

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
(so no secrets touch the server) and the SfSkills FTS5 index for retrieval
(no API keys required).

---

## Tools

| Tool                   | What it does                                                                                              |
| ---------------------- | --------------------------------------------------------------------------------------------------------- |
| `search_skill`         | Lexical search over the SfSkills corpus. Returns ranked skill ids + top chunks. Optional `domain` filter. |
| `get_skill`            | Full SKILL.md + registry metadata for a given skill id. Optional `include_references` for deep context.   |
| `describe_org`         | `sf org display` summary: org id, instance, edition, API version, sandbox/scratch flags.                  |
| `list_custom_objects`  | Custom (or standard) sObjects in the org. Substring filter via `name_filter`.                             |
| `list_flows_on_object` | Flows whose `TriggerObjectOrEvent` matches the given sObject (Tooling API).                               |
| `validate_against_org` | Category-aware probe: "does a skill's guidance already have analogs in the org?"                          |

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

## Install

```bash
# From the repo root
python3 -m pip install -e mcp/sfskills-mcp
```

Python 3.10+ required.

You also need the **Salesforce CLI** (`sf`) on PATH, authenticated to at
least one org:

```bash
# Install: https://developer.salesforce.com/tools/salesforcecli
sf org login web --alias my-dev
sf config set target-org=my-dev
```

The server never sees org credentials — it shells out to `sf`, which uses
its own keyring-backed auth store.

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
  inherits the CLI's keyring-backed auth. Access tokens in `describe_org`
  output are redacted to a short prefix/suffix preview.
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
