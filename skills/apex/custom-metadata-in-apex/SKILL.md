---
name: custom-metadata-in-apex
description: "Use when Apex must read, interpret, or deploy Custom Metadata Type configuration, or when deciding between Custom Metadata Types, Custom Settings, and Custom Labels. Triggers: 'Custom Metadata Type', '__mdt', 'getInstance', 'Apex Metadata API', 'protected custom metadata'. NOT for the Setup-side CMT vs Custom Settings choice — use admin/custom-metadata-types-and-settings. NOT for Hierarchy Custom Settings — use apex/apex-custom-settings-hierarchy. More trigger keywords: getAll, Metadata.Operations.enqueueDeployment, Metadata.DeployCallback, Metadata.CustomMetadataValue, DeployStatus SucceededPartial, __mdt truncated at 255 characters, TestVisible injection for __mdt, customMetadata folder, md-meta.xml, fieldManageability."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I query custom metadata in Apex"
  - "custom metadata type versus custom settings"
  - "Apex Metadata API for custom metadata records"
  - "protected custom metadata in managed package"
  - "do tests see custom metadata records"
  - "read a __mdt configuration record from Apex"
  - "update a custom metadata record from Apex code"
  - "test a class that depends on custom metadata without deploying records"
  - "custom metadata field value comes back truncated"
  - "insert on __mdt is not allowed"
  - "write a Metadata.DeployCallback and test it"
  - "stop enqueueDeployment from running inside an Apex test"
  - "getAll versus SOQL on a custom metadata type"
  - "custom metadata deploy succeeded but the value did not change"
tags:
  - custom-metadata
  - __mdt
  - apex-metadata-api
  - configuration
  - packaging
inputs:
  - "the configuration use case and whether reads only or metadata updates are needed"
  - "packaging model such as unpackaged, unlocked, or managed package"
  - "test behavior, namespace, and visibility constraints"
  - "the longest value any configuration field must carry"
  - "who is allowed to change the configuration after release, and through what"
outputs:
  - "configuration storage recommendation"
  - "review findings for read, test, and deployment risks"
  - "Apex pattern for reading or deploying custom metadata safely"
  - "a deployable __mdt type, its records, a selector class and its test class"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Custom Metadata In Apex

Use this skill when configuration belongs in metadata and Apex is either the consumer or the initiator of a metadata deployment path. The main goal is to keep behavior configurable without designing Custom Metadata Types as if they were ordinary row data.

`references/code-examples.md` carries the deployable version of everything below: the `__mdt` type and its fields, two records, a selector that reads them, a test that swaps the configuration with no DML, and a deployer plus `Metadata.DeployCallback` with a test that never enqueues a real deployment.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the requirement read only configuration, subscriber-editable setup, or package-controlled behavior?
- Does Apex only need to read `__mdt` records, or must some setup flow eventually create or update metadata records?
- Are tests validating multiple configuration variants, packaging visibility, or namespace behavior?

---

## Questions to Ask Before Configuring

