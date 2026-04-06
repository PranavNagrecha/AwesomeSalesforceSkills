---
name: vscode-salesforce-extensions
description: "Use this skill when setting up, configuring, or troubleshooting the Salesforce Extensions for VS Code: Apex Language Server activation, deploy-on-save behavior, Apex debugging, org authorization, and workspace project structure. NOT for Salesforce CLI command reference (use sf-cli-and-sfdx-essentials), scratch org definition files (use scratch-org-management), or CI/CD pipeline configuration."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "Apex Language Server is not starting or showing errors in VS Code"
  - "how do I set up VS Code for Salesforce development with the extension pack"
  - "deploy on save is not working or deploying to the wrong org"
  - "I need to debug Apex code in VS Code — should I use Interactive or Replay Debugger"
  - "VS Code is not recognizing my sfdx-project.json or custom objects"
  - "how do I authorize a Salesforce org from VS Code"
tags:
  - vscode
  - salesforce-extensions
  - apex-language-server
  - deploy-on-save
  - apex-debugger
  - developer-tooling
inputs:
  - "VS Code version and Salesforce Extension Pack version"
  - "Java Development Kit (JDK) version installed (11, 17, or 21)"
  - "Project structure — is sfdx-project.json at the workspace root"
  - "Org type — source-tracked (scratch/sandbox) or non-tracked (production/DE)"
  - "Whether the org has the Apex Interactive Debugger license"
outputs:
  - "Verified workspace configuration with sfdx-project.json and .vscode/settings.json"
  - "Correct deploy-on-save settings for the org type"
  - "Apex debugging launch configuration (Interactive or Replay)"
  - "Org authorization commands and default org setup"
  - "Diagnosis and remediation for Apex Language Server failures"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# VS Code Salesforce Extensions

This skill activates when you need to set up a Salesforce development environment in Visual Studio Code, troubleshoot the Apex Language Server, configure deploy-on-save for source-tracked or non-tracked orgs, choose between Apex Interactive and Replay Debugger, or resolve workspace structure issues. It covers the Salesforce Extension Pack and its constituent extensions but not the underlying CLI commands themselves.

---

## Before Starting

Gather this context before working on anything in this domain:

- **JDK version:** The Apex Language Server requires Java. JDK 21 is recommended; JDK 17 and 11 are also supported. The `salesforcedx-vscode-apex.java.home` setting must point to a valid JDK installation if the system `JAVA_HOME` is not set or points to a JRE.
- **Workspace root:** The extension pack only activates fully when `sfdx-project.json` is in the **top-level folder** opened in VS Code. Opening a parent directory or a subfolder breaks Apex Language Server activation.
- **Org authorization:** At least one org must be authorized via `sf org login web` (or the legacy `sfdx auth:web:login`) before deploy, retrieve, or debug commands will work. The default org is set per-project, not globally.

---

## Core Concepts

### Apex Language Server

The Apex Language Server provides code completion, go-to-definition, inline errors, and rename support for `.cls`, `.trigger`, and anonymous Apex. It runs as a separate Java process managed by the `salesforcedx-vscode-apex` extension. It will not start if:

1. No valid JDK is found (JRE alone is not sufficient).
2. `sfdx-project.json` is missing from the workspace root.
3. The workspace was opened at the wrong directory level.

When the language server starts, it indexes all Apex classes and triggers under the project's `packageDirectories`. Large orgs with thousands of classes may see a startup delay of 30-60 seconds. The status bar shows "Indexing" during this phase.

### Deploy on Save

The `salesforcedx-vscode-core` extension offers a "Push or Deploy on Save" feature controlled by the `salesforcedx-vscode-core.push-or-deploy-on-save.enabled` setting. The behavior differs by org type:

- **Source-tracked orgs** (scratch orgs, source-tracked sandboxes): triggers `sf project deploy start` which uses the source-tracking framework to deploy only changed files.
- **Non-source-tracked orgs** (production, Developer Edition, non-tracked sandboxes): triggers `sf project deploy start --source-dir` on the individual saved file, deploying it immediately regardless of other pending changes.

This distinction is critical because deploying to a non-tracked org will overwrite whatever is on the server with no conflict detection.

### Apex Debugging

Two debugger options exist, each serving different scenarios:

- **Apex Interactive Debugger** requires the "Apex Interactive Debugger" license (included with Performance and Unlimited editions, available as an add-on for others). It sets breakpoints in a live running org and halts execution server-side. A single debug session locks the org — no other debug sessions or Apex executions can proceed.
- **Apex Replay Debugger** requires no special license. It works by replaying a captured debug log locally, simulating variable state and execution flow. It does not halt live execution and is safe for shared orgs.

---

## Common Patterns

### Pattern: Fresh Workspace Setup

**When to use:** Starting a new Salesforce DX project or onboarding a developer to an existing repo.

**How it works:**

1. Install the "Salesforce Extension Pack" from the VS Code marketplace (extension ID: `salesforce.salesforcedx-vscode`).
2. Ensure JDK 21 is installed and `JAVA_HOME` is set, or configure `salesforcedx-vscode-apex.java.home` in `.vscode/settings.json`.
3. Open the folder containing `sfdx-project.json` as the workspace root.
4. Run `SFDX: Authorize an Org` from the Command Palette (or `sf org login web --set-default`).
5. Wait for the Apex Language Server to finish indexing (status bar shows "Indexing complete").

**Why not the alternative:** Opening a parent folder that contains the SFDX project as a subfolder will prevent the Apex Language Server from finding `sfdx-project.json` at root, causing silent feature degradation with no error message.

