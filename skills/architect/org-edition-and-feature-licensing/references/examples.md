# Examples — Org Edition and Feature Licensing

## Example 1: Flow Orchestration "Missing" in Enterprise Org — Enablement Issue, Not Licensing

**Scenario:** An architect designs a solution using Flow Orchestration (multi-stage approvals). During build, the developer reports that Flow Orchestration is not available in the Flow Builder action picker. The org is on Enterprise Edition, which includes Flow Orchestration.

**Root cause:** Flow Orchestration is included in Enterprise Edition but must be explicitly enabled. The developer assumed it was on by default.

**Diagnosis steps:**
1. Setup > Company Information confirms Enterprise Edition.
2. Flow Orchestration is listed as available in Enterprise Edition.
3. Setup > Process Automation Settings > Flow Orchestration > Enable toggle was off.

**Fix:** Enable Flow Orchestration in Setup > Process Automation Settings. No license purchase or edition upgrade needed.

**Lesson:** Always check the feature's setup enable toggle before concluding a licensing gap exists.

---

## Example 2: Agentforce Feature Not Available Despite Unlimited Edition

**Scenario:** A customer on Unlimited Edition tries to enable Agentforce agents for their service team. The Agentforce setup screens are accessible but agent deployments show an error about license capacity.

**Root cause:** Agentforce is not included in any base edition — it requires a separate Agentforce add-on license (currently priced per conversation or as a flat rate). Unlimited Edition gives access to the setup UI but does not grant usage capacity without the add-on.

**Diagnosis steps:**
1. Setup > Company Information > Salesforce Edition = Unlimited.
2. Setup > Company Information > Feature Licenses — Agentforce shows 0 of 0 allocated.
3. Confirm with Account Executive that Agentforce add-on was not purchased.

**Resolution:** Purchase the Agentforce add-on. After provisioning, Feature Licenses will show the purchased capacity, and agent deployments will succeed.

---

## Example 3: Apex Triggers Required — Professional Edition Blocker

**Scenario:** A solution design calls for Apex triggers to enforce a complex business rule on Opportunity updates. The customer is on Professional Edition. During implementation planning, the architect discovers Apex triggers are not available.

**Root cause:** Apex triggers require Enterprise Edition or higher. Professional Edition does not support Apex triggers regardless of add-ons — API access can be added as an add-on to Professional, but Apex requires an edition upgrade.

**Diagnosis steps:**
1. Setup > Company Information > Salesforce Edition = Professional.
2. Apex triggers require Enterprise+.
3. No add-on provides Apex capability for Professional orgs.

**Resolution options:**
- **Upgrade to Enterprise Edition** — the only path to Apex triggers.
- **Redesign using declarative automation** — if the business rule can be expressed in Flow, it can run on Professional. Evaluate complexity and maintainability tradeoffs.

**Lesson:** Apex triggers are a hard edition requirement. Confirm customer edition early in solution design to avoid late-stage discovery.
