# LLM Anti-Patterns — Scoping Rules

Common mistakes AI coding assistants make when asked to build, review, or explain a Salesforce scoping rule. These patterns help the consuming agent self-check its own output before returning it.

## Anti-Pattern 1: Answering With the SOQL `USING SCOPE` Clause Instead of the Setup Feature

**What the LLM generates:** Asked "how do I create a scoping rule", it returns `SELECT Id FROM Account USING SCOPE mine`, or an explanation of the eight `filterScope` values, or Apex that scopes a selector method. The answer is coherent, correct about something, and about a completely different feature.

**Why it happens:** The two features share the word "scope", and the query clause has far more training-data volume — every Apex tutorial, every selector pattern, every SOQL reference page. Retrieval systems make the same error: this repo measured the query "create a scoping rule" routing to the SOQL clause skill, which is what this package exists to correct. The features do touch at one point (`USING SCOPE scopingRule`), which makes the wrong answer feel adjacent rather than wrong.

**Correct pattern:**

```text
"Scoping rule"  = a Setup / Metadata API feature.
                  RestrictionRule with enforcementType = Scoping.
                  Deployed from restrictionRules/*.rule.
                  Built in Object Manager or via Tooling/Metadata API.
                  → admin/scoping-rules

"USING SCOPE"   = an optional SOQL clause, placed after FROM and before WHERE.
                  Values: mine, everything, team, delegated, my_territory,
                  my_team_territory, mine_and_my_groups, scopingRule.
                  → apex/soql-using-scope-clause

They meet at exactly one value: USING SCOPE scopingRule, which asks a query
to honour whatever scoping rule the admin activated on that object.
```

**Detection hint:** If the user's words include "rule", "create", "Setup", "Object Manager", "deploy", "admin", or "default view", they want the Setup feature — a SOQL snippet is the wrong artefact. If the user's words include "query", "SELECT", "Apex", "selector", or "WHERE", they want the clause.

---

## Anti-Pattern 2: Inventing a `ScopingRule` Metadata Type

**What the LLM generates:** A `<ScopingRule>` root element, a `scopingRules/` source directory, a `.scopingRule-meta.xml` suffix, `<name>ScopingRule</name>` in `package.xml`, or a Tooling API `POST` to `/tooling/sobjects/ScopingRule`. None of these exist. All of them look exactly like the real thing.

**Why it happens:** Salesforce metadata type names are overwhelmingly regular — the feature is called X, the type is called X, the folder is the camelCase plural. The model generalises, and here the generalisation is wrong: the feature name and the type name diverge because one metadata type carries two features.

**Correct pattern:**

```xml
<!-- force-app/main/default/restrictionRules/SR_Department_A_Contacts.rule-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<RestrictionRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <description>View contacts from Department A.</description>
    <enforcementType>Scoping</enforcementType>
    <masterLabel>SR for Department A contacts</masterLabel>
    <recordFilter>Department=$User.Department</recordFilter>
    <targetEntity>Contact</targetEntity>
    <userCriteria>$User.UserRoleId = '00Exxxxxxxxxxxx'</userCriteria>
    <version>1</version>
</RestrictionRule>
```

```xml
<types>
  <members>*</members>
  <name>RestrictionRule</name>
</types>
```

Root element `RestrictionRule`. Folder `restrictionRules`. Suffix `.rule`. `enforcementType` is the only thing that makes it a scoping rule.

**Detection hint:** Grep generated output for the string `ScopingRule` outside two legitimate contexts: the `enforcementType` value is `Scoping` (not `ScopingRule`), and `ScopingRule` is correct as a `ListView.filterScope` value and as the SOQL `scopingRule` scope. Anywhere else — a type name, a folder, a file suffix, a Tooling API path — it is fabricated.

---

## Anti-Pattern 3: Presenting a Scoping Rule as a Security Control

**What the LLM generates:** In response to "stop the support team seeing HR cases", "hide investigated claims from ordinary handlers", or "team A must not see team B's accounts", a scoping rule design — often a good one, with sound criteria — described in language like "this ensures users only see their own records" or "restricts visibility to the assigned region".

**Why it happens:** The feature genuinely does hide records from a view, and the demo is convincing. The word "restriction" is in the metadata type name. Salesforce Setup places the two features side by side. And the model has no signal that the user's requirement was confidentiality rather than tidiness, because the user rarely says so.

**Correct pattern:**

```text
Ask first: "if the user deliberately goes looking, is it acceptable that
they find the record?"

  YES  → scoping rule. Focus / productivity requirement.
  NO   → NOT a scoping rule. Sharing model, or admin/restriction-rules.

Quote the platform, do not paraphrase it:
  scoping rules "don't restrict the access that your users have to
  records. Your users can still open and report on all the records that
  they can access according to your org's sharing settings."

Three concrete holes to name when refusing:
  - the user can select a different scope on any list view or report
  - Search and SOSL are absent from the scoping surface table entirely
  - a direct record link opens the record normally
```

