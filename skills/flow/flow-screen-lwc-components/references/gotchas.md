# Gotchas — Flow Screen LWC Components

Non-obvious Salesforce platform behaviors that cause real production
problems when building LWCs that render inside a Flow screen step.

---

## Gotcha 1: Missing `lightning__FlowScreen` target → silently invisible

**What happens:** the LWC deploys cleanly, appears under Setup → Lightning
Components, but Flow Builder's screen-component palette does not list it.
There is no error, no warning, no validation message — the absence is
silent.

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

## Gotcha 2: `@api validate()` must be synchronous — async returns are ignored

**What happens:** an `async validate()` returns a Promise. The Flow runtime
checks the return value synchronously, sees a truthy object that is not the
documented `{ isValid, errorMessage }` shape, and treats the screen as
valid. Navigation proceeds; the validation is silently bypassed.

**When it occurs:** any time the LWC needs to validate against server-side
state (uniqueness check, external system lookup, complex Apex evaluation)
and the author writes the natural-looking async pattern:

```js
@api
async validate() { ... }   // BROKEN — Flow ignores the Promise
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

## Gotcha 3: Reactive screen components require Flow API version 59.0+

**What happens:** two LWCs are wired correctly via Flow variables on the
same screen. Both `FlowAttributeChangeEvent` dispatches fire. But the
consuming LWC's input never updates until the user clicks Next.

**When it occurs:** the Flow's API version (set when the flow was created)
is below 59.0. Reactive screen components shipped in Winter '24 with API
version 59.0. Older flows — including clones of older flows — keep their
original API version and do not opt in automatically.

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
of a 5-screen flow. The runtime treats Finish as terminal: screens 3, 4,
and 5 are skipped, AND any post-screen actions (record updates, subflows,
Apex actions) that were intended to run after the flow completes do not
run for the skipped portion.

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
In Flow Builder, the property correctly appears in the output mapping
panel. The admin maps it to a Flow variable. But the variable always
holds the initial value — typing into the LWC field does not propagate.

**When it occurs:** the LWC author assumes that declaring the role is
enough. It is not — `role="outputOnly"` only changes Flow Builder's
property panel UX. The runtime still requires an explicit
`FlowAttributeChangeEvent` dispatch to push the value back.

**How to avoid:** for every output property in `<targetConfig>`, add a
matching dispatch in the JS:

```js
this.dispatchEvent(new FlowAttributeChangeEvent('myOutput', newValue));
```

Where `'myOutput'` matches the `@api` property name **case-sensitively**.

Code-review pairing rule: every `role="outputOnly"` in meta.xml should
correspond to at least one `FlowAttributeChangeEvent` dispatch in the JS
naming the same property.

---

## Gotcha 6: `FlowAttributeChangeEvent` attribute name is case-sensitive

**What happens:** the dispatch fires; no JS error is thrown; the Flow
variable still does not update. Spending hours adding `console.log`
statements does not reveal the cause because the dispatch *succeeds* — it
just goes to a property name that does not exist.

**When it occurs:** mismatched casing. `FlowAttributeChangeEvent('OutputValue', v)`
for an `@api outputValue` (lowercase first letter) silently no-ops.
Flow's case sensitivity differs from many JS conventions, so this trips
up authors used to forgiving HTML attribute matching.

**How to avoid:** always copy the exact `@api` property name when
constructing the event. Code-review rule: pair every dispatch with the
`@api` declaration on the same screen.

---

## Gotcha 7: `<isExposed>true</isExposed>` is required even for screen-only LWCs

**What happens:** the component has the right target, the right
`<targetConfig>`, but it still does not appear in Flow Builder.

**When it occurs:** the meta.xml has `<isExposed>false</isExposed>` (or
omits the tag, which defaults to `false`). The convention from utility
LWCs (which often ship as internal-only) bleeds into screen LWC authoring.

**How to avoid:** every component that should be available in any builder
surface — Lightning App Builder, Experience Builder, Flow Builder —
needs `<isExposed>true</isExposed>`.

---

## Gotcha 8: Mobile rendering requires explicit `<supportedFormFactors>`

**What happens:** the screen flow runs in the desktop Lightning Experience
correctly. The same flow, opened in the Salesforce mobile app, shows the
flow up to the screen with the custom LWC, then renders an empty screen
or an error.

**When it occurs:** `<supportedFormFactors>` is omitted (default = Large
only) or declares only `Large`. Mobile is `Small`.

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

## Gotcha 9: Firing navigation events when the action is unavailable is silently no-op

**What happens:** the LWC dispatches `FlowNavigationBackEvent` on the very
first screen of a flow. Nothing happens. No error, no log entry.

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

## Gotcha 10: Apex-defined types require `extensionName` on the property

**What happens:** the LWC accepts an Apex-defined type as input. The
`<property type="apex">` declaration deploys, the LWC sees the input as
an empty object at runtime.

**When it occurs:** the meta.xml omits `extensionName`:

```xml
<property name="payload" type="apex"/>   <!-- BROKEN -->
```

**How to avoid:** declare the fully qualified Apex class name:

```xml
<property name="payload"
          type="apex"
          extensionName="MyNamespace.MyApexType"/>
```

If the Apex type is defined in the default namespace, omit the namespace
prefix but keep the attribute. Without `extensionName`, Flow Builder
cannot validate the type and runtime serialization fails silently.
