# LLM Anti-Patterns — NPSP vs. Nonprofit Cloud Decision

Common mistakes AI coding assistants and AI advisors make when generating or advising on the NPSP vs. Nonprofit Cloud decision. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Asserting That an In-Place Upgrade Exists

**What the LLM generates:** "You can upgrade your existing NPSP org to Nonprofit Cloud by installing the NPC managed package" or "Salesforce provides a migration tool to convert your NPSP org in place" or "Run the NPC Transition Assistance Program installer in your current org."

**Why it happens:** LLMs are trained on large corpora of Salesforce documentation where "package upgrade" is a routine operation. They conflate the standard managed package upgrade pattern with the NPSP-to-NPC transition, which is architecturally different. Pre-2023 community posts and third-party blog content may also describe aspirational migration tooling that was never shipped.

**Correct pattern:**

```
There is no in-place upgrade path from NPSP to Nonprofit Cloud.
The transition requires:
  1. Provisioning a new Salesforce org with NPC licenses
  2. Rebuilding all configuration in the new org
  3. Extracting, transforming, and loading data from the NPSP org
  4. Validating data integrity and running parallel operations
  5. Executing a production cutover
This is a reimplementation project, not a package upgrade.
```

**Detection hint:** Flag any response containing "upgrade your NPSP org to NPC," "install NPC on your existing org," "in-place migration tool," or "convert your NPSP org." These phrases signal the anti-pattern.

---

## Anti-Pattern 2: Stating That NPSP Has Been End-of-Lifed or Is Being Discontinued Immediately

**What the LLM generates:** "NPSP is being discontinued in [year]" or "Salesforce has announced end of life for NPSP" or "You must migrate to NPC by [date] or lose support."

**Why it happens:** Community discussions about NPSP's frozen state are often summarized imprecisely. LLMs trained on these discussions reproduce the imprecise framing. The factual status (feature-frozen, security patches only, no hard EOL date as of April 2026) is more nuanced than community shorthand conveys.

**Correct pattern:**

```
As of April 2026, Salesforce has not announced a hard end-of-life
date for NPSP. NPSP is feature-frozen — no new capabilities will
be developed after March 2023, when Nonprofit Cloud launched.
NPSP continues to receive critical security patches and bug fixes.
A migration decision should be driven by a specific feature gap or
strategic need, not by an EOL deadline that has not been announced.
```

**Detection hint:** Flag any response containing a specific EOL date for NPSP, "NPSP support ends," "NPSP is being discontinued," or "you must migrate by." Verify against current Salesforce Help documentation before repeating any EOL claim.

---

## Anti-Pattern 3: Treating Person Accounts and Household Accounts as Interchangeable

**What the LLM generates:** "You can enable Person Accounts in your NPSP org to start using the NPC data model" or "Household Accounts and Person Accounts are just different record types — you can switch between them."

**Why it happens:** LLMs understand that both Person Accounts and Household Accounts are built on the standard Account and Contact objects. They incorrectly generalize that switching between them is a configuration change rather than a fundamental data model difference.

**Correct pattern:**

```
Person Accounts and Household Accounts are mutually exclusive
Account models in Salesforce. Enabling Person Accounts in an org
is an irreversible org-level change that cannot be undone.
NPSP is built on the Household Account model and is incompatible
with a Person Account org. Nonprofit Cloud uses Person Accounts
by default. Switching from NPSP's Household Account model to
NPC's Person Account model requires a full data migration in a
net-new org — it cannot be done by reconfiguring the existing org.
```

**Detection hint:** Flag any response suggesting "enable Person Accounts in your NPSP org," "switch from Household Accounts to Person Accounts," or "convert Account record types." These suggest the LLM is treating an architectural incompatibility as a configuration option.

---

## Anti-Pattern 4: Claiming PMM Migrates Automatically or Is a Direct 1:1 Replacement

**What the LLM generates:** "Your Program Management Module data will migrate automatically to NPC's Program Management" or "NPC Program Management is a drop-in replacement for PMM — all your configurations will carry over."

**Why it happens:** LLMs recognize that both PMM and NPC Program Management manage programs, services, and beneficiary records. They infer that the products are equivalent and that migration is a straightforward data mapping. The actual object model differences and feature parity gaps are not reflected in most LLM training data.

**Correct pattern:**

```
The NPSP Program Management Module (PMM) and NPC's native Program
Management are different products with different object models,
field structures, and relationship architectures. PMM configurations
do not transfer to NPC automatically. Each PMM use case must be
validated against NPC Program Management feature-by-feature before
migration. Some PMM configurations — particularly complex service
delivery workflows, community portal integrations, and custom
reporting structures — may require custom development in NPC.
Include a PMM-to-NPC feature parity assessment as a required step
in the pre-migration decision framework.
```

**Detection hint:** Flag any response containing "PMM migrates to NPC," "drop-in replacement," or "PMM configurations carry over." These signal an unvalidated equivalence assumption.

---

## Anti-Pattern 5: Omitting CRLP Rollup Rebuilding From Migration Scope

**What the LLM generates:** A migration plan that includes object data migration (Contacts, Accounts, Opportunities) but does not mention rebuilding NPSP's Customizable Rollup Summaries (CRLP) in NPC.

**Why it happens:** CRLP rollup definitions are stored as NPSP custom metadata records, not as standard Salesforce records. LLMs generating migration plans tend to enumerate the primary object migration workstreams and miss the CRLP definitions because they are metadata, not data, and because the CRLP framework is NPSP-specific and less commonly documented.

**Correct pattern:**

```
NPSP CRLP (Customizable Rollup Summaries) definitions — which
power Total Giving, Last Gift Date, Number of Gifts, and similar
summary fields — are stored as NPSP managed custom metadata. These
definitions do not exist in Nonprofit Cloud and will not transfer
during a data migration. Each CRLP definition must be:
  1. Inventoried before migration begins
  2. Mapped to an equivalent NPC rollup mechanism
  3. Rebuilt from scratch in the new NPC org
  4. Validated against post-migration data
Failure to include this workstream results in blank or incorrect
donor giving summary fields in the new org after cutover.
```

**Detection hint:** Review any migration plan for mention of CRLP, rollup summaries, or giving summary field validation. If a migration plan covers object data migration but does not explicitly address CRLP, flag it as incomplete.

---

## Anti-Pattern 6: Recommending Migration Without Assessing Customization Complexity

**What the LLM generates:** A blanket recommendation to migrate to NPC without first assessing the degree of NPSP customization in the org (custom Apex, Flows, installed packages, integrations, CRLP definitions, PMM configurations).

**Why it happens:** LLMs are trained to recommend the "current" or "recommended" Salesforce product, and NPC is the current product. They apply this recommendation uniformly without conditioning it on the migration complexity for a specific org.

**Correct pattern:**

```
A migration recommendation must be conditioned on:
  1. Whether a NPC-exclusive feature is required (if yes, migration
     is driven by business need regardless of complexity)
  2. The degree of NPSP customization (custom Apex, active Flows,
     installed packages, CRLP definitions, PMM, integrations)
  3. Data volume and relationship complexity
  4. Budget and implementation capacity

For a highly customized NPSP org with no NPC-exclusive feature
requirement, the correct recommendation is a migration readiness
assessment before a final go/stay decision — not an immediate
migration commitment.
```

**Detection hint:** Flag any migration recommendation that does not mention customization complexity, data volume, or a readiness assessment step. A sound recommendation is always conditioned on org-specific factors, not delivered as a blanket "migrate now."
