# LLM Anti-Patterns — FlexCard Composition

Mistakes AI coding assistants reliably make when designing FlexCard
composition. Each entry names the wrong output, the mechanism producing it, the
corrected version, and a mechanical check.

FlexCards are a high-hallucination surface for two compounding reasons: the
public corpus describes the Vlocity managed package far more than the standard
runtime, and FlexCard concepts (channels, states, data nodes) have same-named
but differently-shaped equivalents in mainstream web frameworks that a model
will substitute without noticing.

---

## Anti-Pattern 1: A Generic pubsub API Instead Of `lightning/omnistudioPubsub`

**What the LLM generates:** a plausible pubsub import and a conventional
subscribe call:

```javascript
// WRONG on every line
import { fireEvent, registerListener } from 'c/pubsub';
import pubsub from 'omnistudio/pubsub';
import { subscribe } from 'lightning/omnistudioPubsub';

registerListener('quoteselected', this.handleQuote, this);
pubsub.subscribe('quoteselected', this.handleQuote);
```

**Why it happens:** `c/pubsub` is the well-known Salesforce LWC pubsub *sample*
from the lwc-recipes repository — it is real, widely copied, and has exactly
this `registerListener`/`fireEvent` shape. The model has seen it thousands of
times in an LWC context and reaches for it. `omnistudio/pubsub` is a
managed-package-era guess produced by pattern-matching the namespace. And
`subscribe`/`unsubscribe` is the near-universal verb pair across pubsub
libraries, so it gets substituted for `register`/`unregister` even when the
import is right.

**Correct pattern:**

```javascript
import pubsub from "lightning/omnistudioPubsub";

// Public methods, per the Lightning Component Reference:
//   register(eventName, callbackobj)
//   unregister(eventName, callbackobj)
//   fire(eventName, action, payload)
```

**Detection hint:** Mechanical. Any import of `c/pubsub`, `omnistudio/pubsub`,
or a named export from `lightning/omnistudioPubsub` is wrong — the module has a
**default** export. Any call to `subscribe`, `unsubscribe`, `registerListener`,
`unregisterListener`, `fireEvent`, `publish`, or `dispatch` on that module is
wrong. Grep for the three real method names.

---

## Anti-Pattern 2: Passing An Event Name Where A Channel Is Expected

**What the LLM generates:** the shape every other pubsub library uses — an
event name and a single handler function:

```javascript
// WRONG — subscribes to a channel named "quoteselected" that nobody fires on
pubsub.register('quoteselected', this.handleQuote.bind(this));
```

**Why it happens:** This is the subtlest error in the domain, and the
documentation invites it: the parameter is *named* `eventName` in the signature
`register(eventName, callbackobj)`, but the official example passes
`"testchannel"`. A model reading the signature does exactly what the parameter
name says. The second argument compounds it — `callbackobj` is a *map of event
names to handlers*, not a handler, and "callback" strongly implies a function.

The result subscribes successfully and receives nothing, with no error on
either side.

**Correct pattern:**

```javascript
connectedCallback() {
  // Retain the object: teardown needs this exact instance.
  this.handleMessage = {
    quoteselected: this.handleQuote.bind(this),
    quotecleared:  this.handleCleared.bind(this),
  };
  // First argument is the CHANNEL.
  pubsub.register('quoteworkspace', this.handleMessage);
}

disconnectedCallback() {
  pubsub.unregister('quoteworkspace', this.handleMessage);
}
```

**Detection hint:** Any `register()` call whose second argument is a function
rather than an object literal. Any `register()` whose first argument matches an
event name used in a `fire()` call elsewhere — publisher and subscriber must
agree on the *channel*, and the event name lives inside the callback object.

---

## Anti-Pattern 3: Inventing A Child-Card Data-Passing Mechanism

**What the LLM generates:** a stringify/parse bridge, or a made-up property:

```text
Parent: set attribute "recordJson" = {JSON.stringify(record)}
Child : parse recordJson in a custom LWC

...or invented properties:
    passDataToChild: true
    childRecords: {records}
    inheritDataSource: true
```

**Why it happens:** "Pass data from parent to child" is one of the most
generic problems in component design, and the model has an enormous prior for
solving it with props. Serialising into a string attribute is the universal
escape hatch when a framework's prop system will not carry an object. The
model does not know two purpose-built mechanisms already exist, so it
reconstructs one — and the reconstruction works well enough to ship, which
removes the corrective feedback.

**Correct pattern:**

```text
Two mechanisms, both on the parent's Flexcard element:

  Data Node field  "select an available data node to pass a record or an
                    array of records to the child Flexcard"
                      {record}   -> the current record's data
                      {records}  -> "sends all data"

  Attributes       enter the attribute name and its value, e.g.
                      Attribute: Id     Value: {Id}
                    Arrives in the child's Input Map; the child references
                    it as {Parent.Id} and fetches its own detail.

Choose by need:
  child renders what the parent already has  -> Data Node
  child needs MORE, or fresher, data         -> Attributes + own fetch
```

**Detection hint:** Any `JSON.stringify` in a FlexCard attribute value. Any
child-card property name not in {Flexcard Name, Data Node, Attributes}. Any
proposal that routes parent-to-child data through a custom LWC when neither
side needs custom rendering.

---

## Anti-Pattern 4: Missing The Data Node Override Rule

**What the LLM generates:** a design where the parent selects a Data Node *and*
the child is configured with its own Integration Procedure, described as "the
child fetches fresh detail while receiving context from the parent."

**Why it happens:** Both configurations are individually valid and individually
documented, and in most component frameworks passing a prop and fetching
internally compose freely. The override is a platform-specific interaction rule
stated in one sentence of one Trailhead unit. Nothing about the two
configurations, read separately, suggests one cancels the other.

