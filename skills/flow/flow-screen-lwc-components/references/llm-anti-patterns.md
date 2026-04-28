# LLM Anti-Patterns — Flow Screen LWC Components

Common mistakes AI coding assistants make when generating or advising on
LWCs that render inside Flow screens. Each entry shows the typical wrong
output, why an LLM defaults to it, the corrected pattern, and a
detection hint a reviewing agent can scan for.

---

## Anti-Pattern 1: `async validate()`

**What the LLM generates:**

```js
@api
async validate() {
    const result = await checkUniquenessApex({ value: this.draft });
    return { isValid: result, errorMessage: 'Already exists.' };
}
```

**Why it happens:** modern JS / TypeScript training data overwhelmingly
favors `async/await` for any function that calls a remote service.
LLMs default to the asynchronous shape because it looks idiomatic.

**Correct pattern:**

```js
// Pre-fetch via @wire so the result is cached on the instance.
@wire(checkUniqueness, { value: '$draft' })
wiredCheck({ data }) {
    this._isUnique = data === true;
}

@api
validate() {
    if (this._isUnique === undefined) {
        return { isValid: false, errorMessage: 'Still checking — try again.' };
    }
    if (!this._isUnique) {
        return { isValid: false, errorMessage: 'Already exists.' };
    }
    return { isValid: true };
}
```

**Detection hint:** any `validate()` method that contains `async`,
`await`, `.then(`, or whose body returns the result of an Apex
imperative call without awaiting first is the broken pattern. Regex:
`(?s)@api\s+(async\s+)?validate\s*\([^)]*\)\s*\{[^}]*\b(await|then|async)\b`.

---

## Anti-Pattern 2: Missing `lightning__FlowScreen` target

**What the LLM generates:**

```xml
<targets>
    <target>lightning__AppPage</target>
    <target>lightning__RecordPage</target>
</targets>
```

…even when the user explicitly asked for a Flow screen component.

**Why it happens:** the most common LWC examples in training data target
Lightning App Builder, not Flow Builder. The model auto-completes the
"normal" target list.

**Correct pattern:**

```xml
<targets>
    <target>lightning__FlowScreen</target>
</targets>
<targetConfigs>
    <targetConfig targets="lightning__FlowScreen">
        <!-- properties -->
    </targetConfig>
</targetConfigs>
```

**Detection hint:** if the user prompt mentions "screen flow", "flow
screen", `FlowAttributeChangeEvent`, or `validate()`, and the generated
meta.xml does NOT contain the literal string `lightning__FlowScreen`,
the output is broken. Regex on the generated `.js-meta.xml`:
`<target>lightning__FlowScreen</target>` must match.

---

## Anti-Pattern 3: Wrong import path for `flowSupport`

**What the LLM generates:**

```js
import { FlowAttributeChangeEvent } from 'lwc/flowSupport';        // wrong
import { FlowAttributeChangeEvent } from '@salesforce/flowSupport'; // wrong
import { FlowAttributeChangeEvent } from 'lightning/flow';          // wrong
```

**Why it happens:** Salesforce module paths are a small, idiosyncratic
namespace (`lightning/...`, `@salesforce/...`, `lwc`, `c/...`). LLMs
frequently mix them up because the training corpus contains all four
patterns and the right one for `flowSupport` is comparatively rare.

**Correct pattern:**

```js
import {
    FlowAttributeChangeEvent,
    FlowNavigationNextEvent,
    FlowNavigationBackEvent,
    FlowNavigationFinishEvent,
    FlowNavigationPauseEvent
} from 'lightning/flowSupport';
```

**Detection hint:** if any line imports `FlowAttributeChangeEvent` or
any `FlowNavigation*Event` and the source path is NOT exactly
`'lightning/flowSupport'`, the import is broken. Regex:
`import\s*\{[^}]*Flow(AttributeChange|Navigation\w+)Event[^}]*\}\s+from\s+['"](?!lightning/flowSupport['"])`.

---

## Anti-Pattern 4: Calling `lwc/wire` to fetch data inside `validate()`

