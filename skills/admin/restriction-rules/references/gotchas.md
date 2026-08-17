# Gotchas — Restriction Rules

Non-obvious platform behaviour that turns a correct-looking restriction rule into a production incident.

## Gotcha 1: The rule is a run-time filter, and Salesforce documents eight gaps in it

**What happens:** Someone asks for sensitive records to be hidden from a group of users. A restriction rule is built, tested by logging in as one of those users, and signed off as "the data is now inaccessible to them." Months later the data turns up in an extract, a Chatter feed, a manager's calendar, or an access-audit dashboard, and nobody can explain how, because the rule is still active and still correct.

**Why:** The rule filters, at query time, the rows the sharing model already granted. It is enforced on Links, List Views, Lookups, Records, Related Lists, Reports, Search, SOQL, and SOSL — a wide net, but a finite one. Outside it, the Considerations page in the Restriction Rules Developer Guide documents the eight gaps below. Seven are paths by which a restricted user still reaches the data; the eighth, `UserRecordAccess`, is a reporting gap that hides the other seven from audit tooling.

| Gap | Documented behaviour |
|---|---|
| System-mode code | "Restriction rules aren't applied for code executed in System Mode." |
| View All Records / View All Data | Those users "can view all records regardless of restriction rules." |
| Modify All Records / Modify All Data | Those users "can view, edit, and delete all records regardless of restriction rules." |
| `UserRecordAccess` | "The UserRecordAccess object doesn't consider whether a user's access is blocked due to a restriction rule." |
| Calendars with Show Details | "In calendars, if the Show Details access level is selected, users can see the subject of all events, regardless of the restriction rules created." |
| Subordinates' calendars | "Users can see their subordinates' events in calendars even if the users have an active restriction rule applied." |
| Global search shortcuts | "After restriction rules are applied, users can still see records that they previously had access to in the global search box shortcuts." |
| Chatter publisher | "If a user creates an event or a task record using the Chatter publisher, the record name is visible in the related Chatter post." |

Note also the negative-space case that trips search testing: "a user with a restriction rule applied might not find all possible matching results when searching for a record." Search behaviour under a rule is imprecise in both directions.

**How to avoid:** Write the bypass inventory as a design artefact before the rule is authored, and get it signed. Two of the eight — system mode and Modify All Data — are precisely the paths integration users take, so an org with any nightly extract on the target object has a live bypass by default. If the requirement is regulatory and needs a guarantee rather than a strong default, the answer is a Private OWD plus removal of whatever sharing layer granted the access; the restriction rule is the wrong tool and no amount of tuning makes it the right one.

**Source:** Restriction Rules Developer Guide — Considerations.

---

## Gotcha 2: `UserRecordAccess` reports the pre-restriction answer, so access audits pass while the rule is working

**What happens:** An admin builds an access-audit report or an Apex check on `UserRecordAccess` to prove which users can reach which records. On an object carrying an active restriction rule, that check returns access for users the rule is currently blocking. The admin concludes the rule is broken and starts debugging a rule that is behaving exactly as designed.

**Why:** `UserRecordAccess` answers a sharing-model question — has any sharing mechanism granted this user this record. Restriction rules are evaluated separately at query time and never write into the sharing tables, so the object has nothing to report. Salesforce states it flatly: "The UserRecordAccess object doesn't consider whether a user's access is blocked due to a restriction rule."

**How to avoid:** Never use `UserRecordAccess` as the test for a restriction rule. The only valid test is executing as a matching user and observing what comes back — a list view, a report, a related list, and a SOQL call, in that order. Annotate any existing dashboard or Apex helper built on `UserRecordAccess` with the objects that carry restriction rules, so the next person reading it knows the number is the pre-restriction figure. This interacts badly with `security/record-access-troubleshooting`, whose primary diagnostic is that same object.

**Source:** Restriction Rules Developer Guide — Considerations.

---

## Gotcha 3: Only EQUALS exists, and two rules do not compose into an AND

**What happens:** A requirement arrives with two conditions. The obvious workaround — one rule for each condition, both active on the object, both targeting the same profile — appears to save. The result is not an AND. Salesforce states the actual behaviour: "If you create two active rules, and both rules apply to a given user, only one of the active rules is observed." Which one is observed is not documented, so the second rule buys nothing and makes the outcome unpredictable.

**Why:** The criteria language accepts a single equality test on each side. "Restriction rules support only the EQUALS operator." "The AND, OR, or any other operators aren't supported." "The use of formulas isn't supported." Separately, the guide constrains composition itself: "Create only one restriction or scoping rule per object per user. In other words, for a given object, only one restriction or scoping rule at most should have the userCriteria field evaluate to true for a given user." Two rules on one object are legitimate only when their `userCriteria` select disjoint audiences.

