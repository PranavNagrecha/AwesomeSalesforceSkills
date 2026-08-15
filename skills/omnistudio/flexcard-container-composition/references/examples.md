# FlexCard Composition — Examples

Data source names, child-card property labels, and the pubsub API below are
quoted from the Omnistudio FlexCards Trailhead modules and the
`lightning/omnistudioPubsub` reference in the Lightning Component Reference.
Where a name comes from the managed package rather than the standard runtime,
it is labelled inline.

---

## Example 0: The Ten Data Source Types, By Exact Label

**Context:** Half of all FlexCard design mistakes are a data source chosen by
convenience rather than by fit, and the other half are a data source named
wrongly in a design doc so nobody can tell which was chosen.

**Solution — the Data Source wizard's complete list, verbatim:**

| Data source type | Verbatim description | Reach for it when |
|---|---|---|
| **Integration Procedures** | "uses an Integration Procedure to return data from multiple internal and external sources" | the default. One place to cache, one place to centralise errors, one place to enforce access. |
| **Omnistudio Data Mapper** | "uses a Data Mapper Extract interface to return data from a Salesforce object" | a single-object read with no aggregation and no callout. |
| **Apex Remote** | "uses an Apex Remote class and method to return data" | logic that genuinely needs code, invoked through the `Callable` interface. |
| **Apex REST** | "uses a REST endpoint of an Apex class to return data" | an existing Apex REST service you do not want to re-wrap. |
| **SOQL Query** | "uses the Salesforce Object Query Language (SOQL) to search an org's Salesforce data" | prototyping only — see Example 5. |
| **SOSL Search** | "uses the Salesforce Object Search Language (SOSL) to construct text-based search queries" | genuine cross-object text search. |
| **Streaming API** | "uses the Salesforce Streaming API to send notifications of general events" | a card that must react to server-pushed events. |
| **SDK** | "uses a method from a Software Development Kit (SDK) to get data to populate fields" | an SDK-backed integration. |
| **Custom** | "uses sample JSON to set up a Flexcard with temporary data that'll eventually be replaced" | design-time scaffolding. Not a shipping state. |
| **None** | for child FlexCards that receive data from parent FlexCards instead | any child fed by its parent — see Example 2. |

**Why it works:** Naming the type exactly is what lets a reviewer check the
decision. "It uses a DataRaptor" is ambiguous between **Omnistudio Data Mapper**
and a Data Mapper called from inside an **Integration Procedure**, and those
have different caching, error-handling, and security properties.

---

## Example 1: Account Overview — One Card, One Integration Procedure

**Context:** A single-record summary on the Account Lightning record page:
account header fields, top three open opportunities, last three cases, two
actions.

**Problem — the version that looks efficient:** four data sources on one card,
one per section. Four server round trips on every render, four independent
failure modes, and four places to change when the access model changes.

**Solution:**

```text
FlexCard: AccountOverview
  Data source type : Integration Procedures
  Integration Proc : Account_Overview   (Type_SubType)
  Input            : recordId  <- from Lightning page context

  States
    ├── Active      condition: {Account.IsActive} == true
    └── Inactive    condition: default

  Actions
    ├── "Open Case"      launch a guided process (OmniScript), flyout
    └── "Edit Industry"  target: an Integration Procedure, not a direct write
```

The Integration Procedure does the aggregation server-side: one round trip, one
error surface, one place to add a Cache Block later, and one place where field
access is enforced.

**Why it works:** Composition choices *are* performance choices. Every data
source on a page is a server call at render; collapsing four into one is a
larger win than any client-side optimisation available afterwards.

---

## Example 2: Parent To Child — The Two Real Mechanisms

**Context:** A quotes list that drills into a quote detail.

**Problem:** People invent a third mechanism — stringify the record into a
custom attribute and parse it in the child — because they have not seen the two
that exist.

**Solution — the parent's Flexcard element has three properties that matter:**

| Property | Purpose |
|---|---|
| **Flexcard Name** field | selects which child card to embed |
| **Data Node** field | "This is where you select an available data node to pass a record or an array of records to the child Flexcard." `{record}` sends the current record's data; `{records}` "sends all data." |
| **Attributes** | pass specific field values — enter the attribute name, then the value, e.g. attribute `Id` with value `{Id}` |

On the child, incoming attributes appear in the **Input Map** section of its
Setup tab, and the child references parent data with `{Parent.Id}` syntax.

