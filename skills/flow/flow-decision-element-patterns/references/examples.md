# Examples — Decision Patterns

Worked examples for the Decision element, grounded in what the operators actually
do rather than what they look like they do.

Three behaviours drive most of what follows, and none of them is visible on the
canvas:

1. **Text comparisons in Decision, Wait, and Collection Filter elements are
   case-insensitive** for Text, Picklist, and Multi-Select Picklist values — with
   the exception of comparisons containing Salesforce Id values, which are
   case-sensitive.
2. **A multi-select picklist is one semicolon-delimited string, not a set.** The
   operators treat `red; blue; green` as a single value.
3. **Some operators exist only for `$Record` in a record-triggered flow.** They
   are how you express "did this change" without comparing to `$Record__Prior` by
   hand. Across Decision, Wait, and Collection Filter elements they are available
   only in Decision elements — but Start-element entry conditions support
   `Is Changed` too, under the conditions in Example 4.

---

## Example 1: Ordered Outcomes, With a Named Default

**Context:** Account tiering with four outcomes.

**Problem:** Outcomes evaluate top-down and the first match wins. An outcome
whose condition is a superset of a later one makes the later one dead code, and
nothing in Flow Builder warns you.

**Solution:**

```xml
<decisions>
    <name>Tier_Account</name>
    <label>Tier Account</label>
    <locationX>352</locationX>
    <locationY>278</locationY>
    <defaultConnector>
        <targetReference>Handle_Tier_Low</targetReference>
    </defaultConnector>
    <defaultConnectorLabel>Tier Low (no criteria met)</defaultConnectorLabel>

    <rules>
        <name>VIP_Premium</name>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>$Record.Rating</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue>
                <stringValue>Hot</stringValue>
            </rightValue>
        </conditions>
        <conditions>
            <leftValueReference>$Record.AnnualRevenue</leftValueReference>
            <operator>GreaterThan</operator>
            <rightValue>
                <numberValue>1000000.0</numberValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Handle_VIP_Premium</targetReference>
        </connector>
        <label>VIP Premium</label>
    </rules>

    <rules>
        <name>VIP_Standard</name>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>$Record.Rating</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue>
                <stringValue>Hot</stringValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Handle_VIP_Standard</targetReference>
        </connector>
        <label>VIP Standard</label>
    </rules>

    <rules>
        <name>Tier_Mid</name>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>$Record.Rating</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue>
                <stringValue>Warm</stringValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Handle_Tier_Mid</targetReference>
        </connector>
        <label>Tier Mid</label>
    </rules>
</decisions>
```

**Why the order is what it is:** `VIP_Standard` (Rating = Hot) is a *superset* of
`VIP_Premium` (Rating = Hot AND revenue > 1M). Listing Standard first would make
Premium unreachable. Most specific first, widest last.

**Why `defaultConnectorLabel` matters:** the default absorbs everything nothing
else matched. Naming it "Tier Low (no criteria met)" rather than leaving it
"Default Outcome" is the difference between a triage that knows the record was
deliberately tiered low and one that cannot tell that from a bug.

---

## Example 2: Wrong vs Right — Null Is Not a Value

**Wrong:**

```xml
<rules>
    <name>Acme_Lead</name>
    <conditionLogic>and</conditionLogic>
    <conditions>
        <leftValueReference>$Record.Company</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue>
            <stringValue>Acme</stringValue>
        </rightValue>
    </conditions>
    <connector>
        <targetReference>Route_To_Acme_Team</targetReference>
    </connector>
    <label>Acme Lead</label>
</rules>
<!-- default: everything else -->
```

Two genuinely different populations — leads at other companies, and leads with no
company at all — both fall to the default. The flow cannot distinguish "this
belongs to another team" from "this record is incomplete," which are different
business outcomes.

**Right:**

```xml
<rules>
    <name>Acme_Lead</name>
    <conditionLogic>and</conditionLogic>
    <conditions>
        <leftValueReference>$Record.Company</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue>
            <stringValue>Acme</stringValue>
        </rightValue>
    </conditions>
    <connector>
        <targetReference>Route_To_Acme_Team</targetReference>
    </connector>
    <label>Acme Lead</label>
</rules>

<rules>
    <name>Company_Missing</name>
    <conditionLogic>and</conditionLogic>
    <conditions>
        <leftValueReference>$Record.Company</leftValueReference>
        <operator>IsNull</operator>
        <rightValue>
            <booleanValue>true</booleanValue>
        </rightValue>
    </conditions>
    <connector>
        <targetReference>Request_Company_Name</targetReference>
    </connector>
    <label>Company Missing</label>
</rules>
```

