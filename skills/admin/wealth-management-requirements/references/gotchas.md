# Gotchas — Wealth Management Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: FinancialAccountParty Junction Exists Only in FSC Core — Managed Package Uses Fixed Lookups

**What happens:** In FSC managed-package orgs, `FinancialAccountRole__c` provides relationship metadata (Primary Owner, Joint Owner, Beneficiary, Power of Attorney) but the actual ownership lookups on `FinServ__FinancialAccount__c` are two fixed lookup fields: `FinServ__PrimaryOwner__c` and `FinServ__JointOwner__c`. This hard-limits financial accounts to two named owners. Household rollup behavior is driven entirely by the Primary Owner's household membership — a Joint Owner in a different household does not see the account rolled up to their household view.

In FSC Core, the `FinancialAccountParty` junction object replaces the fixed lookups. It supports unlimited participants with typed roles, enabling trusts with multiple beneficiaries, family accounts with multiple members, and partnership accounts with named partners.

**When it occurs:** Requirements that call for trust accounts, family limited partnership accounts, or any account with more than two named owners will surface this constraint. It also affects reporting requirements: "show all accounts a person is related to in any role" is easy in Core via a `FinancialAccountParty` query but requires a complex multi-object relationship query in managed-package orgs.

**How to avoid:** During requirements discovery, explicitly ask "will any accounts have more than two named owners?" and "are trust accounts or partnership accounts in scope?" If yes, document this as an architectural forcing function toward FSC Core. Include it in the architecture determination memo.

---

## Gotcha 2: AccountFinancialSummary Requires an FSC PSL Integration User — Not Populated by Standard User Activity

**What happens:** FSC Core's `AccountFinancialSummary` object appears to be a straightforward rollup of household-level financial balances (total assets, total liabilities, net worth). Requirements often assume it will populate automatically when `FinancialAccount` records are created or updated. It does not. `AccountFinancialSummary` is populated by a dedicated batch process that runs under a special FSC Platform Service Layer (PSL) integration user. Without the correct setup of this integration user and the associated permission set license, the object remains empty.

This also means that the "household AUM dashboard" or "advisor client total view" requirements that reference `AccountFinancialSummary` fields will show blank values in production until the PSL integration user is configured — which is an infrastructure concern, not a configuration concern.

**When it occurs:** Any requirement for household-level balance aggregation, net worth calculation, or AUM rollup in an FSC Core org depends on this object. It surfaces in UAT when advisors report that household summary tiles show zero or null values.

**How to avoid:** When scoping household summary or AUM rollup requirements in an FSC Core org, include a requirement item: "FSC PSL integration user must be configured and granted FinancialSummary recalculation permissions." Flag this as a system administration dependency in the requirements package. Assign it as a prerequisite to any story that references `AccountFinancialSummary` fields.

---

## Gotcha 3: Third-Party Custodian ISV Packages May Not Be Certified for FSC Core

**What happens:** Many wealth management implementations rely on third-party custodian data feed and portfolio management packages — Black Diamond, Orion Advisor Services, Addepar, Tamarac, Envestnet. These packages were originally built against the FSC managed-package namespace (`FinServ__`). As FSC Core becomes more prevalent, AppExchange vendors are certifying their packages for Core, but as of Spring '26 not all packages are fully certified.

If an implementation commits to FSC Core architecture without validating ISV package compatibility, the custodian data feed integration may fail to map data to the correct objects, may not write to `FinancialAccountParty` (Core) correctly because it still expects the two-lookup model, or may not support `AccountFinancialSummary` population at all.

**When it occurs:** During requirements discovery when the client confirms they use (or intend to use) an ISV package for custodian data. This is a blocking constraint on the architecture decision: if the required ISV is not FSC Core certified, the org may need to remain on the managed package until the vendor certifies their package.

**How to avoid:** In the architecture determination workshop, enumerate all third-party packages the client uses or plans to use. Check each package on AppExchange for an explicit "Works with FSC Core" or "FSC Core Certified" badge. If a package is not certified, document this as a risk in the requirements package and escalate to the Salesforce AE and ISV vendor before finalizing the architecture decision. Do not proceed to FSC Core design until this is resolved.

---

## Gotcha 4: FinancialPlan and Financial Planning Module Require a Separate License Add-On

**What happens:** The `FinancialPlan` object and the associated financial planning UI module in FSC may not be included in the base FSC license. Requirements gathering sessions often produce detailed goal-based financial planning workflows that rely on `FinancialPlan` + `FinancialGoal` features — but without confirming license entitlement, these features cannot be enabled in Setup.

**When it occurs:** When gathering requirements for goal-based financial planning workflows: "advisor creates a retirement plan linking multiple financial goals," "client can view their financial plan progress in the portal." If the FSC license tier does not include the financial planning module, these features are unavailable regardless of configuration effort.

**How to avoid:** During requirements kickoff, review the client's Salesforce order form or ask the Salesforce AE to confirm which FSC feature modules are licensed. Specifically confirm: Financial Plans and Goals, Actionable Relationship Center (ARC), and Financial Services Analytics. Document confirmed entitlements in the requirements package. Any requirement that depends on an unconfirmed add-on should be flagged as "license validation required" before sprint planning.

---

## Gotcha 5: ActionPlan Recurrence Is Not Built In — Annual Review Scheduling Needs a Separate Automation

**What happens:** `ActionPlan` and `ActionPlanTemplate` are FSC's standard mechanism for repeatable advisor workflows. However, `ActionPlan` records are not self-recurring. Creating a new ActionPlan instance for each client's annual review each year requires a separate automation (typically a Scheduled Flow or Apex Schedulable class) that triggers ActionPlan creation at the appropriate time. Many requirements documents describe "annual review workflows" without capturing this gap — leading developers to discover mid-sprint that ActionPlan alone does not handle recurrence.

**When it occurs:** Any requirement phrased as "automatically remind advisor to conduct annual client review" or "create review checklist for each client every year." The requirement is valid and achievable, but it requires scoping the ActionPlan template AND the recurrence trigger mechanism as separate work items.

**How to avoid:** When gathering requirements for repeatable advisor workflows, always ask "how often should this repeat?" and "what should trigger the creation of a new review cycle?" Document both the ActionPlanTemplate design (task list, responsibilities, due date offsets) and the trigger mechanism (scheduled automation, event-based trigger, manual creation) as separate requirements. Estimate them separately in the fit-gap analysis — the recurrence mechanism is typically more complex than the template itself.