Ask these before writing the type or the class. Each maps to a gotcha in `references/gotchas.md`; skipping them produces code that compiles, deploys, and quietly returns the wrong configuration.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the longest string any of these fields will ever hold?" | `getAll()` and `getInstance()` return "only the first 255 characters… so longer text fields get truncated" (Apex Reference Guide L204569–204572) — silently, with no exception | Which reads may use the cache accessors and which must be SOQL, decided per field rather than per class |
| "Does anything ever need to *change* a record at runtime, or only read one?" | The write path is `Metadata.Operations.enqueueDeployment()`, which is asynchronous, counts as an async Apex job, and cannot delete (Apex Developer Guide L28194–28197, L28226–28229) | Whether this build needs a deployer class, a callback class, and a partial-success branch at all — or none of them |
| "Will this type ship inside a managed package?" | `visibility` on the type (`Public` / `Protected` / `PackageProtected`) and `protected` on each record only mean anything inside a package; unpackaged, "both developer-controlled and subscriber-controlled access behave the same" (Metadata API Developer Guide L41363–41377, L41321–41322) | Both switches set deliberately, and a decision recorded about whether the data is safe for every profile — including guest — to read |
| "Who is allowed to change each field after release — the publisher on upgrade, or the customer?" | `fieldManageability` is per field and one-way: a `SubscriberControlled` field "can't be updated with a package upgrade" (Metadata API Developer Guide L43406–43413) | A `fieldManageability` value in every `.field-meta.xml` instead of the default, and no field the publisher can never correct |
| "What should happen when the record simply is not there?" | All three `getInstance` overloads return null when nothing matches, and `getAll()` returns an empty map (Apex Reference Guide L204569, L204588, L204618–204620) | The named fallback record, the safe default value, and whether a missing record is logged or thrown |
| "Which of these tests are asserting the deployment, and which are asserting the logic?" | Metadata objects stay visible to tests without `SeeAllData=true`, unlike custom settings data (Apex Developer Guide L40707–40709, L13515–13516) — so a test can pass on org state nobody declared | One named test that asserts the org contract, and every other test injecting rows through a `@TestVisible` seam |
| "Will this type ever carry a namespace?" | `Metadata.CustomMetadata.fullName` drops the `__mdt` suffix, and in a namespace both halves must be qualified — `myPackage__MDType1__mdt.myPackage__Component1` (Apex Developer Guide L28199–28203, Apex Reference Guide L170852–170855) | A `fullName` built from a constant plus a namespace prefix, instead of one that works unpackaged and fails after packaging |

What a proper configuration adds over just doing it: the reads that could truncate are SOQL and the rest use the cache, a missing record degrades to a named fallback instead of an NPE, tests state which rows they depend on instead of borrowing the org's, the deployment path branches on `SucceededPartial` rather than reporting a half-applied change as done, and each field's post-release ownership is written into its metadata rather than discovered at the first upgrade.

---

## Core Concepts

### Custom Metadata Is App Configuration

Custom Metadata Types are for durable application configuration. In Apex, that usually means querying `__mdt` records or using generated accessors such as `getInstance()` and `getAll()` where that makes the intent clearer. Treat those records as part of the app contract instead of as business data.

### Three Read Paths, Chosen On Purpose

| Read | Use when | Cost |
|---|---|---|
| `<Type>__mdt.getAll()` | you want the whole small table as a `Map<String, sObject>` keyed by DeveloperName | reads the application cache; every field truncated at 255 characters |
| `<Type>__mdt.getInstance(name)` | you want one record by DeveloperName, record Id, or qualified API name | same cache, same truncation; returns `null` on no match |
| `[SELECT … FROM <Type>__mdt WHERE … ORDER BY …]` | you need filtering, ordering, or a field longer than 255 characters | full field values; no SOQL-query-limit cost at all (Apex Developer Guide L19616–19619) |

"SOQL costs a governor limit" is the wrong reason to prefer the accessors here — it does not. Truncation is the real difference.

### Read Paths And Write Paths Differ

Reading custom metadata in Apex is straightforward. Updating records is different. Do not design business logic around ordinary DML on `__mdt`. Metadata deployment is the real write boundary, and packaging visibility or subscriber-control rules determine what can actually be changed. The write path is a container of `Metadata.CustomMetadata` components handed to `Metadata.Operations.enqueueDeployment()` with a `Metadata.DeployCallback`, and it can create and update but never delete.

### Tests See Metadata Differently Than Data

Apex tests can see custom metadata records without `SeeAllData=true`. That is useful, but it also means tests can quietly rely on org metadata unless the dependency is explicit and deliberate. The way out is not `SeeAllData=true`; it is a `@TestVisible` static the test assigns in-memory `__mdt` sObjects to, with no DML anywhere.

### CMT, Settings, And Labels Solve Different Problems

Use Custom Metadata Types for deployable, versioned configuration. Use Custom Labels for translatable user-facing text. Use Custom Settings only when the org still depends on older hierarchy or runtime semantics that are a better fit than CMT.

---

## Common Patterns

### Configuration Reader Wrapper

**When to use:** Business logic needs stable access to config and should not scatter raw `__mdt` queries everywhere.

**How it works:** Create a small service that loads the relevant record, applies defaults, and exposes intent-level methods such as `isFeatureEnabled()` or `getEndpointKey()`. One `@TestVisible private static Map` holds the loaded rows, and that map is the only injection seam. Worked end to end in `references/code-examples.md` § 3–4; `templates/apex/TriggerControl.cls` is the shipped example of the same shape.

