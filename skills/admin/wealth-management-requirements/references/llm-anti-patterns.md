# LLM Anti-Patterns — Wealth Management Requirements

Common mistakes AI coding assistants make when generating or advising on Wealth Management Requirements.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using FinServ__FinancialGoal__c Without Confirming Architecture

**What the LLM generates:** SOQL queries, Flow field references, acceptance criteria, or user story object references that use the managed-package namespace (`FinServ__FinancialGoal__c`, `FinServ__FinancialPlan__c`, `FinServ__FinancialAccount__c`) without first confirming whether the org uses the managed package or FSC Core.

**Why it happens:** Most publicly available FSC documentation, Trailhead content, and Stack Overflow answers were written before FSC Core GA (Winter '23). The managed-package namespace is therefore far more prevalent in training data. LLMs default to the managed-package naming convention because it is what they have seen most often.

**Correct pattern:**

```
BEFORE generating any FSC object names, API field references, or SOQL:

1. Confirm architecture: is this org managed-package (FinServ__ namespace) or FSC Core (no namespace)?
2. If unknown, instruct the user to check: Setup > Installed Packages > look for a "Financial Services Cloud" package with namespace "FinServ"
   - If present with FinServ namespace → managed package, use FinServ__ prefix
   - If absent → FSC Core, use no prefix

Managed package example: SELECT Id, FinServ__FinancialGoal__c.Name FROM FinServ__FinancialGoal__c
FSC Core example:        SELECT Id, Name FROM FinancialGoal
```

**Detection hint:** Any output containing `FinServ__` should trigger a check: "Has the architecture been confirmed as managed package in this conversation?" If not, flag before proceeding.

---

## Anti-Pattern 2: Assuming ISV Packages Work With FSC Core Without Validation

**What the LLM generates:** Requirements or architecture recommendations that include both FSC Core and a third-party custodian/portfolio management ISV package (Black Diamond, Orion, Addepar, Tamarac, Envestnet) without noting that FSC Core certification for the package must be validated.

**Why it happens:** LLMs are aware of these ISV packages as common FSC integrations, and they know FSC Core is the current recommended architecture. They combine these two pieces of knowledge without registering that ISV certification for Core is a per-package, point-in-time status that may not be true.

**Correct pattern:**

```
When generating requirements or architecture guidance that includes both FSC Core and an ISV package:

1. Note explicitly: "[Package name] must be validated for FSC Core support before committing to this architecture."
2. Instruct the user to: check the package's AppExchange listing for "FSC Core" or "Financial Services Cloud Core" certification badge.
3. If certification status is unknown: flag as a blocking dependency in the requirements document. Do not finalize architecture until resolved.
4. If the package is not certified: document as a constraint that may require remaining on managed-package FSC until the vendor certifies.
```

**Detection hint:** Any response that recommends FSC Core AND mentions Black Diamond, Orion, Addepar, Tamarac, or any other custodian/portfolio management ISV package without a certification caveat is an anti-pattern.

---

## Anti-Pattern 3: Treating AccountFinancialSummary as a Standard Rollup Field

**What the LLM generates:** Requirements or implementation guidance that references `AccountFinancialSummary` as if it automatically populates when `FinancialAccount` records are created or updated — e.g., "the household net worth field on AccountFinancialSummary will update when account balances change."

**Why it happens:** `AccountFinancialSummary` looks like a standard summary or rollup field based on its name and relationship to the Account object. LLMs pattern-match to familiar Salesforce rollup summary field behavior. They do not know that this object requires a dedicated FSC PSL integration user and a batch recalculation process to populate.

**Correct pattern:**

```
AccountFinancialSummary (FSC Core only) is populated by:
- A dedicated FSC Platform Service Layer (PSL) integration user
- A batch recalculation process that must be configured as part of FSC Core setup
- It does NOT auto-populate from FinancialAccount record changes like a standard rollup field

Requirements that depend on AccountFinancialSummary must include:
- Requirement: FSC PSL integration user must be provisioned and granted appropriate permission set license
- Requirement: Recalculation schedule must be defined (frequency, trigger conditions)
- Note: This is a system administration prerequisite, not a configuration item for the standard admin
```

**Detection hint:** Any response that uses `AccountFinancialSummary` without mentioning the PSL integration user requirement is incomplete. Flag and add the infrastructure prerequisite.

---

## Anti-Pattern 4: Conflating Financial Planning Workflow With Portfolio Review Workflow

**What the LLM generates:** A single combined process map or workflow design that mixes goal-based financial planning activities (creating FinancialGoal records, building a FinancialPlan) with portfolio performance monitoring activities (loading FinancialHolding positions, tracking allocation drift). This produces requirements that are ambiguous about which FSC features apply.

**Why it happens:** "Wealth management" is a broad term that encompasses both activities. LLMs generate a unified workflow because they perceive both as part of the same advisory process. In practice, these workflows have different cadences, different data sources, different FSC objects, and different user personas.

**Correct pattern:**

```
Keep these as SEPARATE workflow tracks in requirements documentation:

Financial Planning Workflow (goal-based, client-centric):
- Objects: FinancialGoal, FinancialPlan, ActionPlan
- Cadence: triggered by life events (marriage, job change, inheritance) or annual review
- Persona: financial planner, advisor, client
- Data source: client-provided goal data

Portfolio Review Workflow (performance-based, position-centric):
- Objects: FinancialHolding, FinancialAccount, AccountFinancialSummary
- Cadence: triggered by custodian data load (daily/weekly), market events, or periodic review
- Persona: portfolio manager, advisor
- Data source: custodian data feed (integration requirement)

Each workflow produces a separate set of user stories and a separate fit-gap table.
```

**Detection hint:** If a requirements document or process map combines "goal setting" and "portfolio rebalancing" in the same workflow swimlane without distinguishing them, the two tracks have been conflated.

---

## Anti-Pattern 5: Omitting Volume Discovery From Requirements

**What the LLM generates:** Wealth management requirements, user stories, and fit-gap analyses that describe what advisors need to do without capturing how much: number of client households, financial accounts per household, ActionPlan instances per year, FinancialHolding positions per account, custodian data record volume per daily feed.

**Why it happens:** LLMs generate requirements based on functional scope (what the system should do) and rarely prompt for non-functional requirements like volume, frequency, and load unless explicitly asked. Wealth management volume data is not part of the functional description of a requirement.

**Correct pattern:**

```
Volume questions to ask during every wealth management requirements session:

1. How many client households are in scope (now and at expected 3-year growth)?
2. How many financial accounts per household on average? What is the maximum?
3. How many FinancialHolding position records per account? (Drives FinancialHolding storage sizing)
4. How frequently does the custodian data feed run? How many records per load?
5. How many ActionPlan instances will be created per year (advisors × clients × review frequency)?
6. How many advisors will be active users concurrently during peak load (e.g., end-of-quarter review season)?

Document all answers in requirements. Flag any that indicate:
- >100,000 FinancialHolding records → data storage and query performance concern
- >50,000 ActionPlan records/year → list view and report performance concern
- Custodian loads >50,000 records → Bulk API and governor limit concern
```

**Detection hint:** A requirements document with no volume or frequency data for any wealth management workflow is incomplete. If generating requirements, always include a "Volume and Frequency" section in each user story for data-intensive FSC operations.

---

## Anti-Pattern 6: Scoping FinancialPlan Without Confirming License Entitlement

**What the LLM generates:** Requirements, user stories, or feature lists that include `FinancialPlan` and the Financial Plans and Goals module without noting that this feature requires license confirmation.

**Why it happens:** LLMs know that `FinancialPlan` is a standard FSC object. They generate requirements for it as if it is universally available in all FSC orgs. The license dependency is a commercial/contractual detail that is not encoded in the object reference documentation.

**Correct pattern:**

```
Before scoping FinancialPlan features, include this requirement item:

"License validation required: confirm that the client's FSC contract includes the Financial Plans and Goals module.
Validation method: Setup > Company Information > Feature Licenses, AND review Salesforce order form.
If license is not confirmed, mark all FinancialPlan stories as 'pending license validation' in the backlog."
```

**Detection hint:** Any requirements output that includes `FinancialPlan` without a license validation note should be flagged and the note added.
