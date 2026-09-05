# Gotchas — Requirements Gathering for Salesforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Acceptance Criteria That Cannot Be Tested in a Sandbox

**What happens:** A user story is written with acceptance criteria like "the system should be fast" or "the page should look clean." These criteria cannot be evaluated in a sandbox, produce no clear pass/fail outcome, and get marked "done" in UAT by default because no one knows what "done" looks like.

**When it occurs:** When BAs write acceptance criteria from the stakeholder's language rather than from testable, observable Salesforce behaviors. Common in first drafts of stories when the BA has not yet mapped requirements to specific platform features.

**How to avoid:** Every acceptance criterion must describe an observable state in a Salesforce sandbox. Replace subjective criteria with specific, platform-verifiable statements:
- Replace "the form should be easy to use" with "all required fields are highlighted in red when the Save button is clicked without completing them"
- Replace "managers can see their team's data" with "users with Manager role can see all Opportunities where OwnerId belongs to their direct reports via Role Hierarchy"
- Replace "the integration should work" with "when a new Account is created with Type = Customer, a corresponding record appears in the external billing system within 5 minutes"

---

## Gotcha 2: Confusing Field-Level Security with Sharing

**What happens:** A stakeholder says "only Sales Managers should see the Discount Approved field." The BA writes a story for a sharing rule, but the requirement is actually a Field-Level Security (FLS) requirement. Sharing rules control record access (who sees which records); FLS controls field access (who sees which fields on records they can already see). These are configured in completely different places in Salesforce — sharing rules are in Sharing Settings; FLS is in Object Manager on the field, or on the profile/permission set.

**When it occurs:** When stakeholders describe visibility requirements without distinguishing "who can see this record" from "who can see this field on a record they can already access." Both are called "access" in plain language, but they map to different Salesforce mechanisms.

**How to avoid:** When capturing a visibility requirement, explicitly ask two questions:
1. "Who should be able to see the *record* at all?" → This is a sharing / OWD / role hierarchy question.
2. "Of those who can see the record, who should be able to see *this field*?" → This is an FLS / permission set question.
Document these as separate requirements. Mixing them in a single story leads to the wrong platform feature being configured.

---

## Gotcha 3: Automation Requirements That Assume Cross-Object DML Is Safe

**What happens:** A stakeholder says "when a Case is closed, automatically update the related Account's Last Case Closed Date field." The BA writes this as a single automation requirement. The admin builds it as a record-triggered Flow on Case, which then updates the parent Account. This creates a cross-object DML within the same transaction, which works — until it runs in the context of another flow or trigger that is also touching the Account, causing a "before save" vs "after save" conflict or a row lock.

**When it occurs:** When the BA captures the automation outcome ("update the Account") without asking whether the Account may be updated by other automation at the same time. In high-volume orgs or orgs with complex automation, cross-object updates create transaction ordering problems that are very hard to debug post-deployment.

**How to avoid:** When any automation requirement involves updating a record that is not the trigger record, flag it explicitly in the story:
- Add a note: "This automation writes to [parent/related object] — requires architect review for transaction safety"
- Capture whether the update needs to be synchronous (same transaction) or can be asynchronous (scheduled job, platform event)
- Identify other automations already updating the same target object — this is a dependency that can cause silent failures

---

## Gotcha 4: Volume-Sensitive Requirements Captured Without Volume Data

**What happens:** A BA captures the requirement "when a Lead is converted, create an Opportunity and a Task." The admin builds a record-triggered flow. It works in UAT with 10 test records. In production, a campaign generates 500 lead conversions per hour. The flow hits governor limits; lead conversions fail silently.

**When it occurs:** When the BA treats all automation requirements as equivalent regardless of the number of records affected. Salesforce's governor limits mean that automation behaving correctly on one record may fail catastrophically on 200 records in a single transaction (e.g., a Data Loader import, a mass approval, or a bulk process job).

**How to avoid:** For every automation requirement, capture three numbers and write the bounding
platform fact beside them:

- **Worst-case records in one transaction.** The per-transaction allocations are shared by Flow and
  Apex: 100 SOQL queries synchronous / 200 asynchronous, 50,000 rows retrieved by SOQL, 150 DML
  statements, and 10,000 records processed as a result of DML (*Salesforce Developer Limits and
  Allocations Quick Reference*, Per-Transaction Apex Limits). A "one record at a time" requirement
  that is also reachable from a data load is not a one-record requirement.
