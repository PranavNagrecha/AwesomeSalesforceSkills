# Gotchas — Scoping Rules

Non-obvious Salesforce platform behaviours that cause real production problems when working with scoping rules.

## Gotcha 1: The Rule Is Active and Correct, and Nothing Is Filtered

**What happens:** An admin builds a scoping rule, activates it, logs in as an affected user, opens a list view, and sees exactly the same records as before. Nothing errors. Nothing warns. The Setup page shows the rule as active. The natural conclusion — that the criteria are wrong — is usually false, and hours get spent rewriting a `recordFilter` that was fine.

**Why:** The scope is opt-in on the two surfaces a human actually looks at. Salesforce's surface table gives List Views and Reports the same behaviour — "Applied in Lightning Experience if **Filter by scope** is selected" — while SOQL gets a different one: "Applied, unless a scope other than scopingRule is specified." The `ListView` metadata type says it again from the other direction: the `ScopingRule` value of `filterScope` means "Records that meet a scoping rule's record criteria. In Lightning Experience, scoping rules are applied to list views only if the user selects **Filter by scope**." So the rule was working the whole time — in SOQL, where nobody was looking.

**How to avoid:** Treat rule activation as step one of two. Step two is wiring the surfaces: "for list views and reports, you can apply the scope through Metadata API (using the filterScope field on the ListView type and the scope field on the Report type)". Set `filterScope` to `ScopingRule` on every list view the affected users start their day in, and set `scope` on the corresponding reports. Verify by logging in as a user matched by `userCriteria` — not by reading the Setup page, which will look identical either way. If you want a fast confirmation the rule itself is sound before touching any list view, run a SOQL query as the affected user and compare it against the same query with `USING SCOPE everything`.

---

## Gotcha 2: You Cannot Disable the Rule First

**What happens:** A rule needs to come out. The admin does the obvious thing and deactivates it, and every list view and report that was pointing at it is left both non-functional and non-editable — there is no UI path back to clear the setting and repair them.

**Why:** The dependency runs from the list view and report *to* the rule, not the other way round, and the documented consequence is harsher than "unexpected state". The considerations page gives both halves in two sentences: "To disable a scoping rule, first delete the list views and reports that have **Filter by scope** selected. After a scoping rule is disabled, the list views and reports aren't functional nor modifiable." Note the instruction is *delete*, not *edit* — and note the second sentence, which is why: after the rule goes, the dependent views can no longer be modified, so the window to unwind them closes at the moment of disabling.

**How to avoid:** Reverse the build order on the way out. Enumerate every list view with `filterScope` set to `ScopingRule` and every report with the corresponding `scope` on the target object, delete or re-point them first — Salesforce's word is delete — and only then disable the rule. Build the enumeration while you are creating the rule, not while you are removing it — there is no Setup page that lists "list views that reference this scoping rule", so if you did not write it down you will be grepping metadata. The same asymmetry applies to the components the criteria depend on: deleting a custom permission or a picklist value that a rule references breaks the dependent rule.

---

## Gotcha 3: Hardcoded Org IDs Break on Every Environment Hop

**What happens:** A rule that works perfectly in a sandbox is deployed to production and silently applies to nobody, or to the wrong population. `userCriteria` such as `$User.UserRoleId = '00Exxxxxxxxxxxx'` deploys cleanly — the ID is a valid string, the metadata is well-formed, the deploy succeeds — and then matches zero users because that role ID does not exist in the destination org.

**Why:** Role, profile and record type IDs are org-specific. The documented examples themselves use raw IDs (`$User.UserRoleId = '00Exxxxxxxxxxxx'`, `Agent__c.Owner:User.ManagerId=001xx000003HNy7, 001xx000003HNut`) because the criteria language has no name-based equivalent for these references. Salesforce's considerations call this out directly: org-specific IDs for roles, record types and profiles require modification when deploying between sandboxes or to production if the values differ. Nothing in the deploy pipeline checks that an ID resolves.