**Why not the alternative:** Direct `__mdt` queries in many classes duplicate field knowledge and test assumptions.

### Strategy Table In Metadata

**When to use:** Routing, thresholds, or feature rules differ by region, channel, product, or environment.

**How it works:** Store rule dimensions and outputs in custom metadata, then have Apex resolve the best matching record and execute behavior from that result. When the row names an Apex class to instantiate rather than a value to use, that is the factory variant — `apex/apex-design-patterns` owns it, including the `Type.forName` resolution and the dangling-class-name fallback.

### Metadata Deployment Boundary

**When to use:** Admin tooling or packaged setup must create or update metadata records.

**How it works:** Keep deployment-oriented logic separate from transaction-level business services. One class builds and validates the `Metadata.DeployContainer`; one class implements `Metadata.DeployCallback` and owns the outcome; nothing else in the codebase enqueues. Runtime services stay read-oriented and never pretend that `insert` and `update` on `__mdt` are ordinary persistence.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Versioned config that should move through metadata deployment | Custom Metadata Type | Best fit for deployable app configuration |
| User-facing translatable text only | Custom Labels | Better than forcing text into metadata rows |
| Legacy per-user or hierarchy semantics | Evaluate hierarchy/custom settings carefully | CMT is not always a drop-in replacement |
| Runtime transaction wants to create config as row data | Redesign around metadata deployment or normal objects | `__mdt` is not standard business-data storage |
| A configuration value can exceed 255 characters | Read it with SOQL, or split it across rows | `getAll()` / `getInstance()` truncate silently |
| Config rows must be created and deleted routinely | Custom object or List Custom Setting | The Apex write path cannot delete custom metadata at all |
| Config must hold an API key or token | Named Credential or encrypted field | Outside a managed package, `protected` records are readable by every profile including guest |

---

## Recommended Workflow

1. **Classify the requirement as read-only or read-write.** Answer the first two rows of *Questions to Ask*. A read-only requirement needs the type, the records, a selector, and a test class — and none of `RetryPolicyDeployer` / `RetryPolicyDeployCallback` from `references/code-examples.md` §§ 5–7. Adding the write path when nobody asked for it buys an async job, a callback, and a partial-success branch for nothing.
2. **Design the type against the field-length and manageability questions.** Shape `objects/<Type>__mdt/` and its `fields/*.field-meta.xml` on `references/code-examples.md` § 1 and the shipped `templates/apex/cmdt/Trigger_Setting__mdt/`. Every field gets an explicit `fieldManageability`; the lookup field gets `unique` + `externalId`; no field is allowed to grow past 255 characters unless its read path is already SOQL.
3. **Ship at least one record, including the fallback.** Write the `.md-meta.xml` files as in § 2, with `<value xsi:nil="true"/>` where a field must be cleared rather than left alone. A type with no rows is not configurable, it is broken.
4. **Write the selector with exactly one `@TestVisible` seam.** Follow § 3: `getAll()` memoised into a static `Map`, a named fallback record, and a separate uncached `getInstance()` path for anything that must read the org's real value.
5. **Write the tests before deploying.** § 4 for the read side — inject in-memory rows, never `insert`, never `SeeAllData=true`, and name the one test that deliberately asserts the org contract. § 7 for the write side — assert `DeployContainer.getMetadata()`, call the callback directly with a hand-built `Metadata.DeployResult`, and cover `SucceededPartial` as well as `Succeeded`.
6. **Run the checker over the source tree, then deploy in order.** `python3 skills/apex/custom-metadata-in-apex/scripts/check_custom_metadata_in_apex.py --manifest-dir force-app/main/default`, then type + fields, then records, then Apex — the commands are in § 10.
7. **Verify with the SOQL in § 10, not with the deploy result.** Confirm the fallback record exists and is active, the unique lookup field has no duplicates, and every value is in range. After a runtime deployment, remember the write is asynchronous: an unchanged value means the job has not finished, not that it failed.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Configuration stored in `__mdt` is truly setup, not transactional data.
- [ ] Apex reads are centralized behind a small config boundary where possible.
- [ ] Tests do not rely on accidental org metadata without stating it.
- [ ] No runtime design assumes ordinary DML on custom metadata.
- [ ] Packaging visibility and subscriber edit rules are understood.
- [ ] The choice between CMT, labels, settings, and ordinary data is deliberate.
- [ ] No field read through `getAll()` / `getInstance()` can exceed 255 characters.
- [ ] A fallback record is deployed and a test asserts it exists.
- [ ] `fieldManageability` is explicit on every field, not defaulted.
- [ ] Any `DeployCallback` branches on `SucceededPartial`, not only `Succeeded`.
- [ ] `enqueueDeployment` is unreachable from a trigger, a loop, or a running test.
- [ ] The checker script reports no findings against the source tree.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems. Full versions, with the guide line ranges, in `references/gotchas.md`.

