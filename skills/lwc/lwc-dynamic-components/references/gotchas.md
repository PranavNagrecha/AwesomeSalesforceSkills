# Gotchas — LWC Dynamic Components

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Computed Import Specifiers Are Silently Ignored or Cause Build Errors

**What happens:** A developer tries to construct the module specifier dynamically from a variable — for example, `` `c/${componentName}` `` or `'c/' + this.variant`. The intent is to drive the import entirely from runtime data. At build time, the LWC toolchain cannot analyze the chunk graph because the string is not static. The result is either a build error, a runtime module-not-found failure, or a silently empty component area depending on the environment.

**When it occurs:** Any time the import specifier is not a compile-time constant string literal. This includes template literals, string concatenation, and indirect variable references.

**How to avoid:** All candidate components must appear as explicit literal strings in the source. Use a `switch` statement, `if/else` chain, or a lookup map where every value is a literal string written out in full. The build toolchain analyzes each literal string and creates the corresponding chunk. Routing logic can be dynamic; the specifier strings themselves cannot.

```js
// Wrong — specifier is computed
const mod = await import(`c/${this.componentName}`);

// Correct — specifier is a literal in each branch
let mod;
if (this.variant === 'premium') {
    mod = await import('c/premiumView');
} else {
    mod = await import('c/standardView');
}
```

---

## Gotcha 2: Dynamic Import Is Not Supported in Unlocked Packages

**What happens:** A team builds a managed-package-style routing pattern using `lwc:component` and `import()`, then deploys to an org using an unlocked package. The dynamic import call fails at runtime, and the component silently renders nothing or throws an error depending on the org's error handling surface.

**When it occurs:** Whenever the `lwc:component` directive is used in a component that ships in an **unlocked package** rather than a managed second-generation package. Salesforce's platform restriction is that the `lightning__dynamicComponent` target and dynamic import support require managed packaging.

**How to avoid:** Confirm the package type before investing in this pattern. If the deployment model is unlocked packages, use static imports with `lwc:if`/`lwc:elseif` conditional rendering instead. If the pattern is essential, the project must ship in a managed package.

---

## Gotcha 3: Legacy Locker Service Blocks `import()` Entirely

**What happens:** An org that has not migrated to Lightning Web Security (LWS) will throw a runtime TypeError when `import()` is called from an LWC. The error surface varies — sometimes it appears in the browser console, sometimes the component host element goes blank with no visible message.

**When it occurs:** Orgs where Setup > Session Settings > Lightning Web Security is not enabled. Older Enterprise and Government Cloud orgs are the most common cases, especially orgs that deferred the LWS migration.

**How to avoid:** Before implementing dynamic components in a client org, verify LWS status in Setup. If LWS is off, either assist the team with the migration (which requires testing all existing LWC components for Locker vs. LWS behavioral differences) or use a static conditional rendering pattern that does not require `import()`.

---

## Gotcha 4: `lwc:is` Set to `null` After Load Does Not Unmount Cleanly in All Versions

**What happens:** Setting the reactive property bound to `lwc:is` back to `null` or `undefined` is intended to remove the rendered component. In some older API versions, this does not reliably call `disconnectedCallback` on the child, leading to orphaned event listeners or timers.

**When it occurs:** When the host component re-routes to a different child (sets `lwc:is = null` then immediately sets a new constructor) within the same tick, or when navigating away from a page without an explicit cleanup step.

**How to avoid:** If the dynamic child registers event listeners or setInterval/setTimeout in its `connectedCallback`, ensure `disconnectedCallback` cleans them up. Do not rely on the parent's nulling of `lwc:is` as the only cleanup trigger. Test component removal explicitly during QA.

---

## Gotcha 5: Wire Adapters on the Host Do Not Automatically Re-Trigger the Import

**What happens:** A common pattern is to wire a record or flag value and then call `import()` inside the wire handler. If the wired data changes after the initial load (e.g., the record type is updated), the wire handler fires again — but the previously loaded constructor is still assigned to `lwc:is`. The component does not automatically re-render with the new constructor unless the property is explicitly updated.

**When it occurs:** In record pages where the record type can change via in-place editing, or in scenarios where the wired data source is reactive and can return different values over the component's lifetime.

**How to avoid:** Always reassign `this.dynamicCtor = null` before assigning the new constructor so that LWC has a chance to clear and re-render the host element. Optionally add a brief loading state between the two assignments to prevent the user from seeing stale content during the transition.

```js
@wire(getRecordTypeId, { recordId: '$recordId' })
async handleRecordType({ data }) {
    if (!data) return;
    this.dynamicCtor = null; // clear first to force re-render
    await Promise.resolve(); // yield to the rendering engine
    const { default: Ctor } = await import(this._specifierFor(data));
    this.dynamicCtor = Ctor;
}
```
