---
name: lwc-toast-and-notifications
description: "Show toast, platform, and in-app notifications from LWC — ShowToastEvent, lightning/platformShowToastEvent, Custom Notification types. Triggers: ShowToastEvent, toast LWC, custom notification LWC, toast not showing in Experience Cloud, lightning/toast vs platformShowToastEvent, Messaging.CustomNotification from Apex. NOT for modal overlays — use lwc/lwc-modal-and-overlay."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
tags:
  - lwc
  - toast
  - notifications
  - ShowToastEvent
  - lightning-alert
  - lightning-confirm
  - platform-notifications
  - lightning-toast
  - custom-notification
inputs:
  - "what user action or system event triggered the need for feedback"
  - "whether the feedback requires user acknowledgment or is purely informational"
  - "whether the component runs in Lightning Experience, Experience Cloud, or a mobile context"
  - "the target bundle's .js-meta.xml — its apiVersion and its declared targets"
  - "whether the recipient is on the page at all, or must be reached asynchronously"
outputs:
  - "implementation of the correct notification primitive for the scenario"
  - "review findings for toast misuse, sticky-mode overuse, and Experience Cloud gaps"
  - "Jest test pattern for verifying toast dispatch"
  - "a surface-aware notify.js helper plus its js-meta.xml targets"
  - "an Apex CustomNotification sender with recipient chunking and its test"
triggers:
  - "how do I show a toast message in LWC"
  - "ShowToastEvent not showing in Experience Cloud"
  - "lightning-confirm promise-based dialog LWC"
  - "display success error warning notification LWC"
  - "sticky toast vs dismissable toast when to use"
  - "toast does not appear in LWR site no error thrown"
  - "replace window.confirm before deleting a record in LWC"
  - "send a custom notification from Apex to a queue"
  - "choose between lightning/toast and platformShowToastEvent"
  - "only three toasts show up on the page"
  - "test that my component dispatched a toast in Jest"
  - "close a screen quick action modal from a Lightning web component"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when a component needs to communicate feedback, status, or a decision prompt to the user and the team must choose the right platform primitive. Toast is the default for non-blocking success, warning, and error messages in Lightning Experience; `lightning/alert`, `lightning/confirm`, and `lightning/prompt` replace the browser-native dialogs with promise-based equivalents; a custom notification sent from Apex reaches a user who is not looking at the page at all.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which container does the component actually run in — a Lightning record or app page, an Aura Experience Cloud site, an LWR site, a Flow screen, a screen or headless quick action, a utility bar? The container decides which module works, and one of the combinations fails without an error.
- What is the `apiVersion` in the target bundle's `.js-meta.xml`, and which `<target>` entries does it declare? Both facts change the answer, and both are readable before a line of code is written.
- Does the user need to acknowledge the message (blocking) or just be informed (non-blocking)?
- Is the action irreversible? A promise-returning confirm belongs before a destructive call; a toast after it is a receipt, not a gate.
- Will the recipient be on the page when the event happens? If not, no in-page primitive can reach them and the surface is a custom notification.

---

## Questions to Ask Before Configuring

