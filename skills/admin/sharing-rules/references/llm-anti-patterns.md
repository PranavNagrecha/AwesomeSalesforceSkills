# LLM Anti-Patterns — Sharing Rules

Mistakes AI assistants reliably make when advising on or generating sharing rules.
Use these to self-check output before returning it.

---

## Anti-Pattern 1: Proposing a Sharing Rule to Take Access Away

**What the LLM generates:** "Create a sharing rule that restricts the support team so they can only see cases in their own region," or a rule described as excluding a population, or a claim that a narrower rule overrides a broader one.

**Why it happens:** In most access-control systems rules are evaluated in order and can deny. Salesforce's model is additive and unordered, and that difference does not survive the generalisation from other platforms in training data. The word "restrict" in a requirement pulls the model toward the sharing-rule vocabulary because that is where the word "sharing" lives.

**Correct pattern:**

```
Sharing rules ONLY add access grants. There is no deny rule, no rule ordering,
and no precedence. The most permissive grant on a record wins, whatever
produced it.

  "Give team X access to records they can't see"   -> sharing rule
  "Stop team X seeing records they currently see"  -> admin/restriction-rules
  "Remove the grant a sharing rule produced"       -> change the rule, the
                                                      criteria, or ownership
```

**Detection hint:** Grep generated text for a sharing rule paired with *restrict*, *deny*, *prevent*, *exclude*, *limit to*, or *only*. Every one of those is a signal the requirement is subtractive and the mechanism is wrong.

---

## Anti-Pattern 2: Inventing an `OwnerSharingRule` / `CriteriaBasedSharingRule` Metadata Payload

**What the LLM generates:** Deployment XML using `<CriteriaBasedSharingRule>` or `<OwnerSharingRule>` as the root, or package.xml entries naming those types, or `<accountCriteriaBasedSharingRule>`-style per-object variants.

**Why it happens:** Those types existed and are heavily represented in older training material. The Metadata API guide is explicit that `CriteriaBasedSharingRule` "is removed as of API version 33.0 and is available in earlier versions only. Use SharingRules instead," and the same applies to `BaseSharingRule` → `SharingBaseRule`. Deprecated-but-documented types are exactly the shape a model reproduces confidently.

**Correct pattern:**

```xml
<!-- Current: one file per object, all rule types inside SharingRules -->
<!-- force-app/main/default/sharingRules/Account.sharingRules-meta.xml -->
<SharingRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <sharingOwnerRules>    ... </sharingOwnerRules>
    <sharingCriteriaRules> ... </sharingCriteriaRules>
    <sharingTerritoryRules>... </sharingTerritoryRules>
    <sharingGuestRules>    ... </sharingGuestRules>
</SharingRules>
```

```xml
<!-- package.xml addresses the concrete rule types, not the container -->
<types><members>Lead.testShareRule</members><name>SharingCriteriaRule</name></types>
<types><members>*</members><name>SharingOwnerRule</name></types>
<types><members>Account.*</members><name>SharingTerritoryRule</name></types>
```

**Detection hint:** Any occurrence of `CriteriaBasedSharingRule`, `OwnerSharingRule`, or `BaseSharingRule` in generated metadata or a manifest. Also flag any API version below 33.0 in a `<version>` element alongside sharing-rule types.

---

## Anti-Pattern 3: Omitting `accountSettings` on an Account Rule, or Defaulting It Wide

**What the LLM generates:** An Account sharing rule with `accessLevel` and `sharedTo` and nothing else, or one where `caseAccessLevel`, `contactAccessLevel`, and `opportunityAccessLevel` all mirror the account access level "for consistency."

**Why it happens:** The model treats `accessLevel` as *the* access decision because that is how sharing works on every other object. The nested block is easy to miss and, in the Setup UI, it is three extra pickers below the fold that already have values selected.

**Correct pattern:**