**How to avoid:** Collapse the composite condition into one stored field, populated by a before-save record-triggered flow, and filter the rule on that field. Backfill the field across existing records before activating. When the org needs several rules on the same object, draw the `userCriteria` audiences as a Venn diagram first and confirm the intersections are empty — the platform will not warn you.

The multi-value form is the one exception that looks like an OR and is not one: `recordFilter` accepts comma-separated string or Id values, so `recordTypeId = 012xx0000001AAA, 012xx0000001BBB` keeps both record types. Values containing a comma go in double quotes so the comma is not read as a delimiter: `Name__c='Tom, Anita, "Torres, Jia"'`.

**Source:** Restriction Rules Developer Guide — Considerations and the multiple-values example scenario.

---

## Gotcha 4: 18-character Ids and org-specific Ids both fail, and neither fails loudly

**What happens:** An Id is copied out of a browser URL or a Data Loader export into `recordFilter`, and the rule matches nothing — or, worse, is deployed to a second org where the profile Id in `userCriteria` belongs to a different profile entirely, and the rule silently applies to the wrong audience.

**Why:** Two separate constraints collide. First, "if you reference IDs in the `recordFilter` field, use 15-character IDs instead of 18-character IDs" — and 18 characters is what almost every convenient source hands you. Second, `recordFilter` and `userCriteria` are opaque strings to the deployment machinery, so record type Ids, profile Ids, role Ids, and user Ids inside them are never translated between orgs. Salesforce is explicit: "if you include IDs in your `recordFilter` or `userCriteria` fields that are specific to your Salesforce org, you must modify these IDs in the target org if different from the org where the restriction rules were originally created."

**How to avoid:** Truncate every Id to 15 characters as a deliberate step, not by luck. Maintain an Id remap table alongside the `.rule` file listing every literal, what it points at in the source org, and its counterpart in each target org, and treat updating it as part of the deployment rather than a post-deployment fix. Where the requirement can be expressed against a non-Id User field — `$User.IsActive`, `$User.UserType`, `$User.Department` — prefer it, because those values are portable and Ids are not.

**Source:** Restriction Rules Developer Guide — Considerations.

---

## Gotcha 5: `Owner.` does not work; the Owner reference needs an explicit object type

**What happens:** An admin writes `recordFilter` as `Owner.UserRoleId = $User.UserRoleId`, mirroring the dot-notation traversal that works everywhere else on the platform, and the rule does not behave.

**Why:** Owner is polymorphic — it can point at a User or a Group — so the criteria parser needs to be told which. "When you reference the Owner field, you must specify the object type in your syntax." The working form uses a colon between the field and the object type: `Owner:User.UserRoleId`. Salesforce's own examples use `Owner:User.UserRoleId = $User.UserRoleId` for same-role visibility and `Owner:User.ProfileId = $User.ProfileId` for same-profile visibility. The same shape appears in cross-object form: `Agent__c.Owner:User.ManagerId=001xx000003HNy7, 001xx000003HNut`.

**How to avoid:** Grep every `recordFilter` for `Owner.` with a plain dot and rewrite it as `Owner:User.`. This is the single most common syntax error in hand-written restriction rules because it contradicts the platform's dot-notation habit, and it is the one an LLM will reproduce most reliably from training data. The checker script in this skill flags it.

**Source:** Restriction Rules Developer Guide — Considerations and the same-role / same-profile example scenarios.

---

## Gotcha 6: Restricting a parent does not restrict its children

**What happens:** A rule is placed on a custom parent object and the team assumes the child records inherit the restriction the way they inherit a master-detail sharing decision. Child records stay visible, and because the parent is hidden, they surface without the context that would have made the exposure obvious in review.

**Why:** "Creating a restriction rule for an object doesn't automatically restrict access to its child objects." The rule is scoped to one `targetEntity` and knows nothing about the object graph. This is unlike master-detail sharing inheritance, which is where the wrong intuition comes from.

**How to avoid:** Walk the object graph outward from the restricted object and author a rule per child that needs one, checking each child against the supported `targetEntity` list — a child that happens to be an Opportunity or a Case cannot carry a rule at all, which changes the design. Also check the reverse direction: `recordFilter` referencing a lookup fails closed when the related record is missing, because "if a restriction rule's record criteria uses a lookup field and the related record doesn't exist, access isn't granted." Records with an empty lookup disappear for the restricted user even when you intended them to survive.

**Source:** Restriction Rules Developer Guide — Considerations.

---

## Gotcha 7: Activity related lists undercount under a restriction rule

**What happens:** After a rule is activated on Task or Event, agents report that activities they own are missing from the Open Activities and Activity History related lists — not filtered by the rule, just absent. The record page understates how much work exists.

