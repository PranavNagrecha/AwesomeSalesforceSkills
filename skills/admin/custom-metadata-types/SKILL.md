---
name: custom-metadata-types
description: "Use when designing deployable Salesforce configuration with Custom Metadata Types, especially when choosing between CMTs, Custom Settings, and Custom Objects, protecting packaged defaults, or exposing config to Apex, Flow, and formulas. Triggers: 'custom metadata vs custom settings', 'deployable config', 'protected custom metadata', 'feature flags in Salesforce'. NOT for hierarchical Custom Settings resolution, getInstance/getValues, or their SOQL cost — use admin/custom-metadata-types-and-settings. NOT for high-churn transactional or user-managed business records — use admin/object-creation-and-design. NOT for secrets — use integration/named-credentials-setup. More trigger keywords: __mdt, CustomMetadata .md file, customMetadata folder, getInstance, getAll, xsi:type, visibility PackageProtected, MetadataRelationship, EntityDefinition field, $CustomMetadata."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
tags:
  - custom-metadata-types
  - configuration
  - custom-settings
  - feature-flags
  - deployable-config
triggers:
  - "should this be custom metadata or custom settings"
  - "need deployable configuration across orgs"
  - "how do protected custom metadata records work"
  - "can flow or apex read custom metadata"
  - "feature flags in salesforce without hardcoding"
  - "custom metadata types isn't working"
  - "write the xml for a custom metadata type and its records"
  - "deploy custom metadata records failed field does not exist"
  - "custom metadata value is cut off at 255 characters"
  - "soql on __mdt returns no rows for a non-admin user"
  - "how do I clear a field on a custom metadata record"
  - "what goes in package.xml for a custom metadata type"
  - "getinstance returns null for my custom metadata record"
inputs:
  - "who owns the configuration values and how often they change"
  - "whether the values must move through source control, packaging, or CI/CD"
  - "whether the data needs per-user overrides, secrets, reporting, or end-user editing"
outputs:
  - "storage decision between custom metadata, custom settings, custom objects, and named credentials"
  - "configuration design for Apex, Flow, and formula consumption"
  - "review findings for unsafe or non-deployable configuration patterns"
  - "deployable type, field, and record XML plus the package.xml that carries them"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

Use this skill when the org needs configuration that behaves like software, not like business data. Custom Metadata Types are the right answer when values should be versioned, deployed, packaged, and read consistently by Apex, Flow, and formulas without hardcoding environment-specific behavior.

---

## Before Starting

Gather this context before you decide on the storage model:

- Who changes the values, and how often do they change in production?
- Do the records need to travel through source control, packaging, or deployment pipelines?
- Are the values regular configuration, per-user overrides, reportable business data, or secrets such as tokens and passwords?

---

## Questions to Ask Before Configuring

Ask these before creating the type. Each one decides an element you will have to write into the XML, and an LLM that skips them produces a type that deploys and then behaves wrongly in the target org.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Will this type ever ship in a managed package?" | `visibility` is `Public` by default and `Protected` / `PackageProtected` only mean anything inside a managed package | The `visibility` value, chosen deliberately rather than defaulted |
| "Which records, if any, must the subscriber be unable to read or change?" | Record-level `protected` is a one-way door: a protected record's developer name cannot change after release and the subscriber cannot create records of a protected type | The per-record `protected` flag and a note of what is now frozen |
| "Which fields will the subscriber be allowed to edit after install?" | `fieldManageability` (`Locked` / `DeveloperControlled` / `SubscriberControlled`) is set per field and is valid only on custom metadata type fields | A field-by-field manageability decision instead of a silent default |
| "Can any field value exceed 255 characters?" | `getAll()` and `getInstance()` truncate every field at 255 characters; only SOQL returns the whole value | The Apex access pattern, and a decision to move long values elsewhere |
| "Who reads these records at runtime — Apex, Flow, formulas, or an external system?" | A reader on the Enterprise WSDL or SOAP API is cut off by `enableAdvancedCMTSecurity`, and every non-admin reader needs the type enabled in a permission set | The consumer list and the `customMetadataTypeAccesses` entries to ship with it |
| "Does a field need to point at an object or a field on that object?" | That is a `MetadataRelationship` field to `EntityDefinition` or `FieldDefinition`, not a Text field holding an API name | The relationship field definition and its `metadataRelationshipControllingField` where required |
| "Who deploys this, and do they hold both permissions?" | Creating the type needs "Author Apex"; creating records needs "Customize Application" | A deployment identity that can land the whole package, not half of it |

What a proper configuration adds over just creating the type in Setup: the records deploy as metadata alongside the code that reads them, the visibility and manageability choices are deliberate rather than defaulted, and every runtime consumer — Apex, Flow, formula, and non-admin user — has been proven to read the values before release.

---

## Core Concepts

Custom Metadata Types are metadata records, not transactional rows. That distinction matters because metadata belongs in source control, deployments, and packaging workflows. If the requirement is "same logic, different environment-safe configuration," CMT is usually the best fit. If the requirement is "users update this every day and report on it," it is usually the wrong fit.

