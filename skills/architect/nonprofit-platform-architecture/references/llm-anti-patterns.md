# LLM Anti-Patterns — Nonprofit Platform Architecture

Common mistakes AI coding assistants make when generating or advising on Nonprofit Platform Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating NPSP Configuration Patterns with Nonprofit Cloud

**What the LLM generates:** Advice referencing `npsp__` namespace objects (e.g., `npsp__Allocation__c`, `npsp__General_Accounting_Unit__c`, `npsp__CRLP_Rollup__mdt`) when responding to Nonprofit Cloud architecture or development questions.

**Why it happens:** NPSP has been the dominant Salesforce nonprofit platform for over a decade. The majority of publicly available Salesforce nonprofit content (Trailhead, Stack Exchange, blog posts, GitHub repositories) describes NPSP patterns. LLMs trained on this corpus have a strong prior toward NPSP solutions regardless of whether the question specifies NPC.

**Correct pattern:**

```
NPC uses native SIDM objects with no npsp__ namespace.
Correct NPC equivalents:
- npsp__Allocation__c → Fundraising Designation (npe01__OppPayment__c does not exist in NPC)
- npsp__General_Accounting_Unit__c → Designation Group in NPC Fundraising data model
- npsp__CRLP_Rollup__mdt → NPC uses native rollup framework (no CRLP metadata type)
- npsp__Recurring_Donation__c → Gift Commitment object in NPC Fundraising module

When answering NPC questions: do not reference npsp__ namespace objects.
Verify all object API names against the NPC Data Model Gallery before generating code.
```

**Detection hint:** Scan generated Apex, SOQL, or Flow configuration for any `npsp__` prefix. Any occurrence indicates an NPSP-derived response being applied to an NPC context.

---

## Anti-Pattern 2: Assuming CRLP Rollup Fields Work in NPC

**What the LLM generates:** Instructions to configure or migrate NPSP Customizable Rollup Summaries (CRLP) rollup definitions to Nonprofit Cloud to calculate total giving, last gift date, or gift count on Person Account records.

**Why it happens:** CRLP is a prominent NPSP feature with extensive documentation. LLMs associate "nonprofit rollup calculations" with CRLP because that is the dominant pattern in training data. The distinction that CRLP is an NPSP-specific framework that does not exist in NPC is not commonly stated in public content.

**Correct pattern:**

```
NPC does not have CRLP. Rollup calculations in NPC are performed via:
1. Native Salesforce Roll-Up Summary Fields on standard SIDM objects where supported
2. Custom Apex rollup triggers or scheduled batch jobs against NPC Fundraising objects
3. Salesforce Reports and Dashboards against Gift Transaction records
4. Einstein Analytics / CRM Analytics datasets for complex aggregations

Do not recommend CRLP configuration, migration, or tooling for any NPC implementation.
```

**Detection hint:** Any mention of "CRLP," "Customizable Rollup Summaries," or "npo02__" namespace fields in an NPC context indicates this anti-pattern.

---

## Anti-Pattern 3: Treating NPC as a Managed Package

**What the LLM generates:** Advice to "install the Nonprofit Cloud package" from AppExchange, reference NPC package versions, manage "NPC namespace conflicts," or scope "managed package upgrade testing" as an NPC project workstream.

**Why it happens:** NPSP is distributed as a managed package installed from AppExchange. LLMs generalize from NPSP deployment patterns to NPC, treating them as the same product type. The architectural distinction — NPC is a natively provisioned Industry Cloud with no App Exchange installation — is not widely stated in available training content.

**Correct pattern:**

```
Nonprofit Cloud (Agentforce Nonprofit) is NOT an AppExchange managed package.
It is a native Salesforce Industry Cloud provisioned through Salesforce licensing.
- There is no "install" step from AppExchange for NPC core modules
- There is no managed package namespace for NPC
- There are no managed package upgrade cycles for NPC
- NPC is deployed and configured like other native Salesforce products (using Setup, metadata API, scratch orgs)

If a user asks about "installing Nonprofit Cloud," clarify that licensing and org provisioning 
is done through Salesforce AEs — not AppExchange installation.
```