**What the LLM generates:**

```js
@api
validate() {
    // "I'll just get fresh data right when validation runs!"
    const fresh = wireAdapter({ id: this.recordId });
    if (!fresh.data) {
        return { isValid: false, errorMessage: 'Could not load data.' };
    }
    // ...
}
```

**Why it happens:** the model conflates `@wire` (a decorator that
provisions data into a property) with an imperative function. `@wire`
cannot be invoked at a point in time; it is a reactive declaration. The
generated code does not compile, but a more subtle variant — calling
`getRecord` from `lightning/uiRecordApi` imperatively inside
`validate()` — does compile and silently breaks because the call
returns a Promise that `validate()` ignores.

**Correct pattern:**

```js
@wire(getRecord, { recordId: '$recordId', fields: [...] })
wiredRecord({ data }) {
    this._record = data;
}

@api
validate() {
    if (!this._record) {
        return { isValid: false, errorMessage: 'Record still loading — try again.' };
    }
    // Validate against this._record synchronously.
    return { isValid: true };
}
```

**Detection hint:** any imperative Apex / UI API call appearing inside
the `validate()` body — `getRecord(`, `apexMethod(`, `fetch(`,
`createRecord(` — is broken regardless of `await` usage. Regex on
`validate()` body: `\b(getRecord|getFieldValue|fetch|createRecord|updateRecord)\s*\(`.

---

## Anti-Pattern 5: Recommending a custom LWC when a stock validation rule would suffice

**What the LLM generates:** in response to "I need to enforce that the
phone number on a screen flow is exactly 10 digits", the model outputs
a complete custom LWC with `validate()` and a regex. The user accepts
it, deploys it, and now owns code they did not need to maintain.

**Why it happens:** the model is asked "build an LWC for X", so it
builds an LWC. It does not stop to check whether the simpler stock
solution is better.

**Correct pattern:** route the user to:

1. Stock `Phone` screen component (validates phone format declaratively
   with no code).
2. Stock validation rule on a Number / Text input using a Flow formula
   resource: `IF(LEN({!flowVar_Phone}) <> 10, "Phone must be 10
   digits.", null)` — assigned to the field's "validate" formula.
3. Reactive screen component pattern if the validation depends on
   another field on the same screen.

A custom LWC is justified ONLY when:

- The UI is impossible with stock components (e.g. visualization,
  custom datatable, scanner).
- The validation rule cannot be expressed with a Flow formula
  (e.g. requires server-side lookup, complex regex with conditional
  branches, or cross-record evaluation).
- Programmatic navigation is required (auto-advance after capture).

**Detection hint:** the prompt describes the requirement as a single
input field with a declarative validation rule. Before generating the
LWC, the model should propose the stock alternative and only proceed
to LWC code if the user confirms the gap.

---

## Anti-Pattern 6: Mismatched property name in `FlowAttributeChangeEvent`

**What the LLM generates:**

```js
@api outputValue;
// ...
this.dispatchEvent(new FlowAttributeChangeEvent('OutputValue', val));   // wrong casing
this.dispatchEvent(new FlowAttributeChangeEvent('output_value', val));  // wrong style
this.dispatchEvent(new FlowAttributeChangeEvent('output-value', val));  // wrong style
```

**Why it happens:** LLMs casing-shift between PascalCase, snake_case,
and kebab-case based on what other variables in the file look like.
HTML attribute matching is forgiving; Flow's variable matching is not.

**Correct pattern:** the first argument MUST exactly match the `@api`
property name in JS:

```js
@api outputValue;
this.dispatchEvent(new FlowAttributeChangeEvent('outputValue', val));
```

**Detection hint:** for every `FlowAttributeChangeEvent` constructor
call, locate the `@api` declaration with the matching name. If the
strings are not identical (case included), the dispatch is broken.

---

## Anti-Pattern 7: Firing navigation events without checking `availableActions`

**What the LLM generates:**

```js
this.dispatchEvent(new FlowNavigationBackEvent());   // unconditional
```