### Deployable Configuration, Not User Data

Use CMT when the value should move between sandboxes, scratch orgs, packaging orgs, and production in a controlled way. This is why routing rules, thresholds, feature toggles, and endpoint path fragments fit well. A Custom Object is better when admins or business users need to add and edit records frequently through the UI and treat the records like business data.

### CMT, Custom Settings, And Custom Objects Solve Different Problems

Hierarchy Custom Settings still matter when behavior varies by user or profile and the override must be cheap to change in production. Custom Objects fit reportable, user-managed records. CMT fits org-level or package-level configuration that should be promoted like code. The wrong decision usually comes from optimizing for today's convenience instead of the future deployment model.

### Protection And Visibility Are Packaging Concerns

Protected custom metadata is useful when a managed package needs internal defaults that subscriber admins should not read or edit. It is not a general-purpose data security boundary for the same org. If the real need is secret management, use Named Credentials or another supported secret store, not public CMT records with masked labels.

### The Type Is An Object; The Records Are Separate Components

Three components, three package.xml entries, and one naming asymmetry that causes most first-deploy failures.

| Component | package.xml `<name>` | Member syntax | File |
|---|---|---|---|
| The type | `CustomObject` | `Routing_Rule__mdt` | `objects/Routing_Rule__mdt/Routing_Rule__mdt.object-meta.xml` |
| A field | `CustomField` | `Routing_Rule__mdt.Threshold__c` | `objects/Routing_Rule__mdt/fields/Threshold__c.field-meta.xml` |
| A record | `CustomMetadata` | `Routing_Rule.EMEA_High` | `customMetadata/Routing_Rule.EMEA_High.md-meta.xml` |

The type carries the `__mdt` suffix; the record name drops it. Type-level settings live on the `CustomObject` (`label`, `pluralLabel`, `description`, `visibility`); record-level settings live on the `CustomMetadata` (`label`, `description`, `protected`, and one `<values>` block per populated field). Field values are typed with an `xsi:type` attribute that must match the field definition. Full deployable XML is in `references/metadata-examples.md`.

### Runtime Access Is Easy; Runtime Mutation Is Not

Apex, Flow, and formulas can read CMT records cleanly, but normal business-transaction DML is not the operating model. That is by design. CMT is meant to stabilize configuration, not to become a hidden editable database.

---

## Common Patterns

### Metadata-Driven Routing Or Threshold Rules

**When to use:** A Flow or Apex service needs environment-safe rules such as queue routing, score thresholds, or feature switches.

**How it works:** Model the rules in a CMT, query them by stable keys such as `DeveloperName`, and keep the business logic reading configuration instead of embedding IDs and values in code.

**Why not the alternative:** Hardcoded IDs, labels, or endpoints create deployment drift and sandbox-specific breakage.

### Packaged Defaults Plus Subscriber-Safe Extensions

**When to use:** A managed package needs safe defaults but also wants limited subscriber configuration.

**How it works:** Keep vendor-owned defaults protected where appropriate, expose only the fields and records that should be subscriber-editable, and separate secrets into Named Credentials.

**Why not the alternative:** Public metadata for internal defaults leaks implementation details and invites unsupported edits.

### Deliberate Migration Off Custom Settings

**When to use:** Existing org logic reads List or Hierarchy Custom Settings even though the values should really be source-controlled and deployed.

**How it works:** Inventory the settings, separate true per-user overrides from deployable org config, move the stable org config into CMT, and update Apex/Flow lookups to use metadata keys instead of record IDs.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org-wide rules must deploy through Git and CI/CD | Custom Metadata Type | Configuration behaves like metadata and should be promoted with releases |
| Behavior varies by user or profile | Hierarchy Custom Setting | Per-user and per-profile overrides are the primary requirement |
| Admins need frequent UI editing and reporting on the records | Custom Object | The records are business data, not release-managed configuration |
| The value is a password, token, or client secret | Named Credential or supported secret store | CMT is not the right secret boundary |
| Packaged logic needs internal defaults in a managed package | Protected Custom Metadata where appropriate | Keeps package-owned config private while remaining deployable |

---


## Recommended Workflow

