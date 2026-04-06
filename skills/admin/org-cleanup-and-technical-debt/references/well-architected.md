# Well-Architected Notes — Org Cleanup And Technical Debt

## Relevant Pillars

- **Operational Excellence** — Org cleanup is a core operational excellence practice. Accumulated unused metadata increases cognitive load for admins and developers, slows metadata searches, clutters Setup navigation, and makes impact analysis harder for every future change. Regular cleanup directly improves the team's velocity and reduces the risk surface for deployments.
- **Reliability** — Unused automation that still fires (legacy Workflow Rules, orphaned Process Builder flows) creates unpredictable side effects — duplicate emails, double field updates, and governor limit contention. Removing dead automation improves system reliability by reducing unintended execution paths.
- **Security** — Unused permission sets, stale sharing rules, and orphaned connected apps represent access surface area that serves no business purpose. Cleanup reduces the attack surface and simplifies access audits.

## Architectural Tradeoffs

1. **Immediate deletion vs. deactivate-then-delete:** Immediate deletion frees resources faster but removes the rollback path. Deactivating first and deleting after an observation period is safer but requires discipline to follow through on the second step. For automation (Flows, Workflow Rules), always prefer deactivate-then-delete. For fields with no data and no references, immediate deletion is acceptable.

2. **Manual Setup deletion vs. destructive deploy:** Manual deletion through Setup is simpler for small counts (fewer than 10 items) but does not scale, is not repeatable, and leaves no audit trail in source control. Destructive deploys via Metadata API are repeatable, version-controlled, and testable in sandbox — but require CLI tooling and developer-adjacent skills. For any cleanup affecting more than 10 components, use destructive deploys.

3. **Aggressive cleanup vs. conservative cleanup:** Aggressive cleanup (delete everything flagged by Optimizer) achieves maximum hygiene but risks removing components that have undocumented runtime dependencies. Conservative cleanup (only delete items with zero data AND zero metadata references AND stakeholder confirmation) is slower but safer. Default to conservative for production orgs with no recent metadata backup.

## Anti-Patterns

1. **"Delete it and see what breaks"** — Performing cleanup in production without sandbox testing. Even if Setup allows the deletion, runtime-only references (Flow formulas, dynamic Apex, report formulas) can fail silently for days before a user reports the issue. Always test in sandbox first.

2. **One-time cleanup with no ongoing hygiene** — Performing a large cleanup sprint but establishing no recurring process. Without quarterly Optimizer runs and a metadata hygiene policy, the org returns to the same cluttered state within 6-12 months. Cleanup must be paired with a sustainability plan.

3. **Deleting managed package components** — Attempting to delete fields, objects, or automation that belong to a managed package. These components cannot be removed by the subscriber admin — only the package publisher can deprecate or remove them via a package upgrade. The only subscriber option is to uninstall the entire package, which deletes all package data.

## Official Sources Used

- Salesforce Optimizer (Setup > Optimizer) — org health scanning and unused metadata identification
- Metadata API Developer Guide — destructive deploy mechanics (destructiveChanges.xml, package.xml requirements)
- Salesforce Well-Architected Overview — operational excellence and reliability framing for metadata hygiene
- Salesforce Help: Manage Deleted Custom Fields — field recycle queue behavior and permanent erasure
- Salesforce Admins Blog: Tech Debt — admin-focused technical debt awareness and cleanup guidance
