# Examples — NPSP vs. Nonprofit Cloud Decision

## Example 1: Community Foundation Evaluating NPC for Grantmaking

**Context:** A community foundation has been on NPSP for six years. The development team manages donor relationships and grant awards using custom objects layered on top of NPSP. The foundation's leadership wants to evaluate Salesforce Grantmaking (a native NPC product) and has heard from a peer foundation that "you can upgrade your NPSP org."

**Problem:** Without structured decision guidance, the team spends two months investigating an in-place upgrade path that does not exist, receiving conflicting information from consultants and AI tools. Time and budget are wasted before the correct architecture is understood.

**Solution:**

```
Decision Framework Applied:
─────────────────────────────────────────────────────────────────────
Feature requirement:      Salesforce Grantmaking
Available in NPSP?        NO — Grantmaking is an NPC-exclusive product
Primary decision driver:  Required feature unavailable in NPSP
─────────────────────────────────────────────────────────────────────
Recommendation:           MIGRATE to Nonprofit Cloud
Migration path:           Net-new NPC org + formal data migration
  Step 1 — Provision new org with NPC + Grantmaking licenses
  Step 2 — Rebuild donor, grant, and program configuration in NPC
  Step 3 — Extract NPSP data: Contacts, Accounts, Opportunities,
            custom grant objects
  Step 4 — Transform to NPC data model (Person Accounts,
            Gift Transactions, Designations)
  Step 5 — Load into new org; validate; run parallel for 30 days
  Step 6 — Cutover and decommission NPSP org
─────────────────────────────────────────────────────────────────────
Explicit correction:
  There is NO in-place upgrade. The foundation must provision a
  new org. The existing NPSP org cannot be converted.
```

**Why it works:** The decision framework surfaces the NPC-exclusive feature requirement immediately, making the go/stay decision clear. The explicit correction of the "upgrade myth" prevents the team from pursuing a non-existent path. The step-by-step migration outline gives leadership a realistic project picture before they commit.

---

## Example 2: Mid-Size Human Services Nonprofit — Stay Decision

**Context:** A regional human services nonprofit has been on NPSP for four years. Their org includes custom Apex triggers for constituent matching, 47 active Flows, the Program Management Module (PMM), and integrations with Mailchimp and Stripe. They have heard that "NPSP is being discontinued" and are panicking about needing to migrate immediately.

**Problem:** The organization is considering an immediate, reactive migration to NPC driven by fear of NPSP shutdown — not a business need. A rushed migration of a highly customized org without business driver is an anti-pattern that creates unnecessary risk and cost.

**Solution:**

```
Decision Framework Applied:
─────────────────────────────────────────────────────────────────────
NPC-exclusive feature needed?    NO — all current requirements met
                                 by NPSP
NPSP EOL announced?              NO — no hard EOL date as of April 2026
Customization complexity:        HIGH (Apex triggers, 47 Flows, PMM,
                                 Mailchimp + Stripe integrations)
Migration cost/risk:             HIGH
─────────────────────────────────────────────────────────────────────
Recommendation:                  STAY on NPSP with a defined
                                 re-evaluation trigger
─────────────────────────────────────────────────────────────────────
Re-evaluation triggers to document:
  - Salesforce announces a formal NPSP EOL date
  - A required new feature is NPC-exclusive
  - A critical integration breaks due to NPSP package deprecation
  - A platform consolidation project creates a migration window

Immediate actions:
  1. Correct the "NPSP is being discontinued" misconception —
     NPSP is feature-frozen but still supported
  2. Document the re-evaluation trigger list
  3. Ensure data export / backup procedures are current
  4. Schedule an annual NPSP support status review
```

**Why it works:** The framework prevents a reactive migration with no business driver. A high-complexity org migrating without reason creates disruption and cost without corresponding value. The re-evaluation trigger list converts vague anxiety into a concrete governance mechanism.

---

## Anti-Pattern: Recommending an "NPSP to NPC Upgrade"

**What practitioners do:** Advise a client to "upgrade" their existing NPSP org to Nonprofit Cloud by running a Salesforce-provided migration tool or package upgrade, similar to how managed package versions are upgraded.

**What goes wrong:** No such tool exists. If a practitioner or AI assistant tells a client they can upgrade an existing NPSP org to NPC, the client may:
- Delay planning for a proper net-new org provisioning
- Budget incorrectly (a "package upgrade" costs far less than a full reimplementation)
- Proceed with work in the existing org that then must be redone in a new org
- Lose trust in the advisor when the reality becomes apparent

**Correct approach:** Clearly state that NPSP to Nonprofit Cloud is a full org migration — not an upgrade. The client must: (1) provision a new Salesforce org with NPC licenses, (2) rebuild their configuration, and (3) migrate their data. This is a project, not a button click. Budget and timeline must reflect this reality.
