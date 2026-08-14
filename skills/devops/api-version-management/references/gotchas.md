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

**What happens:** When Salesforce retires an API version, calls fail with a protocol-specific error — REST returns `410:GONE`, SOAP returns `500:UNSUPPORTED_API_VERSION`, and Bulk returns `400:InvalidVersion`. (Do not expect `UNSUPPORTED_API_VERSION` on the REST path; a client matching on that string will not recognise the failure.) There is no automatic forwarding to the nearest supported version. Metadata components pinned to a retired version may fail during deployment with opaque errors.

**When it occurs:** After a retirement wave takes effect. Two waves have completed: 7.0–20.0 retired in Summer '22; 21.0–30.0 deprecated in Summer '22 and retired in Summer '25. External integrations hard-coded to a specific version URL break immediately on the retirement date.

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

---

## Gotcha 6: Crossing API 67.0 Flips a Class's Sharing Default from `without` to `with`

**What happens:** An Apex class carrying no `with sharing` / `without sharing` / `inherited sharing` keyword changes behaviour at the 67.0 boundary. The Apex Developer Guide states: "In API version 67.0 and later, classes without an explicit sharing declaration run in with sharing mode." Below 67.0 the same source ran without sharing. What decides is the `apiVersion` in the class's own `.cls-meta.xml`, not the org's release — a Summer '26 org runs a class pinned to 58.0 with the old default — which is exactly why a version-upgrade project, not a release upgrade, is where this surfaces. There is also an inheritance-chain rule: "If the class is part of an inheritance chain, and any class in that chain is saved as API version 67.0 and later, the class runs in with sharing mode." Bumping one class in a hierarchy can therefore flip untouched parents and children with it.

**When it occurs:** During any tier upgrade whose range crosses 66.0 → 67.0. The failure is silent and one-directional: code that relied on the implicit `without sharing` default — sharing-recalculation utilities, cross-owner roll-up helpers, batch jobs running as a low-privilege automation user — starts returning fewer rows instead of throwing. Tests that seed their own data as the running user will not catch it.

**How to avoid:** Before moving a tier across 67.0, find every `.cls` in it whose class declaration has no sharing keyword and write the intended mode down explicitly *at the old version first* — `without sharing` where the omission was deliberate, `with sharing` where it was an oversight. Deploy that, then bump `apiVersion`, so the version change alters nothing. Note the exception: **Apex triggers run in a without-sharing context at every API version and cannot carry a sharing declaration** ("Apex triggers can't have an explicit sharing declaration"), so this sharing-declaration default never applies to a `.trigger` file itself. That is the only claim this gotcha makes about triggers — the *access mode* of the statements inside a trigger body (FLS, CRUD, user vs. system mode) is a separate dimension, and an upgrade plan should resolve it against `skills/apex/apex-with-without-sharing-decision` rather than inferring it from here. For the full version-gated matrix of read and write idioms, link to [`agents/_shared/AGENT_CONTRACT.md` § "Apex security idiom by API version"](../../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version) rather than keeping a local copy of it.