Ask these before writing the handler. Each one traces to a failure in `references/gotchas.md`, and an agent that skips them produces a component that works in the sandbox page it was built on and nowhere else.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which containers will this bundle be exposed to — record page, Aura site, LWR site, Flow screen, quick action?" | `lightning/platformShowToastEvent` renders nothing on LWR sites, Aura-site login pages, or standalone apps, and throws no error (Gotcha 1) | The `<target>` list for `.js-meta.xml` and the module choice that follows from it |
| "What `apiVersion` is this bundle on, and can we raise it?" | `lightning/toast` needs API 59.0; the event module works from 45.0 (Gotcha 2) | Either a version bump in the deploy, or a documented fallback for a pinned org |
| "Is the recipient looking at this page when the event happens?" | No in-page primitive reaches an absent user; that case is a custom notification sent from Apex | A decision between a toast and a `CustomNotificationType` plus its Apex sender |
| "Does this message carry a link or a substituted value?" | Inline links are supported in both `lightning/toast` properties but not in the event module's title (Gotcha 11) | The module choice, and whether the message needs placeholder substitution at all |
| "Is the action reversible, and what does the user lose if they clicked by mistake?" | Irreversible actions need the promise gate before the call, not a toast after it | An explicit `LightningConfirm.open()` boundary and the branch for `false` |
| "How many of these fire per operation — one, or one per record?" | The toast container caps the page at three and queues the rest until one is dismissed (Gotcha 4) | A summarised single message plus somewhere the per-record detail actually lives |
| "Who gets the custom notification: named users, a queue, or a team, and who may send it?" | Recipient ids expand differently and cap at 500 per send; the sender needs Send Custom Notifications (Gotchas 7, 8) | The recipient strategy, the chunking, and the permission set that has to ship with it |

What a proper configuration adds over just calling `dispatchEvent`: the notification renders in every container the bundle is exposed to, a destructive action cannot fire without a decision, the message survives the platform's own length and count limits, and the Jest suite asserts something that is actually true about the component.

---

## Core Concepts

Notification design in LWC is two decisions in order: **which surface**, then **which module for that surface**. Most defects in this domain come from making the second decision first.

### Choosing the surface

| The user is… | Surface | Why |
|---|---|---|
| On the page, and the message is informational or a receipt | Toast | Non-blocking; the user keeps working |
| On the page, and must read the message before continuing | `lightning/alert` | `.open()` returns a promise that resolves when they dismiss it |
| On the page, and must answer yes or no first | `lightning/confirm` | Resolves `true` on OK and `false` on Cancel |
| On the page, and must supply a value first | `lightning/prompt` | Resolves to the entered value, or `null` on Cancel |
| On the page, and the message belongs to a field or a form | Inline message, not a notification | A toast that scrolls away cannot be re-read next to the field it describes |
| On the page, and the interaction needs a form or multiple steps | `LightningModal` — see `lwc/lwc-modal-and-overlay` | Notification primitives are not containers |
| Not on the page | Custom notification sent from Apex | Desktop and mobile channels, delivered by the platform |

### The two toast modules

Both require a module import, and they are not interchangeable.

| | `lightning/toast` | `lightning/platformShowToastEvent` |
|---|---|---|
| Mechanism | Imperative `show()` call on the module | Dispatch `ShowToastEvent` from the component |
| First available | API 59.0 | API 45.0 |
| LWR Experience Cloud sites | Supported | Not supported |
| Aura-site login pages, standalone apps | — | Not supported |
| Inline links in the title | Supported | Not supported |
| `--slds-c-toast-*` styling hooks | Supported | Not supported |
| Salesforce's own recommendation | Preferred | "We recommend that you use lightning/toast instead" |

Sources for every row: `lwc_guide base-components-all L4649`, `L4651`, `L4652`;
`lwc_guide use-toast L10448`–`L10452`; `lwc_guide base-components-patterns L4773`;
`lwc_guide create-components-css-custom-properties L1721`.

```javascript
// Event module — created with title, message, variant, and mode, then dispatched.
// (lwc_guide use-toast L10456)
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

this.dispatchEvent(
    new ShowToastEvent({
        title: 'Contacts updated',
        message: 'Your changes were saved.',
        variant: 'success'
    })
);
```

UNVERIFIED (2026-09-05): the crawled Developer Guide names `variant` and `mode` as properties but
never prints their accepted values or defaults. Only `variant: 'success'` and `variant: 'error'`
appear in its own samples (`lwc_guide data-table-inline-edit L5694`, `L5746`). The familiar
`info` / `warning` variants and the `dismissable` / `sticky` / `pester` modes come from the
Component Library specification pages, which are not in the corpus — see Gotcha 10.