### Pattern: Replay Debugger for Shared Development Orgs

**When to use:** Debugging Apex logic in a sandbox or scratch org shared by multiple developers, or when the org lacks the Interactive Debugger license.

**How it works:**

1. Set `DEVELOPER_LOG` trace flags on the running user via Setup > Debug Logs, or use `sf apex log get`.
2. Execute the Apex scenario that needs debugging (trigger a page load, run a test, etc.).
3. Retrieve the debug log: Command Palette > `SFDX: Get Apex Debug Logs`.
4. Open the log file, then Command Palette > `SFDX: Launch Apex Replay Debugger with Current File`.
5. Set breakpoints in the source `.cls` files. The replay debugger will stop at those lines and show variable state from the log.

**Why not the alternative:** The Interactive Debugger locks the entire org for the duration of the session. In a shared org, this blocks all other Apex execution (triggers, flows calling Apex, scheduled jobs) until the session ends or times out.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Solo developer on a scratch org | Interactive Debugger | No contention; real-time breakpoints are faster than replaying logs |
| Shared sandbox, no debugger license | Replay Debugger | No license needed; does not lock the org |
| Deploy-on-save for scratch org | Enable push-or-deploy-on-save | Source tracking handles conflict detection automatically |
| Deploy-on-save for production or DE org | Leave disabled; deploy manually | No conflict detection — auto-deploy can silently overwrite server changes |
| Apex LSP not starting | Check JDK path and workspace root | The two most common root causes by a wide margin |
| Large project with slow indexing | Reduce packageDirectories scope | The LSP indexes everything in declared packageDirectories |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner setting up or troubleshooting VS Code for Salesforce development:

1. **Verify prerequisites** — Confirm JDK 21 (or 17/11) is installed (`java -version`), not just a JRE. Confirm the Salesforce Extension Pack is installed and up to date. Check that Salesforce CLI (`sf`) is available on `PATH`.
2. **Open the correct workspace root** — The folder opened in VS Code must contain `sfdx-project.json` at its top level. If working in a monorepo, use VS Code multi-root workspaces or open the SFDX project subfolder directly.
3. **Authorize the target org** — Run `SFDX: Authorize an Org` from the Command Palette. For CI or headless environments, use `sf org login jwt` instead. Set the org as default with `SFDX: Set a Default Org`.
4. **Configure deploy-on-save appropriately** — For source-tracked orgs (scratch orgs, tracked sandboxes), enable `salesforcedx-vscode-core.push-or-deploy-on-save.enabled`. For non-tracked orgs, leave it disabled and deploy manually to avoid silent overwrites.
5. **Validate Apex Language Server** — Open any `.cls` file and verify code completion and error highlighting work. If the status bar shows an error, check `salesforcedx-vscode-apex.java.home` in settings and confirm the workspace root.
6. **Set up debugging** — If the org has the Interactive Debugger license, create a launch configuration of type `Launch Apex Debugger`. Otherwise, configure trace flags and use the Replay Debugger workflow.
7. **Commit workspace settings** — Add `.vscode/settings.json` and `.vscode/launch.json` to version control so team members inherit the same configuration.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] JDK 21 (or 17/11) is installed and the path is configured correctly in VS Code settings or `JAVA_HOME`
- [ ] `sfdx-project.json` is at the root of the opened workspace folder
- [ ] At least one org is authorized and set as the default org for the project
- [ ] Deploy-on-save is enabled only for source-tracked orgs; disabled for non-tracked orgs
- [ ] Apex Language Server shows "Indexing complete" in the status bar and code completion works
- [ ] Debug configuration matches the org type and license availability (Interactive vs Replay)
- [ ] `.vscode/settings.json` and `.vscode/launch.json` are committed to the repo

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **JRE vs JDK** — Installing a Java Runtime Environment (JRE) instead of a full JDK is the most common reason the Apex Language Server fails to start. The extension requires `javac` and related tooling, not just `java`.
2. **Workspace root mismatch** — Opening the Git repo root when `sfdx-project.json` lives one level down produces no error message. The extensions load but the Apex Language Server silently refuses to activate, leaving developers with no code completion and no explanation.
3. **Deploy-on-save on non-tracked orgs overwrites without warning** — Unlike source-tracked orgs where `sf project deploy start` detects conflicts, deploying a single file to a non-tracked org replaces whatever is on the server. If another developer changed the same file via Setup or another tool, their changes are lost.
4. **Interactive Debugger locks the entire org** — A single Interactive Debugger session blocks all other Apex execution in the org (triggers, batch jobs, flows calling Apex). Forgetting to disconnect the debugger can cause production-like failures in shared sandboxes.
5. **Multiple packageDirectories slow indexing** — When `sfdx-project.json` declares many `packageDirectories`, the Apex Language Server indexes all of them. In large monorepos this can take several minutes and consume significant memory.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `.vscode/settings.json` | Workspace settings including JDK path, deploy-on-save toggle, and default org preferences |
| `.vscode/launch.json` | Debug launch configurations for Interactive or Replay Debugger |
| `sfdx-project.json` | Project descriptor that the extension pack requires at the workspace root |

---

## Related Skills

- `sf-cli-and-sfdx-essentials` — For CLI command reference, project creation, and org management commands outside the VS Code GUI
- `scratch-org-management` — For designing scratch org definition files and managing Dev Hub allocations
- `source-tracking-and-conflict-resolution` — For understanding how source tracking works under deploy-on-save
- `salesforce-code-analyzer` — For running static analysis from within VS Code via the Code Analyzer extension
