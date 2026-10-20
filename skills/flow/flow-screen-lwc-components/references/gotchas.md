# Gotchas — Flow Screen LWC Components

Non-obvious Salesforce platform behaviors that cause real production
problems when building LWCs that render inside a Flow screen step.

---

## Gotcha 1: Missing `lightning__FlowScreen` target → invisible in the builder

**What happens:** the LWC deploys cleanly, appears under Setup → Lightning
Components, but Flow Builder's screen-component palette does not list it.
UNVERIFIED (2026-10-20): that there is no error or warning message is observed
behaviour; the target page only says the target "enables a component to be used
on flow screens" (lwcguide targets-lightning-flow-screen).

**When it occurs:** any time the `js-meta.xml` declares targets like
`lightning__AppPage` or `lightning__RecordPage` but omits
`lightning__FlowScreen`. Most commonly when an existing LWC was originally
built for a Lightning page and is now being repurposed for a Screen Flow
without updating the meta.

**How to avoid:** the very first thing to grep when a screen LWC "doesn't
appear" is the target list. The fix is one line:

```xml
<targets>
    <target>lightning__FlowScreen</target>
</targets>
```

If the component should also work on a Lightning page, list both targets
and use separate `<targetConfig>` blocks if behavior diverges.

---

## Gotcha 2: `@api validate()` should be a synchronous plain method — async behaviour is undocumented

**What happens:** an `async validate()` returns a Promise, not the documented
`{ isValid, errorMessage }` pair. UNVERIFIED (2026-10-20): what the runtime does
with it is not in the guide; the observed behaviour is that navigation proceeds
and the validation is bypassed. The guide does say arrow-function `validate`
does not work (lwcguide use-flow-validate-user-input-for-custom-components).

**When it occurs:** any time the LWC needs to validate against server-side
state (uniqueness check, external system lookup, complex Apex evaluation)
and the author writes the natural-looking async pattern:

```js
@api
async validate() { ... }   // suspect — UNVERIFIED 2026-10-20: the guide does not say what Flow does with the Promise
```

**How to avoid:**

- Pre-fetch the data via `@wire` or in `connectedCallback`, store on the
  instance, and validate against the cached value.
- If the data must be fetched on click, gate the user via an explicit
  "Check" button that calls the async logic and only enables Next on
  success — do not put the async call in `validate()`.
- Code-review rule: any `validate()` method whose body contains `await`,
  `.then(`, `async`, or returns a Promise is a defect.

---

## Gotcha 3: Reactive screen components are built in at Flow API version 59.0+

**What happens:** two LWCs are wired correctly via Flow variables on the
same screen. Both `FlowAttributeChangeEvent` dispatches fire. But the
consuming LWC's input never updates until the user clicks Next.

**When it occurs:** the Flow's API version (set when the flow was created)
is below 59.0. For flows on 57.0 and 58.0, reactivity needs the Process
Automation setting `enableFlowReactiveScreens` (default false); the setting
does not apply at 59.0+ (api_meta 264 L120052-120055). UNVERIFIED (2026-10-20):
the corpus is silent below 57.0 and does not name the release for 59.0. Older
flows, including clones, keep their original API version.

**How to avoid:**

- In Flow Builder, open Flow Properties → API Version. Confirm it is 59.0
  or higher.
- For new flows, set 60.0+ to also benefit from later screen-flow
  improvements.
- For migrated flows, bump the API version explicitly after testing — a
  bump can change other behaviors, so test the full screen path.
- Document in the LWC's README that a minimum Flow API version is
  required so future admins do not waste time debugging a clone of an
  ancient flow.

---

## Gotcha 4: `FlowNavigationFinishEvent` from a non-final screen ends the flow abruptly

**What happens:** an LWC fires `FlowNavigationFinishEvent` from screen 2
of a 5-screen flow. Finish "finishes the flow interview" (lwcguide
use-flow-screen-navigate), so screens 3, 4, and 5 are skipped. UNVERIFIED
(2026-10-20): that later record updates, subflows or Apex actions are also
skipped is inferred, not documented.

**When it occurs:** authors copy a snippet that fires `FlowNavigationFinishEvent`
from a single-screen wizard and reuse it in a multi-screen flow without
re-evaluating which screen the LWC ends up on. Also occurs when a flow is
later expanded with extra screens, but the LWC's hard-coded Finish call is
not revisited.

**How to avoid:**

- Default to `FlowNavigationNextEvent`. Use Finish only when the LWC is
  CERTAIN to be on the terminal screen.
- If the LWC may run on multiple screens, inspect `availableActions` — if
  `FINISH` is present and `NEXT` is not, you are on the last screen.
- Code-review rule: every `FlowNavigationFinishEvent` dispatch should have
  a comment explaining why it is correct that the flow terminates here.

---

## Gotcha 5: `role="outputOnly"` does not auto-emit value changes