1. **Confirm CMT is the right store** — run the Decision Guidance table above against the answers to `## Questions to Ask Before Configuring`. If the answer is a per-user or per-profile override, stop here and use `admin/custom-metadata-types-and-settings`; if it is a secret in an unpackaged org, use `integration/named-credentials-setup`.
2. **Fill in the design worksheet** — `templates/custom-metadata-types-template.md` captures the type API name, the key strategy, `visibility`, per-field `fieldManageability`, and the runtime access plan for Apex, Flow, and formulas.
3. **Write the type and its fields** — copy the shapes from `references/metadata-examples.md`: the `CustomObject` with `label`, `pluralLabel`, `visibility`, then one `field-meta.xml` per field. Choose a `MetadataRelationship` field over a Text field holding an API name wherever the value points at an object or a field.
4. **Write the records** — one `.md-meta.xml` per record in `customMetadata/`, each `<values>` block carrying the correct `xsi:type`, and `<value xsi:nil="true"/>` wherever you mean null rather than "leave unchanged".
5. **Run the checker** — `python3 skills/admin/custom-metadata-types/scripts/check_custom_metadata_types.py --manifest-dir force-app/main/default`. It flags records referencing fields that do not exist on the type, empty labels, secret-shaped field names on public types, environment-specific hosts in record values, and DML against `__mdt` in Apex.
6. **Deploy type, fields, and records in one manifest, then verify** — `sf project deploy validate` first; then confirm with the SOQL and the `getInstance` assertion at the end of `references/metadata-examples.md`, and re-run the query as a non-admin user to prove the permission-set custom metadata type access shipped with it.
7. **Read `references/gotchas.md` before release** — the 255-character truncation, the omitted-`<values>` behaviour, and the three separate protection switches all change what you ship, not just how you test it.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The requirement is truly configuration, not business data with reporting and CRUD needs.
- [ ] The chosen storage model matches the deployment and ownership model, not just developer convenience.
- [ ] Stable keys such as `DeveloperName` are part of the lookup contract.
- [ ] No secrets, passwords, or tokens are being stored in public CMT records.
- [ ] Apex, Flow, and formulas read metadata intentionally and do not depend on environment-specific IDs.
- [ ] Any packaging visibility choice is documented, especially for protected defaults.
- [ ] `visibility` on the type and `protected` on each record were chosen deliberately, not left at the default.
- [ ] Every `<values>` block has an `xsi:type` matching its field, and every field meant to be null uses `xsi:nil`.
- [ ] Any field that can exceed 255 characters is read with SOQL, not `getAll()` / `getInstance()`.
- [ ] The permission set or profile that non-admin readers hold enables this custom metadata type.
- [ ] The type, its fields, and its records deploy from one manifest, and the deploy was validated before the real run.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CMT records are metadata, not runtime DML targets** - teams design them like editable rows and then discover the write path does not fit normal transaction logic.
2. **Protected metadata is a package boundary, not an org security model** - it helps managed-package encapsulation but does not replace proper secret handling or field security strategy.
3. **`DeveloperName` becomes part of the contract** - once code, Flow, or formulas key off metadata names, renaming records casually creates breakage.
4. **A deployable model is slower to change by design** - if operations needs hourly production edits by non-release users, the wrong storage type may have been chosen.
5. **The cached accessors truncate at 255 characters** - `getAll()` and `getInstance()` cut every field; only SOQL returns the full value, and SOQL against `__mdt` is unlimited per transaction.
6. **Leaving a `<values>` block out does not clear the field** - it stays at its previous value on an update and lands as null on a first deploy; `xsi:nil` is the only explicit clear.
7. **`visibility` and `protected` are two switches, not one** - plus `PackageProtected`, which the Metadata API guide names as the value for securing API keys and tokens inside a managed package.
8. **A `__mdt` object can be unreadable without any sharing rule** - `PermissionSetCustomMetadataTypeAccess` gates record readability per type from API 47.0, and `enableAdvancedCMTSecurity` hides values from the SOAP API org-wide.

Deeper treatment, with the source for each, in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configuration storage decision | Recommendation for CMT vs Custom Setting vs Custom Object vs Named Credential |
| Metadata model | Suggested type, fields, keys, and visibility model for the configuration |
| Refactor findings | Concrete issues such as hardcoded IDs, public secrets, or wrong storage fit |
| Deployable metadata | `objects/<Type>__mdt/` with its `fields/`, `customMetadata/<Type>.<Record>.md-meta.xml`, and the package.xml carrying all three |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing the deployable XML for the type, its fields, its records, and the package.xml |
| `references/gotchas.md` | Ten platform behaviours that change what you ship — truncation, `xsi:nil`, the protection switches, permission-set access |
| `references/examples.md` | Working through a routing-rules or packaged-defaults scenario end to end |
| `references/well-architected.md` | Justifying the storage choice against Operational Excellence, Reliability, and Security, or citing the official sources |
| `references/llm-anti-patterns.md` | Self-checking generated output for DML on `__mdt`, wrong storage choice, or missing no-code access paths |

---

## Related Skills

- admin/custom-metadata-types-and-settings - the Custom Settings side of the comparison: hierarchical resolution, `getValues`/`getInstance`, and their governor-limit cost.
- apex/custom-metadata-in-apex - use when the storage decision is made and the main question is Apex access and caching patterns.
- apex/apex-dml-patterns - why standard DML never applies to `__mdt` and what the `Metadata.DeployContainer` path costs instead.
- admin/change-management-and-deployment - use when the release process and environment promotion model are the harder problem.
- devops/unlocked-package-development - packaging the type and its records, where `visibility` and record `protected` start to matter.
- admin/assignment-rules - a common consumer: routing configuration modelled as CMT records instead of hardcoded queue Ids.
- admin/object-creation-and-design - when the records turn out to be business data that users edit and report on.
- integration/named-credentials-setup - where endpoint hosts and credentials belong instead of CMT fields.
- admin/process-automation-selection - use when Flow or Apex design is the main decision and CMT is only one part of the solution.