**Why it works:** `IsNull` with a `booleanValue` of `true` is how "is blank" is
expressed in Flow condition metadata — the operator takes a boolean right-hand
value, not an empty string. Comparing to `''` is a different test and will not
match a genuinely null field.

**The general rule:** a field that can be null has three states, not two.
Decide explicitly which branch null takes, and make that decision visible as its
own outcome rather than letting the default swallow it.

---

## Example 3: The Multi-Select Picklist Trap

**Context:** `Product_Interests__c` is a multi-select picklist. The requirement is
"route to the enterprise team if the lead is interested in Platform."

**Problem:** A multi-select picklist value is stored and compared as **one
semicolon-delimited string**. The operators treat `Analytics;Platform;Service` as
a single value, not as three. So `EqualTo` with `Platform` matches only a lead
whose *entire* selection is exactly Platform, and `EqualTo` with
`Analytics;Platform` matches only that exact string in that exact order.

**Solution:** Use a containment operator, and understand what it is matching.

```xml
<rules>
    <name>Interested_In_Platform</name>
    <conditionLogic>and</conditionLogic>
    <conditions>
        <leftValueReference>$Record.Product_Interests__c</leftValueReference>
        <operator>Contains</operator>
        <rightValue>
            <stringValue>Platform</stringValue>
        </rightValue>
    </conditions>
    <connector>
        <targetReference>Route_To_Enterprise</targetReference>
    </connector>
    <label>Interested In Platform</label>
</rules>
```

**Why it works, and the substring hazard it introduces:** `Contains` is a
substring test over the whole delimited string. That gets the right answer here —
and it would also match a value called `Platform Events` or `Multi-Platform`, and
the comparison is case-insensitive, so `platform` matches too. If two API values
in the picklist share a prefix, `Contains` cannot distinguish them.

Where that ambiguity is real, do not solve it in the Decision. Either give the
picklist values that are not substrings of one another, or convert the field to a
proper collection first — a Collection Filter or an Assignment that splits on the
delimiter — and test the collection. Trying to express set semantics through
string operators is where multi-select logic goes wrong quietly.

---

## Example 4: "Did It Change?" — Record-Triggered Operators

**Context:** A record-triggered flow should act only when Stage moves *into*
Closed Won, not on every save of an already-Closed-Won Opportunity.

**Problem:** `$Record.StageName EqualTo 'Closed Won'` is true on every subsequent
save. The naive fix — comparing `$Record.StageName` to
`$Record__Prior.StageName` by hand — works but is verbose and easy to get subtly
wrong on insert, where there is no prior record.

**Solution:** Use the operators that exist for exactly this. A set of operators
is available specifically to evaluate `$Record` or its fields in a
record-triggered flow. Across Decision, Wait, and Collection Filter elements they
are available **only in Decision elements** — not in Wait elements, not in
Collection Filters. Start-element entry conditions are a separate surface and do
support `Is Changed`.

```xml
<rules>
    <name>Newly_Closed_Won</name>
    <conditionLogic>and</conditionLogic>
    <conditions>
        <leftValueReference>$Record.StageName</leftValueReference>
        <operator>IsChanged</operator>
        <rightValue>
            <booleanValue>true</booleanValue>
        </rightValue>
    </conditions>
    <conditions>
        <leftValueReference>$Record.StageName</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue>
            <stringValue>Closed Won</stringValue>
        </rightValue>
    </conditions>
    <connector>
        <targetReference>Create_Renewal_Task</targetReference>
    </connector>
    <label>Newly Closed Won</label>
</rules>
```

**Why it works:** the pair "changed **and** now equals X" is the correct
expression of a transition, and it is the shape a recursion guard needs. The same
flow re-firing on its own update takes the default outcome instead of doing the
work again.

**Where to put it matters:** entry criteria on the Start element are cheaper than
a Decision — the interview never starts — and `Is Changed` is available there,
so prefer entry criteria when the whole test fits. Three cases force it back into
a Decision: the flow must also run on create (the Start-element operator is
update-only), the trigger needs the "only when a record is updated to meet the
condition requirements" option (which `Is Changed` is incompatible with), or the
test belongs on a branch rather than at the gate. Recursion control in depth is
`flow/recursion-and-re-entry-prevention`.

---

## Example 5: Custom Condition Logic — Parenthesise Everything