So the two mechanisms are:

```text
Mechanism A — whole record or array, via Data Node
    Parent  : Flexcard element, Data Node = {record}
    Child   : data source type = None (or anything — see below)
    Use when: the child renders exactly what the parent already fetched

Mechanism B — specific fields, via Attributes
    Parent  : Flexcard element, Attributes: Id -> {Id}
    Child   : Input Map receives Id; child fetches its own detail
    Use when: the child needs MORE than the parent has, or fresher data
```

**The override rule, verbatim, and it surprises people:**

> "If a child uses the parent data source, it doesn't matter if its data source
> is configured or set to None. Either way, the parent's data source overrides
> the child's data source if a data node is selected because the record is
> already set."

That is: **selecting a Data Node on the parent silently disables the child's
own data source.** A child card that "isn't calling its Integration Procedure"
is usually this, not a broken IP. If you want the child to fetch, pass an
attribute (Mechanism B) and leave the Data Node unselected.

**Why it works:** Choosing between A and B is a real design decision — A is one
round trip and a coupled shape; B is two round trips and an independent child.
Knowing the override rule is what stops you accidentally getting A while
believing you configured B.

---

## Example 3: Sibling Cards — The Real pubsub API

**Context:** Two FlexCards on the same Lightning page must communicate, or a
FlexCard must talk to a custom LWC.

**Solution — the standard-runtime module, verbatim from the Lightning Component
Reference:**

```javascript
import pubsub from "lightning/omnistudioPubsub";
```

| Method | Signature | Purpose |
|---|---|---|
| `register` | `register(eventName, callbackobj)` | registers event handlers to a channel |
| `unregister` | `unregister(eventName, callbackobj)` | removes event handlers from a channel |
| `fire` | `fire(eventName, action, payload)` | fires an event to all registered handlers on a channel |

The official example:

```javascript
import omnistudioPubsub from "lightning/omnistudioPubsub";

export default class TestComponent extends LightningElement {
  connectedCallback() {
    this.handleMessage = {
      testevent: this.handleTestEvent.bind(this),
      testeventnew: this.handleTestEventNew.bind(this),
    };
    omnistudioPubsub.register("testchannel", this.handleMessage);
  }

  handleTestEvent(event) {
    //Some logic here
  }

  handleTestEventNew(event) {
    //Some logic here
  }

  disconnectedCallback() {
    omnistudioPubsub.unsubscribe("testchannel", this.handleMessage);
  }
}
```

Three things to read carefully in that example:

1. **The first argument is a channel, not an event.** `register("testchannel",
   …)` subscribes to a channel; the *callback object* maps individual event
   names (`testevent`, `testeventnew`) to handlers. The parameter is named
   `eventName` in the signature but is used as a channel name. Treat it as a
   channel.
2. **Handlers must be bound and retained.** `this.handleMessage` is stored on
   the component precisely so the same object reference can be passed to the
   teardown call. A fresh object literal at teardown unregisters nothing.
3. **The doc's own sample calls `unsubscribe`, not `unregister`.** The
   documented method list contains `register`, `unregister`, and `fire`. Prefer
   `unregister` — it is the method the reference documents — and verify the
   teardown actually fires in your target runtime.

   <!-- UNVERIFIED: whether `unsubscribe` is a real alias for `unregister` or an
   error in the official code sample. The Lightning Component Reference page for
   lightning/omnistudioPubsub lists register/unregister/fire as the public
   methods and then uses unsubscribe in its example. I could not resolve the
   discrepancy against another Salesforce-published source. -->

Teardown is not optional: "to avoid memory leaks or potential errors, always
unregister event handlers when a component is disposed or disconnected," and
you must pass "both the channel name and instance of your event handler
objects."

**Why it works:** The channel/callback-object shape is genuinely unusual — most
pubsub APIs take one event name and one function — and getting it wrong
produces a component that appears to subscribe and never receives anything.

---

## Example 4: Quotes List To Quote Detail, End To End

**Context:** Putting Examples 2 and 3 together.

