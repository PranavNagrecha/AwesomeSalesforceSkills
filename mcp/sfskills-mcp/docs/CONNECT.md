# Connecting `sfskills-mcp` to your AI client

This is the field guide. If your AI tool speaks the Model Context Protocol
(MCP), it can consume the six `sfskills` tools — `search_skill`, `get_skill`,
`describe_org`, `list_custom_objects`, `list_flows_on_object`,
`validate_against_org` — with the recipes below.

> Every recipe assumes you've completed the one-time setup in [Prerequisites](#prerequisites).
> Config-file **paths change occasionally**; if yours doesn't match, check your
> client's current docs and look for the `mcpServers` / `mcp` section.

---

## Contents

- [Prerequisites](#prerequisites)
- [Environment variables](#environment-variables)
- [Per-client setup](#per-client-setup)
  - [Claude Code (CLI)](#claude-code-cli)
  - [Claude Desktop](#claude-desktop)
  - [Cursor](#cursor)
  - [Windsurf (Codeium)](#windsurf-codeium)
  - [Zed](#zed)
  - [VS Code (GitHub Copilot Agent)](#vs-code-github-copilot-agent)
  - [Cline (VS Code extension)](#cline-vs-code-extension)
  - [Continue (VS Code / JetBrains)](#continue-vs-code--jetbrains)
  - [Sourcegraph Cody](#sourcegraph-cody)
  - [OpenAI Codex CLI](#openai-codex-cli)
  - [Gemini CLI](#gemini-cli)
  - [Goose (Block)](#goose-block)
  - [LibreChat](#librechat)
  - [Open WebUI](#open-webui)
  - [JetBrains AI Assistant](#jetbrains-ai-assistant)
  - [5ire](#5ire)
  - [Aider (CLI fallback, no native MCP)](#aider-cli-fallback-no-native-mcp)
  - [Generic stdio MCP client](#generic-stdio-mcp-client)
- [Verifying the connection](#verifying-the-connection)
- [Troubleshooting](#troubleshooting)
- [Security model](#security-model)

---

## Prerequisites

**1. Python 3.10+.**

```bash
python3 --version  # expect 3.10 or newer
```

**2. Install `sfskills-mcp`.**

```bash
git clone https://github.com/PranavNagrecha/AwesomeSalesforceSkills.git
cd AwesomeSalesforceSkills

# Install the MCP package (editable is recommended so repo updates flow through)
python3 -m pip install -e mcp/sfskills-mcp
```

Verify:

```bash
python3 -m sfskills_mcp --help
# → SfSkills MCP server (Salesforce skills + live-org metadata)
```

**3. Install + authenticate the Salesforce CLI.**

```bash
# macOS (Homebrew)
brew install sfdx

# npm (any OS)
npm install --global @salesforce/cli

# Verify
sf --version

# Log in (browser-based OAuth; no credentials touch this MCP server)
sf org login web --alias my-dev
sf config set target-org=my-dev
```

**4. Figure out the absolute path to the SfSkills checkout.**

```bash
cd /path/to/AwesomeSalesforceSkills
pwd   # copy this — you'll paste it into every client's config below
```

Call it `<SFSKILLS_REPO_ROOT>` for the rest of this doc.

---

## Environment variables

| Variable             | Required?  | Purpose                                                                                     |
| -------------------- | ---------- | ------------------------------------------------------------------------------------------- |
| `SFSKILLS_REPO_ROOT` | Recommended | Absolute path to the SfSkills checkout. Auto-detected when the server is installed inside the repo; always set it when configuring a client. |
| `SFSKILLS_SF_BIN`    | Optional   | Absolute path to the `sf` binary. Defaults to whatever `sf` is on the shell's PATH. Set this when your AI client launches without inheriting your shell PATH (common on macOS GUI apps). |

**Finding your `sf` binary path** (for `SFSKILLS_SF_BIN`):

```bash
which sf
# /opt/homebrew/bin/sf     (macOS Homebrew)
# /usr/local/bin/sf        (macOS Intel)
# /usr/bin/sf              (Linux package manager)
# C:\Program Files\sf\bin\sf.exe   (Windows)
```

**Finding your Python binary path** (some clients don't inherit PATH either):

```bash
which python3
# /opt/homebrew/bin/python3
```

When in doubt, use absolute paths in the `command` and `env` fields of every
config below. That eliminates 90% of "it works on CLI but not in my editor" bugs.

---

## Per-client setup

Every snippet below uses the same launch contract:

- **command:** `python3` (or absolute path)
- **args:** `["-m", "sfskills_mcp"]`
- **env:** at minimum `SFSKILLS_REPO_ROOT`; optionally `SFSKILLS_SF_BIN`
- **transport:** `stdio` (implicit; all clients below speak stdio)

### Claude Code (CLI)

**Config file:** `~/.claude.json` (global) or `.mcp.json` in any project root
(project-scoped). Claude Code also provides a `claude mcp` management command.

**Add via CLI (preferred):**

```bash
claude mcp add sfskills \
  --env SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills \
  -- python3 -m sfskills_mcp
```

**Add by editing `~/.claude.json`:**

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

Verify:

```bash
claude mcp list              # sfskills should appear
claude mcp get sfskills      # prints the stored config
```

In a chat, type `/mcp` to confirm the server is connected.

### Claude Desktop

**Config file:**

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**Config:**

```json
{
  "mcpServers": {
    "sfskills": {
      "command": "/opt/homebrew/bin/python3",
      "args": ["-m", "sfskills_mcp"],
      "env": {
        "SFSKILLS_REPO_ROOT": "/absolute/path/to/AwesomeSalesforceSkills",
        "SFSKILLS_SF_BIN": "/opt/homebrew/bin/sf"
      }
    }
  }
}
```

Restart Claude Desktop. Click the **🔌 tools** icon in the composer — `sfskills`
should show six tools.

> macOS tip: Claude Desktop launches via LaunchServices, which strips PATH to a
> minimal default. Always use absolute paths for `command` and `SFSKILLS_SF_BIN`.

### Cursor

**Config file:** `~/.cursor/mcp.json` (global) **or** `.cursor/mcp.json` inside
your project (project-scoped — checked in for your team, overrides global).

**Config:**

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

Restart Cursor. Open **Settings → Cursor Settings → MCP**. `sfskills` should
be listed as `Running`; expand it to see the six tools. The agent will call
them automatically when it detects a Salesforce task, or you can invoke them
explicitly with `@sfskills search_skill "trigger framework"`.

### Windsurf (Codeium)

**Config file:** `~/.codeium/windsurf/mcp_config.json`

**Config:**

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

Restart Windsurf. Cascade picks up the server on launch; invoke with
`@sfskills`.

### Zed

**Config file:** `~/.config/zed/settings.json` (Zed stores MCP servers under
the `context_servers` key).

**Config:**

```json
{
  "context_servers": {
    "sfskills": {
      "command": {
        "path": "python3",
        "args": ["-m", "sfskills_mcp"],
        "env": {
          "SFSKILLS_REPO_ROOT": "/absolute/path/to/AwesomeSalesforceSkills"
        }
      }
    }
  }
}
```

Reload settings (`cmd-shift-p` → "zed: reload") or restart Zed.

### VS Code (GitHub Copilot Agent)

**Config file:** `.vscode/mcp.json` in your workspace (project-scoped) **or**
global under your user settings. VS Code's Copilot Agent exposes MCP servers
in **Agent Mode** only.

**Config (`.vscode/mcp.json`):**

```json
{
  "servers": {
    "sfskills": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "sfskills_mcp"],
      "env": {
        "SFSKILLS_REPO_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

> `${workspaceFolder}` resolves to the current VS Code workspace root. If
> you're using this MCP server from *outside* the SfSkills repo (e.g. in your
> Salesforce project's workspace), replace with the absolute path to the
> SfSkills checkout.

Reload VS Code. In Copilot Chat, switch to **Agent Mode**; `sfskills` tools
appear in the tool picker.

### Cline (VS Code extension)

Cline stores MCP config inside VS Code settings or a project-local file.

**UI path:** Cline side panel → ⚙ → **MCP Servers** → **Edit MCP Settings**.

**Config:**

```json
{
  "mcpServers": {
    "sfskills": {
      "command": "python3",
      "args": ["-m", "sfskills_mcp"],
      "env": {
        "SFSKILLS_REPO_ROOT": "/absolute/path/to/AwesomeSalesforceSkills"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Leave `autoApprove` empty; each org-touching tool call will prompt for
approval the first time. Add specific tool names to `autoApprove` only after
you trust them (e.g. `["search_skill", "get_skill"]` — never the org-mutating
ones, though this server has none).

### Continue (VS Code / JetBrains)

**Config file:** `~/.continue/config.json` (all platforms).

**Config:**

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": {
          "type": "stdio",
          "command": "python3",
          "args": ["-m", "sfskills_mcp"],
          "env": {
            "SFSKILLS_REPO_ROOT": "/absolute/path/to/AwesomeSalesforceSkills"
          }
        }
      }
    ]
  }
}
```

Restart Continue. Tools appear under the **MCP** tool category.

### Sourcegraph Cody

Cody supports MCP via its "OpenCtx" context providers as of late 2025.

**Config file:** `~/.config/cody/cody.json` or per-workspace `.vscode/cody.json`.

**Config:**

```json
{
  "cody.experimental.openctx.providers": {
    "https://openctx.org/npm/@openctx/provider-mcp": {
      "servers": {
        "sfskills": {
          "command": "python3",
          "args": ["-m", "sfskills_mcp"],
          "env": {
            "SFSKILLS_REPO_ROOT": "/absolute/path/to/AwesomeSalesforceSkills"
          }
        }
      }
    }
  }
}
```

Restart Cody. Cody's MCP surface has evolved rapidly — if the key name above
doesn't match your build, search Cody's release notes for "MCP" and use the
current key; the value shape is the same.

### OpenAI Codex CLI

**Config file:** `~/.codex/config.toml`

**Config:**

```toml
[mcp_servers.sfskills]
command = "python3"
args = ["-m", "sfskills_mcp"]

[mcp_servers.sfskills.env]
SFSKILLS_REPO_ROOT = "/absolute/path/to/AwesomeSalesforceSkills"
```

Codex CLI auto-loads servers on launch. Run `codex` then `/mcp` to confirm
`sfskills` is connected.

### Gemini CLI

**Config file:** `~/.gemini/settings.json`

**Config:**

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

Run `gemini` then `/mcp list` to confirm.

### Goose (Block)

**Config file:** `~/.config/goose/config.yaml`

**Config:**

```yaml
extensions:
  sfskills:
    type: stdio
    enabled: true
    cmd: python3
    args:
      - -m
      - sfskills_mcp
    envs:
      SFSKILLS_REPO_ROOT: /absolute/path/to/AwesomeSalesforceSkills
    timeout: 60
```

Run `goose session` — the server is auto-attached.

### LibreChat

**Config file:** `librechat.yaml` (repo root of your LibreChat install).

**Config:**

```yaml
mcpServers:
  sfskills:
    type: stdio
    command: python3
    args:
      - -m
      - sfskills_mcp
    env:
      SFSKILLS_REPO_ROOT: /absolute/path/to/AwesomeSalesforceSkills
    chatMenu: true  # exposes the tools in the agent builder UI
```

Restart the LibreChat container/process. In the agent builder, `sfskills`
tools appear under **Tools → MCP**.

### Open WebUI

Open WebUI supports MCP via its **Tools** extension system. Configure via the
admin UI:

1. **Admin → Settings → Tools → MCP Servers → +**
2. **Command:** `python3`
3. **Args:** `-m, sfskills_mcp` (comma-separated)
4. **Env vars:** `SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills`
5. **Save** and toggle on.

### JetBrains AI Assistant

As of JetBrains 2025.2+, AI Assistant supports MCP servers via **Settings →
Tools → AI Assistant → MCP**.

1. Click **+**.
2. **Name:** `sfskills`
3. **Command:** `python3`
4. **Arguments:** `-m sfskills_mcp`
5. **Env:** `SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills`
6. Click **Test connection**, then **Apply**.

> If the MCP pane isn't visible, ensure AI Assistant is up to date and MCP is
> enabled under **Registry → `platform.ai.mcp.enabled`**.

### 5ire

5ire is a fully graphical MCP client. Configure via its **Tools → MCP** pane:

1. **Add server** → **stdio**
2. **Name:** `sfskills`
3. **Command:** `python3 -m sfskills_mcp`
4. **Environment:** add a row `SFSKILLS_REPO_ROOT` → your path
5. **Save** and toggle **Enabled**.

### Aider (CLI fallback, no native MCP)

Aider doesn't yet speak MCP. Best-effort fallback — expose the skill library
to the model as read-only context:

```bash
# From the repo root
python3 scripts/export_skills.py --platform aider

# Then launch Aider in your Salesforce project with SfSkills conventions loaded
aider --read /absolute/path/to/AwesomeSalesforceSkills/exports/aider/CONVENTIONS.md
```

Track Aider's MCP support in their GitHub releases; once shipped, fall back to
the generic stdio config below.

### Generic stdio MCP client

Any client that speaks the MCP stdio transport works with:

- **command:** `python3` (absolute path if the client doesn't inherit shell PATH)
- **args:** `["-m", "sfskills_mcp"]`
- **env:** `SFSKILLS_REPO_ROOT=<absolute path to the SfSkills checkout>`

If your client expects a single command string instead of `command` + `args`:

```
python3 -m sfskills_mcp
```

---

## Verifying the connection

### From the command line (before wiring into a client)

Launch the server in stdio mode — it'll wait for JSON-RPC on stdin. Press
`Ctrl-C` to exit.

```bash
SFSKILLS_REPO_ROOT=/absolute/path/to/AwesomeSalesforceSkills python3 -m sfskills_mcp
```

If the process exits immediately with an error, read it; the most common
failures are a missing `mcp` package or a bad `SFSKILLS_REPO_ROOT`.

### With the MCP Inspector (canonical debug tool)

The MCP Inspector is the reference debug client:

```bash
npx -y @modelcontextprotocol/inspector \
  python3 -m sfskills_mcp
```

Open the URL it prints. In the Inspector UI:

1. Click **Connect**.
2. Switch to the **Tools** tab — all six `sfskills` tools should list.
3. Call `search_skill` with `{"query": "trigger recursion"}` — expect a list
   of skills.
4. Call `describe_org` with `{}` — expect either a live org summary or a
   structured `{"error": ..., "available_orgs": [...]}` payload.

If step 2 shows tools but step 3 errors, the server is wired correctly and
the failure is upstream (registry missing, bad repo root). If step 2 is
empty, your client config never reached this binary.

### From inside each client

Use the chat / agent surface and ask:

> "List the sfskills tools you have access to, and call describe_org."

Every client above will route that through the MCP tool surface and reply
with the six tool names.

---

## Troubleshooting

### `Could not locate the SfSkills repo root.`

Set `SFSKILLS_REPO_ROOT` in the `env` block of your client config to the
absolute path of your SfSkills checkout. Relative paths won't work — most
MCP clients launch the server with an unpredictable CWD.

### `Salesforce CLI ('sf') was not found on PATH.`

Your AI client is launching the server without your shell's PATH (very
common in macOS GUI apps — Claude Desktop, Cursor, VS Code). Fix:

```json
"env": {
  "SFSKILLS_REPO_ROOT": "/abs/path/to/AwesomeSalesforceSkills",
  "SFSKILLS_SF_BIN": "/opt/homebrew/bin/sf"   // output of `which sf`
}
```

### `ModuleNotFoundError: No module named 'sfskills_mcp'`

The server was launched with the wrong Python. Switch `command` to the
absolute path returned by `which python3` (or the venv's `bin/python3`) and
re-install:

```bash
/opt/homebrew/bin/python3 -m pip install -e /abs/path/to/AwesomeSalesforceSkills/mcp/sfskills-mcp
```

### `ModuleNotFoundError: No module named 'mcp'`

The Python MCP SDK isn't installed for that interpreter. Install it:

```bash
/opt/homebrew/bin/python3 -m pip install 'mcp>=1.2.0'
```

### `sf command timed out after 90s`

A single CLI call took too long — usually a cold auth refresh or a very
large `list_custom_objects` response on a huge org. Re-run; if it keeps
timing out, file an issue and include `sf --version` output.

### Tools don't appear in the client UI, but the process is running

- Confirm your client reloaded the config. Most clients require a full
  restart, not just a window refresh.
- Check the client's logs for MCP errors (Cursor: **Output → Cursor MCP**;
  Claude Desktop: `~/Library/Logs/Claude/mcp*.log` on macOS).
- Verify with the Inspector (above). If Inspector sees six tools and your
  client doesn't, the problem is in the client's config shape — re-read its
  section above and check casing (`mcpServers` vs `context_servers` vs
  `servers` — they differ across clients).

### `describe_org` returns `{"error": "No target org set"}`

Run `sf config set target-org=<your-alias>` in your shell, or pass the
`target_org` argument to each tool call. The server never guesses which org
to hit.

### Access tokens leaking into agent context

They can't, by design — `describe_org` redacts the `accessToken` field to
a `prefix…suffix` preview, and no other tool includes it in its output.

---

## Security model

| Concern                    | How `sfskills-mcp` handles it                                                                   |
| -------------------------- | ----------------------------------------------------------------------------------------------- |
| **Credentials**            | Never in-process. All org calls shell out to `sf`, which uses its own keyring-backed auth store. |
| **Access tokens**          | Redacted in tool outputs. Only a `prefix…suffix` preview is returned, never the full token.     |
| **Destructive operations** | None. Every tool is read-only (`sobject describe`, `sobject list`, `data query`, `org display`, `org list`). The server never writes metadata, runs apex, or executes DML. |
| **Network scope**          | Only `sf`-initiated calls to the Salesforce instance the user is already authenticated to. The server itself opens no sockets. |
| **Secrets in env**         | `SFSKILLS_REPO_ROOT` and `SFSKILLS_SF_BIN` are the only env vars read. Neither is a secret.    |

If you ever want to gate tool calls behind per-invocation approval (e.g. to
prevent an agent from running `data query` on a production org without your
consent), use the client-side approval mechanism (Cline's `autoApprove: []`,
Claude Code's default-approval-off behavior, Cursor's per-tool confirmation).
The server itself does not gate — it assumes the client does.