**Correct pattern:**

```text
Verbatim: "If a child uses the parent data source, it doesn't matter if its
data source is configured or set to None. Either way, the parent's data
source overrides the child's data source if a data node is selected because
the record is already set."

So: selecting a Data Node SILENTLY DISABLES the child's own data source.

  Want the child to render the parent's data?
      -> select Data Node, set child data source to None (for legibility)

  Want the child to fetch its own?
      -> leave Data Node UNSELECTED, pass an Attribute instead

  Want both a parent-supplied record AND an independent fetch?
      -> these are siblings, not parent/child. Use a pubsub channel.
```

**Detection hint:** Any design or configuration where a Data Node is selected on
the parent's Flexcard element and the child's data source type is anything other
than **None**. The child's data source is dead code; either the Data Node or the
data source is wrong.

---

## Anti-Pattern 5: The SOQL Data Source On A User-Facing Card

**What the LLM generates:** the fastest path to data:

```text
Data source type: SOQL Query
Query: SELECT Id, Name, SSN__c, AnnualIncome__c FROM Contact WHERE Id = '{recordId}'
```

**Why it happens:** SOQL is the Salesforce data-access idiom the model knows
best by a wide margin, and the SOQL data source is the option that most
resembles writing code. The model also has no signal about the card's eventual
audience — a card built for an internal console and a card built for a guest
Experience Cloud page look identical at design time. Selecting every field the
template might want is standard practice everywhere else.

**Correct pattern:**

```text
SOQL Query and Custom are PROTOTYPING data sources. They have nowhere to put:
    - field-level security enforcement
    - a Cache Block
    - requiredPermission
    - an error branch

Ship on:
    Integration Procedures      "returns data from multiple internal and
                                 external sources" - aggregation, caching,
                                 error handling, access enforcement
    Omnistudio Data Mapper      "uses a Data Mapper Extract interface to
                                 return data from a Salesforce object"
                                 with fieldLevelSecurityEnabled = true

Project down: return only the fields the card renders. The payload crosses
the network and lands in the browser whether or not the template shows it.
```

**Detection hint:** `SOQL Query` or `Custom` as the data source type on any card
destined for a Lightning page, Experience Builder site, or external host. Also
flag any data source returning fields the card's template does not reference.

---

## Anti-Pattern 6: Treating A State As An Access Control

**What the LLM generates:** "Place the Escalate action in the AtRisk state so
only at-risk accounts can be escalated," presented as a security design.

**Why it happens:** Conditional rendering *is* the access-control mechanism in
plenty of front-end architectures the model has learned from, where the server
is assumed to enforce separately and the UI just reflects it. FlexCard states
look exactly like that pattern. The model states the security conclusion
because in its reference architectures the server-side half is implicit — but
here nobody wrote it.

**Correct pattern:**

```text
"A Flexcard state determines what the user can see and do on the card."
Conditions evaluate data the browser already holds. Evaluation is CLIENT-SIDE.

States are a UX mechanism. Authorization lives on the action's target:
    - requiredPermission on the target OmniScript or Integration Procedure
    - object and field permissions of the running user
    - the sharing model

Hiding an action and preventing it are different things. They look identical
for a well-behaved user, which is why this survives review.
```

**Detection hint:** Any state condition described with security vocabulary —
"only", "restricted to", "prevents", "not allowed". Ask what happens if the
action's target is invoked directly. If the answer is "it would work," the
control is cosmetic.

---

## Anti-Pattern 7: The Fat Card

**What the LLM generates:** one FlexCard specification with seven states, five
data sources, and a dozen actions, in response to "design a card for the
account workspace."

**Why it happens:** The prompt asks for *a card*, singular, so the model
produces one artifact. Decomposition into a container plus children or siblings
requires inventing structure the prompt did not ask for, and models default to
satisfying the literal request. The single-artifact answer also *reads* as more
complete, which makes it the more rewarded output.

**Correct pattern:**

```text
Every data source on the page fires at render. Five data sources on one card
is five round trips before first paint, and the user waits for the slowest.

Decompose:
    container card  -> layout and composition, often no data source
    child cards     -> fed by Data Node where the parent already has the data
    sibling cards   -> own their fetch, communicate over a pubsub channel

"There's no limit to the number of child Flexcards on one Flexcard", so the
platform does not constrain this - only design does.

The cost is an event contract you must write down. The benefit is that each
piece is independently reviewable, reusable, and optimisable.
```

**Detection hint:** More than two data sources on a single card, or more than
three states. Either is a decomposition signal. Also flag any card whose states
have overlapping conditions — that is the specific defect a fat card hides,
because no reviewer can hold seven conditional layouts in mind at once.

---

## Anti-Pattern 8: Hardcoded URLs In Navigation Actions

**What the LLM generates:**

```text
Action type: Navigate
Target: /lightning/r/Quote/{Id}/view
```

**Why it happens:** The model has seen that URL shape constantly — it is what
appears in a browser address bar and in every screenshot and bug report. It is
also correct in exactly one host. FlexCards publish to Lightning pages,
Experience Builder sites, external CMSs such as Adobe Experience Manager, and
custom web containers such as Heroku, and `/lightning/r/...` resolves in only
the first.

**Correct pattern:**

```text
Use the Navigate action type and let the platform resolve the destination
from the record and target, rather than composing a path.

FlexCard action types cover: launching guided processes, displaying flyout
windows, navigating to other records, listening for events from other
FlexCards, and notifying components.

A hardcoded /lightning/ path breaks silently the day the card is reused on
an Experience Builder page, which is also the day nobody is looking at it.
```

**Detection hint:** Any literal `/lightning/`, `/s/`, `/apex/`, or full-domain
URL in an action target. Any string concatenation that builds a path. Any
navigation that would need editing to work on a second host.