- **Who else can push these records in.** The quick reference draws the line for the loader
  explicitly: "Any data operation that includes more than 2,000 records is a good candidate for Bulk
  API 2.0… Jobs with fewer than 2,000 records should involve 'bulkified' synchronous calls in REST
  (for example, Composite) or SOAP." Data Loader's own maximum import batch size is 200 records for
  SOAP and 10,000 for Bulk API, and Bulk API 2.0 sets batch size automatically (*Data Loader Guide*,
  Settings).
- **The one-off migration nobody mentions.** The go-live backfill is almost always an order of
  magnitude larger than the steady-state rate, and it is the number that sizes the design.

If the answer is hundreds of records per trigger event, record it in the catalogue's `data_volume`
column and route the row to `architect/large-data-volume-architecture` before the admin starts
building — not after UAT passes on ten records.

---

## Gotcha 5: A Requirement That Arrives as a Build Instruction Never Meets the Automation Tree

**What happens:** A stakeholder or a technical lead says "we need a trigger on Opportunity for this."
The BA writes it down as the requirement. It reaches the backlog as "build an Apex trigger on
Opportunity", is sized as development work, and is built as Apex — without anyone ever asking what
the outcome was. The org gains a class, a test class, and a permanent coverage obligation for
behaviour a before-save Flow would have delivered with none of them.

**When it occurs:** Whenever the loudest person in discovery is technical, and whenever the BA is
uncomfortable pushing back on a mechanism they do not own. It is most common on enhancement projects
in orgs that already have Apex, because "we already have triggers there" reads as a reason.

**How to avoid:** Treat any sentence naming a Salesforce mechanism as evidence, not as the
requirement. Run the Solution-to-Requirement Rewind in `SKILL.md`: write the sentence down verbatim,
ask what happens today without it and what the stakeholder would see that proves it worked, and put
*that* in `statement`. Move the original into `automation_candidate`, then walk
`standards/decision-trees/automation-selection.md` from Q1 and record the step in
`decision_tree_step`. The checker fails a row that has the candidate and not the step.

The asymmetry is worth stating to the stakeholder in the room, because it is the reason the tier is
not a preference: Apex carries a deployment gate that Flow does not — "unit tests must cover at least
75% of your Apex code, and all of those tests must complete successfully" (*Apex Developer Guide*,
Testing Apex). Choosing Apex where Flow fits buys a permanent obligation for one release's
convenience.

---

## Gotcha 6: A Visibility Requirement That Names No Layer Cannot Be Built

**What happens:** The catalogue says "only managers should see returns from other branches." An admin
reads it and writes a criteria-based sharing rule. It works for the four people in the demo and fails
in three separate ways in production: peers in the same role see records they should not (the OWD was
never tightened), a regional director sees nothing (the requirement meant the role hierarchy, not a
rule), and finance sees the record but not the credit amount they were promised (that was FLS all
along). Each fix is in a different part of Setup, and each is deployed separately.

**When it occurs:** When a visibility answer is captured in the stakeholder's words and never
translated. "Only managers see X" is a sentence about people; the platform needs a sentence about
mechanisms, and there are seven of them applied in a fixed order.

**How to avoid:** Never close a visibility requirement until the row names its layer. The ordered
sequence in `standards/decision-trees/sharing-selection.md` is OWD → Role Hierarchy → Sharing Rules
→ Teams → Manual/Apex → Restriction/Scoping Rules → Implicit, where every layer after OWD broadens
access except Restriction Rules, which narrow it. Ask the two-part question from `SKILL.md` — can
they open the record at all, versus can they see this field on a record they can already open — and
write the answers as separate rows, because they are configured in separate places. External users
are not a layer in that sequence at all; the tree treats Experience Cloud sharing as a different
world, and a partner-visibility requirement is a licence decision before it is a sharing one.

---

## Gotcha 7: A Reporting Requirement Can Ask for a Join the Report Type Cannot Express

**What happens:** The GM asks for "returns by branch and reason, showing the original order line,
including returns that have no matching order line." It is signed off as a reporting requirement and
sized as an afternoon of report building. During the build the admin discovers the custom report type
cannot be created: the chain runs one object too long, or the "including returns with no matching
order line" clause forces an outer join early in the sequence, after which the remaining joins are
illegal. The requirement is renegotiated in the last sprint, in front of the person who asked for it.

**When it occurs:** On any reporting requirement whose sentence contains "and also show" or
"including the ones without". Both phrases are join instructions in disguise, and neither survives an
arbitrary number of hops.

**How to avoid:** Capture every reporting requirement as base object plus an ordered join chain plus
an explicit answer to "must rows appear when the related record does not exist?" Then check it
against the Metadata API's own constraint on `ObjectRelationship`: "A maximum of four objects can be
joined in a custom report type. When more than two objects are joined, an inner join isn't allowed if
there has been an outer join earlier in the join sequence." Anything reachable by a dotted path from
an already-joined table is a column, not a join — moving lookup parents out of the chain frequently
turns an illegal five-object requirement into a legal two-object one. Prove the chain with
`admin/report-type-strategy` before the number is promised, and mark the row `blocked` until it is
proved.