The rule that follows from the table is not "detect the container at run time". It is: default to
`lightning/toast`, and treat the event module as the exception you take only on an org pinned
below API 59. `references/code-examples.md` § 1 implements that as a `notify.js` helper taking the
surface as a declared parameter rather than sniffing for it.

### Toast container behaviour is page-level, not component-level

`lightning/toastContainer` controls position and how many toasts a page shows at once. The
defaults are three toasts, `top-center`, `fixed`; only one container instance is supported per
page; and its configuration governs toasts from **both** modules
(`lwc_guide use-toast L10457`–`L10463`). A page over its cap does not drop the extra toast — it
holds it until one is dismissed (`L10464`). Design for one notification per operation.

### The promise-returning dialogs

`lightning/alert`, `lightning/confirm`, and `lightning/prompt` (all API 54.0) exist because "the
HTML specification has deprecated support for the `window.alert()`, `window.confirm()`, and
`window.prompt()` methods when used in a third-party context"
(`lwc_guide base-components-patterns L4768`), and because the native calls "aren't supported for
cross-origin iframes in Chrome and Safari" (`lwc_guide use-dialog-alert L10401`). The behavioural
difference that changes your code: "these modules' `.open()` method don't halt execution on the
page, and they each return a promise" (`L4769`). Code that used to run after a native `confirm()`
must move inside the `await`.

The parameter names differ between the three — alert takes `message`, `theme`, `label`; confirm
takes `message`, `variant`, `label`; prompt takes `message`, `theme`, `label`, `defaultValue`
(`use-dialog-alert L10404`, `use-dialog-confirm L10418`, `use-dialog-prompt L10432`).

### Custom notifications: the surface for an absent user

`Messaging.CustomNotification` "is used to create, configure, and send custom notifications from
Apex code" (Apex Reference Guide L166556). The declarative half is a `CustomNotificationType` with
its desktop and mobile channels — owned by `admin/custom-notification-type-design`. The Apex half
belongs here: set the type id, title, body, and a target, then `send(Set<String> users)`. Its
limits are hard and quiet — 250-character title, 750-character body, 500 recipient values per
send — and `send()` throws when no target is set at all. See Gotchas 7–9 and
`references/code-examples.md` § 5.

### Notification surfaces this skill does not own

- **Aura `lightning:notificationsLibrary`** — Aura-only. "In Lightning web components, import the `lightning/platformShowToastEvent` module… LWC doesn't support notices yet" (`lwc_guide migrate-map-aura-lwc-components L11713`). There is no LWC notices equivalent to migrate to.
- **Closing a screen quick action** — dispatch `CloseActionScreenEvent`, imported from `lightning/actions` (`lwc_guide use-quick-actions-screen L10572`). That is navigation, not notification; `lwc/lwc-quick-actions` owns it. Note that a headless quick action can dispatch toasts (`lwc_guide use-quick-actions-headless L10615`), and that LWC quick actions "are available only on record pages in Lightning Experience. They're not supported in Aura Experience Builder sites or on the Salesforce mobile app" (`lwc_guide use-quick-actions L10526`).
- **Flow screens** — a flow local action's toast has the same LWR caveat: "Use the `lightning/toast` module instead to display a toast notification on LWR sites" (`lwc_guide use-flow-local-actions L8813`). Flow-side design belongs to `lwc/lwc-in-flow-screens`.

---

## Common Patterns

### Toast After Apex DML

**When to use:** A component calls an Apex method to save, update, or delete a record and needs to confirm the outcome without interrupting navigation.

**How it works:** Report success in the `then`/`await` branch and failure in the catch branch. Read the message out of the error rather than stringifying it — the guide's own samples read `error.body.message` (`lwc_guide data-table-inline-edit L5703`). Normalising the many shapes an LWC error can take is `lwc/lwc-error-boundaries`' job; import its utility rather than re-deriving one.

**Why not the alternative:** A blocking dialog for a routine save trains users to dismiss dialogs unread, which is exactly the reflex you need intact when something serious appears.

### Confirm Before Destructive Action