**How to avoid:** Keep an explicit ID remap table alongside the `.rule` file, one column per environment, and make remapping a required step in the deploy runbook rather than something the deployer is expected to remember. Where the criterion can be expressed against a durable attribute instead of an ID — a custom permission, a custom User field, `$User.Department` — prefer that; those survive promotion unchanged. After every deploy, verify as a user who *should* match, because a rule matching nobody looks exactly like a rule that is working.

---

## Gotcha 4: Salesforce Reserves the Right to Turn Your Rule Off

**What happens:** A rule that has been in production for months stops taking effect. No release update, no admin action, no deploy. Users start seeing the unscoped record set again and nobody can explain why.

**Why:** The considerations page states it plainly: "Salesforce reserves the right to disable a scoping rule if a rule you create is inefficient or if your data model has so much data that scoping rules cause slowness when applied." The scope is evaluated on every list view render, report run and unqualified SOQL query against the target object, so an expensive `recordFilter` — particularly one built on the SOQL operator that traverses a junction object across a large table — multiplies out fast as data grows. A rule that was cheap at 200,000 records is not necessarily cheap at 5,000,000.

**How to avoid:** Measure before you ship, and design so the criterion is selective and indexable. Salesforce's own guidance is to test in a sandbox before production and to test the SOQL performance through an API client to predict how efficient the rule will be — do this in a full sandbox with production-scale data, because a scratch org or a developer sandbox will tell you nothing about the shape of the query at volume. Run the subquery standalone as the affected user first; if it is slow on its own it will be slow as a rule. Treat "is this rule still active" as a monitored condition on high-volume objects rather than an assumption. This behaviour has no numeric threshold published, so there is no limit you can design against — only headroom. `[STALE-RISK: re-read the Considerations for Scoping Rules page for any published efficiency threshold or Setup-visible warning that Salesforce adds later.]`

---

## Gotcha 5: `USING SCOPE EVERYTHING` Is Mandatory in Nested Subqueries, Not Just the Outer One

**What happens:** A SOQL-operator `recordFilter` is written with `USING SCOPE EVERYTHING` on the outer `SELECT` and the nested `SELECT` inside the `IN (...)` is left plain, because that is exactly what Salesforce's own worked example does. The stated rule says that is wrong. The example says it is fine. One of them is going to be true in your org and the documentation will not tell you which.

**Why:** Two constraints stack. First, "the SELECT statement, including nested SELECT statements, must include USING SCOPE EVERYTHING" — the requirement is explicitly recursive. Second, and this is the mechanism rather than the rule: the surface table says SOQL is scoped by default, "unless a scope other than scopingRule is specified". A subquery inside a scoping rule's own criteria is itself a SOQL query against a scoped org, so without an explicit override it would be filtered by the very rule being defined. `EVERYTHING` is the escape hatch, and it has to appear at every level because every level is a query.

**How to avoid:** Put `USING SCOPE EVERYTHING` on every `SELECT`, including nested ones. That satisfies the stated rule and is a strict superset of the documented example, so it is correct under either reading — but treat a mismatch as a flag to verify in the org rather than as proof of a broken rule, because the platform's own example ships with the mismatch. When reviewing, count the `SELECT` keywords and count the `USING SCOPE EVERYTHING` occurrences. Two further constraints travel with it and are easy to trip on the same line: "USING SCOPE EVERYTHING is the only valid scope clause syntax for scoping rules" (no `mine`, no `team`), and "the SOQL operator doesn't support $User syntax except for $User.Id" — so `$User.Department` is legal in a plain comparison filter and illegal inside a SOQL operator. Also note "the SOQL query object and the scoping rule target entity can't be the same object", which rules out the tempting self-referential filter.

```text
SOQL(Id, SELECT AccountId FROM BranchUnitCustomer USING SCOPE EVERYTHING WHERE BranchUnitId IN(SELECT CurrentBranchId From Banker WHERE UserOrContactId = $User.Id))
```

