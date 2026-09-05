# Gotchas — LWC Toast And Notifications

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Line citations are into the crawled Lightning Web Components Developer Guide (`lwc_guide <page
slug> L<n>`), the Apex Reference Guide, or the Metadata API Developer Guide. Anything the crawled
corpus does not state carries an `UNVERIFIED (2026-09-05)` marker beside the claim it affects.

## Gotcha 1: Toast Events Are Silent in LWR Sites, Aura-Site Login Pages, and Standalone Apps

**What happens:** A component dispatches `ShowToastEvent` and no toast appears on screen. No
JavaScript error is thrown. The event fires and disappears without any visible feedback.

**When it occurs:** `lightning/platformShowToastEvent` "isn't supported on login pages in Aura
sites, LWR sites for Experience Cloud, and standalone apps" (`lwc_guide use-toast L10449`; the
same restriction, phrased as "isn't supported in LWR sites", is in the base-component catalogue at
`lwc_guide base-components-all L4649`). The event-based mechanism needs a host that listens for
it; in those containers there is none.

**How to avoid:** Use `lightning/toast` — "This is the preferred method to display a toast"
(`lwc_guide use-toast L10448`) and "lightning/toast is also supported in LWR sites"
(`base-components-all L4651`). The guide states the recommendation twice more, unconditionally:
"We recommend that you use lightning/toast instead" (`use-toast L10452`,
`base-components-patterns L4773`). No runtime environment sniffing is needed — pick the module,
do not detect the container. The bundled checker flags the event module in a bundle that declares
a `lightningCommunity__` target. The sibling `lwc/lwc-base-component-recipes` carries the same
L4773 rule from the base-component angle; read it there rather than duplicating the reasoning here.

---

## Gotcha 2: The Two Toast Modules Have Different API Floors, So "Just Use lightning/toast" Can Fail to Save

**What happens:** A developer follows the recommendation, imports `lightning/toast`, and the
component will not save or deploy in an org whose component API version is set below 59.

