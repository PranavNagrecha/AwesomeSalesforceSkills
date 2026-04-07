# Gotchas — CPQ Apex Plugins

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: CPQ Settings Plugin Registration Is Org Data, Not Metadata

**What happens:** After deploying a new Apex plugin class via change set, package, or Salesforce CLI, the plugin never fires. CPQ behaves as if the plugin does not exist, even though the class is deployed and compiles cleanly.

**When it occurs:** Any time a plugin class is deployed without a separate post-deployment step to update the `SBQQ__CustomActionSettings__c` record. The plugin registration fields on that object are org data rows — they are not part of any `.settings`, `.object`, or custom metadata file and are therefore not carried by source deployments.

**How to avoid:** After deployment, manually navigate to **Setup > Installed Packages > Salesforce CPQ > Configure** and enter the Apex class name in the appropriate plugin field. For automated pipelines, write a post-deploy Apex anonymous script or a data loading step that upserts the `SBQQ__CustomActionSettings__c` record with the correct class name. Document this step in your release runbook so it is never skipped.

---

## Gotcha 2: A JS QCP Hook Returning `undefined` Freezes the Quote Save UI Indefinitely

**What happens:** The quote save spinner appears and never resolves. The user sees no error message. After several minutes the session may time out or the user force-refreshes, losing unsaved quote data.

**When it occurs:** Any JS QCP hook function that does not have an explicit `return Promise.resolve()` statement returns `undefined` by default in JavaScript. CPQ's calculation engine awaits the return value of each hook as a Promise. When `undefined` is returned, the engine's `await` never resolves because `undefined` is not a thenable.

This commonly happens when a developer adds a conditional branch that returns early without a Promise:

```javascript
// WRONG — early return without Promise
export function onAfterCalculate(quoteModel, quoteLineModels, conn) {
    if (quoteLineModels.length === 0) {
        return; // returns undefined — engine hangs
    }
    // ... logic ...
    return Promise.resolve();
}
```

**How to avoid:** Wrap the entire hook body in a pattern that always returns a Promise regardless of the code path. The simplest safe pattern is:

```javascript
export function onAfterCalculate(quoteModel, quoteLineModels, conn) {
    return new Promise(function(resolve) {
        // All logic here — resolve() at the end of every branch
        resolve();
    });
}
```

Alternatively, ensure every conditional branch ends with `return Promise.resolve()`.

---

## Gotcha 3: Apex Plugin Classes Must Be `global` — `public` Compiles but Fails at Runtime

**What happens:** The Apex plugin class deploys without compile errors and CPQ Settings shows the class name correctly registered. When a rep saves a quote, CPQ silently skips the plugin or throws an opaque `System.TypeException: Method is not visible` error visible only in debug logs.

**When it occurs:** The CPQ managed package (`SBQQ` namespace) defines its plugin interfaces as `global`. When your implementing class uses the `public` access modifier instead of `global`, the Apex compiler accepts the class because `public` satisfies the interface in a local-namespace compilation context. At runtime, the CPQ package's instantiation code (which runs in the `SBQQ` namespace) cannot access `public` class members from an external namespace. Only `global` members are visible across namespace boundaries.

**How to avoid:** Always declare the plugin class and all overridden methods as `global`:

```apex
global class MyOrderPlugin implements SBQQ.OrderPlugin {
    global void onBeforeInsert(List<Order> orders,
                               SBQQ.DefaultOrderProduct defaultProduct,
                               Database.UnitOfWork uow) { ... }
    global void onAfterInsert(List<Order> orders,
                              SBQQ.DefaultOrderProduct defaultProduct,
                              Database.UnitOfWork uow) { ... }
}
```

Lint for `public class` or `public void` in any file that also contains `implements SBQQ.`.

---

## Gotcha 4: Only One Plugin Per Type — No Chaining, Silent Replacement

**What happens:** A second Apex plugin of the same type is registered by overwriting the CPQ Settings field. The first plugin stops firing entirely with no warning or error. All customizations in the original plugin are silently abandoned.

**When it occurs:** CPQ does not support multiple registered plugins of the same type running in sequence. The Settings field holds a single class name. Writing a new class name to that field replaces the previous registration. This happens in practice when different teams add plugins independently, or when a new developer does not check the existing registration.

**How to avoid:** Before registering any new plugin, query `SBQQ__CustomActionSettings__c` and document the current value of the relevant field. If a plugin is already registered, combine the new logic into the existing class using a dispatcher pattern — one `global` class that delegates to private inner classes or methods — rather than registering a replacement. Treat the registration field as a singleton and manage it deliberately.

---

## Gotcha 5: `SBQQ.CalculateCallback` Errors After `callback.run()` Are Silently Swallowed

**What happens:** An Apex `QuoteCalculatorPlugin` implementation performs async logic, then calls `callback.run(quoteLinesMap)`. Any exception thrown after `callback.run()` is called does not propagate to the CPQ UI as a user-visible error. The quote appears to save successfully even though the plugin's post-run logic failed.

**When it occurs:** When developers add logging, DML, or platform event publishing after `callback.run()` and assume that exceptions from that code will surface as quote save errors. They do not — CPQ considers the callback fulfilled once `run()` is invoked and does not monitor subsequent execution in the same stack frame.

**How to avoid:** Perform all validation and data mutation before calling `callback.run()`. Any operation that must succeed for the plugin to be considered healthy must complete and be checked for errors before `callback.run()` is called. If post-run side effects are needed, use a platform event or a `@future` method that logs failures independently to a custom error object.
