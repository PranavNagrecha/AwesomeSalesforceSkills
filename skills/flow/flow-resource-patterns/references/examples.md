# Examples — Flow Resource Patterns

Two worked scenarios and one anti-pattern showing how to pick the
right Flow resource type so the flow stays compact, debuggable, and
free of stale-derived-value bugs. Examples are written as Flow-element
pseudocode (Flow doesn't export to a hand-readable text format; the
structure here matches what you'd build in Flow Builder).

---

## Example 1: Derive `isEligibleForUpsell` once, reference from three paths

**Context:** A renewal-process Screen Flow asks the user a few
questions, then routes them through one of three paths: a "discount
offer" path, a "standard renewal" path, and a "escalate to AE" path.
All three paths need to check whether the current contract is
"eligible for upsell" — meaning `Account.Annual_Revenue__c > 1000000`
AND `Opportunity.IsClosed = FALSE` AND `Contact.Do_Not_Contact__c =
FALSE`. The same composite condition appears in the entry conditions
of three Decision elements.

**Problem:** Practitioners copy the three-clause boolean into each
Decision's outcome condition. That's three places to edit when the
business changes "1M USD" to "1.5M USD" — and three places where the
clauses can drift apart. Worse, a fourth Decision later in the flow
needs the same condition to decide which email template to use, so
the duplication grows to four copies. Six months later one path has
the threshold at 1.2M, another at 1M, and nobody remembers which is
correct.

**Solution:** Define one Formula resource. Reference it from every
Decision and from the email-template selector. No Assignment needed —
Formula resources evaluate from their inputs every time they're
referenced, so the value is always current.

```
Formula: f_isEligibleForUpsell  (Return Type: Boolean)
  Expression:
    AND(
      NOT(ISBLANK({!recAccount.Annual_Revenue__c})),
      {!recAccount.Annual_Revenue__c} > 1000000,
      NOT({!recOpportunity.IsClosed}),
      NOT({!recContact.Do_Not_Contact__c})
    )
  Description: "Single source of truth for the upsell-eligibility
                rule. Used by 3 Decision elements and 1 email-template
                selector. Edit the threshold here only."

Decision: Route_To_Path
  Outcome A — "Discount":
    Condition: {!f_isEligibleForUpsell} = TRUE
               AND {!screen_PreferDiscount} = TRUE
  Outcome B — "Standard":
    Condition: {!f_isEligibleForUpsell} = TRUE
               AND {!screen_PreferDiscount} = FALSE
  Default — "Escalate"

Decision: Pick_Email_Template
  Outcome A — "Upsell Email":
    Condition: {!f_isEligibleForUpsell} = TRUE
  Default — "Standard Email"

Decision: Set_Approval_Required
  Outcome A — "Manager Approval":
    Condition: {!f_isEligibleForUpsell} = TRUE
               AND {!recOpportunity.Amount} > 50000
  Default — "No approval"
```

**Why it works:** The Formula resource is the canonical home for a
derived boolean used in more than one place. Changing the threshold
edits one line in `f_isEligibleForUpsell`; the three Decisions pick
up the change automatically on the next flow execution. The
Description field makes the intent discoverable from the References
panel — when a future admin runs "Where Is This Used?" on the
formula, they see all four reference sites. Critically, this skill
deliberately uses Formula (not Assignment) because the inputs may
change between Decision evaluations as the user advances through the
screen flow — an Assignment would cache the value at one moment and
risk going stale if the user navigated back and edited an answer.

---

## Example 2: Filter a Contact collection with Collection Filter, no Loop

**Context:** A Screen Flow lets a sales rep pick an Account, then
shows a multi-select picklist of the Account's Contacts who are
*decision-makers* (`Title__c` contains "VP" or "Director" or "Chief")
AND are *opted in to email* (`Email_Opt_Out__c = FALSE`). The flow
currently has 8 elements: Get Records (all Contacts on Account),
Loop, three Decision elements inside the loop, an Assignment that
adds matches to a new collection, and a Screen with a Collection
Choice Set fed by that filtered collection. The flow is hard to
read and the loop runs N iterations per render.

**Problem:** The Loop + Assignment + Decision pattern is the
go-to-by-default for collection filtering, but it bloats the flow
canvas, makes the intent harder to read, and runs N iterations for
N records. Flow's debug log shows every iteration, which buries the
actual problem when something goes wrong.

**Solution:** Replace the Loop, three Decisions, and Assignment with
a single **Collection Filter** element (introduced in Summer '23).
Collection Filter applies a set of conditions to a source collection
and writes the matches into a new collection in one step.

```
Get Records: get_AllContactsOnAccount
  Object: Contact
  Filter: AccountId = {!recordId}
  Store: All records → collection col_AllContacts
  Fields to retrieve: Id, FirstName, LastName, Title__c, Email_Opt_Out__c

Collection Filter: filter_DecisionMakersOptedIn
  Source Collection: {!col_AllContacts}
  Conditions (All Conditions Are Met — AND):
    Title__c CONTAINS "VP"          ← logical group: any-of via "OR"
    Title__c CONTAINS "Director"
    Title__c CONTAINS "Chief"
    Email_Opt_Out__c EQUALS FALSE
  Output Collection: {!col_DecisionMakers}

  Note: Collection Filter in Summer '23+ supports a single AND/OR
        group. For the multi-Title OR-then-AND pattern shown above,
        use a Formula resource that returns a Boolean and reference
        it as the single condition:

        Formula: f_isTargetContact (Return Type: Boolean)
          OR(
            CONTAINS({!currentItem.Title__c}, "VP"),
            CONTAINS({!currentItem.Title__c}, "Director"),
            CONTAINS({!currentItem.Title__c}, "Chief")
          )
          AND NOT({!currentItem.Email_Opt_Out__c})

Screen: scr_PickContacts
  Collection Choice Set: ccs_DecisionMakers
    Source: {!col_DecisionMakers}
    Label Field: FirstName + " " + LastName + " (" + Title__c + ")"
    Value Field: Id
    Stored in: {!col_SelectedContactIds}  ← Text Collection variable
```

**Why it works:** Collection Filter is a declarative replacement for
the Loop+Decision+Assignment pattern. The canvas shrinks from 8
elements to 3 (Get Records, Collection Filter, Screen). The debug
log shows one line per filter execution instead of N. Because
Collection Filter operates on the in-memory collection, no SOQL is
issued for the filtering step — the original Get Records already
retrieved every Contact on the Account, and the filter just picks
the matching subset. The Collection Choice Set then renders the
filtered collection as a multi-select picklist on the screen,
storing the chosen Ids in a Text Collection variable that downstream
elements can iterate over for a DML.

The deliberate choice here is **Collection Variable** (an SObject
Collection holding Contact records) feeding a **Collection Choice
Set** — not a Record Choice Set, because Record Choice Set issues
its own SOQL with its own filter and can't reflect the
*already-fetched-and-filtered* result. Using the in-memory collection
keeps the data path single-source.

---

## Anti-Pattern: Global Variable for a value that should be a Formula

**What practitioners do:** A flow needs to compute `Days_In_Stage =
TODAY() - Opportunity.LastStageChangeDate__c` and reference it in
two Decisions and one screen-display field. Practitioners create a
Variable, an Assignment to compute the value, and reference the
Variable everywhere.

```
Variable: v_DaysInStage  (Number)
  Default Value: (none)

Assignment: assign_ComputeDays
  v_DaysInStage = TODAY() - {!recOpportunity.LastStageChangeDate__c}

Decision: Is_Stale
  Outcome: {!v_DaysInStage} > 30 → "Stale"

Decision: Is_Critical
  Outcome: {!v_DaysInStage} > 90 → "Critical"

Screen Display Text: txt_StageAge
  "This opportunity has been in {!recOpportunity.StageName}
   for {!v_DaysInStage} days."
```

**What goes wrong:** The Assignment runs once, at the moment the
flow reaches it. If the flow updates `LastStageChangeDate__c` later
(e.g., after a Stage transition triggered by user input on a
subsequent screen), the Variable holds the old value. The Decisions
and Screen display the stale computation. The bug is invisible until
a user reports "the screen says 47 days but the report says 0" —
which they will, because the bug only manifests when the source
field changes mid-flow.

There's a second cost: the Variable + Assignment occupy two flow
elements on the canvas. A Formula resource is zero elements (it lives
in the Resources panel, not the canvas) and reads as a single line
of intent.

There's also a Process Builder migration trap: practitioners who
migrated from PB carry over the "compute then assign" habit because
PB didn't have formula resources, only formula fields and immediate
actions. Flow's Formula resource is the right home for derived
values in the platform that replaced PB.

**Correct approach:** Promote the derived value to a Formula
resource. Delete the Variable and the Assignment. Reference the
Formula directly from the Decisions and Screen.

```
Formula: f_DaysInStage  (Return Type: Number)
  Expression:
    TODAY() - DATEVALUE({!recOpportunity.LastStageChangeDate__c})
  Description: "Days the Opportunity has been in its current stage.
                Recomputed on every reference — always current."

Decision: Is_Stale
  Outcome: {!f_DaysInStage} > 30 → "Stale"

Decision: Is_Critical
  Outcome: {!f_DaysInStage} > 90 → "Critical"

Screen Display Text: txt_StageAge
  "This opportunity has been in {!recOpportunity.StageName}
   for {!f_DaysInStage} days."
```

The narrow exception where a Variable is the right answer:
the formula is computationally expensive (heavy nested IF, REGEX,
date math) AND is referenced many times inside a loop. In that case,
compute it once with an Assignment from the formula at the top of
the loop body and reference the cached Variable inside — see
`flow/flow-formula-and-expression-patterns` for the cache pattern.
For values referenced 2–4 times outside a loop, always Formula.
