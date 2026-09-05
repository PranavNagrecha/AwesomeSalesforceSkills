# Gotchas — Territory Design Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Each one is something a territory *design* can get wrong on paper, weeks before anyone opens Setup.

Grounding convention: quoted sentences are from the Metadata API Developer Guide
(`https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf`) or the Object
Reference (`.../object_reference.pdf`), section named inline.

---

## Gotcha 1: The "Date Fields Are Not Valid Criteria" Rule Is Folklore — But Date Criteria Still Rot

**What happens:** A territory design document specifies date-based segmentation ("assign the account
to the Renewal Q2 territory when `Contract_Renewal_Date__c` falls between April 1 and June 30").
Either the builder cannot configure it, or — worse — they can, and the assignment is correct on the
day the rules run and progressively wrong every day after.

**When it occurs:** Whenever a requirements document treats a date as a coverage dimension.

**UNVERIFIED (2026-09-05):** the widespread claim that ETM assignment rules *reject* Date and
DateTime fields outright is not stated anywhere in the Metadata API Developer Guide or the Object
Reference. `Territory2RuleItem` › `field` is documented only as "The standard or custom object field
that the rule item operates on," with no type restriction, and the `operation` enum includes
`lessThan`, `greaterThan`, `lessOrEqual` and `greaterOrEqual` — the comparisons a date range needs.
Confirm the behaviour in a sandbox before either asserting or denying it in a design document.

**How to avoid:** The design argument does not depend on the disputed restriction. Assignment rules
"run automatically when object records are created and edited" (`Territory2Rule` › `active`) — they
are not re-evaluated because a date passed. A date predicate is therefore only as fresh as the last
record edit or the last manual rule run. Specify a derived picklist (`Renewal_Quarter__c`, populated
by a record-triggered Flow) so that the *field value changing* is what re-triggers evaluation. That
holds whether or not the platform would have accepted the date.

---

## Gotcha 2: Overlapping Assignment Rule Criteria Assign an Account to Every Matching Territory

**What happens:** Two territories have rules that can match the same account — `BillingState equals
CA` on one, `AnnualRevenue greaterThan 1000000` on another. A large Californian company matches
both and gets an `ObjectTerritory2Association` row for each. Both reps hold access, both managers
see it, and if the two territories share a territory *type*, the opportunity is assigned to neither.

**When it occurs:** When requirements do not state the mutual-exclusivity constraint for primary
coverage. Overlays create multi-territory assignment on purpose; primary coverage almost never does.

**How to avoid:** State the constraint per hierarchy level in the design, and make it structural
rather than aspirational: give every primary rule a discriminating item (a segment picklist, a
named-account flag set to false) so the criteria cannot both be true. Then write the acceptance test
that proves it — `references/worked-examples.md` §7 test 3 groups
`ObjectTerritory2Association` by `ObjectId` over the geo territory Ids and expects zero rows with a
count above one. Where multi-territory coverage *is* the requirement, express it as a separate
territory type with its own unique priority, so opportunity assignment stays deterministic.

---

## Gotcha 3: Territory Type Priority Runs the Opposite Way, and a Tie Assigns Nothing

**What happens:** A design gives the named-account type priority `5` and the geographic type `10`,
with a note that "lower is higher priority." After activation, opportunities on named accounts
forecast into the geographic rep's territory instead. In a second variant, two named-account books
share the type, an account lands on both, and the opportunity ends up with **no** territory at all —
so it vanishes from every territory forecast rather than appearing in the wrong one.

**When it occurs:** Any hybrid design. The direction is counter-intuitive because most Salesforce
priority fields (assignment rules, escalation rules, matching-rule order) run lowest-first.

**How to avoid:** The Metadata API Developer Guide and the Object Reference say the same thing on
`Territory2Type` › `priority`: "The account-assigned territory whose territory type priority is
highest is then assigned to the opportunity. The `priority` field value on each territory type must
be unique. Further, if there are multiple territories with the same territory type (and therefore
the same priority) assigned to the account, no territory is assigned to the opportunity." Three
requirements follow: give the type that should win the **largest** integer; make every type's
integer unique; and prove that no account can land in two territories *of the same type*. The third
is the one designs forget, and it is silent — nothing errors, the opportunity is simply unassigned.
Space the integers (10 / 20 / 30 / 40) so a type can be inserted later without renumbering.

---

## Gotcha 4: Territory Access Cannot Restrict Below the Org-Wide Default

**What happens:** A requirements document states "sales reps should only see accounts in their
assigned territory." The org's Account OWD is Public Read/Write. ETM is configured exactly as
designed, and every rep still sees every account, because territory membership only ever adds.

**When it occurs:** When coverage and access are written as one requirement without checking the
sharing baseline. It also shows up inverted at deploy time: with a Public Read/Write account model
"valid values are only `Edit` and `All`" for `accountAccessLevel`, so a design that specified `Read`
is rejected by the deploy rather than merely ineffective.

**How to avoid:** Read the access-level definitions literally — a territory grants access to records
"that are assigned to this territory and are otherwise inaccessible" (`Territory2` ›
`accountAccessLevel`). "Otherwise inaccessible" is the whole mechanism: where the OWD already grants
it, the territory adds nothing. Capture the four current OWDs (Account, Opportunity, Contact, Case)
as a pre-condition in the requirements document and route any restriction requirement to
`admin/sharing-and-visibility` as an OWD change with its own risk assessment. Note also that
`Territory2ObjSharingConfig` is **not** the mechanism for account or opportunity access — it is a
read-mostly SOAP object (API 56.0+) hanging off `TerritoryMgmtObjectConfig` for the objects enabled
via `Territory2Settings.supportedObjects`, where the guide states "The only supported object type is
`Lead`."

---

## Gotcha 5: Rules Are Not Retroactive, and Metadata API Cannot Run Them

**What happens:** After go-live, a new Southwest territory and its rules are added and deployed. The
deploy succeeds. Accounts in Arizona and New Mexico stay where they were: the new rep sees nothing,
and the Southwest forecast is empty. Nothing failed, so nothing raised an alert.

**When it occurs:** Any time rules are added or edited on a model that is already Active — which is
every realignment. Rules "run automatically when object records are created and edited"
(`Territory2Rule` › `active`); a change to the *rule* is not a change to the *record*, so no
evaluation is triggered. And the deploy cannot fix it: "Rules can't be run via Metadata API"
(`Territory2Rule` › Usage).

**How to avoid:** Treat the rule run as a named, owned, scheduled step in the requirements document,
not an implementation detail — a person holding Manage Territories, a window, and a completion check
that reads `Territory2AlignmentLog` (Object Reference, API 54.0+; carries `StartTime`, `EndTime`,
`Status`, `RunAsId`, and a null `Territory2Id` when the run was for the whole model) rather than
eyeballing the model page. `references/worked-examples.md` §6 shows the step in a realignment
runbook.

---

## Gotcha 6: Ten Rule Items Is a Hard Ceiling, and Their Order Is Load-Bearing

**What happens:** A design lists fourteen countries as fourteen `equals` conditions on one rule. It
cannot be built. In the repair, someone reorders the surviving items to read more naturally, and a
`booleanFilter` of `(1 AND 2) OR 3` silently starts meaning something else.

**When it occurs:** Whenever segmentation is expressed as an enumeration rather than a set. The
ceiling is documented as a property of the rule: "A territory rule can have up to 10 rule items"
(`Territory2Rule` › Usage).

**How to avoid:** Count rule items in the design, per rule, and treat the count as a review column
in the assignment-rule matrix. Collapse enumerations with the `includes` operation and a
semicolon-delimited value (`US;CA;MX;BR;AR`) rather than one item per value; where more than ten
genuinely distinct predicates are needed, the requirement is a proxy field on Account, not a rule.
Two related constraints belong in the same review: "The sort order of rule items is implicitly
derived from the position of the rule items in the XML," so item order is data, not formatting; and
`booleanFilter` numbering "must start at 1 and must be contiguous," so a deleted item invalidates
the filter rather than shifting it.

---

## Gotcha 7: Three Separate Switches Stop Rules From Evaluating a Record, All Silently

**What happens:** Assignment rules run, the alignment log reports success, and a specific set of
accounts is still unassigned. The rules are correct. The accounts were never offered to them.

**When it occurs:** Three documented mechanisms suppress evaluation independently, and none of them
raises an error:

- `IsExcludedFromRealign` on the record — active rules run on create and edit, with "the exception
  … when the value of the `IsExcludedFromRealign` field on an object record is true, which prevents
  record assignment rules from evaluating that record" (`Territory2Rule` › `active`; the Object
  Reference repeats it on `ObjectTerritory2AssignmentRule` › `IsActive` for accounts).
