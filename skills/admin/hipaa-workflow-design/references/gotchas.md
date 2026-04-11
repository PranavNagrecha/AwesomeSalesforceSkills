# Gotchas — HIPAA Workflow Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Standard Field History Tracking Is Not HIPAA-Sufficient

**What happens:** An org uses standard Field History Tracking (the default Salesforce field history feature) for PHI fields, then fails a HIPAA audit because the 18-month retention window does not satisfy the 6-year audit log retention requirement.

**When it occurs:** When implementation teams design audit controls without comparing the platform's default capabilities to HIPAA's specific retention requirements. Standard Field History Tracking appears to satisfy audit requirements until the retention duration is compared against the regulation.

**How to avoid:** Always specify Shield Field Audit Trail (not standard Field History Tracking) for PHI fields in HIPAA implementations. Shield Field Audit Trail supports up to 10 years of retention. Standard Field History Tracking must explicitly NOT be used as the primary audit mechanism for PHI fields.

---

## Gotcha 2: Event Monitoring Logs Expire in 30 Days Without Streaming

**What happens:** Event Monitoring is enabled for HIPAA compliance but logs are never streamed to a SIEM. After 30 days, all access audit logs are permanently deleted. An audit request for login and data access history from 2 years prior finds no data.

**When it occurs:** When Event Monitoring is treated as a one-time configuration task rather than an ongoing operational requirement with a streaming pipeline. Teams often enable Event Monitoring but do not connect it to a SIEM or build the streaming pipeline.

**How to avoid:** The Event Monitoring streaming pipeline to a SIEM must be part of the HIPAA implementation scope, not an afterthought. The retention policy must be at least 6 years. Monitor the streaming pipeline health as an ongoing operational control — a pipeline failure silently loses logs.

---

## Gotcha 3: BAA Coverage Is Product-Specific, Not Org-Wide

**What happens:** A customer signs the Salesforce BAA and assumes all Salesforce products and AppExchange packages installed in the org are covered. PHI is subsequently stored or processed by an uncovered product, creating a compliance gap.

**When it occurs:** Multi-cloud orgs where Health Cloud (covered) is used alongside products like Marketing Cloud connectors (may require separate BAA addendum), specific AppExchange managed packages (most are not BAA-covered), or Chatter features (not covered by default BAA).

**How to avoid:** Review the Salesforce BAA coverage list with the Salesforce account team and legal counsel. For every Salesforce product and AppExchange package that may process or store PHI, explicitly confirm BAA coverage. Document covered products in the compliance record.

---

## Gotcha 4: Consent Objects Do Not Enforce PHI Access Control

**What happens:** Implementation teams configure Health Cloud consent objects (AuthorizationFormConsent) and assume that consent tracking automatically restricts PHI access for patients who have not consented.

**When it occurs:** When requirements conflate "consent tracking" (recording that consent was obtained) with "access control enforcement" (restricting who can see PHI). These are separate architectural concerns in Salesforce.

**How to avoid:** Consent tracking (AuthorizationFormConsent) is a documentation object — it records that consent was obtained but does not technically restrict record access. HIPAA access control must be implemented separately via OWD settings, sharing rules, and permission sets. The enrollment workflow must explicitly check consent status before proceeding.
