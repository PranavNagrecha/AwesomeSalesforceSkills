# Well-Architected Notes — OmniScript Versioning

## Relevant Pillars

- **Operational Excellence** — Version management is an operational discipline. Pre-activation DataPack backups, controlled activation windows, and documented rollback procedures are the operational controls that prevent production incidents from becoming extended outages.
- **Reliability** — The single-active-version constraint means any activation immediately affects all users. A structured versioning process (test in sandbox first, backup before activation, immediate smoke test after) directly reduces mean time to recovery when a defective version is activated.

## Architectural Tradeoffs

**Activate immediately vs export DataPack first:** Activating without a backup is fast but leaves no rollback artifact if the prior version is later needed. Exporting a DataPack adds 2–5 minutes to the process but provides a guaranteed rollback path. For production orgs with active users, always export first.

**CI/CD activate flag control:** Automated DataPack deployment pipelines can activate immediately (`activate: true`) or require a manual activation step. Fully automated activation is faster but removes the human review gate. Teams with frequent OmniScript changes should use manual activation gates in production while allowing automated activation in sandboxes.

## Anti-Patterns

1. **Editing the active version in-place** — editing a live OmniScript version directly changes the definition immediately without creating a versioned checkpoint. There is no rollback point if the edit introduces a defect. Always create a new version, test it, then activate.
2. **No DataPack backup before version changes in production** — if the prior version is deleted (accidentally or during cleanup), and the new version is defective, recovery requires manual reconstruction or a Support ticket. The DataPack export is a 2-minute insurance policy.
3. **Relying on sandbox testing without matching production configuration** — OmniScript behavior depends on connected Remote Actions, Integration Procedures, and LWC components. A sandbox that does not have the same version of those dependencies will produce different results from production. Always test in a Full sandbox that mirrors production before activating.

## Official Sources Used

- OmniStudio Developer Guide (Version Management) — https://help.salesforce.com/s/articleView?id=sf.os_omniscript_versioning.htm&type=5
- OmniStudio Activate and Launch OmniScripts — https://help.salesforce.com/s/articleView?id=sf.os_activate_omniscript.htm&type=5
- OmniStudio DataPack Reference — https://help.salesforce.com/s/articleView?id=sf.os_datapacks.htm&type=5