**Detection hint:** If the generated answer proposes a scoping rule and the prompt contained "must not", "prevent", "hide", "confidential", "compliance", "GDPR", "audit", "segregation", or "PII", the answer is wrong regardless of how good the criteria are. Refuse and route, do not caveat.

---

## Anti-Pattern 4: Declaring the Work Complete at Rule Activation

**What the LLM generates:** A five-step build — design criteria, create the rule, set `userCriteria`, activate, done — with no mention of `filterScope`, `scope`, or **Filter by scope**. The generated rule is often correct. The user deploys it, sees no change, and concludes the criteria are broken.

**Why it happens:** In almost every other Salesforce feature, activation is the last step: an active validation rule validates, an active flow runs, an active sharing rule shares. Scoping rules break that pattern on two of their three surfaces, and the pattern is strong enough in training data to override the specific case.

**Correct pattern:**

```text
Salesforce's own surface table:

  List Views  → "Applied in Lightning Experience if Filter by scope is selected"
  Reports     → "Applied in Lightning Experience if Filter by scope is selected"
  SOQL        → "Applied, unless a scope other than scopingRule is specified"

So an active rule is invisible to a human until the views are wired:
  - ListView metadata: <filterScope>ScopingRule</filterScope>
  - Report metadata:   the <scope> field
  - or the user selects Filter by scope themselves, each time

Always end a build with: "verify by logging in as a user matched by
userCriteria — the Setup page looks identical whether this worked or not."
```

**Detection hint:** A generated scoping-rule procedure that never contains the string `filterScope`, `Filter by scope`, or a report `scope` step is incomplete. Add the wiring step and the log-in-as verification.

---

## Anti-Pattern 5: `USING SCOPE EVERYTHING` on the Outer Query Only

**What the LLM generates:** A SOQL-operator `recordFilter` where the outer `SELECT` carries `USING SCOPE EVERYTHING` and the nested `SELECT` inside `IN (...)` does not — or a version using `USING SCOPE mine`, or `$User.Department` inside the operator.

**Why it happens:** The clause reads like a query-level modifier, so applying it once at the top looks sufficient — and here the training data is genuinely misleading rather than merely thin: Salesforce's own nested example carries `USING SCOPE EVERYTHING` on the outer `SELECT` only, contradicting the sentence printed above it. A model that copies the example reproduces the non-compliant form faithfully. Separately, `$User.Department` is valid in a plain comparison filter on the very same object, so the model reasonably assumes it is valid everywhere in the criteria language.

**What this means for review:** generate the compliant superset (the clause on every `SELECT`), but do not report the documented form as a defect in someone else's metadata without saying that Salesforce publishes it that way. See `gotchas.md` Gotcha 5 and the Contradiction Log in `well-architected.md`.

**Correct pattern:**

```text
SOQL(Id, SELECT AccountId FROM BranchUnitCustomer USING SCOPE EVERYTHING
     WHERE BranchUnitId IN(SELECT CurrentBranchId From Banker
                           WHERE UserOrContactId = $User.Id))

Rules, all four from the same page:
  - "The SELECT statement, including nested SELECT statements, must
     include USING SCOPE EVERYTHING"
  - "USING SCOPE EVERYTHING is the only valid scope clause syntax for
     scoping rules"  → no mine, no team, no my_territory
  - "The SOQL operator doesn't support $User syntax except for $User.Id"
     → $User.Department is legal in a comparison filter, illegal here
  - "In SOQL operators, the SOQL query object and the scoping rule
     target entity can't be the same object"
  - "These objects aren't supported in the SOQL operator": ActivityHistory,
     Attachments, Event, EventAttendee, Note, OpenActivity, tag objects,
     Task  → Event and Task are scopeable TARGET entities and still barred
     from the subquery

Why the recursion matters: SOQL is scoped by default when a rule is
active, so a subquery inside the rule's own criteria would be filtered
by the rule being defined. EVERYTHING breaks that.

And: the SOQL operator is API-only. "You can use a SOQL operator in
record criteria only when creating scoping rules via the API."
```

**Detection hint:** Count `SELECT` occurrences and `USING SCOPE EVERYTHING` occurrences inside any generated `SOQL(...)` string. They must be equal. Separately, flag any `$User.` reference inside a `SOQL(...)` that is not `$User.Id`, and flag any generated Setup click-path that claims to build a `SOQL(...)` criterion.

---

## Anti-Pattern 6: Fabricating Supported Objects, Editions, or Limits

**What the LLM generates:** A scoping rule on Order, Campaign, Asset, Quote, Contract, or Knowledge. Or a claim that the feature is available in Enterprise edition. Or invented numbers — "up to 10 rules per object", "a 3,900-character criteria limit", "available since Winter '22".

**Why it happens:** Salesforce features usually support most standard objects, so a short supported-object list reads as unlikely and gets generalised away. Edition tables and numeric limits are exactly the shape of fact a model will confabulate fluently, and the scoping and restriction feature pages carry *different* object lists and *different* edition lists, which makes cross-contamination easy.