Count them in that string: two `SELECT` statements, one `USING SCOPE EVERYTHING`. It is Salesforce's own published example, it appears in that form on both quick-start pages and for both the Account and the Lead variant, and it does not satisfy the sentence printed a few paragraphs above it. Every single-`SELECT` example in the documentation does satisfy it, so there is no published example that both nests and complies. Write the compliant form; verify in a sandbox before you trust either reading. `[STALE-RISK: if Salesforce corrects the nested example or the prose, this gotcha collapses into a plain rule — recheck both quick-start pages.]`

---

## Gotcha 6: Scoping Narrows Duplicate Detection Even When the Duplicate Rule Says Not To

**What happens:** A duplicate rule is deliberately configured with *Bypass sharing rules* so that a user creating a record is warned about duplicates they cannot themselves see — the standard pattern for preventing duplicate Accounts across regional teams. After a scoping rule goes live, that warning stops appearing for some duplicates, and duplicate records start accumulating.

**Why:** Salesforce's considerations state that "scoping rules limit the potential duplicates that are shown, even when Bypass sharing rules is turned on." The bypass is a sharing-model bypass. The scope is not the sharing model, so the bypass does not reach it. This is the one place where a feature documented as having no effect on access has a visible effect on a data-quality control.

**How to avoid:** Inventory the duplicate rules on any object before you scope it, and specifically flag any that rely on *Bypass sharing rules*. If cross-scope duplicate detection is a real requirement, the scoping rule and the duplicate rule are in conflict and you must decide which one wins — narrowing the scoping rule's `userCriteria` so it does not apply to the users who create records is usually the cheaper fix. See `admin/duplicate-management` for the duplicate rule side of this. Test the interaction with a real duplicate that falls outside the scope; this will not show up in a criteria review.

---

## Gotcha 7: Object Manager Cannot Express Half the Feature

**What happens:** An admin is told the rule is straightforward, opens Object Manager, and finds there is no way to enter the criterion the design calls for. Or worse, an approximation is entered that compiles and matches the wrong records.

**Why:** The Setup editor and the API do not expose the same capability. "You can use a SOQL operator in record criteria only when creating scoping rules via the API." Object Manager builds comparison criteria; anything requiring a junction hop, a subquery, or an `IN (...)` against a related object is API-only. Salesforce documents both paths as equals — "create and manage scoping rules by navigating to a supported object in the Object Manager. Or use the RestrictionRule Tooling API object or RestrictionRule Metadata API type" — without flagging on that page that one path is a strict subset of the other.

**How to avoid:** Make the comparison-vs-SOQL-operator decision during design, before anyone opens Setup, because it determines the whole build path. If the criterion is `Field = $User.Field`, Object Manager is fine and faster. If the criterion has to traverse anything, plan for a `.rule` file and a deploy from the start. A related asymmetry catches people in the same session: several field shapes are simply unsupported in criteria regardless of path — IsPersonAccount fields on Account are not supported ("don't use IsPersonAccount fields such as PersonDepartment or PersonLeadSource in record filter criteria"), dot-notation lookups are limited to one level, owner references must be typed (`Owner:User`), and Salesforce says outright not to create rules on `Event.IsGroupEvent`.

---

## Gotcha 8: The Edition Banner and the Limits Text Disagree About Developer Edition

**What happens:** A team checks whether their Developer edition sandbox supports scoping rules, reads the availability banner, concludes it does not, and abandons a design that would have worked.

**Why:** The two official pages carry different edition lists. The Scoping Rules overview page states "Available in: Lightning Experience in **Performance**, **Unlimited**, and **Developer** editions." The Considerations page's banner states "Available in: Lightning Experience in **Performance** and **Unlimited** Editions" — while the body of that same page then gives a Developer-edition limit: "Create up to two active scoping rules per object in Developer editions." A banner that omits an edition the same page then sets a limit for is an internal inconsistency in the documentation, not a behaviour difference.

