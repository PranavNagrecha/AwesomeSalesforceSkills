# Gotchas — VS Code Salesforce Extensions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: JDK Required, Not JRE

**What happens:** The Apex Language Server fails to start. The Output panel shows a Java-related error, but VS Code does not display a prominent notification. Code completion, inline errors, and go-to-definition silently stop working.

**When it occurs:** When the developer has a Java Runtime Environment (JRE) installed but not a full Java Development Kit (JDK). This is common on machines where Java was installed solely to run applications. The `salesforcedx-vscode-apex.java.home` setting (or `JAVA_HOME`) must point to a JDK that includes `javac`.

**How to avoid:** Install JDK 21 (recommended) or JDK 17/11. Verify by running `javac -version` in the terminal. Set `salesforcedx-vscode-apex.java.home` explicitly in `.vscode/settings.json` rather than relying on system-level `JAVA_HOME`, which may be overridden by other tools.

---

## Gotcha 2: Deploy-on-Save Behaves Differently by Org Type

**What happens:** On a non-source-tracked org (production, Developer Edition, or a sandbox without source tracking enabled), saving a file triggers an immediate deploy of that single file. This silently overwrites whatever version exists on the server, with no conflict detection and no prompt.

**When it occurs:** When a developer enables the `push-or-deploy-on-save` setting while connected to a non-tracked org. They expect the same safe, diff-based behavior they see with scratch orgs, but the extension falls back to a direct `sf project deploy start --source-dir` call.

**How to avoid:** Only enable deploy-on-save for source-tracked orgs (scratch orgs and sandboxes with source tracking). For non-tracked orgs, deploy manually using the Command Palette (`SFDX: Deploy This Source to Org`) or the right-click context menu, and always retrieve before deploying to check for conflicts.

---

## Gotcha 3: Interactive Debugger Locks the Entire Org

**What happens:** When an Apex Interactive Debugger session is active, the org enters a single-user debug mode. All other Apex execution — triggers, batch jobs, scheduled Apex, Flows that invoke Apex — is blocked. Other users experience timeouts or failures.

**When it occurs:** Any time a developer starts an Interactive Debugger session and forgets to disconnect, or leaves it running during lunch. The lock persists until the session is explicitly ended or the 30-minute timeout elapses.

**How to avoid:** Use the Replay Debugger for shared orgs. Reserve the Interactive Debugger for personal scratch orgs where no other execution occurs. If Interactive Debugger must be used on a shared org, coordinate with the team and set a reminder to disconnect.

---

## Gotcha 4: sfdx-project.json Must Be at Workspace Root

**What happens:** All Salesforce extensions appear to load (icons show in the status bar, commands appear in the Command Palette), but the Apex Language Server never activates. No error message is displayed. Code completion and inline validation are absent.

**When it occurs:** When VS Code opens a parent directory of the SFDX project (e.g., the Git repo root) and `sfdx-project.json` is in a subdirectory. The extensions scan only the top-level workspace folder for `sfdx-project.json`.

**How to avoid:** Always open the folder containing `sfdx-project.json` directly. For monorepos, use a `.code-workspace` file with multi-root workspace configuration so each project root is declared separately.

---

## Gotcha 5: Extension Pack vs Individual Extensions Version Mismatch

**What happens:** After updating some extensions individually, the Apex Language Server or deploy commands start throwing unexpected errors. Features regress or disappear.

**When it occurs:** When a developer updates individual extensions within the pack (e.g., `salesforcedx-vscode-apex`) without updating the full Extension Pack (`salesforce.salesforcedx-vscode`). The extensions within the pack are designed to be version-aligned; mixing versions causes subtle incompatibilities.

**How to avoid:** Always update via the Extension Pack rather than updating individual extensions. Disable automatic extension updates for the individual pack components if they tend to update independently. Pin the Extension Pack version in team documentation.
