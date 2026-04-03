# Gotchas — LWC Performance

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `@track` Doesn’t Deeply Observe `Date`, `Set`, Or `Map`

**What happens:** A component mutates a `Date`, `Set`, or `Map` and expects the template to refresh. The UI stays stale even though the code changed internal state.

**When it occurs:** The field is decorated with `@track` or is otherwise assumed to be reactive, but the value is not a plain object or array. Salesforce documents deep tracking only for plain objects and arrays.

**How to avoid:** Reassign a new instance instead of mutating internal state in place. For example, replace a `Date` with a cloned `new Date(oldDate.getTime())` after changing it.

---

## Gotcha 2: `if:true` And `if:false` Are The Legacy Conditional Path

**What happens:** A component chains `if:true` and `if:false` conditions and passes review because the UI works, but the template does more work than necessary and the code sits on a directive pair Salesforce says may be removed in the future.

**When it occurs:** Teams copy older LWC examples or Aura-era patterns and never migrate to `lwc:if`, `lwc:elseif`, and `lwc:else`.

**How to avoid:** Move to `lwc:if` chains and push nontrivial boolean logic into getters. Salesforce notes that `lwc:if` and `lwc:elseif` getters are accessed only once per directive instance.

---

## Gotcha 3: `key={index}` Breaks Stable Row Identity

**What happens:** A repeated list reuses the loop index as the `key`. When rows are inserted, removed, or sorted, the framework can no longer map row identity to the underlying record cleanly. Users see unnecessary rerenders or state jump between rows.

**When it occurs:** The incoming dataset does not expose an explicit identifier, or the developer reaches for the loop index as a shortcut.

**How to avoid:** Use a stable identifier from the dataset, typically the Salesforce record Id. If you must synthesize keys, generate them once and store them in private state rather than deriving them from list position.

---

## Gotcha 4: Dynamic Components Don’t Behave Like A General Purpose Bundle Splitter

**What happens:** A team uses `import()` casually for LWC lazy loading and is surprised when the component fails in an unlocked package or feels slower because the module is fetched only at runtime.

**When it occurs:** The component relies on dynamic components without enabling LWS, without declaring `lightning__dynamicComponent`, or in an unlocked-package scenario where Salesforce says dynamic components are unsupported.

**How to avoid:** Start with static imports. Move to dynamic components only when the renderer is genuinely optional or runtime-selected, keep the imports statically analyzable where possible, and verify the package model and LWS requirement up front.