**How to avoid:** Treat the overview page and the limits sentence as the stronger evidence — both name Developer edition, and a published per-object cap for an edition is hard to read as anything other than support for that edition. Then confirm in the actual org rather than arguing from documentation: open Object Manager on a supported object and look for the Scoping Rules node. Note also that Enterprise edition appears in neither scoping-rule list, though it does appear in the restriction-rule limits ("Enterprise/Developer Editions: up to 2 active rules per object") — so do not infer scoping-rule availability in Enterprise from a restriction-rule page. `[STALE-RISK: edition availability for scoping rules is exactly the kind of thing a seasonal release changes; re-check both the overview and considerations banners before quoting an edition list.]`

---

## Gotcha 9: One Operator. No AND. No OR.

**What happens:** A requirement arrives with two conditions — "reps should land on open opportunities in their own region". The criteria box accepts free text, the syntax looks like SOQL, so the author writes something with an `AND` in it. It either refuses to save, or it saves and scopes to something nobody asked for.

**Why:** The criteria language is not a query language. Salesforce's considerations state it in one line: "Unless you use SOQL, scoping rules support only the EQUALS operator. The AND and OR operators aren't supported." That is the same operator budget restriction rules get — the two features differ on almost everything else, but not on this. The only concession is multi-value equality on the right-hand side: "Comma-separated ID or string values are supported in the Record Criteria field", which behaves like an OR across values of *one* field, not across fields. Nulls are excluded as well: "Including a null or blank value in record criteria isn't supported and can result in unexpected behavior."

**How to avoid:** Decide the shape of the criterion during design, not in Setup. One field equals one value (or one comma-separated list of values) is the whole declarative surface. For a genuine two-condition requirement there are two honest routes: precompute the combination into a formula or workflow-maintained field on the record and match that single field, or move to the SOQL operator, accept that the rule becomes API-only, and put the extra conditions in the subquery's `WHERE` clause. If a stakeholder is promised a compound criterion in a Setup click-path, that promise is already broken.

---

## Gotcha 10: The Scope Reaches Less Far Than the Surface Table Suggests — and Once Further

**What happens:** A rule is live and wired, list views behave, and then the complaints arrive from the edges. A related list on the parent record still shows everything. A report combining two objects filters more than expected. A rule built on Account is assumed to cascade to its Contacts and does not. And a banker's `SOQL(...)` filter on Task is rejected outright even though Task is on the supported-object list.

**Why:** Four separate statements in the considerations page, none of which appear in the three-row surface table:

- "Creating a scoping rule for an object impacts only that object and doesn't affect child objects."
- "In related lists, all associated records that a user can access are visible, regardless of scope, except in the contact role related list." A contact scoping rule *does* reach the contact role related list on account, opportunity, case and contract records — "So it's possible that users, such as members of a sales team, see a filtered set of contact roles without knowing that the list is filtered."
- "In reports that contain data for multiple objects, all relevant scoping rules are applied when **Filter by scope** is selected." Two objects in one report means two rules applied, not one.
- "These objects aren't supported in the SOQL operator": ActivityHistory, Attachments, Event, EventAttendee, Note, OpenActivity, tag objects, and Task. Event and Task are scopeable target entities *and* barred from the subquery — the two lists are independent and the overlap is a trap.

**How to avoid:** Treat the surface table as the list of places a scope is *applied by user choice*, not as the boundary of the feature's effects. Before shipping, walk the parent objects that carry a related list of the scoped object and confirm the behaviour is what the stakeholder expects — silent filtering of contact roles is the one that produces "the customer contact vanished from the opportunity" tickets. Check whether any report crosses objects that each carry a rule. And if the design needs a junction hop from Event or Task, stop: that criterion cannot be expressed at all, and the answer is a different field on the record, not a cleverer subquery.