**When it occurs:** `lightning/platformShowToastEvent` is "First Available in API Version" 45.0;
`lightning/toast` is 59.0 and `lightning/toastContainer` is 58.0 (`lwc_guide base-components-all
L4649`, `L4651`, `L4652`). `lightning/alert`, `lightning/confirm`, and `lightning/prompt` are all
54.0 (`L4647`, `L4648`, `L4650`). A bundle inherits the `apiVersion` in its `.js-meta.xml`, and
from Spring '25 "all components must specify an API version" (`lwc_guide
reference-configuration-tags L18700`).

**How to avoid:** Read the `apiVersion` in the target bundle's `.js-meta.xml` before choosing the
module, and raise it deliberately rather than as a side effect. On an org pinned below 59, the
event module is the only toast available — and that is exactly the org where an LWR placement will
fail silently, so the honest answer there is an inline message, not a toast.

---

## Gotcha 3: The Guide Names Different Parameters for alert, confirm, and prompt

**What happens:** A `theme` passed to `LightningConfirm.open()` (or a `variant` passed to
`LightningAlert.open()`) is ignored, and the dialog renders in the default styling. Nothing throws.

**When it occurs:** The Developer Guide describes three sibling modules with three parameter
lists. Alert: "message, theme, and label attributes" (`lwc_guide use-dialog-alert L10404`).
Confirm: "message, variant, and label attributes" (`lwc_guide use-dialog-confirm L10418`).
Prompt: "message, theme, label, and defaultValue attributes" (`lwc_guide use-dialog-prompt
L10432`). The symmetry of the three APIs invites copy-paste between them, and the odd one out is
confirm.

**How to avoid:** Copy the parameter names from the page for the module you are actually calling,
not from the neighbouring one. UNVERIFIED (2026-09-05): the accepted *values* of `theme` and
`variant` are not printed anywhere in the crawled guide — those lists live only on the
lightning/alert, lightning/confirm, and lightning/prompt Component Library specification pages,
which the guide links to but which are not part of the corpus. Treat any specific literal
(`'warning'`, `'header'`, `'error'`) as unconfirmed until you read the specification tab.

---

## Gotcha 4: Only One Toast Container per Page, and the Fourth Toast Waits in Line

**What happens:** A batch operation reports its outcome per record. Three toasts appear; the rest
do not — until the user dismisses one, at which point another materialises. The code looks like it
dropped messages.

**When it occurs:** `lightning/toastContainer` defaults to a maximum of 3 toasts, a `top-center`
position, and a `fixed` container position (`lwc_guide use-toast L10458`–`L10460`). "When the page
displays the maximum number of toasts, any attempt to display an additional toast results in the
toast being displayed only when a toast is closed or dismissed" (`L10464`). "Only one instance of
toast container is supported on a page" (`L10462`), and that one container governs toasts from
both modules: it "manages toasts that are created using the lightning/toast and
lightning/platformShowToast modules. If you have different components that use either module on a
single page, the toasts created by those modules are subject to the toast container's
configuration" (`L10463`).

**How to avoid:** One notification per user-initiated operation, not one per record. Summarise
("4 of 12 cases could not be closed") and put the detail somewhere the user can read at leisure.
If a page genuinely needs a different position or a different cap, add exactly one
`lightning/toastContainer` and treat it as page-level configuration — a second component that adds
its own will collide with it.

---

## Gotcha 5: `--slds-c-toast-*` Styling Hooks Do Nothing on the Event Module

**What happens:** A designer supplies toast styling hooks. They work in a prototype built on
`lightning/toast` and have no effect in the shipped component, which uses `ShowToastEvent`.

**When it occurs:** "The lightning/platformShowToastEvent module doesn't support the
--slds-c-toast-* custom properties. The lightning/toast and lightning/toastContainer modules do
support these properties" (`lwc_guide create-components-css-custom-properties L1721`). A second
trap sits behind it: "Component styling hooks are not yet supported in SLDS 2" and Salesforce
recommends keeping the org on SLDS 1 themes if custom components use `--slds-c-*` hooks
(`L1718`, `L1701`).

**How to avoid:** Treat toast appearance as a reason to choose the module, decided before the
styling work starts. Do not override SLDS classes directly to compensate — "CSS overrides are not
supported because SLDS classes and base component internals can change in future releases"
(`L1710`). `lwc/lwc-styling-hooks` owns the hook mechanics.

---

## Gotcha 6: A Passing Jest Test Proves Dispatch, Not Display

**What happens:** The toast test is green and the toast never appears in the org. The team trusts
the suite and ships the LWR regression from Gotcha 1.

**When it occurs:** The documented assertion reads the dispatched event:
`expect(handler.mock.calls[0][0].detail.title).toBe(TOAST_TITLE)` and the same for `message` and
`variant` (`lwc_guide unit-testing-using-jest-patterns L12630`–`L12635`). That asserts your
component fired the event correctly. Whether a host caught and rendered it is a property of the
container, which Jest does not run. Compounding it, Salesforce's base-component mocks "match the
API of the actual components but don't have all the functionality"; "no events are fired from
these mocks but you can call dispatchEvent() against them" (`L12622`, `L12627`). And the module
under test may not even be the module you think: without a `moduleNameMapper` entry the import
"resolves to the stub" in `sfdx-lwc-jest`; with one it resolves to your own mock, whose "custom
logic … adds other properties to the event object" (`L12646`, `L12647`).

**How to avoid:** Keep the Jest assertion, and add one manual placement check per container the
component is exposed to. `lwc/lwc-testing` owns the wider Jest contract; the notification-specific
part is that "the event was dispatched" and "the user saw it" are two different claims.

---

## Gotcha 7: `Messaging.CustomNotification.send()` Throws When the Target Is Omitted, Even Though Neither Target Field Is Required

**What happens:** Apex that sets a title, a body, a type, and a recipient set throws at `send()`.
The exception is easy to misread as a permission problem.

**When it occurs:** "You must specify a target for a notification. The target can be specified
using either the targetID or the targetPageRef attribute. Neither attribute is required, but if
both are omitted, send() throws an exception" (Apex Reference Guide L166572–L166573). The
documented workaround is explicit: "If there's no natural target for a notification, set the
targetID to a dummy value, such as 000000000000000AAA. A dummy value prevents the exception, and
also prevents automatic navigation when responding to the notification in the client app"
(L166574–L166575). A separate failure with a similar smell: the running user needs the Send Custom
Notifications user permission, and "If you don't have the required permission, the send() method
fails" (L166593).

**How to avoid:** Validate the target in your own code before calling `send()`, so the error names
the real cause. When the notification has no record to open, set the dummy id deliberately and
comment why. `admin/custom-notification-type-design` owns the declarative half — the type, its
desktop and mobile channels, and who may send it.

---

## Gotcha 8: The Custom Notification Limits Truncate Silently at the Edges

**What happens:** A notification built from a record description arrives with the end of the
sentence missing, or a bulk send reaches only some of the intended audience.

**When it occurs:** Title maximum is 250 characters and body maximum is 750 (Apex Reference Guide
L166708, L166711). The recipient set accepts "up to the maximum of 500 values" (L166775), and a
value is not necessarily one person: an AccountId sends to the account team, an OpportunityId to
the opportunity team, a GroupId to the group's active members, a QueueId to the queue's active
members, and a UserId only "if this user is active" (L166769–L166774). A single QueueId therefore
expands to an unknown headcount, while 500 UserIds is a hard ceiling.

**How to avoid:** Truncate to the documented maximums in your own code so the cut is deliberate
and testable, and chunk recipients into sets of 500. Prefer a GroupId or QueueId over enumerating
users — one value, no ceiling arithmetic, and membership stays an admin concern.

---

## Gotcha 9: `CustomNotificationType` Refuses the Wildcard in `package.xml`

**What happens:** A `package.xml` with `<members>*</members>` under `CustomNotificationType`
retrieves nothing, and the deploy that follows drops a notification type nobody noticed was
missing until the first send throws.

**When it occurs:** "This metadata type doesn't support the wildcard character * (asterisk) in the
package.xml manifest file" (Metadata API Developer Guide L41893). The type has been available
since API 46.0, with the `.notiftype` suffix in the `notificationtypes` directory (L41791,
L41779–L41780).

**How to avoid:** Name every notification type explicitly in the manifest and keep the list beside
the Apex that queries it by `DeveloperName`. A retrieve that returns an empty
`notificationtypes` directory is the symptom.

---

## Gotcha 10: `sticky` Mode on Success Toasts Creates Hostile UX

**What happens:** Users must manually close every success confirmation, even for routine saves
that require no further action. On high-frequency workflows the friction accumulates on every
save.

**When it occurs:** When a mode value is applied uniformly across variants rather than selectively
to messages the user must act on — usually because an error case was written first and the pattern
was copied.

**How to avoid:** Reserve persistent modes for messages that carry an action; let routine success
messages use the default. UNVERIFIED (2026-09-05): the crawled guide names `mode` as a
`ShowToastEvent` property and notes that its sample "uses the default value for mode, so it's not
included" (`lwc_guide use-toast L10456`), but it never prints the accepted values or which one is
the default. The familiar `dismissable` / `sticky` / `pester` triple comes from the
platformShowToastEvent Component Library specification and from the Aura `showToast` equivalence
statement — "ShowToastEvent supports the same parameters, modes, and variants as Aura's showToast"
(`lwc_guide migrate-map-aura-lwc-components L11713`) — not from the guide itself. Confirm the
literal against the specification page before relying on it.

---

## Gotcha 11: Placeholder Substitution Is Not the Same Feature on Both Modules

**What happens:** A message written with `{0}` renders the literal `{0}` to end users, or an
inline link renders as plain text in the toast title.

**When it occurs:** For `lightning/toast`, "Provide a title using the required label property. The
toast message property is optional. Both properties support inline links using the placeholder
syntax {N} or {linkName}" (`lwc_guide use-toast L10451`). For the event module the guide says the
opposite about the title: "Inline links are not supported in the toast title" (`L10449`). So the
same message string behaves differently depending on which module renders it.

**How to avoid:** Keep link-bearing messages on `lightning/toast`. UNVERIFIED (2026-09-05): the
`messageData` property that supplies the substitution values is not mentioned anywhere in the
crawled guide — neither its name, its shape, nor the `{url, label}` object form. It comes from the
Component Library specifications. If you use it, read the specification for the module you chose
and keep the placeholder count and the array length in step; a mismatch is what produces the
literal `{0}` on screen. The bundled checker cannot verify this because it cannot know which
module a given call resolves to at run time.

---

## Gotcha 12: `lightning-alert` / `lightning-confirm` Replace the Native Dialogs for a Standards Reason, Not a Locker Reason

**What happens:** Someone "fixes" a broken `window.confirm()` by adding a Locker exemption, or
concludes the native dialogs are fine outside Lightning Experience.

**When it occurs:** The guide's stated reason is the web platform, not the Salesforce sandbox:
"the HTML specification has deprecated support for the window.alert(), window.confirm(), and
window.prompt() methods when used in a third-party context, we recommend that you use these
notification components instead" (`lwc_guide base-components-patterns L4768`). Each module page
adds the browser-level detail: the native function "isn't supported for cross-origin iframes in
Chrome and Safari" (`use-dialog-alert L10401`, `use-dialog-confirm L10415`, `use-dialog-prompt
L10429`). The behavioural difference that actually changes your code: the native calls block, and
"these modules' .open() method don't halt execution on the page, and they each return a promise"
(`base-components-patterns L4769`).

**How to avoid:** Replace the call, not the container. `LightningConfirm.open()` "resolves to true
when you click OK and false when you click Cancel" (`use-dialog-confirm L10418`);
`LightningPrompt.open()` "returns a promise that resolves to the input value" or "resolves to
null" on Cancel (`use-dialog-prompt L10432`). Because none of them block, any code that used to
sit after a native `confirm()` must move inside the `await`. The bundled checker reports
`window.alert` / `window.confirm` / `window.prompt` as an ERROR for this reason. UNVERIFIED
(2026-09-05): the claim that these modules are unsupported in Visualforce pages or standalone
HTML is not in the crawled guide — the guide says only "To display an alert modal in Lightning
Experience" (`use-dialog-alert L10400`). Verify the container before repeating the stronger claim.