**Why:** Salesforce does not publish the mechanism, but it documents the outcome directly and unconditionally: "if you use Open Activities and Activity History related lists, when restriction rules are applied, it's possible that fewer than 50 records are displayed when more activities exist that the user has access to." The guide's recommendation is to "use the Activity Timeline instead of activity related lists."

**How to avoid:** Ship the layout change with the rule, not after it. Every page layout used by a profile matched by the `userCriteria` should present the Activity Timeline rather than the legacy related lists. If a report is the workaround, verify it as the restricted user — reports are an enforced surface, so the counts there are filtered but complete, which makes them a better audit surface than the related list.

**Source:** Restriction Rules Developer Guide — Considerations.

---

## Gotcha 8: External objects behave differently enough to invalidate the design

**What happens:** A restriction rule is designed against an external object, tested in a sandbox pointing at a small test endpoint, and then performs badly or silently loses search in production.

**Why:** Four separate constraints apply only to external objects. "Only external objects created using the Salesforce Connect: OData 2.0, OData 4.0, and Cross-Org adapters support restriction rules" — the custom adapter is not supported at all. "External objects created using the Cross-Org adapter don't support search or SOSL when a rule is applied to a user," so two of the nine enforcement surfaces disappear for that adapter. "Restriction rules for external objects don't include organization-wide defaults or sharing mechanisms," which means the rule is not narrowing a sharing grant — there is no sharing grant. And because the data lives outside Salesforce, "editing or deleting a restriction rule on an external object causes an additional database call," with further calls each time search runs against external object records. External objects also "don't appear in Object Manager," so the Setup path used for every other object does not exist here.

**How to avoid:** Confirm the adapter before designing anything. Use only indexed fields in record criteria — the guide recommends it "especially in record criteria" — and avoid external Ids there. Load-test with production-scale data rather than a test endpoint, because the additional database calls are the cost that a small sandbox dataset hides.

**Source:** Restriction Rules Developer Guide — Considerations, "Restriction Rules and External Objects".

---

## Gotcha 9: The active-rule ceiling is per object and per edition, and drafts hide it

**What happens:** A third requirement lands on an object that already carries two active rules in an Enterprise Edition org, and the design assumes it can simply be added. It cannot, and the discovery happens at deployment rather than at design.

**Why:** "You can create up to two active restriction rules per object in Enterprise and Developer Editions and up to five active restriction rules per object in Performance and Unlimited Editions." The ceiling counts `active` rules, so a repository can accumulate inactive `.rule` files that give no signal of how close the object is to its limit.

Scoping rules are counted against a *separate* ceiling, not the same one: the Scoping Rules guide states "Create up to two active scoping rules per object in Developer editions. Create up to five active scoping rules per object in Performance and Unlimited editions." Nothing in either guide combines the two budgets, so two active restriction rules and two active scoping rules on the same object are both legal at once — do not treat a scoping rule as consuming a restriction-rule slot. (Note the scoping page names only Developer, Performance and Unlimited; it states no Enterprise number.) What the two kinds genuinely share is the composition constraint from Gotcha 3: even well under both ceilings, only one restriction or scoping rule may apply to a given user on a given object.

[STALE-RISK: re-check the per-edition active-rule ceilings and the supported `targetEntity` list each release against the Considerations page and the `RestrictionRule` metadata reference. Both are the kind of limit Salesforce revises, and both were last verified 2026-08-15 against API 52.0-and-later documentation. Whether the supported-object list has changed since the feature shipped was not verified and is not claimed here.]

**How to avoid:** Count active rules on the object as the first step of any design, counting `Restrict` and `Scoping` separately against their own ceilings, then check the per-user constraint across both. When a ceiling is the binding constraint, consolidating two rules into one by precomputing a composite field (Gotcha 3) is usually cheaper than an edition upgrade. The checker script in this skill counts active rules per `targetEntity` *per `enforcementType`* across a metadata directory and flags anything above the ceiling for that kind of rule.

**Source:** Restriction Rules Developer Guide — Considerations; Scoping Rules Developer Guide — Considerations; RestrictionRule metadata type (API version 52.0 and later).

---

## Gotcha 10: Salesforce Classic is a documented prerequisite problem

**What happens:** Rules are built and activated in an org where some users still work in Salesforce Classic, and the behaviour observed by those users does not match the design.

**Why:** Restriction rules are available in Lightning Experience, and the guide opens its Considerations with a prerequisite rather than a caveat: "Before creating restriction rules, we recommend that you Turn Off Salesforce Classic for Your Org." The recommendation is placed first in the list, ahead of the supported-object list.

**How to avoid:** Establish which users can still reach Classic before the rule is designed, not after. In an org that cannot yet retire Classic, treat the Classic population as another entry in the bypass inventory from Gotcha 1 and state it explicitly to whoever is signing off the restriction.

**Source:** Restriction Rules Developer Guide — Considerations.