```xml
<!-- All three are REQUIRED on Account rules. Each takes None | Read | Edit.
     There is no "inherit" and no "leave unchanged". -->
<accountSettings>
    <caseAccessLevel>None</caseAccessLevel>
    <contactAccessLevel>Read</contactAccessLevel>
    <opportunityAccessLevel>None</opportunityAccessLevel>
</accountSettings>
```

Default every child to `None` and raise only the ones the requirement names. "Read the account" does not mean "read the pipeline."

**Detection hint:** An `Account.sharingRules-meta.xml` payload with no `accountSettings` block, or one where all three children equal the parent `accessLevel`. Either is a review stop.

---

## Anti-Pattern 4: Treating a `RowCause = 'Rule'` Share Row as Editable Data

**What the LLM generates:** Apex or a Data Loader plan that inserts, updates, or deletes rows on `AccountShare` / `MyObject__Share` in order to grant or revoke access that a sharing rule controls. Sometimes it generates an `update` that changes `RowCause` or `ParentId`.

**Why it happens:** The share object appears in the schema like any other sObject, supports DML syntactically, and describe calls do not communicate that the platform owns particular rows. Nothing fails loudly, which removes the correction signal — the rows come back on the next recalculation, hours later, attributed to nothing.

**Correct pattern:**

```apex
// Yours to manage: Manual shares and Apex managed shares with a custom reason.
Project__Share s = new Project__Share(
    ParentId    = projectId,
    UserOrGroupId = userId,
    AccessLevel = 'Edit',
    RowCause    = Schema.Project__Share.RowCause.Audit_Review__c
);
insert s;

// NOT yours: RowCause 'Rule', 'Owner', 'ImplicitChild', 'ImplicitParent',
// 'Team', 'TerritoryRule'. Deleting these is a no-op that looks like a fix.
// ParentId and RowCause can't be updated on any share row.
```

Use share-table DML to *create* Apex managed shares; use share-table SOQL to *diagnose* everything else.

**Detection hint:** Any `delete`/`update` DML against a `*Share` sObject that is not filtered to `RowCause = 'Manual'` or a custom Apex sharing reason. Also flag `AccessLevel = 'All'` in generated share inserts — the Apex Developer Guide marks `All` as internal only.

---

## Anti-Pattern 5: Promising That Access Is Live Once the Rule Is Saved

**What the LLM generates:** "Save the rule and the users will immediately have access," or a runbook whose verification step is "ask a user to refresh," or a migration plan that sequences a rule deployment directly into a go-live smoke test with no wait.

**Why it happens:** Configuration changes in most systems take effect on commit, and the page that saves a sharing rule returns without linking to the job it just started. The model has no representation of a background process, and no reason to look for one on a different Setup page.

**Correct pattern:**

```
Recalculation is asynchronous and its duration scales with matched records
x resolved group membership. It IS observable, so never claim otherwise:
Setup -> Background Jobs shows progress, Setup Audit Trail shows recent
sharing operations, and Salesforce emails you when recalculation completes
for all affected objects.

Verify like this, not by asking a user:
  SELECT COUNT(Id) FROM AccountShare
  WHERE RowCause = 'Rule' AND UserOrGroupId = '00G...'

Run it twice, minutes apart. Rising count = job in progress. Do NOT edit or
delete the rule while it is climbing; that queues more work, not less.

For bulk structural change (reorg, mass transfer, user load), use defer
sharing calculation and treat the RESUME as the maintenance window.
```

**Detection hint:** The words *immediately*, *instantly*, *right away*, or *takes effect on save* anywhere near a sharing rule step. Also flag any runbook that lacks a share-table verification query — and the opposite overcorrection, a claim that recalculation progress cannot be monitored.

---

## Anti-Pattern 6: Mis-Shaping the Rule-Count Limit

**What the LLM generates:** Either an uncited number presented as fact, or the shape of the real limit gets mangled — "300 sharing rules plus 50 criteria-based ones", "50 criteria-based rules per object", "the caps depend on your edition", "Salesforce will raise it on request". Models trained to be cautious produce a second failure instead: refusing to state any limit at all, on the false premise that the figure is unpublished.

