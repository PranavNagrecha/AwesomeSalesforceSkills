# Examples — Restriction Rules

## Example 1: Walling Legal's contracts off from a 400-user sales org

**Context:** An Enterprise Edition org has Contract OWD set to Public Read Only, inherited from a 2016 implementation nobody wants to touch because eleven reports and two managed packages depend on it. Legal has started storing settlement agreements as Contract records with a dedicated record type. Those must not be visible to the sales organisation.

**Problem:** Tightening Contract OWD to Private is the correct fix but breaks the eleven reports and needs a change-control window nobody will fund this quarter. Sales users reach the settlement contracts through the OWD grant — list views, the Contracts related list on Account, global search, and the API all return them.

**Solution:**

Author one restriction rule that keeps only the non-settlement record type for the sales profile. Because record criteria accepts a comma-separated Id list, the surviving record types are enumerated rather than the excluded one negated — there is no `!=`.

```xml
<!-- restrictionRules/Sales_Contracts_Only.rule -->
<?xml version="1.0" encoding="UTF-8"?>
<RestrictionRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>false</active>
    <description>Sales profile sees only standard and renewal contracts, not settlements.</description>
    <enforcementType>Restrict</enforcementType>
    <masterLabel>Sales Contracts Only</masterLabel>
    <recordFilter>recordTypeId = 012xx0000001AAA, 012xx0000001BBB</recordFilter>
    <targetEntity>Contract</targetEntity>
    <userCriteria>$User.ProfileId = '00exx0000000AAA'</userCriteria>
    <version>1</version>
</RestrictionRule>
```

Both Ids are 15 characters, not 18 — record criteria wants the 15-character form.

Validate before activating. Run the record filter as a query and confirm the surviving row count:

```soql
SELECT COUNT() FROM Contract WHERE RecordTypeId IN ('012xx0000001AAA','012xx0000001BBB')
```

Compare against the total:

```soql
SELECT RecordType.DeveloperName, COUNT(Id) FROM Contract GROUP BY RecordType.DeveloperName
```

Then flip `active` to `true` and log in as a sales user to confirm the settlement contracts have gone from the Account related list, from search, and from a Contract report.

**Why it works:** The restriction rule filters the result set that the Public Read Only OWD produced, on all nine documented enforcement surfaces — Links, List Views, Lookups, Records, Related Lists, Reports, Search, SOQL, and SOSL. The OWD grant is untouched, so nothing else in the org changes.

**What it does not do:** any sales manager holding View All on Contract still sees every settlement, and any Apex or integration reading Contract in system mode still returns them. Those are documented and unfixable at this layer. If Legal's requirement is a hard guarantee rather than a strong default, the OWD change has to be funded after all.

**Source:** Restriction Rules Developer Guide — Considerations and the record-type example scenario (URLs in `well-architected.md`).

---

## Example 2: Own-tasks-only for a shared services desk

**Context:** A 60-person shared services team logs client interactions as Tasks. All 60 sit under one role. The role hierarchy plus the org's activity settings mean every member sees every other member's tasks, including tasks logged against clients they do not support.

**Problem:** The requirement is "each agent sees only tasks they own." Activity sharing settings are org-wide, so tightening them would affect the whole company. Sharing rules cannot be used to *remove* the access the hierarchy already granted.

**Solution:**

```xml
<!-- restrictionRules/Services_Own_Tasks.rule -->
<?xml version="1.0" encoding="UTF-8"?>
<RestrictionRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <description>Shared services agents see only the tasks that they own.</description>
    <enforcementType>Restrict</enforcementType>
    <masterLabel>Services Own Tasks</masterLabel>
    <recordFilter>OwnerId = $User.Id</recordFilter>
    <targetEntity>Task</targetEntity>
    <userCriteria>$User.ProfileId = '00exx0000000BBB'</userCriteria>
    <version>1</version>
</RestrictionRule>
```

Two layout changes ship with the rule, not after it:

1. Replace the Open Activities and Activity History related lists with the Activity Timeline on every layout the restricted profile uses. Under a restriction rule those related lists can display fewer than 50 records when more exist that the user is entitled to, so an agent looking at the old related list sees a truncated and misleading picture of their own work.
2. Confirm the profile's users do not have calendar Show Details on each other. With Show Details selected, "users can see the subject of all events, regardless of the restriction rules created" — that applies to Events rather than Tasks, but a team that logs both will assume the rule covers the calendar and it does not.

Test through the API, authenticated as the restricted agent — not from Execute Anonymous as an admin, which runs in system mode and is therefore outside the rule entirely:

