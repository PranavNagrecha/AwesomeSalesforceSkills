# FlexCard Composition — Gotchas

Behaviour that makes a correctly-configured card do nothing, leak data, or
render the wrong thing. Property labels are from the Omnistudio FlexCards
Trailhead modules; the pubsub API is from the Lightning Component Reference.

---

## 1. Selecting A Data Node On The Parent Silently Disables The Child's Data Source

**What happens:** A child FlexCard with a perfectly good Integration Procedure
never calls it. The IP shows no invocations. Nothing errors.

**When it occurs:** The parent's Flexcard element has a **Data Node** selected.
The documented rule, verbatim:

> "If a child uses the parent data source, it doesn't matter if its data source
> is configured or set to None. Either way, the parent's data source overrides
> the child's data source if a data node is selected because the record is
> already set."

The child's configured data source is not merely unused — it is overridden, and
the designer gives no indication.

**How to avoid:** Decide the mechanism explicitly. If the child should render
what the parent already fetched, select a **Data Node** (`{record}` for the
current record, `{records}` to send all data) and set the child's data source to
**None** so the intent is legible. If the child needs to fetch its own detail,
leave Data Node unselected and pass an **Attribute** instead — the child
receives it in its **Input Map** and fetches with it.

Debugging shortcut: a child that "isn't calling its data source" is this rule
roughly every time. Check the parent's Flexcard element before investigating
the child.

---

## 2. `register()`'s First Argument Is A Channel, Not An Event

**What happens:** A component subscribes and never receives anything. No error.

**When it occurs:** The parameter is *named* `eventName` in the signature —
`register(eventName, callbackobj)` — but the official example passes
`"testchannel"`. Individual event names live as **keys inside the callback
object**:

```javascript
this.handleMessage = {
  testevent: this.handleTestEvent.bind(this),
  testeventnew: this.handleTestEventNew.bind(this),
};
omnistudioPubsub.register("testchannel", this.handleMessage);
```

Passing the event name as the first argument and a bare function as the second
— the shape every other pubsub library uses — registers a subscription on a
channel nobody publishes to.

**How to avoid:** Read the first argument as a channel. Build the callback
object as a map of event name to bound handler. Then check the publisher: it
must `fire` on the same channel string, and the payload arrives at the handler
keyed by the event name inside the object.

---

## 3. Teardown Needs The Same Object Reference, Not An Equivalent One

**What happens:** Handlers accumulate across navigations. A console workspace
that opens and closes tabs fires the same handler several times per event, and
memory grows.

**When it occurs:** The teardown call constructs a fresh callback object rather
than passing the retained one. The documentation is explicit that you must pass
"both the channel name and instance of your event handler objects" — an
equivalent object is not the same instance.

**How to avoid:** Store the callback object on the component in
`connectedCallback()` and pass that same property in `disconnectedCallback()`.
"To avoid memory leaks or potential errors, always unregister event handlers
when a component is disposed or disconnected."

Note also that the official sample calls `unsubscribe()` in its
`disconnectedCallback()` while the documented method list contains `register`,
`unregister`, and `fire`. Prefer `unregister`, and verify the teardown actually
fires in your runtime.

---

## 4. Channel And Event Names Are A Flat, Page-Wide Namespace

**What happens:** Two unrelated cards on the same Lightning page interfere. A
row click in one refreshes the other.

**When it occurs:** Both use a generic name — `rowselected`, `refresh`,
`update`. Channel and event names are lowercase strings with no namespacing
mechanism, and the page is the scope.

**How to avoid:** Prefix by workspace, not by component:
`quoteworkspace`/`quoteselected`, `caseworkspace`/`caseselected`. Prefixing by
component breaks the moment a second consumer legitimately wants the event.
Record the contract — channel, event, payload shape, publisher, consumers,
version — somewhere both authors will see it.

---

## 5. Every Data Source On The Page Fires At Render

**What happens:** A page with a parent and four children takes five round trips
to first paint, and the user waits for the slowest.

**When it occurs:** Each card with its own data source fetches independently.
There is "no limit to the number of child Flexcards on one Flexcard," so
nothing constrains this but design.

**How to avoid:** Where the parent already has the data, pass it down with a
**Data Node** rather than letting the child fetch — one round trip instead of
two. Where the pieces are genuinely independent, keep them independent but
make sure the aggregate is deliberate. Aggregating server-side in one
Integration Procedure is almost always cheaper than aggregating client-side in
card composition, because it collapses N round trips into one.

---

## 6. The SOQL Data Source Has Nowhere To Put Enforcement, Caching, Or Error Handling

**What happens:** A card ships with a SOQL data source, is later placed on an
Experience Cloud page, and returns fields the external audience should not see.