- `Territory2Settings.tm2BypassRealignAccInsert` (API 53.0+) — "If true, account assignment rules
  don't run during account insert jobs." Org-wide, and usually inherited from whichever org the
  settings file was copied from.
- `Territory2ObjectExclusion` (Object Reference, API 54.0+) — "Represents the objects that aren't
  included in territory assignment rule runs, even when they meet assignment rule criteria," scoped
  per account and per territory.

**How to avoid:** Make all three explicit in the requirements document rather than discovering them
in triage. Ask whether any data-load process sets `IsExcludedFromRealign`; ask for the current value
of `tm2BypassRealignAccInsert` in the org whose settings will be inherited (a data load run with it
true will assign nothing and report success); and record whether `Territory2ObjectExclusion` rows
exist as a deliberate carve-out, because a design that assumes full coverage plus an undocumented
exclusion list produces a coverage gap nobody can find in the rules.

---

## Gotcha 8: Archiving Is One-Way, and an Archived Model Blocks Its Own Name Forever

**What happens:** A design says "we re-cut the model each year and archive the old one." Year two,
the sandbox has `Territory_Model` in `Planning` and production has `Territory_Model` in `Archived`.
The deploy fails and cannot be made to succeed under that name.

**When it occurs:** Any realignment cadence that reuses a model developer name, and any rollback
plan that assumes an archived model can be brought back. Deploy is permitted only for models in
`Planning` or `Active`: "sometimes you can have a model in `Planning` state on a sandbox org, and a
model with the same developer name in `Archived` state on your production org. The `deploy()`
operation on production fails because that model's state is `Archived` and that state prevents
changes to the model" (`Territory2Model` › Usage). Deleting instead of archiving is not an escape —
`delete()` "changes the model's state to `Deleting` and cascade deletes all territories, rules, and
user associations in the model."

