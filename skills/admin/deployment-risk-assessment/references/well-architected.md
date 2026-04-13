# Well-Architected Notes — Deployment Risk Assessment

## Relevant Pillars

- **Reliability** — Primary pillar for this skill. The Well-Architected Reliable pillar defines reliable systems as those that can withstand failure and recover gracefully. Deployment risk assessment is a pre-release reliability practice: it identifies what could fail, ensures rollback paths are real rather than hypothetical, and ensures the team can recover within an acceptable time window. Without pre-deployment risk classification, a team discovers its rollback assumptions during a production incident rather than before it.

- **Operational Excellence** — Risk classification, rollback runbooks, and go/no-go criteria are operational process artifacts. The Well-Architected framework explicitly calls for documented change procedures, defined escalation paths, and post-release verification as elements of operational excellence. This skill operationalizes those requirements into concrete pre-deployment artifacts.

- **Security** — Security metadata (PermissionSets, Profiles, SharingRules, ConnectedApps, AuthProviders) consistently receives HIGH risk classification because misconfiguration can silently over-share or under-share access at org-wide scale. The risk assessment process surfaces these components for explicit scrutiny rather than treating them as equivalent to layout changes.

- **Performance** — Indirectly relevant. HIGH-risk deployments that include bulk-affecting automation (Record-Triggered Flows, Apex triggers on high-volume objects) are assessed for governor limit exposure and bulk-execution behavior as part of classification. A deployment that passes functional validation in a low-data sandbox may perform differently at production data volumes.

- **Scalability** — Indirectly relevant. Risk classification considers whether components have been validated against representative data volumes, which is a scalability readiness check embedded in the pre-deployment process.

## Architectural Tradeoffs

**Rollback fidelity vs. deployment speed:** The fastest deployment method (direct org config in Setup) has the worst rollback fidelity — no artifact, no version, no automated undo path. The slowest path to initial setup (unlocked packages with version management) provides the best rollback fidelity. Teams must decide where they sit on this spectrum. The Well-Architected Resilient guidance recommends preferring packaged deployments for HIGH-risk changes precisely because version-based rollback is faster and more reliable than re-deploying manually captured metadata.

**Risk decomposition vs. release velocity:** Decomposing a large release into smaller, lower-risk releases reduces the blast radius of any single failure and makes rollback cheaper. This trades release velocity for reliability. The Well-Architected framework favors smaller, more frequent releases over large infrequent ones for this reason. Risk classification often surfaces bundled releases that should be split.

**Pre-deployment preparation time vs. release window length:** Investing time in pre-deployment risk classification, rollback runbook authoring, and destructive change preparation reduces the expected duration and complexity of rollback execution if it is needed. Teams that skip this preparation get faster deployment window starts but longer, more chaotic recovery events.

## Anti-Patterns

1. **Treating risk assessment as optional for "simple" releases** — The decision that a release is simple enough to skip risk assessment is itself a risk classification decision made without a framework. Practitioners consistently underestimate risk for UI-adjacent changes that have hidden automation dependencies. A required lightweight classification process (even a five-minute review against the HIGH / MEDIUM / LOW criteria) catches the hidden dependencies that intuition misses.

2. **Defining rollback trigger conditions under pressure** — Deciding whether the current production symptoms justify a rollback during an incident introduces human judgment bias, communication overhead, and time delay at the worst possible moment. Pre-agreed observable trigger conditions (error rate, exception type, latency threshold) allow the rollback call to be made by comparing observed data against a pre-written standard, not by negotiating under pressure.

3. **Relying on sandbox state as a rollback source** — Some teams plan to retrieve from a Full sandbox if rollback is needed, assuming the sandbox reflects production. Sandbox state diverges from production every time a production-only change is made outside the sandbox track. A rollback plan that depends on sandbox state is unreliable by design. The rollback artifact must be a production retrieve taken immediately before the deployment window.

## Official Sources Used

- Salesforce Well-Architected: Reliable Pillar — https://architect.salesforce.com/well-architected/trusted/reliable
- Salesforce Well-Architected: Resilient (Adaptable Pillar) — https://architect.salesforce.com/well-architected/adaptable/resilient
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