**When it occurs:** The SOQL Query data source "uses the Salesforce Object
Query Language (SOQL) to search an org's Salesforce data" — it runs the query
you typed. Unlike an Integration Procedure, there is no step where field-level
security is enforced, no Cache Block, no `requiredPermission`, and no error
branch.

**How to avoid:** Treat SOQL and Custom as prototyping data sources. Ship on
**Integration Procedures** or **Omnistudio Data Mapper** with
`fieldLevelSecurityEnabled` true. The projection matters independently of
security: a payload crosses the network and lands in the browser whether or not
the template renders it.

---

## 7. A State Hides An Action; It Does Not Prevent It

**What happens:** An "Escalate" action is placed only in the `AtRisk` state,
and this is recorded as an access control.

**When it occurs:** "A Flexcard state determines what the user can see and do on
the card," and conditions select the state from data the browser already holds.
The evaluation is client-side.

**How to avoid:** Enforce on the target, not the state — the OmniScript's or
Integration Procedure's `requiredPermission`, and the underlying object and
field permissions of the running user. Use states for UX; use platform
permissions for authorization. The two are frequently confused because the
observable behaviour is the same for a well-behaved user.

---

## 8. The Author's Preview Is Not The Audience's Runtime

**What happens:** A card works in the designer and fails, or over-shares, for an
Experience Cloud user.

**When it occurs:** Preview runs with the author's permissions and the author's
context. The card's real audience may be a guest, a portal user, or a user with
a narrower profile, and FlexCards publish to several very different hosts:
Lightning pages via Lightning App Builder, Community and portal pages via
Experience Builder, external content management systems such as Adobe
Experience Manager, and custom web containers such as Heroku.

**How to avoid:** Test in the target host as a user from the target audience,
and compare the *payload*, not only the rendering. An over-permissive data
source is invisible in the rendered card and obvious in the network response.

---

## 9. `OmniUiCard` Is Marked Internal Use Only

**What happens:** Someone writes an Apex utility or a data-loader job to bulk
create, edit, or clean up FlexCard records.

**When it occurs:** `OmniUiCard` is a real standard object, present in the
object reference from API 51.0 through 67.0 — and the object reference states:
"This object and associated records are only for internal use. Don't perform
any create, edit, or delete operations on this object." It adds: "Modifying or
deleting this object's records may result in errors with your implementation."

**How to avoid:** Never DML `OmniUiCard`. Read it if you need an inventory;
change FlexCards through the designer or through your deployment tooling.

Worth knowing when planning deployment: the **Omnistudio Metadata API Types**
page lists ten types — Flow for Omnistudio, `OmniDataTransform`,
`OmniExtTrackingDef`, `OmniIntegrationProcedure`, `OmniInteractionAccessConfig`,
`OmniInteractionConfig`, `OmniScript`, `OmniscriptDefinition`,
`OmniStudioSettings`, `OmniTrackingGroup` — and `OmniUiCard` is **not** among
them.

<!-- UNVERIFIED: what that absence means for FlexCard deployment. Third-party
sources (Gearset documentation, community posts) state OmniUiCard can be
deployed as a standard metadata type once the OmniStudio Metadata setting is
enabled, which is in tension with its absence from the Omnistudio Metadata API
Types list and with the object's internal-use-only marking. I could not resolve
this against a Salesforce-published source. Verify your FlexCard deployment path
in a sandbox before committing a release process to it. -->

---

## 10. `{Parent.Id}` Only Resolves For A Child That Received An Attribute

**What happens:** A card uses `{Parent.something}` merge syntax and renders
blank.

**When it occurs:** The `{Parent.…}` reference is available to a **child**
FlexCard for values that arrived through the parent's **Attributes**, surfaced
in the child's **Input Map**. A sibling card communicating over a pubsub channel
has no parent, and a card embedded some other way has no Input Map entry to
resolve against.

**How to avoid:** Match the merge syntax to the composition mechanism.
Parent/child with Attributes → `{Parent.…}`. Siblings over a channel → the
payload delivered to the handler. Page context → the input parameter (e.g.
`recordId`) the host supplies.

---

## 11. Input Parameters Are Evaluated At Render; They Do Not React

**What happens:** A value passed in as an input parameter does not update when
the underlying state changes, and the card looks stale.

**When it occurs:** Input parameters carry the immutables — record id, layout
flags, context — and are resolved when the card renders. They are not a
reactive binding.

**How to avoid:** Separate the two categories deliberately in the design:
immutables travel as input parameters and Attributes; mutables travel as events
on a channel. A value that must change during the card's life belongs in the
second category. Trying to make an input parameter reactive is how cards
acquire forced re-render hacks.