**How to avoid:** Two lines in the requirements document. First, developer names carry the cycle:
`FY26_Alignment`, `FY27_Alignment`. Second, the rollback position is *"do not archive the outgoing
model until the new one has closed a forecast period"* — an un-archived model in `Planning` can be
re-activated; an archived one cannot. While you are there, note that the `State` picklist is wider
than the three states everyone designs against — `Planning`, `Activating`, `Activation Failed`,
`Active`, `Archiving`, `Archiving Failed`, `Archived`, `Deleting`, `Deletion Failed` (Object
Reference, `Territory2Model` › `State`) — so a cutover checklist that tests only for `Active`
reports a stuck `Activating` as a clean failure to activate.

---

## Gotcha 9: The Release Path Is Decided Before the Design Is: No Change Sets, No Packages

**What happens:** A territory design is signed off with a release plan that reads "promote via change
set with the Q3 release." At build time the components cannot be added to the change set at all,
and the release slips while a source-deploy path and a Manage Territories holder are arranged.

**When it occurs:** In orgs whose entire delivery process is change-set based. Every Sales Territories
metadata type repeats the same Usage sentence — "Sales Territories components don't support packaging
or change sets and aren't supported in CRUD calls" (`Territory2`, `Territory2Model`, `Territory2Rule`,
`Territory2Type`). Unlocked packaging additionally "requires packages without a namespace."

**How to avoid:** Capture the release mechanism as a requirement, not an implementation choice: a
source deploy, run by a named person who holds **Manage Territories** (required for `deploy()` on all
territory management entities), plus the separate manual rule run afterwards. Retrieval has its own
trap worth noting in the same paragraph — `retrieve()` without Manage Territories "returns only
entities that belong to a `Territory2Model` in `Active` state," so a baseline pulled by an
under-permissioned service user is partial and silently so. The mechanics live in
`admin/enterprise-territory-management`; what belongs *here* is that the design cannot promise a
delivery date on a path that does not exist.

---

## Gotcha 10: Membership Rows Cannot Be Updated, and Inactive Ones Persist

**What happens:** A design's coverage maths — territories per user, users per territory — is
computed from a `UserTerritory2Association` row count after go-live and comes back inflated. Reps who
moved territories mid-year still have rows. A separate attempt to "correct" a rep's role in a
territory by updating the association fails outright.

**When it occurs:** From the first membership change onward. `UserTerritory2Association` supports
`create()`, `delete()`, `describeSObjects()`, `query()` and `retrieve()` — there is no `update()`
in its supported-call list (Object Reference). It also "doesn't support adding custom fields," so
there is nowhere on the row to record why a membership exists. `IsActive` distinguishes whether the
user is active in that territory, and `RoleInTerritory2` takes `Owner`, `Administrator` or
`Sales Rep`.

**How to avoid:** Write the membership model as a *set of rows to create and delete*, not as records
to edit, and say so in the realignment runbook — a role change is a delete plus a create, and it
loses whatever history the row carried unless `UserTerritory2AssocLog` is enabled (API 57.0+, gated
on `Territory2Settings.tm2EnableUserAssignmentLog` and on activating a model to start tracking). Any
ratio or coverage query in the acceptance tests must filter `IsActive = true`, or it counts people
who left the territory months ago. Where the design delegates membership changes to regional
managers rather than a central admin, that is `TerritoryAdminAssignment` (API 63.0+) with
`CanManageMembers` true and `CanManageHierarchy` false, and the delegates need the Administer
Territory Operations permission.
