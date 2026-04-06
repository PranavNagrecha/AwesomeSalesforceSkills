# Examples — VS Code Salesforce Extensions

## Example 1: Setting Up a New Developer Workstation

**Context:** A developer joins a team working on a Salesforce DX project stored in Git. They have VS Code installed but have never done Salesforce development.

**Problem:** Without proper setup order, the Apex Language Server fails silently and the developer gets no code completion, no inline errors, and no go-to-definition — but no error message either.

**Solution:**

```bash
# 1. Install JDK 21 (macOS example with Homebrew)
brew install openjdk@21
export JAVA_HOME=$(/usr/libexec/java_home -v 21)

# 2. Install Salesforce CLI
npm install -g @salesforce/cli

# 3. Clone the repo and open the SFDX project root (not the Git root if different)
git clone https://github.com/acme/sf-project.git
cd sf-project
code .

# 4. In VS Code, Command Palette > SFDX: Authorize an Org
#    Browser opens, log in, grant access

# 5. Verify: open any .cls file — status bar should show "Indexing" then "Indexing complete"
```

**.vscode/settings.json for the team:**

```json
{
  "salesforcedx-vscode-apex.java.home": "/usr/local/opt/openjdk@21",
  "salesforcedx-vscode-core.push-or-deploy-on-save.enabled": true,
  "editor.formatOnSave": true
}
```

**Why it works:** By setting `java.home` explicitly in workspace settings (committed to Git), every team member gets the same JDK path without relying on individual `JAVA_HOME` environment variables. The deploy-on-save setting is safe here because the team uses scratch orgs (source-tracked).

---

## Example 2: Debugging a Complex Trigger with Replay Debugger

**Context:** An `AccountTrigger` is silently failing to update a related `Opportunity` field. The sandbox is shared by five developers, and the org does not have the Interactive Debugger license.

**Problem:** Without a debugger, the developer resorts to `System.debug()` statements scattered through the code, redeploying after each change, then scanning raw log text. This is slow and error-prone.

**Solution:**

```bash
# 1. Set trace flags on the running user (via Setup > Debug Logs or CLI)
sf apex log tail --color

# 2. Trigger the scenario: update an Account record

# 3. Download the log
# Command Palette > SFDX: Get Apex Debug Logs > select the relevant log

# 4. Open the downloaded .log file in the editor

# 5. Command Palette > SFDX: Launch Apex Replay Debugger with Current File
```

Then in VS Code:
- Set breakpoints in `AccountTrigger.trigger` and `AccountTriggerHandler.cls`
- The Replay Debugger steps through execution showing variable values at each line
- Identify that `Trigger.newMap` contains the expected records but a filter condition on line 42 incorrectly excludes them

**Why it works:** The Replay Debugger reconstructs execution state from the debug log without connecting to the live org. No license is required, no org lock occurs, and other developers continue working uninterrupted.

---

## Anti-Pattern: Opening the Wrong Workspace Root

**What practitioners do:** They open the Git repository root in VS Code when `sfdx-project.json` is nested inside a subdirectory like `salesforce/` or `force-app-project/`.

**What goes wrong:** The Salesforce extensions load (status bar shows "Salesforce Extensions" icons), but the Apex Language Server never activates because it looks for `sfdx-project.json` only at the top-level workspace folder. There is no error notification. Code completion simply does not appear. Developers assume the extensions are broken and waste time reinstalling.

**Correct approach:** Always open the folder that directly contains `sfdx-project.json`. In monorepo setups, use VS Code multi-root workspaces:

```json
// workspace.code-workspace
{
  "folders": [
    { "path": "salesforce" },
    { "path": "web-app" }
  ]
}
```

This ensures each root has its own `sfdx-project.json` and the Apex Language Server activates correctly for the Salesforce folder.
