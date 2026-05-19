# Gotchas — LWC ShowToast Patterns

Five behaviors of `ShowToastEvent` from `lightning/platformShowToastEvent`
that surprise practitioners after the first "Hello, Toast" works.
These are the second-order issues that show up once you try to
ship real flows that span runtimes, lifecycle timing, and the
`messageData` link shape.

---

## Gotcha 1: `ShowToastEvent` is silently ignored outside Lightning Experience and Aura sites

**What happens:** A practitioner builds a LWC that dispatches
`ShowToastEvent` in Lightning Experience, sees the toast appear,
and ships the same component to an LWR Experience Cloud site or a
standalone LWC app. No toast appears. No JavaScript error throws.
The dispatch call returns normally; the event simply has no
listener at the runtime host because the LWR / standalone shell
does not include the platform's toast container that
`ShowToastEvent` requires to render.

**When it occurs:** LWR (Lightning Web Runtime) Experience Cloud
sites — the runtime introduced for Build Your Own (LWR) and
Customer Service (LWR) templates. Also standalone LWC apps
(`@salesforce/lwc/v/*` deployment patterns), `lightning-out` hosts
on bare HTML, and Mobile Publisher apps whose host shell hasn't
been updated to include the platform's notification region. The
Aura-based Experience Cloud templates (Customer Service, Partner
Central, etc.) DO render `ShowToastEvent` because they ship the
Aura `lightning:notificationsLibrary` in the page chrome.

**How to avoid:** Detect the runtime before dispatching. The
documented modern alternative for LWR / standalone surfaces is the
`lightning/toast` module — call `Toast.show(this, { label, message,
variant, mode })` (note `label`, not `title`, for that API). For
components that need to run in both runtimes, write a single
helper that picks `ShowToastEvent` for Lightning Experience and
Aura Experience Cloud, and `lightning/toast.show()` for LWR /
standalone. If the runtime can't be determined, prefer
`lightning/toast` — it works in more surfaces than the event-based
API does. Per the official `lightning/platformShowToastEvent` docs,
the event is "not supported in environments like LWR sites for
Experience Cloud or standalone apps" — there is no runtime
fallback baked into the platform itself.

---

## Gotcha 2: Toasts dispatched from `connectedCallback` may not fire because the component isn't in the DOM yet

**What happens:** A practitioner wants the component to greet the
user immediately on load, so they `this.dispatchEvent(new
ShowToastEvent({ ... }))` from inside `connectedCallback`. The
toast does not appear. No error. The same call from a button
handler works fine.

**When it occurs:** Components that fire feedback on mount —
"Welcome back, {user.firstName}", "Loaded N records", "Background
sync in progress". Also components that fetch data in
`connectedCallback` and dispatch a toast from inside the `.then()`
of a Promise that resolves before the component is actually
attached to the DOM tree. The platform's toast container subscribes
to events bubbling up through the DOM — if the component dispatching
hasn't reached the container in the tree yet, the event has
nowhere to land.

**How to avoid:** Defer the dispatch to `renderedCallback` (and
guard with a one-shot boolean to prevent it firing on every
re-render), or to the next microtask via
`Promise.resolve().then(() => this.dispatchEvent(...))`. The
cleanest pattern is `renderedCallback` with an `_didGreet` flag —
the first render guarantees the component is in the DOM. For
toasts that fire after async data load, await the data work
*then* dispatch in a `.then()` or after `await`; by the time async
work resolves, the component has typically been attached. Never
dispatch `ShowToastEvent` synchronously from inside
`connectedCallback` before any render cycle has completed — the
event has no host to bubble to.

---

## Gotcha 3: `mode: 'dismissible'` (the default) auto-dismisses after 5 seconds — too short for long error messages

**What happens:** A practitioner writes a multi-sentence validation
error into the `message` field and leaves `mode` at the default.
The toast renders, the user starts reading, and at 5 seconds the
toast disappears mid-sentence. The user has no recourse to re-read
— the close button they would have clicked to keep it open is
already gone. They retry the action to trigger the error again,
which is the wrong primitive for "I want to re-read the error."