1. **`getAll()` and `getInstance()` truncate every field at 255 characters** - silently, so the failure surfaces as a bad comparison somewhere else.
2. **SOQL against `__mdt` has no query-limit cost** - which means "save a query" is not a reason to prefer the cache accessors.
3. **Tests can see custom metadata without `SeeAllData=true`** - helpful, but easy to misuse if the dependency is never named.
4. **Write paths are metadata deployments, not normal DML** - code that treats `__mdt` like `__c` data eventually breaks, and the deploy path cannot delete at all.
5. **`SucceededPartial` is a real status** - a callback that tests only for `Succeeded` reports a half-applied change as a failure, or worse, as a success.
6. **An omitted field is not a cleared field** - on an update, leaving a `<values>` block out preserves the old value.
7. **Protected and subscriber-controlled behavior matters in packages** - a design that works unpackaged can fail once namespace and visibility rules apply, and unpackaged `protected` protects nothing.
8. **`fieldManageability` is chosen once** - a `SubscriberControlled` field can never again be fixed by a package upgrade.
9. **Custom Labels are not structured configuration** - once rules need keys, thresholds, or multiple rows, labels are the wrong storage model.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configuration decision | Recommendation for CMT vs labels vs settings vs ordinary data |
| Apex config review | Findings on read boundaries, test assumptions, and deployment risks |
| Metadata pattern scaffold | Reader service or metadata-deploy boundary example |
| Deployable slice | `__mdt` type + fields + records + selector + test, per `references/code-examples.md` |
| Checker report | JSON findings from `scripts/check_custom_metadata_in_apex.py` |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are building it: the `__mdt` type, its fields, its records, the selector, the DML-free test, the `Metadata.Operations` deployer, the `DeployCallback`, their tests, `package.xml`, deploy order, and the verification query |
| `references/gotchas.md` | You are reviewing, or something already behaves oddly — 12 grounded platform behaviours from 255-character truncation to `SucceededPartial` and namespace-qualified full names |
| `references/llm-anti-patterns.md` | You are checking generated Apex, or you are the agent that just generated it — six mistakes with detection hints, including two claims LLMs repeat that the guides do not support |
| `references/examples.md` | You want the short worked scenarios: a feature-flag reader, a routing strategy table, and the `.md-meta.xml` rows behind it |
| `references/well-architected.md` | You are justifying the design, or you need the source behind a specific claim — the pillar framing, the trade-offs, and the nine sources with the claim each supports |

---

## Related Skills

- `admin/custom-metadata-types` - use when the question is how to model and protect the type itself in Setup rather than how Apex reads it.
- `admin/custom-metadata-types-and-settings` - use for the CMT vs Custom Settings decision before any code exists.
- `apex/apex-custom-settings-hierarchy` - use when the requirement really is per-user or per-profile resolution, which custom metadata does not do.
- `apex/apex-metadata-api` - use when Apex must deploy metadata other than custom metadata records, such as custom fields or picklist values.
- `apex/apex-design-patterns` - use when the `__mdt` row names an Apex class and the real subject is the strategy/factory seam.
- `apex/apex-mocking-and-stubs` - use when the dependency to isolate is a callout or a selector rather than a configuration row.
- `admin/connected-apps-and-auth` - use when the real problem is integration credential governance, not where Apex stores config.
- `apex/test-class-standards` - use when metadata-dependent tests are part of a broader testing problem.
- `data/roll-up-summary-alternatives` - use when the actual gap is summary behavior over data relationships rather than configuration storage.