**What happens:** the meta.xml declares the property `role="outputOnly"`.
The admin maps it to a Flow variable, but reactive targets and conditional
visibility never see typed values. (The runtime also reads each component's
current `@api` state on Next or Finish, but the guide says not to rely on it,
lwcguide use-best-practices-reactivity.)

**When it occurs:** the LWC author assumes that declaring the role is
enough. It is not — `role="outputOnly"` only changes Flow Builder's
property panel UX. The runtime still requires an explicit
`FlowAttributeChangeEvent` dispatch to push the value back.

**How to avoid:** for every output property in `<targetConfig>`, add a
matching dispatch in the JS:

```js
this.dispatchEvent(new FlowAttributeChangeEvent('myOutput', newValue));
```

Where `'myOutput'` matches the `@api` property name exactly (see gotcha 6 for what is and is not documented).

Code-review pairing rule: every `role="outputOnly"` in meta.xml should
correspond to at least one `FlowAttributeChangeEvent` dispatch in the JS
naming the same property.

---

## Gotcha 6: `FlowAttributeChangeEvent` attribute name must match the `@api` name exactly

**What happens:** the dispatch fires; no JS error is thrown; the Flow
variable does not update. UNVERIFIED (2026-10-20): the guide says to pass the
name as it appears in the JS and `.js-meta.xml` (lwcguide
use-best-practices-reactivity) but does not state case-sensitivity or a silent
no-op; both are observed behaviour.

**When it occurs:** mismatched casing, e.g. `FlowAttributeChangeEvent('OutputValue', v)`
for an `@api outputValue`.

**How to avoid:** always copy the exact `@api` property name when
constructing the event. Code-review rule: pair every dispatch with the
`@api` declaration on the same screen.

---

## Gotcha 7: `<isExposed>true</isExposed>` is required even for screen-only LWCs

**What happens:** the component has the right target, the right
`<targetConfig>`, but it still does not appear in Flow Builder. If `isExposed`
is false the component is not available to builders (api_meta 264 L86762-86765).

**When it occurs:** the meta.xml has `<isExposed>false</isExposed>` (or
omits the tag; UNVERIFIED (2026-10-20): the default when omitted is not stated). The convention from utility
LWCs (which often ship as internal-only) bleeds into screen LWC authoring.

**How to avoid:** every component that should be available in any builder
surface — Lightning App Builder, Experience Builder, Flow Builder —
needs `<isExposed>true</isExposed>`.

---

## Gotcha 8: Mobile rendering and `<supportedFormFactors>` (undocumented for FlowScreen)

**What happens:** UNVERIFIED (2026-10-20): the lightning__FlowScreen target page
of the LWC guide does not document `<supportedFormFactors>`, so the snippet below
is the Lightning-page form (lwcguide use-config-form-factors) applied by analogy
and the "empty screen on mobile" outcome is observed behaviour.

**When it occurs:** `<supportedFormFactors>` is omitted or declares only
`Large`. Mobile is `Small`.

**How to avoid:** explicitly declare both form factors when the flow is
intended to run on mobile, AND test on a real device:

```xml
<supportedFormFactors>
    <supportedFormFactor type="Large"/>
    <supportedFormFactor type="Small"/>
</supportedFormFactors>
```

Some base components have different mobile behaviors (touch targets,
soft keyboards, gesture handling) — visual-correctness on desktop does
not guarantee mobile correctness.

---

## Gotcha 9: Firing navigation events when the action is not in `availableActions`

**What happens:** the LWC dispatches `FlowNavigationBackEvent` on the very
first screen of a flow, where Back is not available (lwcguide
use-flow-screen-navigate). UNVERIFIED (2026-10-20): that nothing happens and no
error is logged is observed behaviour.

**When it occurs:** the action is not in the screen's `availableActions`
list (Back is unavailable on screen 1; Next is unavailable on the last
screen if Finish is the only terminal action).

**How to avoid:** read `availableActions` before dispatching. The Flow
runtime auto-populates this `@api` array on every screen LWC:

```js
@api availableActions = [];

handleClick() {
    if (this.availableActions.find((a) => a === 'NEXT')) {
        this.dispatchEvent(new FlowNavigationNextEvent());
    }
}
```

This also gives the LWC a reliable way to detect "am I on the last
screen" — `FINISH` present, `NEXT` absent.

---

## Gotcha 10: Apex-defined types use the `apex://` type form

**What happens:** the LWC accepts an Apex-defined type as input, but the
`<property type="apex">` form is not the documented one. UNVERIFIED
(2026-10-20): the "empty object at runtime" outcome is observed behaviour.

**When it occurs:** the meta.xml uses a bare `type="apex"` (with or without an
`extensionName` attribute, which the LWC guide does not list):

```xml
<property name="payload" type="apex"/>   <!-- not the documented form -->
```

**How to avoid:** use the `apex://` form (lwcguide targets-lightning-flow-screen):

```xml
<property name="payload" type="apex://MyNamespace.MyApexType"/>
```

If the class is in the component's own namespace, omit the namespace; for a
managed-package class, specify the package namespace.
