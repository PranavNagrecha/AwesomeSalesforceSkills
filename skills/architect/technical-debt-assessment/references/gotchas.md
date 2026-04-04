# Gotchas — Technical Debt Assessment

Non-obvious Salesforce platform behaviors that affect how technical debt is identified, measured, and reported.

---

## Inactive Flow Versions Are Not Harmless

**What happens:** Inactive Flow versions continue to count against the org's 2,000 Flow version limit per org, even when they are deactivated and no longer executing. An org with a long history of iterative Flow development can approach this limit silently — each save of a Flow creates a new version, and older versions are rarely deleted.

**When it occurs:** Any org where Flows have been edited many times without periodic version cleanup. Orgs that used Flows heavily before version management was understood.

**Why it matters for debt assessment:** An org with 1,900+ Flow versions is at operational risk. The moment the 2,000 limit is hit, Salesforce will not allow new Flow versions to be activated — which blocks all Flow-based deployments and sandbox promotions until versions are purged.

**How to check:** Setup → Flows → View All Flow Versions → sort by count. The aggregate can also be retrieved via Tooling API: `SELECT count() FROM FlowVersion`. The limit is hard at 2,000.

**Remediation:** Delete inactive Flow versions for obsolete or archived Flows. Keep the most recent inactive version of any Flow as a rollback reference, but delete older versions. Salesforce provides a "Delete Old Inactive Versions" option per Flow.

---

## Process Builder and Workflow Rules Execute Even When They "Look Inactive"

**What happens:** A Process Builder flow or Workflow Rule with status `Active` continues to execute regardless of whether the team considers it "legacy" or "replaced." Deactivating a Process Builder flow or Workflow Rule requires an explicit action in Setup — it does not happen automatically when a replacement Flow is created.

**When it occurs:** Teams build a new Record-Triggered Flow to replace an old Process Builder flow but forget (or do not know) to deactivate the Process Builder flow. Both execute. The Process Builder may have stale logic, may send duplicate emails, or may overwrite field values set by the new Flow.

**Why it matters for debt assessment:** Process Builder and Workflow Rules execute in the order-of-execution after after-save Record-Triggered Flows. A "replaced" Process Builder flow running after the new Flow can overwrite the new Flow's field writes, producing behavior that appears to work in testing (low data volume, predictable order) but fails in production under concurrent saves.

**How to check:** Setup → Process Builder → filter by Active status. Setup → Workflow Rules → filter by Active. Do not assume that because a team "moved to Flow" that legacy automation was actually deactivated. Always verify status directly in Setup.

**Common trap:** Process Builder flows that are `Draft` status (never activated) but were partially built also appear in Setup and create confusion. Draft Process Builders do not execute — but they occupy the namespace and create maintenance noise. Include them in the inventory as Low-severity hygiene findings.

---

## Dead Apex Classes Still Consume Metadata Limits and Can Block Deployments

**What happens:** Apex classes that are no longer called by any other code or metadata still exist in the org's Apex codebase. They contribute to:
- The org's overall Apex class count (there is no hard per-org limit, but large counts slow Salesforce internal processing).
- **Test coverage calculations.** If a dead class has zero test methods covering it, it lowers the org's overall coverage percentage. If that class has many lines of code, it can drag the org below the 75% minimum required for all deployments.
- **Deployment validation.** When deploying other changes, all Apex in the org is compiled, and all test classes run (in a full deploy). Dead classes with broken references (deleted fields, renamed classes, removed dependencies) cause the deployment to fail even though the deploying team didn't touch those classes.

**When it occurs:** Classes accumulate over years as features are retired, integrations are replaced, or package dependencies change. The class is removed from use but never deleted from the org.

**How to check:** Pull the full coverage report. Any class with 0 covered lines and 0 uncovered lines has no executable code (or no test touching it). Cross-reference against inbound references from other classes and Flow invocable actions. If there are no references and no coverage, it is a deletion candidate.

**Important caveat:** Before deleting a class, verify it is not called dynamically (via `Type.forName()`, Apex scheduled job class names, or invocable method wiring that is stored as a string rather than a direct reference). Check the Scheduled Jobs list and any CMDT or Custom Settings that might store class names as configuration values.

---

## Managed Package Components Create Debt You Cannot Modify — Report Separately

**What happens:** Managed packages install Apex classes, Flows, triggers, and other components into the org that the org's team cannot edit or delete (they are IP-protected by the package publisher). These components can be sources of debt (deprecated package Flows, overly broad package permission sets, legacy package Apex with low coverage) but cannot be remediated by the org team.

**When it occurs:** Any org with AppExchange packages installed — this includes common packages like DocuSign, Conga, DemandTools, Copado, and many others. Each package occupies namespace-prefixed metadata that appears in coverage reports, Setup views, and metadata API retrieves.

**Why it matters for debt assessment:** Counting managed package components as "own debt" misleads the remediation backlog. A coverage report that shows 30 Apex classes at 0% may have 25 of them in managed package namespaces — uncountable and unreachable.

**How to handle:**
- Filter all findings by namespace. Findings in a managed package namespace (any class prefixed with `pkg__` or a non-blank namespace) should be documented separately as **Vendor Debt — Informational Only**.
- Do not include managed package components in the severity-rated remediation backlog. They are actionable only by contacting the vendor or upgrading/removing the package.
- A managed package that is installed but not actively in use IS a finding: the package's Apex counts against overall coverage, its permission sets may grant excess access, and its triggers fire on objects even if the package's features are not being used. Document as a separate "Unused Managed Package" finding and recommend review with the business on whether the package should be uninstalled.