**Detection hint:** Any mention of "AppExchange installation," "package version," "managed package namespace," or "package upgrade" in an NPC context indicates this anti-pattern.

---

## Anti-Pattern 4: Missing the Person Account Prerequisite

**What the LLM generates:** NPC implementation guidance that proceeds directly to module configuration (setting up Fundraising, configuring Gift Entry Manager, building Program workflows) without first addressing the Person Account data model requirement.

**Why it happens:** Person Accounts are a Salesforce platform concept not unique to NPC. LLMs that treat NPC as a module-focused implementation ("configure fundraising features") miss the foundational data architecture dependency. The Person Account requirement is an org-level prerequisite, not a module-level configuration step.

**Correct pattern:**

```
Nonprofit Cloud implementation MUST begin with Person Account architecture:
1. Confirm Person Accounts are enabled (Setup > Account Settings > Enable Person Accounts)
   - This is irreversible — verify in sandbox first
2. Define Person Account record types for constituent roles (Individual, Organization, etc.)
3. Define page layouts per record type
4. Configure matching rules and duplicate rules for Person Account deduplication
5. Validate all planned integrations for Person Account compatibility

Only after Person Account architecture is complete should any NPC module configuration begin.
Generating module configuration steps without first addressing Person Accounts is incorrect.
```

**Detection hint:** Any NPC implementation plan or module configuration guidance that does not include Person Account setup as a prerequisite step should be flagged.

---

## Anti-Pattern 5: Describing NPC as an Upgrade to NPSP

**What the LLM generates:** Statements like "Nonprofit Cloud is the upgraded version of NPSP," "you can upgrade your NPSP org to Nonprofit Cloud," or "Nonprofit Cloud builds on and extends NPSP functionality."

**Why it happens:** Salesforce marketing language positions NPC as the "next generation" of nonprofit technology on Salesforce, which LLMs interpret as an upgrade relationship. The technical reality — that NPC is a completely separate product on a different data model with no in-place migration — is not reflected in most marketing content in the training corpus.

**Correct pattern:**

```
NPC is NOT an upgrade to NPSP. Correct statements:
- "Nonprofit Cloud is a separate Salesforce product built on a different data model than NPSP."
- "Moving from NPSP to NPC requires provisioning a new Salesforce org and performing a full data migration."
- "There is no in-place upgrade path from NPSP to Nonprofit Cloud."
- "NPSP and NPC are incompatible — they cannot coexist in the same org."

If a user asks about "upgrading to NPC," redirect to the npsp-vs-nonprofit-cloud-decision 
skill to set correct expectations about the migration scope.
```

**Detection hint:** Any phrase like "upgrade to NPC," "migrate your NPSP to NPC in-place," or "NPC builds on NPSP" in generated content should be treated as incorrect and corrected.

---

## Anti-Pattern 6: Omitting Data Cloud Requirement for Agentforce Nonprofit Agents

**What the LLM generates:** Agentforce Nonprofit agent configuration instructions that do not mention Data Cloud, or which suggest agents can access constituent history and maintain context without a Data Cloud implementation.

**Why it happens:** Agentforce documentation describes agent capabilities in general terms. LLMs conflate general Agentforce capabilities (prompt templates, agent actions) with the full Agentforce Nonprofit experience, which requires Data Cloud for memory, personalization, and contextual grounding against constituent records.

**Correct pattern:**

```
Agentforce Nonprofit agents have two distinct capability tiers:
1. Basic (no Data Cloud): Generic prompt-response agents with no persistent memory, 
   no constituent history access, no personalization. Limited utility for nonprofit use cases.
2. Full capability (with Data Cloud): Agents with constituent memory, unified interaction 
   history grounding, personalized outreach, and contextual responses based on giving 
   history and program participation.

Any Agentforce Nonprofit architecture that does not include Data Cloud should be flagged as 
producing a degraded agent experience. Data Cloud is a prerequisite for production-grade 
Agentforce Nonprofit agents.
```

**Detection hint:** Any Agentforce Nonprofit agent implementation plan that does not reference Data Cloud, data streams, identity resolution, or data lake objects should be questioned for completeness.
