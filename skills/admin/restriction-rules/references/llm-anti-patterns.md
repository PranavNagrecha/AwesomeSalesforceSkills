# LLM Anti-Patterns — Restriction Rules

Mistakes AI assistants make repeatedly when asked to design, write, or review a restriction rule. Use these as self-checks on generated output.

## Anti-Pattern 1: Proposing a restriction rule on Account, Opportunity, Case, or Lead

**What the LLM generates:** "Create a restriction rule on Opportunity so the EMEA team sees only EMEA deals," usually with a plausible-looking `recordFilter` and a `targetEntity` of `Opportunity`.

**Why it is wrong:** For `enforcementType` `Restrict`, `targetEntity` accepts `Contract`, `Event`, `Quote`, `Task`, `TimeSheet`, `TimeSheetEntry`, custom objects, and external objects. The core CRM objects are not on that list. The confusion is real and structural: the *same* metadata type with `enforcementType` `Scoping` **does** support Account, Case, Contact, Event, Lead, Opportunity, and Task — so training data contains `RestrictionRule` files with `<targetEntity>Opportunity</targetEntity>`, and they are all scoping rules.

**Correct form:**

```
enforcementType Restrict  → Contract, Event, Quote, Task, TimeSheet, TimeSheetEntry,
                            custom objects, external objects
enforcementType Scoping   → Account, Case, Contact, Event, Lead, Opportunity, Task,
                            custom objects

Asked to hide Opportunities from a group?
  → Not a restriction rule. Tighten Opportunity OWD and remove the sharing
    layer that granted the access. See admin/sharing-and-visibility.
```

**Detection hint:** grep generated `.rule` files for `<enforcementType>Restrict</enforcementType>` and a `targetEntity` outside the supported list. That combination is always wrong.

---

## Anti-Pattern 2: Writing a `recordFilter` with AND, OR, or an operator other than `=`

**What the LLM generates:**

```xml
<recordFilter>Department__c = 'Legal' AND Status__c != 'Archived'</recordFilter>
```

**Why it is wrong:** "Restriction rules support only the EQUALS operator." "The AND, OR, or any other operators aren't supported." "The use of formulas isn't supported." The generated filter reads like a SOQL `WHERE` clause because that is what the model has seen ten million times, and `recordFilter` is a string field that accepts anything at write time — so the wrongness is not caught by a schema.

**Correct form:**

```xml
<!-- one EQUALS test, nothing else -->
<recordFilter>Restriction_Key__c = 'Legal|Active'</recordFilter>
```

Multi-condition requirements are precomputed into a single stored field by a before-save record-triggered flow, then filtered on that field. The one construct that legitimately resembles an OR is the comma-separated value list, which is a set membership test on a single field:

```xml
<recordFilter>recordTypeId = 012xx0000001AAA, 012xx0000001BBB</recordFilter>
<!-- values containing a comma go in double quotes -->
<recordFilter>Name__c='Tom, Anita, "Torres, Jia"'</recordFilter>
```

**Detection hint:** any generated `recordFilter` or `userCriteria` containing ` AND `, ` OR `, `!=`, `<`, `>`, `LIKE`, `IN (`, `NOT`, or a parenthesis is invalid.

---

## Anti-Pattern 3: Describing the rule as a security boundary or an absolute block

**What the LLM generates:** "Once the restriction rule is active, users with that profile cannot access these records through any entry point, including the API." Sometimes phrased as "restriction rules trump sharing."

**Why it is wrong:** The rule is enforced on Links, List Views, Lookups, Records, Related Lists, Reports, Search, SOQL, and SOSL, and Salesforce documents eight gaps in it. Two of them describe ordinary org infrastructure rather than edge cases: "Restriction rules aren't applied for code executed in System Mode," and users with Modify All Records or Modify All Data "can view, edit, and delete all records regardless of restriction rules." A nightly integration user with Modify All Data is unaffected by every restriction rule in the org. The "trumps sharing" phrasing is doubly wrong — the rule does not override sharing, it filters what sharing already returned.

**Correct form:**

```
Say: "A restriction rule filters, at query time, the records the sharing model
already granted. It is enforced on nine surfaces including SOQL and SOSL. It is
NOT applied to code running in system mode, and it does NOT apply to holders of
View All / Modify All Records or Data. UserRecordAccess will still report access.
Treat it as defence in depth, not as a control an auditor can test."

Then produce the bypass inventory: who holds View All / Modify All on this object,
and which Apex or integration paths read it in system mode.
```

**Detection hint:** flag the words "cannot access", "no way to see", "trumps", "overrides sharing", "absolute", or "guaranteed" in any generated description of a restriction rule. Also flag any answer that describes the enforcement without also naming at least the system-mode and Modify All exceptions.

---

## Anti-Pattern 4: `Owner.Field` instead of `Owner:User.Field`

**What the LLM generates:**

```xml
<recordFilter>Owner.UserRoleId = $User.UserRoleId</recordFilter>
```

**Why it is wrong:** Owner is polymorphic, so the criteria parser requires the object type: "when you reference the Owner field, you must specify the object type in your syntax." The correct separator is a colon, which appears almost nowhere else in Salesforce query grammar, so the model reproduces the familiar dot form with high confidence. Salesforce's own examples are unambiguous: `Owner:User.UserRoleId = $User.UserRoleId` and `Owner:User.ProfileId = $User.ProfileId`, and in cross-object form `Agent__c.Owner:User.ManagerId = 001xx000003HNy7`.

**Correct form:**

