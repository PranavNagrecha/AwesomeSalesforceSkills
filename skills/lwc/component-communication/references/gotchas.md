# Gotchas - Component Communication

## Default Event Propagation Is Narrower Than Many Teams Expect

**What happens:** A child dispatches a custom event, but the parent or ancestor never receives it.

**When it occurs:** The event needs to bubble or cross a shadow boundary, but `bubbles` and `composed` were not set intentionally.

**How to avoid:** Decide the propagation scope up front and set event options explicitly rather than assuming the default is enough.

---

## Event Names Are Public API

**What happens:** A component ships event names with uppercase letters, spaces, or `on` prefixes, and consumers struggle to wire listeners consistently.

**When it occurs:** Teams treat event names like arbitrary strings instead of markup-facing API contracts.

**How to avoid:** Use lowercase, intention-revealing event names and keep them stable once consumers depend on them.

---

## LMS Without Cleanup Creates Sticky Behavior

**What happens:** Components continue reacting to messages after the user has navigated away or changed workspace context.

**When it occurs:** A subscription is created but not released at the right lifecycle boundary.

**How to avoid:** Subscribe intentionally, keep the subscription handle, and unsubscribe when the component scope ends.

---

## Mutable Shared Objects Make Ownership Ambiguous

**What happens:** A parent and child both mutate the same object reference, and rerender behavior becomes confusing.

**When it occurs:** Teams pass rich objects down and treat them like shared state rather than input plus event-driven updates.

**How to avoid:** Keep data flow directional. Clone or reconstruct state in the owner component and pass only what the child needs.

---

## A Child That Mutates An Object It Received Through `@api` Throws — But Only Where You Can See It

**What happens:** `this.someApiObject.field = 'x'` inside the child raises
`Uncaught Error: Invalid mutation: Cannot set "msg" on "[object Object]". "[object Object]" is read-only.`
Non-primitive values arriving from a parent are wrapped in a proxy.

**When it occurs:** Any time a child treats a passed-in record, array, or config object as
shared mutable state. The error surfaces only with Lightning Web Security enabled and
debug mode active, so the same code can look like it "works" in a production org and then
break the moment someone turns debug mode on to investigate something else.

**How to avoid:** Never write through an `@api` reference. Make a shallow copy in the
owner (`this.obj = { ...this.obj, msg: 'new' }`) or send an event upward and let the owner
reassign. A shallow copy inside the *child* rerenders the child only and never propagates
to the parent, which is usually not what the author intended either.

*Grounded: `create-components-data-binding` (`lwc_guide.txt` L2005, L2007–L2011);
`create-components-data-flow` L2021.*

---

## `compact="false"` On A Boolean Public Property Evaluates To True

**What happens:** A parent writes `<c-case-priority-card compact="false">` to turn a
feature off and the child sees `true`. Boolean public properties follow the HTML boolean
attribute rule: presence means true, and any string value is present.

**When it occurs:** Whenever the boolean is written literally in markup rather than bound
to a getter. It also occurs when a public boolean is given a default of `true` in the
child — there is then no way at all to statically set it to `false` from markup.

**How to avoid:** Always default a public boolean to `false`, omit the attribute to mean
false, and write the attribute bare (`compact`) to mean true. To toggle it at runtime, bind
a computed value from the parent: `<c-child compact={isCompact}>`.

*Grounded: `js-props-boolean` (`lwc_guide.txt` L2492, L2497).*

---

## `bubbles: true, composed: true` Signs Every Ancestor Up To Your Event Name

**What happens:** The event travels to the document root. The event type becomes part of
the public API of the dispatching component *and of every consuming component and all of
its ancestors*. Because it reaches the root, two unrelated components using the same event
name collide and the wrong listener fires.

**When it occurs:** Copied from Aura-era snippets, or added while debugging "the parent
isn't receiving it" when the real fix was to move the listener onto the child's own tag.

**How to avoid:** Start at `bubbles: false, composed: false` and widen only with a written
reason. If you genuinely need document-root reach, namespace the type
(`mydomain__myevent`), and accept that the markup listener becomes `onmydomain__myevent`.
For the "child inside a slot needs to reach the grandparent" case, `bubbles: true,
composed: false` is enough and stops at the shadow boundary.

*Grounded: `events-propagation` (`lwc_guide.txt` L5224–L5225, L5241);
`events-best-practices` L5275.*

---

## `@wire(MessageContext)` Is Unreadable Until The Component Is In The DOM

**What happens:** Calling `subscribe()` or `publish()` from `constructor()` fails because
the wired `messageContext` field has no value yet. A component must be attached to the DOM
before the property decorated with `@wire(MessageContext)` can be used.

**When it occurs:** Constructor-time initialisation, and any helper called from the
constructor that eventually reaches the message service.

**How to avoid:** Subscribe in `connectedCallback()`, publish in event handlers. For an API
module component that is not a `LightningElement` and therefore cannot use the wire adapter
at all, use `createMessageContext()` and release it explicitly with
`releaseMessageContext()` — that context is *not* released for you.

*Grounded: `use-message-channel-publish` (`lwc_guide.txt` L9993);
`use-message-channel-subscribe` L10008, L10054.*

---

## Default Subscriber Scope Is "The Active Area", And A Utility Bar Is Always In It

**What happens:** A subscriber in a console workspace tab that is not the currently
selected tab receives nothing at default scope. A subscriber in the utility bar receives
everything at default scope, because utility items are always active.

**When it occurs:** The common misreading is that `APPLICATION_SCOPE` is "the utility bar
option". It is the *background subtab* option. Adding it to a utility-bar component costs
nothing but hides the real reason it is there; omitting it from a background console
component produces a panel that only updates while you are looking at it.

