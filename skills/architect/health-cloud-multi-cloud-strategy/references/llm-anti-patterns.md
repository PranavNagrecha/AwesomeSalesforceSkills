# LLM Anti-Patterns — Health Cloud Multi-Cloud Strategy

Common mistakes AI coding assistants make when generating or advising on Health Cloud Multi-Cloud Strategy.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Experience Cloud as Included in the Health Cloud License

**What the LLM generates:** "Since you have Health Cloud, you can create an Experience Cloud site for your patient portal — the license is included." Or: architecture diagrams that show Experience Cloud as a component of the Health Cloud bundle without flagging it as a separate add-on.

**Why it happens:** LLMs conflate the fact that Health Cloud uses Experience Cloud as the portal delivery mechanism with the licensing reality. Because Health Cloud and Experience Cloud are deeply integrated technically, training data often describes them together without clarifying that the add-on SKU is required for production use.

**Correct pattern:**

```
Experience Cloud for Health Cloud is a SEPARATE add-on SKU.
It is not included in the base Health Cloud license.
Each external portal user also requires the "Health Cloud for Experience Cloud"
permission set license assigned explicitly.
Architecture documents must list this as a separate purchase item.
```

**Detection hint:** Search output for phrases like "included in Health Cloud," "comes with Health Cloud," or "no additional license needed for the portal." Any such claim about Experience Cloud in a Health Cloud context is almost certainly wrong.

---

## Anti-Pattern 2: Recommending a Separate Service Cloud License Purchase for Internal Care Coordinators

**What the LLM generates:** "Your care coordinators will need both a Health Cloud license AND a Service Cloud license to use Cases and Omni-Channel for care coordination." Or: procurement guidance that lists Service Cloud as a separate line item for internal users alongside Health Cloud.

**Why it happens:** LLMs are trained on general Salesforce licensing content that describes Service Cloud and Health Cloud as distinct products. Without specific Health Cloud bundling knowledge, the model defaults to listing them separately. The bundling is a Health Cloud-specific nuance not present in general Salesforce licensing documentation.

**Correct pattern:**

```
Health Cloud licenses implicitly include Service Cloud capabilities
at the same edition level (Enterprise or Unlimited).
Internal care coordinators, nurses, and case managers access Cases,
Omni-Channel, Entitlements, and all standard Service Cloud features
under their Health Cloud license.
Do NOT add a separate Service Cloud license line for internal care team users.
```

**Detection hint:** Look for "Service Cloud" appearing as a separate license recommendation alongside "Health Cloud" for internal (non-portal) users. This is almost always a bundling error.

---

## Anti-Pattern 3: Assuming One HIPAA BAA Covers All Connected Salesforce Products

**What the LLM generates:** "You already have a HIPAA BAA in place for your Salesforce org, so you can connect Marketing Cloud and send PHI for appointment reminders." Or: data flow diagrams that show PHI flowing from Health Cloud to Marketing Cloud without flagging the separate BAA requirement.

**Why it happens:** LLMs treat "Salesforce" as a single entity. The HIPAA BAA for Salesforce (Health Cloud) is conceptually understood, but the separate-product boundary for Marketing Cloud is not consistently represented in training data. Marketing Cloud's distinct infrastructure and BAA requirements are a compliance nuance that requires Health Cloud-specific expertise.

**Correct pattern:**

```
A HIPAA BAA for Health Cloud (the CRM platform) does NOT extend to Marketing Cloud.
Marketing Cloud is a separate product with its own data processing infrastructure.
A dedicated Marketing Cloud HIPAA BAA must be executed with Salesforce
before any PHI (patient demographics, care program enrollment, appointment data)
flows from Health Cloud into Marketing Cloud environments.
Until that BAA is in place, only de-identified or non-PHI data may be synced.
```

**Detection hint:** Look for any advice that sends PHI from Health Cloud to Marketing Cloud without explicitly flagging the Marketing Cloud HIPAA BAA as a prerequisite. Also flag output that refers to "the Salesforce BAA" as a singular document covering all products.

---

## Anti-Pattern 4: Incomplete OmniStudio PSL Assignment — Listing Only Two of Three Required PSLs

**What the LLM generates:** "To use OmniStudio in Health Cloud, assign the Health Cloud PSL and the OmniStudio User PSL to your care coordinators." The Health Cloud Platform PSL is omitted.

