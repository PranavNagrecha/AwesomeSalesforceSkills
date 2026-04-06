# VS Code Salesforce Extensions — Work Template

Use this template when setting up or troubleshooting a Salesforce development environment in VS Code.

## Scope

**Skill:** `vscode-salesforce-extensions`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **JDK version:** (output of `java -version` and `javac -version`)
- **VS Code version:** (output of `code --version`)
- **Extension Pack version:** (from Extensions panel > Salesforce Extension Pack)
- **Salesforce CLI version:** (output of `sf version`)
- **Workspace root contains sfdx-project.json:** Yes / No
- **Org type:** Scratch Org / Source-Tracked Sandbox / Non-Tracked Sandbox / Production / Developer Edition
- **Org authorized:** Yes / No (output of `sf org list`)
- **Interactive Debugger license available:** Yes / No / Unknown

## Approach

Which pattern from SKILL.md applies and why:

- [ ] Fresh Workspace Setup — new developer or new project
- [ ] Replay Debugger — debugging in shared or unlicensed org
- [ ] Deploy-on-save configuration — adjusting deployment behavior
- [ ] Apex Language Server troubleshooting — LSP not starting or not indexing

## .vscode/settings.json

```json
{
  "salesforcedx-vscode-apex.java.home": "TODO: /path/to/jdk-21",
  "salesforcedx-vscode-core.push-or-deploy-on-save.enabled": false
}
```

> Set `push-or-deploy-on-save.enabled` to `true` ONLY for source-tracked orgs.

## .vscode/launch.json (if debugging)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch Apex Debugger",
      "type": "apex",
      "request": "launch",
      "saleforceProject": "${workspaceRoot}"
    }
  ]
}
```

> Use type `"apex"` for Interactive Debugger. For Replay Debugger, use the Command Palette workflow instead of a launch configuration.

## Checklist

- [ ] JDK 21/17/11 installed and `javac -version` confirms it is a JDK (not JRE)
- [ ] `sfdx-project.json` is at the root of the opened workspace folder
- [ ] Org is authorized and set as default (`sf org list` shows it)
- [ ] Deploy-on-save is enabled only for source-tracked orgs
- [ ] Apex Language Server shows "Indexing complete" in the status bar
- [ ] Debug configuration matches org type and license availability
- [ ] `.vscode/settings.json` and `.vscode/launch.json` are committed to version control
- [ ] `.sfdx/` and `.sf/` directories are in `.gitignore`

## Notes

Record any deviations from the standard pattern and why:

-