---

## Gotcha 8: An Integration Requirement Without a Pattern Decision Is Sized as Configuration

**What happens:** "Pull the customer's credit limit from the ERP" is captured as one line in the
catalogue and sized alongside a picklist change. Nobody has asked which direction the data moves, how
fresh it must be, how many rows a day, or who owns the record. In the sprint it turns out to be three
different pieces of work — an authentication story, a nightly ingest, and an error-handling story —
and the picklist-sized estimate has already been committed to a steering committee.

**When it occurs:** When the external system appears in the requirement as a *source of a value*
rather than as a system. Requirements that mention a field ("credit limit", "invoice number",
"stock level") hide the integration; requirements that mention a system name do not.

**How to avoid:** Any requirement whose data does not originate in Salesforce becomes an integration
row carrying four facts before it is sized: direction, latency tolerance, volume per day, and which
system owns the record. Those four facts are exactly what
`standards/decision-trees/integration-pattern-selection.md` needs — Direction 1 for Salesforce
calling out, Direction 2 for external systems writing in, where Q5 routes on volume and Q6 on latency
— and the resulting branch goes in `decision_tree_step`. Record the API arithmetic alongside it: the
Enterprise Edition allocation is 100,000 calls per 24 hours plus (number of licences × calls per
licence type) plus purchased add-ons, with a Salesforce licence contributing 1,000 (*Salesforce
Developer Limits and Allocations Quick Reference*, API Request Limits and Allocations). A requirement
that quietly assumes per-record callouts at scale is visible the moment that number is on the page.

---

## Gotcha 9: The Licence Is Chosen by the Answer to "Who Does This", Not by the Design Review

**What happens:** Discovery captures "distributors should be able to raise their own returns" as a
functional requirement and moves on. Design proceeds on the assumption that a distributor is a user.
Months later, at the point of costing, the persona resolves to an external community licence — and
the design has to change, because external licences do not carry the same object access, the same
sharing model, or the same API allocation as the internal one it was drawn against.

**When it occurs:** Whenever a requirement names a role ("distributor", "customer", "contractor",
"franchisee") rather than a licence, which is almost always. It is worst on projects where the portal
is a later phase, because the phase-1 design silently assumes internal users.

**How to avoid:** Add a `licence_implication` value to every row whose actor is not a payroll
employee, and escalate the row to `architect/license-optimization-strategy` rather than resolving it
in discovery. The number that makes this concrete early is the per-licence API allocation, which
differs by an order of magnitude between internal and external users: per 24 hours, a Salesforce
licence contributes 1,000 calls in Enterprise Edition and 5,000 in Unlimited/Performance, while
Customer Community contributes 0, Customer Community Login 0, Customer Community Plus 200, Partner
Community 200, and Partner Community Login 10 (*Salesforce Developer Limits and Allocations Quick
Reference*, API Request Limits and Allocations). A portal requirement that also expects API traffic
is a costing conversation on day one, not after the site is built. Route the requirement itself to
`admin/portal-requirements-gathering`.

---

## Gotcha 10: "Same As Today" Requirements Migrate the Workaround, Not the Process

**What happens:** The As-Is capture records a `HOLD?` column, a status called "Pending — Do Not
Touch", or a rule that every record must be saved twice. These arrive in the To-Be as a checkbox, a
picklist value, and a validation rule, because "the users are used to it." None of them describe a
business rule. They describe compensations for a limitation of the tool being replaced — a
spreadsheet with no locking, a legacy CRM with no approval, a form that lost data on the first save.
The new org inherits the scar tissue and, with it, the reason nobody trusts the data.

**When it occurs:** In every migration from a spreadsheet or an ageing system, and especially when
the person interviewed is the person who invented the workaround. It is invisible in the interview
because the workaround is described in exactly the same tone as the genuine rules around it.

**How to avoid:** Tag every As-Is step keep / drop / replace as it is captured, and for anything
tagged keep, ask one question: "if the new system did that for you, would you still need this step?"
A step that survives is a business rule. A step that does not is a workaround, and it is recorded as
a `descoped` row with a note saying what it compensated for — not deleted, because the person who
invented it will ask where it went. Any step whose purpose nobody present can explain is `blocked`
with a named owner and a decision date, not carried forward as a field. A field built for a rule
nobody can state is a field nobody will ever be able to retire.
