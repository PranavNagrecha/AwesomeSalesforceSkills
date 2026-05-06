# Examples — Report Type Strategy

## Example 1: A-with-B inner join (primary requires secondary)

**Use case:** Renewals team needs Opportunities that have at least
one Quote. An Opportunity with no Quote should not appear.

**CRT design:**

- Primary object: Opportunity
- Secondary object: Quote
- Relationship to Primary: "Each 'A' record must have at least
  one related 'B' record"

**Why:** Inner join semantics. The report row exists only if the
Opportunity has a Quote. Opportunities without Quotes are
silently excluded from the report — which is exactly what the
renewals team wants.

---

## Example 2: A-with-or-without-B outer join

**Use case:** Sales Ops needs every Account, with the count of
Open Cases when present (zero when absent). An Account without
Cases must still appear.

**CRT design:**

- Primary object: Account
- Secondary object: Case
- Relationship: "'A' records may or may not have related 'B'
  records"

**Why:** Outer join. Account row appears regardless. Case fields
are blank when no Case exists — `RowCount` of Cases is 0.

A common bug: setting the join to "must have at least one" for
this shape, then writing a formula `IF(ISBLANK(Case.Id), 0, 1)`
to count — but the row never appears at all because the inner
join already filtered it out.

---

## Example 3: A-without-B (subtraction via joined report)

**Use case:** Find Accounts that have no Open Opportunities. CRTs
cannot directly model this — there's no "must NOT have related"
join.

**Joined report design:**

- Block 1: "Accounts" CRT, all Accounts.
- Block 2: "Accounts with Opportunities" CRT, filtered to Open.
- Filter: Block 1's Account.Id NOT IN Block 2's Account.Id.

Joined reports do not support `NOT IN` directly across blocks.
The practical workaround:

- Use a Cross Filter on a single CRT: "Accounts WITH Opportunities
  where Stage = 'Open'" → invert with the Cross Filter operator
  "without".

Cross Filters are the per-CRT mechanism for negation joins —
they avoid joined-report fragility.

---

## Example 4: Three-level CRT with related-via-lookup

**Use case:** Report on Cases, with the related Account's Industry
and the Account Owner's Region.

**CRT design:**

- Primary: Case
- Secondary: Account (via Case.AccountId)
- Tertiary: User as related to Account.OwnerId — this is a
  *related-via-lookup* join through the Owner lookup. Salesforce
  treats Owner specially; some CRTs surface "Account Owner" fields
  directly without needing the third level.

**Why:** Three levels are the practical max in a single CRT. Going
further (Region of the Owner of the Account on the Case)
typically needs Account Owner.Region__c on Account itself
(formula via lookup), or a flattened field via Flow.

---

## Example 5: Curated field layout for a 200-field object

**Bad:** All 200 fields visible in the field picker. Users scroll
endlessly, can't find "Annual Revenue", and end up using "Amount"
by mistake.

**Good:**

- **Account Information** (8 fields): Name, Owner, Industry,
  Annual Revenue, Type, Rating, Phone, Website
- **Renewal Tracking** (5 fields): Renewal Date, Renewal Owner,
  Renewal Stage, Renewal Amount, Auto-Renew Flag
- **System Fields** (4 fields): Created Date, Last Modified Date,
  Last Activity, Record Type

Hide the other 183. They are still searchable for power users
but no longer clutter the default field picker. The 60-field
display limit becomes irrelevant when the layout is this tight.

---

## Example 6: Documenting the CRT for the report-builder picker

**Bad description:** "Custom report type for Accounts."

**Good description:** "Use for renewal pipeline analysis.
Includes only Accounts with at least one open Renewal
Opportunity. Excludes closed-lost. For all-Accounts reporting
use the standard 'Accounts' report type instead."

The description appears in the report-builder picker. A good
description steers users to the right CRT and away from the
ones with side-effecting filters they didn't expect.
