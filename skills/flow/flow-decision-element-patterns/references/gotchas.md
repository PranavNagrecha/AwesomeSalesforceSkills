# Gotchas — Decision Element

Non-obvious behaviours of Flow conditions and outcomes.

---

## Gotcha 1: Text Comparisons Are Case-Insensitive — Except for Ids

**What happens:** A Decision intended to distinguish two similar values matches
both, or an Id comparison that looks correct never matches.

**When it occurs:** Text comparisons in Decision, Wait, and Collection Filter
elements are case-insensitive for Text, Picklist, and Multi-Select Picklist
values. The exception is comparisons that contain Salesforce Id values, which are
**case-sensitive**.

**How to avoid:** Stop relying on case to distinguish values — it does nothing.
And treat Id comparisons as a different class: a hand-copied 15-character Id and
the 18-character version differ in case handling, so compare Ids to references
rather than to literals wherever possible. This asymmetry is the reason a
hardcoded `005` outcome can look right and never fire.

---

## Gotcha 2: A Multi-Select Picklist Is One String, Not a Set

**What happens:** `EqualTo 'Platform'` matches almost nothing on a multi-select
field, and the author concludes the field is broken.

**When it occurs:** Always. A multi-select picklist value is stored and compared
as one semicolon-delimited string — the operators treat `red; blue; green` as a
single value. `EqualTo` therefore matches only when the *entire* selection is
exactly that string, in that order.

**How to avoid:** Use `Contains` for membership, and know what you have bought: a
substring test over the whole delimited string. It will also match a value that
is a substring of another (`Platform` matches `Platform Events`), and it is
case-insensitive. Where two API values share a prefix, `Contains` cannot separate
them — rename the values, or split the string into a real collection before
testing.

---

## Gotcha 3: Null Fails Equality Silently

**What happens:** `{!$Record.Field} = 'X'` returns false when the field is null,
and the null population lands in the default outcome alongside genuinely
different values.

**When it occurs:** Always. It is not an error and not an exception — just false.
Any branch relying on "field is X, or null means X" loses the null case.

**How to avoid:** A field that can be null has three states. Add an explicit
outcome using the `IsNull` operator with a `booleanValue` of `true` — the
operator takes a boolean right-hand value, not an empty string, so comparing to
`''` is a different and usually wrong test.

---

## Gotcha 4: First Match Wins, So a Superset Kills What Follows

**What happens:** An outcome never fires and there is no warning anywhere.

**When it occurs:** Outcomes evaluate top-down and the first match wins. If
outcome A's condition is a superset of outcome B's, and A is listed first, B is
dead code. Flow Builder does not analyse overlap.

**How to avoid:** Order most specific to widest, and review the list as an
ordered sequence rather than a set. A useful review question per outcome: "which
record reaches this one and not the one above it?" If you cannot answer, the order
is wrong or the outcome is redundant.

---

## Gotcha 5: The Default Outcome Absorbs Everything Nobody Named

**What happens:** A record takes a path nobody expected and there is no record of
which condition failed to match.

**When it occurs:** Whenever the default is left as "Default Outcome." It is
simultaneously the intended fallback and the catch-all for every case that was
never considered, and nothing distinguishes them afterwards.

**How to avoid:** Set `defaultConnectorLabel` to the case it actually represents
— "Tier Low (no criteria met)" rather than "Default Outcome." In a flow whose
misrouting matters, have the default write a log row naming the record, so the
difference between "deliberately defaulted" and "silently unmatched" is
observable.

---

## Gotcha 6: Picklist Comparisons Use the API Value

**What happens:** A condition written against a picklist label works for
English-speaking users and fails for everyone on a translated locale.

**When it occurs:** The comparison is against the stored API value. Labels are
translatable; API values are not. Reading the value off the UI gives you the
label.

**How to avoid:** Take the API value from Setup → Object Manager → the field's
value set, not from a record's detail page. Note that this is orthogonal to
Gotcha 1: case-insensitivity does not rescue you from comparing against the wrong
string entirely.

---

## Gotcha 7: "Is Changed" Is Decision-or-Start, Not Wait or Collection Filter

**What happens:** An author tries to use "is changed" in a Collection Filter or a
Wait element and cannot find it — or, the other way round, is told it is
unavailable in entry criteria and builds a Decision they did not need.

**When it occurs:** A set of operators exists specifically to evaluate `$Record`
and its fields in a record-triggered flow. Across Decision, Wait, and Collection
Filter elements they are available only in **Decision** elements. Start-element
entry conditions are a different surface and do support `Is Changed`, but only on
flows triggered when a record is *updated* (not on create), and only when the
trigger is set to run **every time a record is updated** rather than "only when a
record is updated to meet the condition requirements."

