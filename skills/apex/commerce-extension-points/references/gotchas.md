# Gotchas — Commerce Extension Points

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: DML Exception Is Silent Until Runtime

**What happens:** A DML statement (insert, update, delete, upsert) inside a `CartExtension` hook method throws `System.DmlException` at runtime with the message "DML not allowed during cart recalculation." This does not manifest at compile time or deploy time. Unit tests that directly invoke `calculate()` without running the live cart recalculation pipeline also do not catch it — the restriction is enforced by the pipeline itself, not by the Apex compiler or test runner.

**When it occurs:** The first time the actual Commerce cart recalculation pipeline invokes the registered extension in a live store or full integration test. A buyer adding items to a cart triggers recalculation; the extension fires; the DML statement throws; the cart enters an error state; the buyer cannot proceed to checkout.

**How to avoid:** Audit every line of the `calculate()` method (and any method it calls) for DML statements before deploying. If state needs to be persisted, buffer it in a static variable or Platform Cache during the extension run, then flush via Platform Event or Queueable after the recalculation pipeline returns control to the caller.

---

## Gotcha 2: EPN String Typo Produces No Error — Extension Silently Never Fires

**What happens:** If the `ExtensionPointName` field in the `RegisteredExternalService` metadata record contains a typo, incorrect casing, or an outdated EPN string, the platform does not throw a deploy-time error. It does not log a warning at runtime. The Apex class is deployed and valid; the metadata record is deployed and valid. The extension simply never fires during cart recalculation. Pricing, inventory, or checkout behavior appears unchanged.

**When it occurs:** Any time the EPN is typed manually rather than copied verbatim from the official documentation. Common mistakes include replacing underscores with hyphens (`Commerce-Domain-Pricing-CartCalculator`), using lowercase, or using an abbreviated EPN from an older API version.

**How to avoid:** Copy the EPN string character-for-character from the official B2B Commerce Extensions documentation. The correct EPN for pricing is exactly `Commerce_Domain_Pricing_CartCalculator`. After deployment, verify the extension is firing by adding a debug log entry at the start of `calculate()` and checking the debug log during a cart recalculation in a sandbox store.

---

## Gotcha 3: After-Hook HTTP Callout Compiles But Throws at Runtime

**What happens:** An HTTP callout placed inside an after-phase hook method compiles successfully and deploys without error. The `System.CalloutException: "You have uncommitted work pending. Please commit or rollback before calling out"` (or similar callout-prohibited message) is only thrown at runtime when the cart recalculation pipeline reaches the after phase.

**When it occurs:** Any after-phase `calculate()` or equivalent method that calls `new Http().send(req)`. This is particularly common when an extension is initially written without understanding the before/after distinction and the callout is placed in the main `calculate()` method which is actually an after hook.

**How to avoid:** Verify which lifecycle phase the base class method belongs to before placing a callout. Before hooks run before the platform commits calculated values; after hooks run after. Move any callout logic to a before hook. If the design requires calling an external system after values are committed, consider whether a Platform Event published from the after hook (which is permitted) and an external subscriber is the right architecture instead.

---

## Gotcha 4: Only One RegisteredExternalService Record Per EPN Per Store

**What happens:** When a second `RegisteredExternalService` record is deployed for the same `ExtensionPointName` and store, the platform does not raise a conflict error. The last deployed record silently wins and becomes the active extension. The previously registered extension stops firing. There is no runtime warning, no admin notification, and no indication in the Commerce setup UI that an override has occurred.

**When it occurs:** During incremental development where a developer creates a new `RegisteredExternalService` record for an updated version of an extension rather than updating the existing record's `ExternalServiceProvider` reference. Also common during org merges where two sandboxes independently register extensions for the same EPN.

**How to avoid:** Before creating a new `RegisteredExternalService` record, query the existing records for the target EPN. If a record already exists, update its `ExternalServiceProvider` field rather than creating a new record. In a source-tracked org, use SFDX to diff the metadata before deployment to confirm no duplicate EPN records are being pushed.

---

## Gotcha 5: Async Apex Inside Extension Causes Immediate Exception, Not Deferral

**What happens:** Calling `System.enqueueJob()`, `@future` methods, `Database.executeBatch()`, or `Messaging.sendEmail()` inside a cart extension hook does not silently defer the work — it throws `System.AsyncException` immediately, before the async call even begins. The exception propagates up through the recalculation pipeline and causes the entire cart recalculation to fail.

**When it occurs:** Any attempt to use async Apex patterns inside `calculate()` or any method it invokes synchronously. Developers familiar with trigger-based async patterns often assume the same approach works inside Commerce extensions.

**How to avoid:** All logic inside a cart extension must be synchronous. If background work is genuinely required (logging, notifications, data sync), publish a Platform Event from inside the extension — Platform Event publish is permitted and the subscriber can run asynchronously. Never use `@future`, `enqueueJob`, or batch Apex inside any hook method.
