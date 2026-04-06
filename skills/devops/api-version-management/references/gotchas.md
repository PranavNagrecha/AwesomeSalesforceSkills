# Gotchas — API Version Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: sourceApiVersion Is a CLI Setting, Not a Runtime Override

**What happens:** Developers update `sourceApiVersion` in `sfdx-project.json` to the latest version and believe all Apex classes, triggers, and components now execute at that version. They do not. Each component runs at the version declared in its own `-meta.xml` file. The `sourceApiVersion` controls only what version the Salesforce CLI uses during `sf project deploy`, `sf project retrieve`, and `sf project generate` operations.

**When it occurs:** Every project that updates `sfdx-project.json` without also updating individual component metadata files. Particularly common after a new developer joins and "modernizes" the project config.

**How to avoid:** Always treat `sourceApiVersion` updates as a two-step process: (1) update `sfdx-project.json`, (2) update every component's `<apiVersion>` element. Run a version audit after any sourceApiVersion change.

---

## Gotcha 2: Apex Behavior Changes Silently Between API Versions

**What happens:** Moving an Apex class from version 40.0 to version 63.0 changes the runtime behavior of certain System methods without any compile-time error or warning. Known examples include: `String.valueOf(null)` returning `'null'` vs `null`; SOQL relationship query field accessibility; `Trigger.new` deep-copy semantics; `JSON.deserialize` handling of unknown fields; and `Database.insert` partial-success return value structure.

**When it occurs:** During a version upgrade of any Apex class that uses affected methods. Because there are no compiler warnings, the first sign is a failing test or — worse — incorrect production data.

**How to avoid:** Before upgrading a component's API version, consult the Salesforce release notes for every version in the upgrade range. Run the full test suite in a sandbox at the new version. Pay special attention to null-handling, serialization, and trigger context code.

---

## Gotcha 3: Retired Versions Cause Hard Errors, Not Graceful Degradation

**What happens:** When Salesforce retires an API version, REST calls to `/services/data/vXX.0/` return a `UNSUPPORTED_API_VERSION` error. SOAP calls to `/services/Soap/c/XX.0` also fail. There is no automatic forwarding to the nearest supported version. Metadata components pinned to a retired version may fail during deployment with opaque errors.

**When it occurs:** After a retirement wave takes effect (e.g., versions 7.0-30.0 retired in Summer '22). External integrations hard-coded to a specific version URL break immediately on the retirement date.

**How to avoid:** Monitor the Salesforce API End-of-Life policy page. Query `ApiTotalUsage` event logs to detect runtime calls to versions approaching retirement. Upgrade integration endpoints at least one release before the retirement date.

---

## Gotcha 4: LWC Without Explicit apiVersion Inherits the Org Default — But That Is Now Deprecated

**What happens:** Before Spring '25, LWC components without an `<apiVersion>` in `.js-meta.xml` implicitly used the org's current API version. This meant the same component could behave differently across orgs at different release levels. Starting in Spring '25, Salesforce requires explicit version declaration. Components without it still work but use deprecated implicit behavior that may be removed in a future release.

**When it occurs:** Any LWC bundle created before Spring '25 that was never updated to include explicit versioning. Particularly problematic in managed packages deployed to subscriber orgs at different release levels.

**How to avoid:** Add `<apiVersion>63.0</apiVersion>` (or current) to every `.js-meta.xml` file. Include a CI check that rejects LWC bundles without explicit version declarations.

---

## Gotcha 5: Package.xml Version Is Not the Same as Component API Version

**What happens:** The `<version>` element in `package.xml` controls which metadata types and fields are visible to the Metadata API during retrieve and deploy operations. It does not set or change the `<apiVersion>` of individual components. A `package.xml` at version 63.0 can retrieve Apex classes that are individually pinned to version 35.0. Developers confuse these two version concepts and assume that deploying with a modern `package.xml` modernizes all components.

**When it occurs:** During manual Metadata API deployments, change set-adjacent workflows, or any process that generates `package.xml` files.

**How to avoid:** Understand that `package.xml` version and component `apiVersion` serve different purposes. After deploying with a modern `package.xml`, still audit individual component versions. They will not have changed.