**When to use:** A delete, archive, or bulk overwrite the user cannot undo.

**How it works:** `await LightningConfirm.open({...})` before the Apex call, and return early when it resolves `false`. The gate is visible in the diff and testable in Jest by mocking the resolved value both ways — see `references/code-examples.md` § 4.

**Why not the alternative:** A full `LightningModal` is a container for a task, not a question; and a post-hoc toast reporting "12 records deleted" is a receipt for a mistake.

### Reporting a Batch Outcome

**When to use:** One user action produces many per-record results.

**How it works:** One notification summarising the operation, plus a place — a datatable of failures, a section on the page — where the detail is still readable a minute later. The container caps concurrent toasts at three by default and queues the rest (Gotcha 4), so a per-record toast loop is a design that hides its own output.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Confirm a save succeeded, Lightning page | Toast via `lightning/toast` | Non-blocking, and the same code works if the component is later exposed to a site |
| Any component exposed to `lightningCommunity__*` targets | `lightning/toast` only | The event module is not supported in LWR sites |
| Org pinned below API 59.0 | `ShowToastEvent`, and no LWR placement | `lightning/toast` does not exist below 59.0 |
| Message must be read before the user proceeds | `lightning/alert` | Promise resolves after dismissal; control flow stays explicit |
| Irreversible action | `lightning/confirm` before the call | Resolves `true`/`false`; cheaper than a modal for one question |
| A value is needed before proceeding | `lightning/prompt` | Resolves to the input value, or `null` on Cancel |
| Message belongs to one field | Inline message | A notification cannot be re-read beside the field |
| Recipient is not on the page | `Messaging.CustomNotification` from Apex | Desktop and mobile delivery, with a `CustomNotificationType` behind it |
| Multi-step or form-bearing dialog | `LightningModal` (`lwc/lwc-modal-and-overlay`) | Notification primitives are not form containers |
| Toast appearance must be themed | `lightning/toast` | The event module ignores `--slds-c-toast-*` |

---

## Recommended Workflow

1. **Read the bundle's `.js-meta.xml` first** — record its `apiVersion` and every `<target>`. Those two lines decide the module before any handler is written; the container matrix in Core Concepts turns them into a choice.
2. **Pick the surface, then the module** — walk the surface table (absent user → custom notification; decision → confirm; receipt → toast), then the two-module table. Write down which row you used; that sentence is the whole justification a reviewer needs.
3. **Build the bundle from `references/code-examples.md`** — § 1 for `notify.js`, § 2 for the confirm-gated component, § 3 for the dual-target `.js-meta.xml`, § 5 for the Apex sender when the surface is a custom notification. Reference `templates/lwc/component-skeleton/` and `templates/lwc/jest.config.js` rather than re-deriving them.
4. **Write the two Jest cases that matter** — the toast event detail (`detail.title`, `detail.message`, `detail.variant`) and both branches of the confirm promise. § 4 has the `moduleNameMapper` entries; without them the imports resolve to the stock stubs.
5. **Run the checker over the source tree** — `python3 scripts/check_lwc_toast_and_notifications.py --manifest-dir force-app/main/default`. It reads each bundle together with its `.js-meta.xml`, which is the only way the LWR/event-module pairing is visible.
6. **Deploy in the order in § 7** — notification type, Apex, then LWC — and run the verification steps there, including the deliberate LWR placement that proves the silent-failure mode is understood rather than assumed.
7. **Walk `references/gotchas.md`** against the finished component, and record which `UNVERIFIED` claims you relied on so the reviewer can check them against the Component Library.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The module choice matches the bundle's declared targets — no `lightning/platformShowToastEvent` in a bundle exposed to `lightningCommunity__*`.
- [ ] The bundle's `apiVersion` is at least 59.0 if it imports `lightning/toast`.
- [ ] Every `variant` and `mode` literal used has been checked against the Component Library specification, because the Developer Guide does not print those values.
- [ ] Destructive actions await `LightningConfirm.open()` and return early on `false`.
- [ ] No `window.alert`, `window.confirm`, or `window.prompt` anywhere in the bundle.
- [ ] One notification per user operation, not one per record.
- [ ] Error messages are read out of the error object, not `JSON.stringify`d into the message.
- [ ] Jest asserts the dispatched event's `detail`, and a human has seen the toast render in each container the bundle is exposed to.
- [ ] Apex custom notifications set a target, chunk recipients at 500, and truncate title/body at 250/750.
- [ ] `CustomNotificationType` members are named explicitly in `package.xml` — the wildcard does not work for this type.
- [ ] The checker script reports no ERROR against the source tree.