```xml
<recordFilter>Owner:User.UserRoleId = $User.UserRoleId</recordFilter>
<recordFilter>Owner:User.ProfileId = $User.ProfileId</recordFilter>
<!-- OwnerId compared to the running user needs no object type -->
<recordFilter>OwnerId = $User.Id</recordFilter>
```

There is a second traversal limit the model will happily exceed: "You can use only one 'dot' (one lookup level from the targetEntity)." A generated `recordFilter` of `Account.Owner:User.Manager.Department` is two hops past what the parser accepts.

**Detection hint:** grep for `Owner.` immediately followed by a letter in any `recordFilter`. `OwnerId` and `Owner:User.` are the only valid Owner forms. Separately, count lookup hops from the `targetEntity` — more than one is invalid.

---

## Anti-Pattern 5: Emitting 18-character Ids, or hardcoding org-specific Ids with no remap note

**What the LLM generates:** a `userCriteria` of `$User.ProfileId = '00e5g000001AbCdEAA'` — an 18-character Id, often invented rather than looked up — with no mention that it changes per org.

**Why it is wrong:** Two documented constraints. "If you reference IDs in the `recordFilter` field, use 15-character IDs instead of 18-character IDs." And deployment does not translate them: "if you include IDs in your `recordFilter` or `userCriteria` fields that are specific to your Salesforce org, you must modify these IDs in the target org." A generated rule with a hallucinated 18-character profile Id deploys cleanly and restricts nobody, or restricts the wrong population.

**Correct form:**

```xml
<userCriteria>$User.ProfileId = '00exx0000000AAA'</userCriteria>
```

with an explicit note attached to the output:

```
Ids in this file are org-specific and must be remapped for every target org.
Use 15-character Ids. Prefer portable User fields where the requirement allows:
  $User.IsActive = true
  $User.UserType = 'CSPLitePortal'
  $User.Department = 'Legal'
```

**Detection hint:** any 18-character Id literal, or any Id literal at all with no accompanying remap warning.

---

## Anti-Pattern 6: Blurring restriction rules and scoping rules because they share a metadata type

**What the LLM generates:** a `.rule` file whose description promises confidentiality but whose `enforcementType` is `Scoping`, or prose that uses "restriction rule" and "scoping rule" as synonyms for "filter the records users see."

**Why it is wrong:** One file format, two entirely different mechanisms. `Restrict` filters access across nine surfaces including SOQL and SOSL. `Scoping` sets the default record set in list views and reports and removes no access — a user can change the filter and see everything they were always entitled to. Shipping `Scoping` against a confidentiality requirement produces a change that passes review and protects nothing.

**Correct form:**

```
Requirement is "they must not be able to reach it"      → enforcementType Restrict
Requirement is "declutter the default view/report"       → enforcementType Scoping
                                                            (see admin/scoping-rules)

Each kind is counted against its OWN per-object active-rule ceiling — they do
not share one budget — but both are bound by "Create only one restriction or
scoping rule per object per user."
```

**Detection hint:** compare the `description` field's intent against `enforcementType` on every generated file. A description containing "sensitive", "confidential", "must not see", or "compliance" alongside `Scoping` is a defect.

---

## Anti-Pattern 7: Proposing `UserRecordAccess` or an Apex test as the verification step

**What the LLM generates:** a verification plan built on `SELECT RecordId, HasReadAccess FROM UserRecordAccess WHERE UserId = :u`, or an Apex test class that inserts records, runs a query, and asserts the restricted rows are absent.

**Why it is wrong:** `UserRecordAccess` is documented as not restriction-rule aware — it "doesn't consider whether a user's access is blocked due to a restriction rule" — so it returns the pre-restriction answer and the check passes whether or not the rule works. The Apex route runs into the system-mode exclusion: restriction rules "aren't applied for code executed in System Mode," and none of the Restriction Rules Developer Guide pages describe how rules behave inside a test context, so an assertion written there is testing something undocumented.

**Correct form:**

```
Verify by execution as a matching user, on the surfaces the docs name:
  1. Open a list view of the object          → restricted rows absent
  2. Run a report on the object              → restricted rows absent
  3. Open a parent record's related list     → restricted rows absent
  4. Issue the query through the API as that user → restricted rows absent
  5. Repeat 1-4 as a NON-matching user       → rows present (proves scoping)

Do NOT use UserRecordAccess. Annotate any existing dashboard built on it.
```

**Detection hint:** any generated test plan whose only assertion runs in Apex or reads `UserRecordAccess`.

---

## Anti-Pattern 8: Claiming the rule writes sharing rows, cascades to children, or can be recalculated

**What the LLM generates:** "the restriction rule will recalculate sharing and remove the `__Share` rows," or "child records inherit the parent's restriction," or advice to run a sharing recalculation after activating a rule.

**Why it is wrong:** These borrow the mental model of sharing rules, which is the wrong one. A restriction rule is evaluated as an access policy at query time; it does not delete or create sharing rows, so there is nothing to recalculate and no recalculation job to monitor. And Salesforce is explicit about the graph: "creating a restriction rule for an object doesn't automatically restrict access to its child objects." The related trap in the other direction is real and worth generating: "if a restriction rule's record criteria uses a lookup field and the related record doesn't exist, access isn't granted" — records with an empty lookup vanish for the restricted user.

**Correct form:**

```
Restriction rule       → evaluated at query time; no __Share rows written or removed;
                         no recalculation job; activation takes effect on the next query
Sharing rule           → materialises share rows; membership changes trigger recalculation
Child objects          → need their own rule, checked against the supported object list
Lookup in recordFilter → missing related record means access is NOT granted
```

**Detection hint:** flag "recalculate", "__Share", "sharing recalculation", or "inherits" appearing in generated guidance about a restriction rule.