**Correct pattern:**

```text
Scoping rules — supported objects (this list is exhaustive):
  custom objects, Account, Case, Contact, Event, Lead, Opportunity, Task

Restriction rules — different list, do not substitute:
  custom objects, external objects, Contract, Event, Quote, Task,
  TimeSheet, TimeSheetEntry
  (only Event and Task appear on both)

Editions: Lightning Experience in Performance, Unlimited, and Developer.
  Enterprise appears in neither scoping-rule list. It DOES appear in the
  restriction-rule caps — do not carry it across.

Active rules per object:
  two in Developer editions; five in Performance and Unlimited editions.
  Plus: "Create only one scoping or restriction rule per object per user."

Operators — do not upgrade this:
  "Unless you use SOQL, scoping rules support only the EQUALS operator.
  The AND and OR operators aren't supported."
  Multi-value equality is comma-separated on the right-hand side; that is
  the whole of it. Null and blank values aren't supported either.

If a number is not on this list, do not state it. There is no published
character limit for recordFilter, no published org-wide rule total, and
no published data-volume threshold at which Salesforce disables a rule.
```

**Detection hint:** Any object name in a generated `targetEntity` that is not in the eight-item scoping list is a defect. Any numeric claim about scoping rules that is not "two", "five", or "one per object per user" should be traced to a source or deleted.

---

## Anti-Pattern 7: Silently Dropping the Required `description`, or Shipping `active` as the Default

**What the LLM generates:** A `.rule` file with `masterLabel`, `recordFilter`, `targetEntity`, `userCriteria` and `version` but no `description` — or with `active` omitted and a build procedure that never activates the rule.

**Why it happens:** `description` is optional on nearly every other Salesforce metadata type, so it gets treated as documentation and trimmed for brevity. And `active` reads as a runtime state rather than a deployable field, so it is left out and assumed to default true.

**Correct pattern:**

```text
description  — documented as REQUIRED on RestrictionRule. Do not trim it.
active       — optional, and defaults to FALSE.

So the two most common "my rule does nothing" causes are:
  1. active was never set (deployed inactive)
  2. active is true but no list view has filterScope = ScopingRule

Recommended build order: deploy with active = false, remap any org-specific
IDs for the destination org, then activate. Deploying active skips the
remap window and can apply a wrong-population rule to production users.
```

**Detection hint:** Validate every generated `RestrictionRule` against the required set — `description`, `enforcementType`, `masterLabel`, `recordFilter`, `targetEntity`, `userCriteria`, `version` — before returning it. Then check whether the accompanying procedure ever activates the rule and ever remaps IDs.

---

## Anti-Pattern 8: Untyped Owner References and Multi-Level Lookup Paths in Criteria

**What the LLM generates:** `Owner.ManagerId = $User.Id`, `Account.Owner.Manager.Department = ...`, `Owner.Profile.Name = 'Sales'`, or a person-account criterion such as `PersonDepartment = $User.Department`. All read as ordinary SOQL relationship syntax.

**Why it happens:** The criteria language looks like SOQL and mostly behaves like it, so SOQL habits transfer — including polymorphic-owner traversal and multi-hop dot notation, both of which SOQL allows and the criteria language does not.

**Correct pattern:**

```text
Owner is polymorphic, so the reference must be typed. Salesforce's own
example: the Owner field on an event "can contain a user or a queue, but
queues aren't supported in scoping rules" — so the type to name is User.
Do not generate Owner:Group as an alternative.
  WRONG:  Agent__c.Owner.ManagerId=001xx000003HNy7
  RIGHT:  Agent__c.Owner:User.ManagerId=001xx000003HNy7

Dot-notation lookups are limited to ONE level — "one lookup level from
the targetEntity", e.g. Owner.UserRoleId.

Only EQUALS: "Unless you use SOQL, scoping rules support only the EQUALS
operator. The AND and OR operators aren't supported." A generated
criterion containing AND, OR, >, <, LIKE or != is invalid.

Supported data types in recordFilter and userCriteria:
  boolean, date, dateTime, double, int, reference, string, time,
  and single picklist values.

Not supported:
  IsPersonAccount fields on the account object — "don't use IsPersonAccount
  fields such as PersonDepartment or PersonLeadSource in record filter
  criteria"
  null or blank values in record criteria

And explicitly warned against:
  "Don't create rules on Event.IsGroupEvent"

Multiple values are comma-delimited; a value containing a comma must be
double-quoted, because "double-quotes specify that the value inside the
quotes isn't considered a delimiter":
  Name__c='Tom, Anita, "Torres, Jia"'   → three values, not four
```

**Detection hint:** In any generated `recordFilter` or `userCriteria`, flag a bare `Owner.` (it must be typed, and for scoping rules that means `Owner:User.` — queues aren't supported), count the dots in each lookup path (more than one level is invalid), flag any IsPersonAccount field name (`PersonDepartment`, `PersonLeadSource`, and the rest of the list on the Account page), and check that any literal string value containing a comma is double-quoted.