**When it occurs:** Error toasts in general, but especially when
the error body is something like "Record could not be saved
because field 'Annual Revenue' must be greater than zero when
Status is 'Customer'. Update the field and try again." — a
typical Salesforce validation-rule message that's intentionally
verbose to be actionable. Also affects toasts that include
generated URLs in `messageData` where the user wants time to
click the link.

**How to avoid:** For error variants and any toast a user is
expected to read carefully or interact with (click a link, copy a
value), set `mode: 'sticky'` explicitly. `sticky` keeps the toast
visible until the user clicks the close (X) button — no
auto-dismiss. The `pester` mode also stays visible until dismissed
but is documented as valid only for `variant: 'error'` (per the
component library reference) — `sticky` is the more general
choice. The 5-second default suits brief success confirmations
("Saved"); it does not suit anything the user needs to read or
act on. As a general rule for the team's review checklist: any
`ShowToastEvent` with `variant: 'error'` should default to
`sticky` and only fall back to `dismissible` when the message is
genuinely a single short sentence.

---

## Gotcha 4: In legacy Aura Experience Cloud, omitting `<lightning:notificationsLibrary>` from the page makes toasts silently fail

**What happens:** A practitioner adds a LWC to an Aura-based
Experience Cloud page, the component dispatches `ShowToastEvent`,
and no toast appears. The same component works fine when dropped
onto a Lightning Experience record page. The Experience Cloud
template is one of the older Aura templates (Customer Service
template, Partner Central, etc.), but the page itself was built
without including the `<lightning:notificationsLibrary>` tag in
its Aura wrapper.

**When it occurs:** Custom Aura pages inside legacy Aura
Experience Cloud sites. Lightning Experience pages have the
notifications library installed by the platform as part of the
LEX chrome. Aura Experience Cloud sites bundle a notifications
library at the template level for built-in pages, but custom
pages added by a developer have to include
`<lightning:notificationsLibrary aura:id="notifLib"/>` at the
page root. Without it, toast events bubble up to a host that
isn't listening for them.

**How to avoid:** When building an Aura wrapper page in an
Aura-template Experience Cloud site, add
`<lightning:notificationsLibrary>` at the top of the page's Aura
markup. This is documented in the Lightning Component Library's
notifications-library reference. The LWR templates handle this
differently (see Gotcha 1 — LWR doesn't support `ShowToastEvent`
at all, so the notifications library question doesn't apply
there). For pure-LWC Experience Cloud pages on Aura templates
(no custom Aura wrapper), the platform installs the library
automatically — the gotcha hits only when there's a custom
Aura page hosting LWCs in the path.

---

## Gotcha 5: `messageData` URL-link entries require `{ url, label }` shape — `{ href, text }` silently renders the literal `[object Object]` string

**What happens:** A practitioner adapts an anchor-tag pattern they
know from elsewhere and passes
`messageData: [{ href: '/lightning/r/Account/001.../view', text: 'Acme' }]`
to substitute a clickable link into the message. The toast
appears, but where the link should be, the user sees the literal
text `[object Object]` (or, in some platform versions, an empty
substitution — the visible text disappears). No error logs. The
JavaScript ran cleanly; the event dispatched cleanly; the
substitution silently failed.

**When it occurs:** Practitioners coming from React / Vue / plain
HTML who use `{ href, text }` as muscle memory for anchor data.
Also practitioners copying from outdated tutorials that predate
the `{ url, label }` standardization, or from internal helper
libraries that wrap the toast call with a custom shape that the
platform doesn't recognize. Hits hard the first time a team adds
a clickable link inside a toast because the visual symptom
(`[object Object]`) doesn't lead the developer to "wrong property
names" — it looks like a serialization bug.

**How to avoid:** Use exactly `{ url, label }` for each link
entry in `messageData`. The `url` value is the link's href; the
`label` value is the visible link text the user clicks. Anything
else falls through to the platform's default string serialization,
which is `[object Object]` for object values without a `toString`
override. The official `lightning/platformShowToastEvent` reference
documents the shape under the `messageData` parameter — `url` and
`label` are the only recognized keys. For mixed substitutions
(plain text at one index, link at another), each `messageData`
entry can be a string OR an object — the platform checks each
entry's type. A typo like `Url` or `Label` (case-sensitive) also
silently fails. Add a code-review check: every `messageData`
entry that's an object should have exactly the keys `url` and
`label`, no others.
