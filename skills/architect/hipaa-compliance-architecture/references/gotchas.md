# Gotchas — HIPAA Compliance Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Shield Platform Encryption Alone Does NOT Satisfy HIPAA Technical Safeguards

**What happens:** Teams enable Shield Platform Encryption and declare HIPAA technical safeguard compliance. In a HIPAA audit or security assessment, the covered entity receives findings for: missing unique user ID enforcement, no automatic session logoff configuration, absent transmission security documentation, and no emergency access procedures. Shield SPE satisfies only the encryption at rest requirement under 45 CFR §164.312(a)(2)(iv) and §164.312(e)(2)(ii) — it does not address the full technical safeguard set.

**When it occurs:** Any implementation where the architecture review stops at "we have Shield" without producing a complete HIPAA Security Rule safeguard-to-control mapping. Common in projects where the Salesforce team and the covered entity's compliance team do not overlap.

**How to avoid:** Produce a HIPAA Security Rule safeguard matrix as a required output artifact before go-live. Map every required safeguard — administrative, physical, and technical — to either a Salesforce platform control or an organizational policy. Shield controls populate part of the technical safeguard column. The remaining gaps become remediation items with owners assigned.

---

## Gotcha 2: Standard Chatter Is NOT Covered Under the Salesforce BAA

**What happens:** Clinical teams request Chatter for care coordination communication. Developers enable Chatter. PHI (patient names, diagnoses, care plan details) appears in Chatter posts and comments. Standard Chatter is not included in the Salesforce HIPAA BAA as of current published guidance. The PHI posted to Chatter is stored in a service outside the covered BAA scope — creating a potential reportable breach.

**When it occurs:** When clinical workflows are designed without checking BAA scope, or when a BAA is signed without the implementation team reviewing the covered product list. Chatter is enabled by default in most Salesforce editions, making it easy to overlook.

**How to avoid:** As part of BAA scope validation (the first step of the recommended workflow), explicitly verify whether Chatter is listed in the executed BAA. If it is not covered, disable Chatter or enforce a validation rule or Flow that prevents PHI from being posted to feed items. Communicate to clinical users which communication channels are HIPAA-covered. Review the current Salesforce HIPAA help article because covered product lists are updated with each release.

---

## Gotcha 3: Shield Is a Paid Add-On Not Included in Any Salesforce Edition

**What happens:** An org is architected assuming Shield Platform Encryption, Field Audit Trail, and Event Monitoring are available. At the time of license negotiation, Shield was not included in the contract quote. The go-live architecture is then missing its primary encryption and audit controls, requiring a contract amendment that delays the launch or forces a scope reduction.

**When it occurs:** When architecture is designed before licensing is confirmed, or when stakeholders assume Shield is part of the standard Health Cloud or Enterprise Edition license. Shield must be quoted and purchased separately as a paid add-on regardless of the org edition.

**How to avoid:** Confirm Shield licensing in writing before the architecture design phase begins. Verify in `Setup > Company Information > Permission Set Licenses` that Shield Platform Encryption User, Shield Event Monitoring User, and Shield Field Audit Trail User licenses are present in the org. If Shield is not licensed, document the encryption gap in the risk register and evaluate alternative controls (Classic Encryption, which has significant limitations, or re-scoping PHI out of Salesforce).

---

## Gotcha 4: AppExchange Packages Require Their Own BAA Addenda

**What happens:** An implementation uses an AppExchange package (e-signature, document generation, scheduling, telehealth integration). PHI is passed to the package's managed objects or sent to the ISV's external service. The ISV's managed package is not covered by the Salesforce BAA — the Salesforce BAA covers Salesforce Inc. services only. The ISV is a separate Business Associate and requires its own signed BAA addendum. Without one, passing PHI to the package constitutes sharing PHI with an uncovered business associate — a HIPAA violation.

**When it occurs:** Any AppExchange package that stores PHI in its managed objects or transmits PHI to an external service. Even packages running entirely in the Salesforce platform (no external callout) store data in objects owned by the ISV namespace, which is outside Salesforce's contractual scope.

**How to avoid:** During the BAA scope validation step, flag every AppExchange package that will interact with PHI. Contact each ISV and request a signed BAA addendum before activating the package with PHI. Some large ISVs (DocuSign, etc.) have published HIPAA BAA processes; smaller ISVs may not support a BAA. If an ISV cannot or will not provide a BAA, the package must not process PHI — re-architect the integration to avoid PHI exposure or select an alternative vendor.

---

## Gotcha 5: Standard Field History Tracking Is Insufficient for HIPAA Audit Requirements

**What happens:** An org tracks PHI field changes using standard Salesforce Field History Tracking (available in all editions). Standard Field History Tracking retains data for 18 months. HIPAA Security Rule requires covered entities to retain documentation of security activities, and state medical records laws often require longer retention. An audit request for PHI access history from 2 years ago returns no data because standard tracking has already purged it.

**When it occurs:** When Shield Field Audit Trail is not licensed or not configured, and the implementation relies on standard Field History Tracking for audit compliance. Also occurs when FAT is licensed but retention is not configured — the default FAT retention may not be set to the required 10 years.

**How to avoid:** License and enable Shield Field Audit Trail. In `Setup > Field Audit Trail`, configure the retention policy to 10 years for all PHI fields. Verify FAT is configured via the FieldHistoryArchive object and that PHI fields appear in the archive retention policy. Do not use standard Field History Tracking as the primary audit control for PHI in a HIPAA-covered org.