**How to avoid:** Prefer entry criteria when the transition test can live there —
a non-match means the interview never starts, which is strictly cheaper than a
Decision. Fall back to a Decision when the flow must run on create as well, when
the "only when updated to meet" trigger option is required, or when the test
belongs on a path the entry criteria cannot express. Do not assume either
location is unavailable.

---

## Gotcha 8: Custom Condition Logic Without Parentheses Is a Bet

**What happens:** `1 AND 2 OR 3` behaves differently from what the author
intended, and the review did not catch it because the expression looked
readable.

**When it occurs:** Whenever a mixed AND/OR expression is written without
grouping. `conditionLogic` accepts an expression referencing conditions by number
and supports parentheses — `1 AND (2 OR 3)` — so the ambiguity is entirely
optional.
`UNVERIFIED (2026-09-12):` the precedence applied when the parentheses are
omitted is not stated in the Metadata API guide, which documents only that
advanced logic of the form `1 AND (2 OR 3)` is accepted. The guidance here
deliberately does not depend on knowing it.

**How to avoid:** Parenthesise every mixed expression, always. And treat a
`conditionLogic` string with more than about four numbered terms as a rule that
has outgrown the element — extract it to a named Formula resource, or to Custom
Metadata if it is really a routing table.

---

## Gotcha 9: A Formula Referenced by Several Outcomes Is Evaluated Each Time

**What happens:** A Decision with six outcomes, each referencing the same
cross-object formula, costs six times what the author expected — and inside a
200-interview batch that arrives as a CPU limit.

**When it occurs:** Formula resources are computed where they are referenced,
not cached across references.

**How to avoid:** For an expensive formula — nested IFs, cross-object lookups —
compute it once into a variable with an Assignment before the Decision and
reference the variable. Cheap formulas are not worth the extra element; the
distinction is whether the formula reaches across objects or does real work.

---

## Gotcha 10: Roll-Up Summary Values Are Stale in a Before-Save Flow

**What happens:** A before-save Decision branches on a roll-up and is
consistently one save behind. Single-record testing passes because the roll-up
did not move.

**When it occurs:** Roll-up summaries are recalculated as part of the save; a
before-save flow reads the pre-transaction value.

**How to avoid:** If the decision genuinely needs the post-save roll-up, it
belongs in an after-save flow — accepting the extra DML that before-save was
chosen to avoid. Where the roll-up is a convenience, computing the needed value
from data the flow already holds is usually cheaper than either.

---

## Gotcha 11: Every Outcome's Cost Multiplies by the Batch Size

**What happens:** A Decision-heavy flow fails on CPU with no obvious expensive
element.

**When it occurs:** Record-triggered and schedule-triggered flows batch up to 200
interviews into one transaction sharing a 10,000 ms synchronous CPU budget. A
Decision whose conditions dereference cross-object formulas is doing that work
200 times.

**How to avoid:** Count the per-interview cost and multiply. Move expensive
evaluation before the Decision into a single Assignment, and prefer conditions
over fields the interview already holds to conditions that reach.

---

## Gotcha 12: A Routing Table Encoded as Branches Is Expensive to Change

**What happens:** Adding a region or a product tier means editing, testing, and
deploying a flow, every time, forever.

**When it occurs:** Whenever the outcomes enumerate *data* — regions, tiers,
product families, queue assignments — rather than *logic*. The tell is that the
outcomes all have the same shape and differ only in a literal.

**How to avoid:** Put the mapping in Custom Metadata, Get Records the matching
row, and let the Decision test whether a row was found. Adding a region becomes a
data change with no deploy. This is the single highest-leverage refactor
available in this domain and it is almost never the first thing anyone reaches
for.

---

## Gotcha 13: Advanced Condition Logic Is Capped at 1,000 Characters

**What happens:** A rule that started as `1 AND 2` grows term by term until the
expression stops being something anyone can review — and eventually stops being
something the field can hold.

**When it occurs:** `FlowRule.conditionLogic` takes `and`, `or`, or advanced
logic such as `1 AND (2 OR 3)`; when advanced logic is used the string can
contain up to 1,000 characters (`api_meta.txt` L71306–L71313). The same three
shapes apply to the Start element's entry conditions
(`api_meta.txt` L72299–L72301 shows `And` / `Or` there).

**How to avoid:** Treat the cap as a design signal rather than a budget. An
expression approaching even a tenth of it is a business rule that has outgrown
one element — lift it into a named Formula resource (`isEscalatable`,
`isAtRiskRenewal`) so the Decision reads as one comparison, or into Custom
Metadata if it is really a lookup table. Nothing good happens at 900 characters.

---

## Gotcha 14: "Only When Changed to Meet Criteria" Exists Per Outcome, Not Only at the Start