**Context:** "Route to the escalation queue if the case is high priority AND
either the account is a Platinum customer or the case has been reopened."

**Solution:**

```xml
<rules>
    <name>Escalate</name>
    <conditionLogic>1 AND (2 OR 3)</conditionLogic>
    <conditions>
        <leftValueReference>$Record.Priority</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue>
            <stringValue>High</stringValue>
        </rightValue>
    </conditions>
    <conditions>
        <leftValueReference>varAccountTier</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue>
            <stringValue>Platinum</stringValue>
        </rightValue>
    </conditions>
    <conditions>
        <leftValueReference>$Record.Reopened__c</leftValueReference>
        <operator>EqualTo</operator>
        <rightValue>
            <booleanValue>true</booleanValue>
        </rightValue>
    </conditions>
    <connector>
        <targetReference>Escalate_Case</targetReference>
    </connector>
    <label>Escalate</label>
</rules>
```

**Why it works:** `conditionLogic` accepts an expression referencing conditions by
number, and parentheses group them. `1 AND (2 OR 3)` says exactly what the
requirement says.

**Write the parentheses even when you believe you know the precedence.**
`1 AND 2 OR 3` has *a* meaning; relying on which one is a bet placed on behaviour
that is not worth reasoning about at review time. Parentheses cost nothing and
make the expression self-documenting to the next reader, who will otherwise have
to work it out.
`<!-- UNVERIFIED: the precedence of AND over OR in Flow custom condition logic
when parentheses are omitted was not confirmed against a fetchable official page
during authoring. The guidance above deliberately does not depend on it. -->`

**Keep the condition count low.** A `conditionLogic` string with eight numbered
terms is a business rule that has outgrown the element. Extract the sub-expression
into a Formula resource with a name that states what it means (`isEscalatable`),
and let the Decision read as one comparison.

---

## Anti-Pattern: A Hardcoded User Id or Name as the Routing Rule

**What practitioners do:** Write an outcome as `CreatedById Equals 005...` or
`Owner.LastName Equals "Patel"` — because that is how the org actually behaves
today, and copying an Id out of a record feels like configuration.

**What goes wrong:** It is configuration stored as a person. Deactivation, a
name change, a role change, and a sandbox refresh all break it, and none of them
produces an error. The flow still runs; that outcome simply never fires again,
and the records that should have routed there fall silently to the default. The
Id case is worse after a sandbox refresh, where the Id exists but belongs to a
different person.

**Correct approach:** route on something that describes the *role*: a Custom
Permission, a Queue, a Public Group, or a Custom Metadata record holding the
User or Queue Id so the value has a name and a change process. A literal `005`
in flow XML should not survive review. And note the case-sensitivity asymmetry
while you are here — comparisons containing Salesforce Id values are
case-sensitive, unlike every other text comparison in a Decision, so a
hand-copied 15-character Id can fail to match an 18-character one.

---

## Anti-Pattern: Branching on a Roll-Up in a Before-Save Flow

**What practitioners do:** A before-save flow branches on a roll-up summary field
to decide whether to stamp a value.

**What goes wrong:** roll-up summary fields are recalculated by the platform as
part of the save; a before-save flow reads the value from before this
transaction's changes. The Decision branches on the previous total, so the flow
is consistently one save behind — and the bug is invisible in single-record
testing because the discrepancy only appears when the roll-up actually moves.

**Correct approach:** if the decision genuinely depends on the post-save roll-up,
it belongs in an after-save flow (or later still), which costs the extra DML that
before-save was chosen to avoid. Make that trade knowingly. Where the roll-up is
just a convenience, computing the value the flow needs from data it already has
is usually cheaper than either.

---

## Anti-Pattern: Deeply Nested Decisions Mirroring the Narrative

**What practitioners do:** Transcribe a business description — "if A, then if B,
then if C" — into three chained Decision elements.

**What goes wrong:** the canvas becomes a tree whose leaves are hard to enumerate,
so nobody can confirm every combination is handled. Each level adds a default
outcome that silently absorbs cases, and the combinations that fall through the
defaults are exactly the ones nobody thought about. Debugging requires walking the
tree rather than reading a list.

**Correct approach:** flatten to one Decision with explicit outcomes covering the
real combinations, ordered most specific first. Cap nesting at two. When
flattening produces more outcomes than fit comfortably in one element, that is a
signal to extract a subflow named after the decision domain — and to check
whether the rule belongs in Custom Metadata rather than in flow structure at all.
A routing table with a dozen combinations is data, and encoding data as branches
is what makes it expensive to change.
