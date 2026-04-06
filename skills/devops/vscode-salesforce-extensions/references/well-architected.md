# Well-Architected Notes — VS Code Salesforce Extensions

## Relevant Pillars

- **Operational Excellence** — The primary pillar. VS Code extension configuration directly impacts developer productivity, deployment reliability, and team onboarding speed. Standardized workspace settings (`.vscode/settings.json`, `.vscode/launch.json`) committed to source control ensure consistent tooling across the team and reduce "works on my machine" issues.
- **Reliability** — Deploy-on-save misconfiguration (enabling it for non-tracked orgs) can silently overwrite server-side changes, causing data loss and regressions. Correct configuration prevents these reliability failures. The Interactive Debugger's org-locking behavior also creates reliability risks in shared environments.
- **Security** — Org authorization tokens are stored locally by the Salesforce CLI and should not be committed to version control. `.sfdx/` and `.sf/` directories must be in `.gitignore`. JDK selection should use LTS versions with current security patches.

## Architectural Tradeoffs

1. **Deploy-on-save convenience vs safety.** Enabling deploy-on-save for source-tracked orgs dramatically improves development speed. Enabling it for non-tracked orgs trades safety for speed — there is no conflict detection, so concurrent changes by other developers or admins are silently overwritten. The Well-Architected Framework favors reliability; disable deploy-on-save for non-tracked orgs.

2. **Interactive Debugger depth vs org availability.** The Interactive Debugger provides superior debugging (real-time breakpoints, step-through, variable inspection on live data). However, it locks the org for all other Apex execution. For shared environments, the Replay Debugger trades real-time interactivity for zero-impact debugging, aligning with the reliability pillar.

3. **Centralized workspace settings vs developer autonomy.** Committing `.vscode/settings.json` ensures every developer has the correct JDK path, deploy-on-save setting, and debug configuration. However, it can conflict with individual developer preferences (theme, font size). Use workspace settings only for Salesforce-specific keys and leave personal preferences to user-level settings.

## Anti-Patterns

1. **Not committing workspace settings** — Each developer configures their own environment from scratch, leading to inconsistent JDK versions, deploy-on-save enabled where it should not be, and debug configurations that reference local paths. This violates Operational Excellence by making onboarding slow and error-prone.

2. **Using deploy-on-save on production or non-tracked orgs** — Treats every file save as a deployment, bypassing conflict detection. Changes made through Setup or by other team members are overwritten. This violates Reliability and creates a class of silent regressions that are difficult to diagnose.

3. **Leaving Interactive Debugger sessions connected** — Developers start a debug session, investigate an issue, then switch to another task without disconnecting. The org remains locked, blocking all other Apex execution for up to 30 minutes. This violates Reliability in shared environments.

## Official Sources Used

- Salesforce Extensions for VS Code documentation — https://developer.salesforce.com/tools/vscode
- Apex Language Server — https://developer.salesforce.com/tools/vscode/en/apex/language-server
- Deploy on Save — https://developer.salesforce.com/tools/vscode/en/deploy-changes/deploy-on-save
- Apex Interactive Debugger — https://developer.salesforce.com/tools/vscode/en/apex/interactive-debugger
- Apex Replay Debugger — https://developer.salesforce.com/tools/vscode/en/apex/replay-debugger
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