**What happens:** An author hand-builds `IsChanged` + `EqualTo` in a Decision
because they believe the "changed to meet criteria" behaviour is a Start-element
setting — or, worse, retrofits one at the Start element and breaks every other
outcome in the flow.

**When it occurs:** `doesRequireRecordChangedToMeetCriteria` is a boolean on
`FlowRule`, available in API version 50.0 and later: "If set to true, conditions
evaluate to true only if the record didn't meet the required conditions before
the triggering update but now meets the conditions after the update"
(`api_meta.txt` L71320–L71324). The identically named field also exists on
`FlowStart` (`api_meta.txt` L72322), which is the one everybody knows about.

**How to avoid:** Decide deliberately where the transition test belongs. At the
Start element it gates the whole interview and every outcome inherits it; on one
`FlowRule` it scopes the transition to that outcome alone and leaves the others
evaluating plain state. When only one branch of several is transition-shaped, the
per-rule flag is the correct place and it is the one most reviewers never look
for in the XML.
`UNVERIFIED (2026-09-12):` how (or whether) Flow Builder surfaces the per-rule
flag in the outcome editor is not stated in the Metadata API guide; the field is
documented as metadata, so a retrieved flow may carry a setting the canvas does
not show.

---

## Gotcha 15: A `rightValue` Carries Exactly One Typed Child

**What happens:** A hand-edited or model-generated condition sets both a literal
and a reference on the same right-hand side, and the reviewer reads whichever one
matches their expectation.

**When it occurs:** `rightValue` is a `FlowElementReferenceOrValue`, whose
definition is explicit: "Defines a reference to an existing element or a
particular value that you specify. Make sure that you specify only one of the
fields" (`api_meta.txt` L70411–L70412). The typed children are mutually
exclusive by contract — `booleanValue`, `stringValue`, `numberValue`,
`dateValue`, `dateTimeValue`, `elementReference`, and the rest each repeat the
warning "If you want to specify a different data type or element reference, don't
use this field."

**How to avoid:** One child per `rightValue`, and let the operator pick which
one. The guide's own Decision example pairs `IsNull` with
`<booleanValue>false</booleanValue>` (`api_meta.txt` L73342–L73344), which is the
canonical shape for the null operators. Comparing a field to another field means
`elementReference` and nothing else.
`UNVERIFIED (2026-09-12):` the guide states the constraint but does not say what
the platform does when two children are present — whether deployment is rejected
or one value silently wins is not documented, so do not rely on either.

---

## Gotcha 16: `None` Is a Real Operator and It Deploys

**What happens:** A half-built outcome ships. The condition looks incomplete in
Flow Builder, so everyone assumes the platform would have stopped it.

**When it occurs:** `None` is a valid `FlowComparisonOperator` whose documented
purpose is to "Save a flow with an incomplete condition, so you can finish
building the flow later," available in API version 58.0 and later
(`api_meta.txt` L70104–L70106). It is a deliberate save-my-work affordance, not
an error state.

**How to avoid:** Grep the flow XML for `<operator>None</operator>` before every
deploy — it is a one-line check and the only reliable one, because an incomplete
condition does not announce itself downstream. The package's checker flags it as
an ERROR for exactly this reason.

---

## Gotcha 17: Every Operator Has an API-Version Floor, and the Flow Carries Its Own `apiVersion`

**What happens:** An operator that exists in the documentation is missing from
the org, or a flow copied from a newer org fails to deploy into an older
package — and the diagnosis wanders into permissions and feature licences.

**When it occurs:** The operator list is versioned, per entry:
`WasSet` from 30.0, `IsChanged` from 52.0 (`api_meta.txt` L70095–L70096), `In`
and `NotIn` from 56.0 (`api_meta.txt` L70089, L70108–L70109), `None` from 58.0,
`IsBlank` and `IsEmpty` from 61.0 (`api_meta.txt` L70090–L70094, L70097–L70098),
`HasError` from 64.0 (`api_meta.txt` L70087–L70088). Meanwhile `Flow.apiVersion`
is "The API version that defines the execution behavior of the flow"
(`api_meta.txt` L68075) — a per-flow value, not an org-wide one.

**How to avoid:** Check the floor before reaching for a newer operator, and check
the flow's own `apiVersion` rather than the org's. The distinction that actually
bites is `IsBlank` versus `IsNull`: `IsBlank` is "a text value with zero
characters or with only whitespace… for other data type values, use to determine
whether a field or variable is null," while `IsNull` is "a value that is either
not set or references no value" (`api_meta.txt` L70090–L70094, L70099–L70101).
On a text field they are different tests — a field holding a single space is
blank but not null — and only one of them is available below API version 61.0.