```text
FlexCard: QuoteList                       [parent]
  Data source : Integration Procedures -> Quote_ListForAccount
  Input       : accountId <- page context
  Layout      : one row per quote

  Row action  : notify other components
                channel  : "quoteworkspace"
                event    : "quoteselected"
                payload  : { quoteId: "{Id}" }

FlexCard: QuoteDetail                      [sibling, NOT a child]
  Data source : Integration Procedures -> Quote_Detail
  Input       : quoteId
  Subscribes  : channel "quoteworkspace", event "quoteselected"
                -> sets quoteId, re-fetches
```

**Why sibling and not parent/child here:** a child fed by a Data Node renders
what the parent already has. A quote *detail* needs more fields than a quote
*list* row carries, so the child would have to fetch anyway — and if the parent
selects a Data Node, the child's own data source is overridden and it cannot.
Siblings communicating over a channel keeps each card owning its own fetch.

**Channel naming.** Channel and event names are lowercase strings in a flat
namespace shared by everything on the page. Two cards using `rowselected` will
interfere. Prefix by workspace: `quoteworkspace` / `quoteselected`,
`caseworkspace` / `caseselected`. Record the contract somewhere both cards'
authors will see it:

```json
{
  "channel": "quoteworkspace",
  "event": "quoteselected",
  "payload": { "quoteId": "0Q0xx0000004C92GAE" },
  "firedBy": "QuoteList",
  "consumedBy": ["QuoteDetail", "QuoteActivityPanel"],
  "version": 2
}
```

---

## Example 5: The SOQL Data Source Is A Prototyping Tool

**Context:** A card needs three fields from Contact. The SOQL Query data source
is two clicks.

**Problem:** The SOQL data source runs a query you typed. It is the one data
source with no place to put access enforcement, no place to put a cache, and no
place to put error handling — everything an Integration Procedure gives you for
free is absent by construction.

**Solution — what the same read looks like through an IP:**

```text
Integration Procedure: Contact_CardSummary
  ├── Data Mapper Extract   getContact
  │      fieldLevelSecurityEnabled = true
  │      returns only: Name, Title, Email, Phone
  └── Response Action       returnSummary
```

The IP version gives you a projection (only the fields the card renders leave
the server), FLS enforcement on the read, one place to add a Cache Block, and a
`requiredPermission` hook. The SOQL version gives you none of those and is
faster to build, which is exactly why it ships.

**Why it works:** The projection alone justifies it. A card that renders four
fields should not have a data source capable of returning forty, because the
payload crosses the network and lands in the browser regardless of what the
template displays.

---

## Example 6: States Are Conditional Layouts, Not Conditional Fields

**Context:** A card must look different for an active vs. a churned account.

**Solution:** "A Flexcard state determines what the user can see and do on the
card." Conditions evaluate the data and select the matching state
automatically.

```text
FlexCard: AccountHealth
  States, evaluated in order
    ├── AtRisk      condition: {HealthScore} < 40
    │                 elements: red banner, "Escalate" action (OmniScript)
    ├── Watch       condition: {HealthScore} < 70
    │                 elements: amber banner, "Add Note" action
    └── Healthy     condition: default
                      elements: standard summary, no escalation action
```

The design consequence people miss: **a state changes the available actions,
not just the visuals.** Putting "Escalate" only in the `AtRisk` state is a UX
decision, not an access control — the state is evaluated client-side against
data the browser already has. If escalation must be *prevented* rather than
*hidden*, enforce it on the action's target (the OmniScript's or IP's
`requiredPermission` and the underlying object permissions), not on the state.

**Why it works:** States collapse what would otherwise be several cards and a
routing rule into one card that adapts. The failure mode is treating a hidden
element as a secured one.

---

## Anti-Pattern: The Fat Card

**What practitioners do:** one FlexCard with seven states, five data sources,
and a dozen actions, because it is one artifact to deploy and one place to look.

**What goes wrong:** every data source fires at render, so load time is the sum
of the slowest paths rather than of the ones the user will look at. Nothing is
reusable — a second page that needs one of those seven views must take all
seven. And the card becomes un-reviewable: no reader can hold seven conditional
layouts and their interactions in mind, so state-condition overlaps go
unnoticed until a user reports the wrong layout.

**Correct approach:** a container plus children or siblings, each owning one
data source and one concern. There is "no limit to the number of child
Flexcards on one Flexcard," so decomposition is not constrained by the platform.
Compose with Data Nodes where the parent already has the data, and with a
pubsub channel where the pieces are genuinely independent. The cost is an event
contract you must write down; the benefit is that each piece can be reviewed,
reused, and made fast on its own.