**Why it happens:** The OmniStudio User PSL is the most visible PSL in OmniStudio-specific documentation. The Health Cloud Platform PSL is a secondary license that grants CRUD access to Health Cloud's extended data model objects — it is documented in Health Cloud administration guides, not in OmniStudio documentation. LLMs that retrieve context from OmniStudio docs alone will miss the third PSL.

**Correct pattern:**

```
OmniStudio users in a Health Cloud org require ALL THREE of the following PSLs:
1. Health Cloud PSL               — base Health Cloud object visibility
2. Health Cloud Platform PSL      — CRUD rights on Health Cloud data model objects
                                    (EpisodeOfCare, CarePlan, ClinicalEncounter, etc.)
3. OmniStudio User PSL            — right to execute OmniScripts and FlexCards

Assigning only 1 and 3 (without Health Cloud Platform) causes DataRaptor
steps that read/write Health Cloud objects to return empty results silently
rather than throwing a permission error.
```

**Detection hint:** Any PSL assignment advice for OmniStudio in Health Cloud that lists fewer than three PSLs is incomplete. Flag output that only mentions "Health Cloud" and "OmniStudio User" without "Health Cloud Platform."

---

## Anti-Pattern 5: Recommending a Separate "Portal Org" for Patient Data Isolation

**What the LLM generates:** "To keep patient data isolated from your internal operations, create a separate Salesforce org for the patient portal and integrate it with your Health Cloud org via REST APIs." Or: architecture diagrams showing a dedicated portal org with bidirectional sync to the primary Health Cloud org.

**Why it happens:** LLMs trained on general enterprise architecture patterns apply a microservices or multi-tenancy separation instinct to Salesforce. The "separate system for external users" pattern is common in non-Salesforce architectures. LLMs may also confuse this pattern with Salesforce's own hub-and-spoke architecture documentation, which describes multi-org patterns for large multi-entity health systems — not for standard patient portal use cases.

**Correct pattern:**

```
Patient portals in Health Cloud should be built as Experience Cloud sites
within the SAME Salesforce org as the internal Health Cloud implementation.
Experience Cloud for Health Cloud (the add-on SKU) provides the portal
delivery mechanism while keeping all data in a single org.
Data isolation between internal users and portal users is achieved via:
- Organization-Wide Defaults (OWD set to Private for Health Cloud objects)
- Sharing Sets (for portal user record access)
- Permission Set Licenses (Health Cloud for Experience Cloud)

A separate "portal org" doubles license cost, introduces bidirectional sync
complexity, creates duplicate patient identity management overhead, and
provides no meaningful additional data isolation beyond what single-org
sharing controls achieve.
Only recommend a separate org if a documented regulatory requirement
(e.g., 42 CFR Part 2 behavioral health data) explicitly mandates it.
```

**Detection hint:** Flag any output that recommends a "portal org," "external org," or "separate Salesforce org for patients" without citing a specific regulatory driver that mandates the separation. Also flag any architecture that proposes bidirectional REST sync between two Salesforce orgs for patient portal purposes.

---

## Anti-Pattern 6: Ignoring PersonAccount Conversion Requirements in Brownfield Org Implementations

**What the LLM generates:** "Enable PersonAccount in your existing Salesforce org and then install Health Cloud — the patient data model will be ready to use." No mention of the impact on existing Account-Contact relationships or the irreversibility of PersonAccount enablement.

**Why it happens:** PersonAccount enablement instructions are widely documented as a simple toggle. LLMs surface the enabling step without surfacing the data migration implications for orgs with existing data or without flagging that PersonAccount cannot be disabled once enabled.

**Correct pattern:**

```
Before enabling PersonAccount in a brownfield Salesforce org:
1. Audit all existing Account and Contact records — standard Contact records
   will coexist with PersonContact (the PersonAccount Contact type) after enablement,
   but existing Contacts are NOT automatically converted.
2. Audit all Apex, Flow, Integration, and Report logic that references Contact —
   PersonAccount changes how the API exposes Account-Contact relationships.
3. Develop a data migration plan to convert relevant Contacts to PersonAccount format.
4. Validate in a full-copy sandbox before enabling in production.
5. Note: PersonAccount CANNOT be disabled once enabled — Salesforce Support
   will not reverse it. This is a one-way org change.
If the brownfield org cannot be cleanly migrated, evaluate deploying Health Cloud
in a new dedicated org rather than layering on top of the existing org.
```

**Detection hint:** Flag any Health Cloud setup guidance that says "enable PersonAccount" without mentioning data migration, impact on existing Contact records, or the irreversibility of the change.