**Why it happens:** the example snippets in docs often omit the
`availableActions` guard for brevity. LLMs reproduce the brevity in
production code where the guard is necessary.

**Correct pattern:**

```js
@api availableActions = [];

handleBack() {
    if (this.availableActions.find((a) => a === 'BACK')) {
        this.dispatchEvent(new FlowNavigationBackEvent());
    } else {
        // optionally render a hint that Back is unavailable on this screen
    }
}
```

**Detection hint:** any dispatch of `FlowNavigation(Next|Back|Finish|Pause)Event`
NOT preceded by an `availableActions.find` / `includes` check is
fragile. Regex: `dispatchEvent\(new FlowNavigation\w+Event\(\)\)` —
review each match for an enclosing `availableActions` guard.

---

## Anti-Pattern 8: Hardcoding `FlowNavigationFinishEvent` in a reusable LWC

**What the LLM generates:**

```js
// "After capturing the value, finish the flow."
this.dispatchEvent(new FlowAttributeChangeEvent('captured', value));
this.dispatchEvent(new FlowNavigationFinishEvent());
```

**Why it happens:** the original example was a single-screen flow. The
model reproduces the Finish dispatch when the user adapts the LWC to
a multi-screen flow.

**Correct pattern:** default to `Next`. Use Finish only when
`availableActions` shows `FINISH` and not `NEXT`:

```js
const isLastScreen = this.availableActions.includes('FINISH')
                     && !this.availableActions.includes('NEXT');
this.dispatchEvent(new FlowAttributeChangeEvent('captured', value));
this.dispatchEvent(isLastScreen ? new FlowNavigationFinishEvent()
                                : new FlowNavigationNextEvent());
```

**Detection hint:** any `FlowNavigationFinishEvent` dispatch in a
reusable LWC (one that does not own its consuming flow) is suspect.
Pair it with an explanatory comment or rewrite as conditional.

---

## Anti-Pattern 9: Forgetting `<isExposed>true</isExposed>`

**What the LLM generates:**

```xml
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>61.0</apiVersion>
    <targets>
        <target>lightning__FlowScreen</target>
    </targets>
    <!-- isExposed missing -->
</LightningComponentBundle>
```

**Why it happens:** internal-only utility LWCs in the training corpus
omit `<isExposed>` (defaulting to false). LLMs reproduce that minimal
shape even when a builder-exposed component is required.

**Correct pattern:**

```xml
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>61.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__FlowScreen</target>
    </targets>
</LightningComponentBundle>
```

**Detection hint:** any `js-meta.xml` declaring a `lightning__*` target
that does not contain `<isExposed>true</isExposed>` is broken.

---

## Anti-Pattern 10: Recommending `pubsub` or `lightning/messageService` for cross-LWC state on a screen

**What the LLM generates:** when asked "how do I share state between
two LWCs on the same Flow screen", the model suggests the standard
LWC-to-LWC communication pattern: Lightning Message Service.

**Why it happens:** LMS is the canonical answer for cross-LWC
communication on Lightning pages. The model treats the Flow screen as
just another rendering context.

**Correct pattern:** route state through a Flow variable:

1. Source LWC dispatches `FlowAttributeChangeEvent` for an output
   property.
2. Admin in Flow Builder maps the output to a Flow variable.
3. Admin maps the Flow variable to the consuming LWC's input property.
4. With Flow API 59+, the consuming LWC sees the input update reactively.

**Why LMS is wrong here:**

- Flow Debug shows variable changes but not LMS messages — debugging is
  blinded.
- The state is invisible to other Flow elements (Decision, Assignment,
  Loop) that need to read the value.
- Reactive screen semantics depend on the Flow variable model; LMS
  bypasses it.

**Detection hint:** any `import { ... } from 'lightning/messageService'`
or `import { ... } from 'c/pubsub'` inside a component targeted at
`lightning__FlowScreen` is suspect. Confirm the cross-LWC need cannot
be solved with a Flow variable before accepting the import.