---

## Salesforce-Specific Gotchas

The full set, each with what happens, when it occurs, how to avoid it, and its guide line, is in
`references/gotchas.md`. The five that cause the most rework:

1. **The event module renders nothing in LWR sites, Aura-site login pages, and standalone apps — and throws no error.** Discovered in QA, after the deploy (Gotcha 1).
2. **`lightning/toast` needs API 59.0.** Following the recommendation on a pinned org fails to save (Gotcha 2).
3. **Three toasts per page by default; the fourth waits for a dismissal.** A per-record toast loop silently withholds most of its output (Gotcha 4).
4. **`send()` throws when both `targetId` and `targetPageRef` are omitted, although neither field is required.** The exception reads like a permission problem (Gotcha 7).
5. **A green Jest toast test proves the event was dispatched, not that anyone saw it.** Two different claims (Gotcha 6).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `notify.js` helper | Surface-aware module that routes to `lightning/toast` or the event module from a declared flag |
| Confirm-gated component | Bundle with `.html`, `.js`, and dual-target `.js-meta.xml` |
| Jest suite | Tests asserting the toast event detail and both branches of the confirm promise |
| `CustomNotificationSender.cls` + test | Apex sender with target validation, recipient chunking, and length truncation |
| `package.xml` + deploy order | Manifest naming the `CustomNotificationType` explicitly, with retrieve/deploy/test commands |
| Checker report | ERROR/WARN/ADVISORY findings from `scripts/check_lwc_toast_and_notifications.py` |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are building: the `notify.js` helper, the confirm-gated component, its `.js-meta.xml`, the Jest tests, the Apex sender, the manifest, and the deploy and verification steps |
| `references/gotchas.md` | A notification does not appear, appears late, truncates, or throws — twelve grounded platform behaviours with guide line citations |
| `references/examples.md` | You want a worked before/after narrative for a save flow and a destructive bulk action |
| `references/llm-anti-patterns.md` | You are reviewing generated code, or self-checking your own output, for the mistakes assistants make in this domain |
| `references/well-architected.md` | You are justifying the surface choice in a design review, or need the source list behind the claims here |

---

## Related Skills

- `lwc/lwc-error-boundaries` — owns normalising an error into a displayable message before it reaches a toast; import its utility rather than writing another `reduceErrors`.
- `lwc/lwc-base-component-recipes` — owns the base-component catalogue and carries the same `lightning/toast` versus `platformShowToastEvent` rule from the composition angle.
- `lwc/lwc-modal-and-overlay` — use when the interaction needs a task container or form input rather than a single-line notification.
- `lwc/lwc-testing` — owns the Jest contract; this skill only specifies the notification-specific assertions.
- `lwc/component-communication` — use when the message has to travel from a child or a sibling before anything is displayed.
- `lwc/lwc-quick-actions` — owns `CloseActionScreenEvent` and the quick-action targets.
- `lwc/lwc-styling-hooks` — owns `--slds-c-*` hooks and the SLDS 1 / SLDS 2 constraint behind Gotcha 5.
- `admin/custom-notification-type-design` — owns the declarative `CustomNotificationType`, its channels, and who may send it.
- `apex/debug-and-logging` — owns what happens to the exception when a notification send fails.
- `lwc/lifecycle-hooks` — use when notification timing issues are really rerender or async sequencing problems.