```soql
-- as the restricted agent: expect the count of tasks they own
SELECT COUNT() FROM Task

-- as the restricted agent, with their own 18-character User Id substituted:
-- expect zero rows
SELECT Id, Subject, OwnerId FROM Task WHERE OwnerId != '005xx000001AbCdAAA' LIMIT 5
```

The second query returning zero rows proves the filter. Running the same pair as an unrestricted user must return rows — that control is what proves the rule is scoped to the intended audience rather than to the whole org.

**Why it works:** `OwnerId = $User.Id` is a single EQUALS test with a `$User` merge value on the right-hand side, which is exactly the shape the criteria language supports. `userCriteria` scopes the rule to one profile, so the rest of the org is untouched — a rule applies only to users its `userCriteria` matches.

**Source:** Restriction Rules Developer Guide — "Allow Users to See Only Records That They Own" example plus the activity-related-list consideration.

---

## Example 3 (failure): the rule that passed UAT and leaked in production

**Context:** A team shipped a restriction rule on a custom `Case_Note__c` object to hide clinical notes from a general support profile. UAT passed: the tester logged in as a support user and the notes were gone from list views, search, and reports.

**What went wrong:** Three weeks later a data-warehouse extract surfaced every clinical note in a reporting tool that the whole company can open. Nothing about the rule had changed.

The extract ran as a dedicated integration user carrying Modify All Data. Salesforce documents that users with Modify All Records or Modify All Data "can view, edit, and delete all records regardless of restriction rules." The rule had been correct from day one; the integration was never in scope for it.

A second, quieter failure was found in the same review. The team's access-audit dashboard queried `UserRecordAccess` to prove which users could reach which notes, and it had been reporting that support users had access all along. That was also correct behaviour: "The UserRecordAccess object doesn't consider whether a user's access is blocked due to a restriction rule." The dashboard was not broken and the rule was not broken — the two artefacts answer different questions and the team had assumed they answered the same one.

**Recovery:**

1. Inventory every principal holding View All Records, View All Data, Modify All Records, or Modify All Data on the object, including permission sets and permission set groups, not just profiles.
2. For the integration user, remove Modify All Data and grant the narrow object permissions the extract actually needs — or, if the extract genuinely must read everything, accept that and remove the clinical notes from its field selection instead.
3. Audit every Apex entry point that touches the object. Anything running in system mode is outside the rule; anything running in user mode is inside it.
4. Re-label the access dashboard. `UserRecordAccess` output on a restriction-rule object is the pre-restriction answer and must be annotated as such wherever it is displayed.
5. Add a control test to the release checklist: the same query run as the restricted user *and* as the integration user, with the expected row counts written down for both.

**The lesson to carry forward:** the bypass inventory is part of the design, not part of the post-mortem. A restriction rule that has not been tested against the org's system-mode and View/Modify All paths has not been tested.

**Source:** Restriction Rules Developer Guide — Considerations (system mode, View All / Modify All, `UserRecordAccess`).

---

## Example 4: a two-condition requirement that a restriction rule cannot express

**Context:** "Contractors should see time sheet entries only when the entry belongs to their own department *and* the entry is not yet approved."

**Problem:** That is two conditions joined by AND. The criteria language supports only the EQUALS operator, and "the AND, OR, or any other operators aren't supported." Formulas are not supported either, so the condition cannot be folded into a formula field and referenced.

**Solution:** Precompute the composite into a single stored field on the record and filter on that.

1. Add a text field, `Restriction_Key__c`, on the target object.
2. Populate it with a before-save record-triggered flow so the value is written on insert and on every update — for example `Finance|Draft` when the department is Finance and the status is Draft.
3. Set `recordFilter` to `Restriction_Key__c = $User.Department` only if the user-side value can be made to match; where it cannot, drive `userCriteria` off a User field that maps one-to-one onto the key instead.

```xml
<recordFilter>Restriction_Key__c = 'Finance|Draft'</recordFilter>
<userCriteria>$User.ProfileId = '00exx0000000CCC'</userCriteria>
```

4. Backfill the field across existing records before activating the rule. Any record where `Restriction_Key__c` is blank is a null on the record side, and "including a null or blank value in record criteria isn't supported and can result in unexpected behavior."

**Why it works:** the composite condition is evaluated once, at save time, by automation that *does* support AND — and the restriction rule then performs the single equality test it is capable of.

**Why not force it with two rules:** two active rules on the same object cannot both apply to the same user. Salesforce's constraint is "create only one restriction or scoping rule per object per user," so a second rule scoped to the same profile does not compose into an AND; it is a configuration error.

**Source:** Restriction Rules Developer Guide — Considerations (operators, formulas, null values, one rule per object per user).