**Why it happens:** Sharing-rule limits are heavily repeated in forum posts, blogs, and certification material, so the digits are strongly represented and weakly sourced. The edition dependency is genuine but attaches to a different dimension — which *objects* support sharing rules, not how many rules each object gets — and that is exactly the kind of swap that survives paraphrase.

**Correct pattern:**

```
The Salesforce Security Guide publishes the cap in one sentence:

  "You can define up to 300 total sharing rules for each object, including
   up to 50 criteria-based or guest user sharing rules, if available for
   the object."

  300 = every rule type on one object, combined
   50 = criteria-based AND guest user rules together, INSIDE the 300
        - not additive to it
        - not reserved for criteria-based rules

Edition affects object availability, not the numbers:
  "Only account, asset, campaign, and contact sharing rules are available
   in Professional Edition."
```

**Detection hint:** Any limit written as 300 *plus* 50; any statement that the 50 belongs to criteria-based rules alone; any claim that the caps vary by edition or are "extensible on request"; and any figure with no adjacent official source. Also flag the overcorrection — a refusal to state the cap on the grounds that it is unpublished.

---

## Anti-Pattern 7: Building Guest Access as an Ordinary Sharing Rule

**What the LLM generates:** A criteria-based rule whose `sharedTo` is a public group described as "containing the site guest user," and often `accessLevel` of `Edit` because the site has a form.

**Why it happens:** Guest users are users, public groups take users, and the composition looks valid. `SharingGuestRule` arrived at API version 47.0 — later than the bulk of sharing-rule material — so the model's default shape for "share to someone" predates it.

**Correct pattern:**

```xml
<sharingGuestRules>
    <fullName>Published_Programs_To_Site_Guest</fullName>
    <accessLevel>Read</accessLevel>   <!-- the ONLY accepted value -->
    <label>Published Programs to Site Guest</label>
    <sharedTo><guestUser>Course_Catalogue_Site</guestUser></sharedTo>
    <criteriaItems>
        <field>Publication_Status__c</field>
        <operation>equals</operation>
        <value>Published</value>
    </criteriaItems>
    <includeHVUOwnedRecords>false</includeHVUOwnedRecords>
</sharingGuestRules>
```

`SharingGuestRule` is available in API version 47.0 and later; its `criteriaItems` and `booleanFilter` in 48.0 and later. Guest writes are not a sharing-rule problem — that path is Apex or a flow running in an appropriate context.

**Detection hint:** A guest user or an Experience Cloud site named in the requirement while the generated payload uses `sharingCriteriaRules` or `sharingOwnerRules`. Also flag any guest rule with `accessLevel` other than `Read`.

---

## Anti-Pattern 8: Emitting a `booleanFilter` That References Criteria That Do Not Exist

**What the LLM generates:** `<booleanFilter>1 AND (2 OR 3)</booleanFilter>` above two `criteriaItems`, or a filter string left in place after a criterion was removed during editing, or `1 AND 2` on a rule with a single criterion.

**Why it happens:** The filter string and the criteria list are separate elements with no syntactic link, so nothing in the generated text is internally inconsistent to the model. It is a cross-reference, and cross-references are where generation drifts.

**Correct pattern:**

```
The integers in booleanFilter are 1-based positions into criteriaItems, in
document order. Every index must resolve, and every criterion should be
referenced.

  2 criteriaItems -> valid: "1 AND 2", "1 OR 2"
                  -> invalid: "1 AND 2 AND 3", "1 AND (2 OR 3)"
  1 criteriaItem  -> omit booleanFilter, or use "1"
```

**Detection hint:** Extract the integers from `booleanFilter` and compare against the count of sibling `criteriaItems`. Any index above the count is a deploy failure; any unreferenced criterion is a logic bug. `scripts/check_sharing_rules.py` performs exactly this check.