**How to avoid:** Decide from where the subscriber physically sits. Selected navigation
tabs, console workspace tabs, console subtabs, console navigation items, utility items and
ES6 libraries make up the active area — and only the *selected* tabs count. Scoping is
available only through `@wire(MessageContext)`; `createMessageContext()` has no scope
option.

*Grounded: `use-message-channel-scope` (`lwc_guide.txt` L9960–L9961, L9972);
`use-message-channel-considerations` L10071.*

---

## An Unsubscribed Component Can Outlive The Page That Created It

**What happens:** Lightning Message Service delivers to a subscriber until the destroy
phase of that component's lifecycle. Navigating away from a Lightning page does not always
destroy its components — they can be cached — and a cached, application-scoped subscriber
keeps publishing to and receiving from the service.

**When it occurs:** Console apps and any navigation that caches pages. The symptom is a
component that reacts to a selection made in a context the user has already left, or a
handler that runs twice because `connectedCallback` fired again on a component that never
disconnected.

**How to avoid:** Keep the subscription handle, unsubscribe in `disconnectedCallback()`,
and null the handle. Guard `subscribe()` with `if (this.subscription) return;` so a second
`connectedCallback` cannot double-subscribe. `@wire(MessageContext)` does unregister on
destroy — the failure mode is precisely the case where destroy never happens.

*Grounded: `use-message-channel-publish` (`lwc_guide.txt` L9986, L9991).*

---

## An Event Sent Into An Enclosing Aura Component Is Handled Once, By The First Wrapper

**What happens:** A Lightning web component inside an Aura wrapper (a quick action, an
older page region, a Lightning Out app) dispatches `filterchange`. The `onfilterchange`
handler can only be specified in the first Aura component that the DOM event bubbles to.
Handlers declared further up the Aura hierarchy never run.

**When it occurs:** Aura-coexistence layouts, and LWC quick actions that Salesforce wraps
in Aura at runtime. It is often misdiagnosed as a `composed` problem and "fixed" by
setting `composed: true`, which changes nothing about which Aura component may declare the
handler.

**How to avoid:** Put the handler on the innermost Aura wrapper and, if other Aura
components need to know, have that wrapper fire an Aura event. Name the LWC event so the
Aura attribute is legible: event `filterchange` → handler attribute `onfilterchange`.

*Grounded: `events-sending-to-aura-components` (`lwc_guide.txt` L11326, L11331).*

---

## LMS Stops At An Iframe, And Does Not Exist In Some Containers At All

**What happens:** A published message is constrained by the iframe boundary. Lightning
Message Service also does not work with Salesforce Tabs + Visualforce sites or with
Visualforce pages inside Experience Builder sites.

**When it occurs:** The design was validated in Lightning Experience and then reused in an
Experience Cloud site, an embedded Visualforce page, or Lightning Out. Nothing errors —
subscribers simply never fire.

**How to avoid:** Confirm the container before choosing LMS: it is supported in Lightning
Experience standard and console navigation, the Salesforce mobile app for Aura and LWC (not
for Visualforce pages), and Aura- and LWR-based Experience Builder sites. To cross an
iframe boundary, use `sforce.one.subscribe()` / `sforce.one.unsubscribe()`. In containers
with no LMS support at all, the `pubsub` module is the documented fallback — and it is "no
longer officially supported or actively maintained", so treat it as a container
constraint, not a design choice (see `lwc/lwc-pubsub-patterns`).

*Grounded: `use-message-channel-considerations` (`lwc_guide.txt` L10062–L10072);
`events-pubsub` L5250.*

---

## `isExposed` On A Message Channel Is A One-Way Door

**What happens:** `isExposed` controls whether components in *other namespaces* can use the
channel. Once it is set to `true` you cannot set it back to `false` — for channels in
managed packages and for channels that other components reference.

**When it occurs:** A channel is flipped to `true` during development to unblock a
Visualforce page or a second package, and the decision then cannot be reversed. Separately,
AppExchange Security Review requires `isExposed` to be `false`, and Visualforce supports
only channels where it is `true`, so a managed package that uses LMS from Visualforce
cannot pass review.

**How to avoid:** Default every channel to `isExposed` `false` and treat raising it as a
packaging decision with a named owner, not a debugging step. If a Visualforce consumer is a
requirement and the package is managed, resolve that before the first release rather than
after.

*Grounded: Metadata API Developer Guide, `LightningMessageChannel`
(`api_meta.txt` L84290–L84296, L84321–L84324).*

---

## `@track` Is Not What Makes A Property Reactive

**What happens:** A component adds `@track` to a string or a public property expecting it
to fix a rerender problem, and nothing changes. Primitive fields are already reactive, and
public properties used in a template are already reactive. `@track` only adds *deep*
observation of plain objects and arrays.

**When it occurs:** Debugging "the child isn't updating" by sprinkling `@track`. The real
cause is usually that a new value was never assigned — LWC compares with `===`, so mutating
a nested property of an object leaves identity unchanged.

**How to avoid:** Assign a new value (`this.obj = { ...this.obj, msg }`) or, when deep
observation genuinely helps, use `@track` on a field holding a plain `{}` or `[]`. It does
**not** observe class instances, `Date`, `Set`, or `Map`; LWC logs
`Property "x" … is set to a non-trackable object` in the browser console when you try.
A tracked object also rerenders only for properties that were read during the previous
render cycle.

*Grounded: `reactivity-fields` (`lwc_guide.txt` L2287–L2289, L2295, L2305, L2325);
`reactivity-public` L2264.*
