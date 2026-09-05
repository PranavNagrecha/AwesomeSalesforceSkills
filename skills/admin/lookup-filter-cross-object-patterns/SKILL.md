---
name: lookup-filter-cross-object-patterns
description: "Design or repair lookup filters that constrain a child lookup using fields from the parent record (or a sibling record on the same object). Triggers: 'limit lookup based on another field', 'cross-object lookup filter', 'lookup filter $Source vs $User', 'lookupFilter block in field-meta.xml', 'booleanFilter with three filterItems', 'picker still shows every record after deploy', 'lookup filter error message not translated'. NOT for choosing lookup vs master-detail - use admin/lookup-and-relationship-design. NOT for duplicate matching rule criteria - use admin/duplicate-management. NOT for the rest of the CustomField element set - use admin/custom-field-creation."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
triggers:
  - "lookup filter not narrowing the picker results"
  - "how do I limit a contact lookup to the account's contacts only"
  - "lookup filter referencing parent field stopped working after deploy"
  - "$Source field versus parent record field in lookup filter"
  - "required lookup filter blocking save on existing records"
  - "write the lookupFilter block in a field-meta.xml"
  - "combine three lookup filter conditions with booleanFilter"
  - "restrict a user lookup to the same region as the record"
  - "lookup filter deployed but the picker still shows every record"
  - "lookup filter error message shows in the wrong language"
  - "convert a NamedFilter to the lookupFilter field on CustomField"
tags:
  - lookup-filter
  - data-integrity
  - admin
  - cross-object
inputs:
  - "object and field names of the lookup, the parent (or related) object, and the constraint expression"
  - "whether the filter is required (block save) or optional (informational)"
  - "user profiles that should be exempt"
outputs:
  - "a `lookupFilter` block inside the lookup field's `.field-meta.xml`"
  - "rollout plan covering existing records that may now violate the filter"
  - "list of field-level visibility prerequisites"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Lookup Filter Cross Object Patterns

Activate when a user lookup picker shows too many records, when a filter referencing a parent field returns nothing, or when a deploy of a lookup filter blocks legitimate saves on existing data. The skill produces a deployable `lookupFilter` block, a backfill plan for legacy records that violate the new filter, and an exemption strategy.

A lookup filter is not its own metadata component. It is the `lookupFilter` element inside the lookup field's `CustomField` definition — "the metadata associated with a lookup filter is now represented by the lookupFilter field in the CustomField component" (api_meta.txt:44513–44514). The old standalone `NamedFilter` type was removed in API version 30.0 (api_meta.txt:43860–43862).

---

## Before Starting

Gather this context before working on anything in this domain:

- Which object owns the lookup, which object the lookup points to, and what field provides the constraint. The filter lives on the *source* object's field; the left side of each `filterItem` names a field on the *target*.
- Whether the filter must be **required** (`isOptional` `false`) or **optional** (`isOptional` `true`). Both are required booleans in the metadata (api_meta.txt:43865–43891), so there is no "unset" — you are always making this choice.
- Whether the org already has records whose current lookup value would fail the new filter. Count them before you deploy, not after.
- Whether any field you want to reference is a compound field (Address, Geolocation). "You can't use compound fields in lookup filters, except to filter distances that are within or not within given ranges" (object_reference.txt:2934–2935).

---

## Questions to Ask Before Configuring

Ask these before opening Setup; the answers decide the shape of the `lookupFilter` block, and an LLM that skips them writes a filter that deploys cleanly and constrains nothing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is this filter shaping the picker, or enforcing a rule?" | Sets `isOptional`. Shaping and enforcing are different products, and only one of them needs a backfill | The `isOptional` value plus a decision on whether a validation rule is also needed |
| "How many records already hold a value this filter would reject?" | Required filters have to be introduced into data that predates them | A SOQL count, and a go/no-go on deploying required on day one |
| "What is the exact relationship path from the source record to the constraining value?" | Decides whether the value is reachable at all or needs a flattening formula field first | Either a reachable field name or a new formula field on the parent |
| "Who must be allowed through when the filter would otherwise block them?" | `LookupFilter` has no bypass element — the seven fields are `active`, `booleanFilter`, `description`, `errorMessage`, `filterItems`, `infoMessage`, `isOptional` (api_meta.txt:43864–43891) — so an exemption has to be an OR'd filter item | An explicit exemption condition inside `booleanFilter`, or a documented decision that there is none |
| "What should the user read when the filter rejects their choice?" | `errorMessage` is "the error message that appears if the lookup filter fails" and `infoMessage` is "the information message displayed on the page" (api_meta.txt:43872, 43886–43888) — they are separate strings for separate moments | Two written strings instead of a silent, empty picker |
| "Does this org run in more than one language?" | Filter messages are translated through `LookupFilterTranslation` on `CustomObjectTranslation`, which carries `errorMessage` and `informationalMessage` (api_meta.txt:46075–46087) — a separate component in a separate deploy | The translation files added to the same package |
| "Is more than one condition involved, and what is the logic between them?" | `booleanFilter` "specifies advanced filter conditions" (api_meta.txt:43868) and indexes the `filterItems` positionally | The literal `booleanFilter` string, e.g. `1 AND (2 OR 3)`, agreed before the items are written |

What a proper configuration adds over just adding a filter in Setup: the picker narrows to the rows that are actually valid, the rejection message explains itself, existing violators are counted and dealt with before enforcement starts, and the whole thing is a reviewable diff in `objects/<Object>/fields/<Field>__c.field-meta.xml` rather than a click someone made once.

---

## Core Concepts

### The metadata shape

`LookupFilter` has exactly seven fields (api_meta.txt:43864–43891). There is nothing else to set.

| Element | Type | What the guide says | Line |
|---|---|---|---|
| `active` | boolean | "Required. Indicates whether the lookup filter is active (true) or not (false)." | 43865–43866 |
| `booleanFilter` | string | "Specifies advanced filter conditions." | 43868 |
| `description` | string | "A description of what this filter does." | 43870 |
| `errorMessage` | string | "The error message that appears if the lookup filter fails." | 43872 |
| `filterItems` | `FilterItem[]` | "Required. The set of filter conditions. You can have up to 10 FilterItems per lookup filter." | 43883–43884 |
| `infoMessage` | string | "The information message displayed on the page. Use to describe things the user possibly doesn't understand, such as why certain items are excluded in the lookup filter." | 43886–43888 |
| `isOptional` | boolean | "Required. Indicates whether the lookup filter is optional (true) or not (false)." | 43890–43891 |

Each `FilterItem` carries `field`, `operation`, and then **either** `value` **or** `valueField` — `valueField` "specifies if the final column in the filter contains a field or a field value" (api_meta.txt:43922–43924). Field-to-field comparison is what makes a filter cross-object; field-to-literal is a plain static filter.

`FilterOperation` is a closed enum: `equals`, `notEqual`, `lessThan`, `greaterThan`, `lessOrEqual`, `greaterOrEqual`, `contains`, `notContain`, `startsWith`, `includes`, `excludes`, `within` — and `within` is "(DISTANCE criteria only)" (api_meta.txt:43903–43916). There is no `LIKE`, no function call, and no nesting.

### `$Source` versus a target-object reference

The left-hand `field` of each item names a field on the object the lookup points **at**. The `valueField` names the value to compare it against, drawn from the record being edited.

UNVERIFIED (2026-09-04): the `$Source.` prefix (e.g. `$Source.AccountId`, and `$Source.Account.Region__c` for one hop up) is the syntax the platform emits and accepts in `valueField`, but the Metadata API Developer Guide documents only the *purpose* of `valueField`, never its grammar; the legacy `NamedFilter` type is the closest the guide comes, with a `sourceObject` field described as "the object that contains the lookup field that uses this lookup filter — set this field if the lookup filter references fields on the source object" (api_meta.txt:44580–44583). Retrieve one working filter from a sandbox and copy the literal string it produces rather than trusting a hand-written prefix.

### Enforcement semantics, and how well each claim is grounded

| Claim | Grounding |
|---|---|
| `filterItems` is capped at 10 per filter | Grounded — api_meta.txt:43883–43884 |
| `LookupFilter` has no admin-bypass element | Grounded by the complete field table — api_meta.txt:43864–43891 |
| Compound (Address / Geolocation) fields are unusable except for distance ranges, and distance filters are Metadata-API-only | Grounded — object_reference.txt:2934–2935, 2957–2961 |
| `LookupFilter` is not supported on the article type object | Grounded — api_meta.txt:43500 |
| A required filter (`isOptional` `false`) is enforced on saves that never open the picker — API, Apex, Data Loader | UNVERIFIED (2026-09-04): neither the Metadata API guide nor the Data Loader guide states where the filter is evaluated; the guide only says `errorMessage` "appears if the lookup filter fails" (api_meta.txt:43872). Test one API save before relying on it |
| Filters are not applied retroactively to stored values | UNVERIFIED (2026-09-04): no statement in the fetched guides either way. Behaviourally consistent with `errorMessage` firing on save, but confirm in a sandbox before promising it to a stakeholder |
| `valueField` cannot traverse two relationships up from the source | UNVERIFIED (2026-09-04): the guides place no documented depth limit on `valueField`. Treat one hop as the safe assumption and verify anything deeper by deploying it |

Read `references/gotchas.md` for what each of these costs when it surprises you.

---

## Common Patterns

### Pattern: child contact must belong to the case's account

**When to use:** `Case.ContactId` should only allow contacts on the same account as `Case.AccountId`.

**How it works:** One `filterItem` — `field` `Contact.AccountId`, `operation` `equals`, `valueField` pointing at the source record's `AccountId`. `isOptional` `false`. Full XML in `references/metadata-examples.md` §1.

**Why not the alternative:** A validation rule alone fires only on save; the picker still lists every contact, so users keep choosing wrong ones and losing typed work.

### Pattern: informational filter with `infoMessage`

**When to use:** The constraint is a strong preference, not a rule — e.g. show partner-managed accounts first but let a rep pick another.

**How it works:** `isOptional` `true` plus an `infoMessage` explaining what was hidden. The guide's own framing for `infoMessage` is "why certain items are excluded in the lookup filter" (api_meta.txt:43886–43888), which is exactly the optional-filter job.

### Pattern: dependent lookup driven by a field on the same record

**When to use:** `Region__c` on the record decides which `Territory__c` records are selectable.

**How it works:** One item comparing the target's region field against the source record's own `Region__c`. This is the lookup equivalent of a controlling/dependent picklist — see `admin/field-dependency-and-controlling` for the picklist form, which uses `controllingField` and does not share this mechanism.

### Pattern: three conditions with `booleanFilter`

**When to use:** Active AND (in-region OR globally-approved).

**How it works:** Three `filterItems` and `booleanFilter` `1 AND (2 OR 3)`. The numbers are positional over the `filterItems` in document order — a reordered deploy silently changes the logic.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Constraint must hold on every write path, including integrations | Required filter **and** a validation rule | The filter shapes the picker; the validation rule is the one whose enforcement surface is documented for non-UI saves |
| Filter exists to declutter the picker, not to enforce | `isOptional` `true` + `infoMessage` | Optional is the guide's own word for "the user can still choose otherwise" |
| The right-hand side needs a calculation or a two-hop path | Add a formula field, then reference it | `FilterOperation` is a closed enum with no functions (api_meta.txt:43903–43916); see `admin/formula-fields` |
| An integration user must be exempt | Extra `filterItem` OR'd in through `booleanFilter` | There is no bypass element in `LookupFilter` |
| Existing records will violate the new required filter | Deploy optional → count violators with SOQL → backfill → flip `isOptional` to `false` | The count is cheap; the support ticket three weeks later is not |
| Constraint is "hide these records from this user" | Do not use a filter — use sharing | A filter is a picker behaviour, not an access control |

---

## Recommended Workflow

1. **Locate the field, not the filter.** The filter has no file of its own. Open `objects/<Object>/fields/<Lookup>__c.field-meta.xml`; if it is not in the tree, retrieve it with the `sf project retrieve start` command in `references/metadata-examples.md`. Confirm the field's `type` is `Lookup` or `MasterDetail` and note its `referenceTo` — that object is what the left side of every `filterItem` must name.
2. **Answer the seven questions above** and write down the `booleanFilter` string before you write any `filterItems`, because the item numbering is positional.
3. **Write the `lookupFilter` block** by copying the closest shape from `references/metadata-examples.md` (§1 required cross-object, §2 optional with `infoMessage`, §3 target status/record type, §4 same-record dependent lookup, §5 three items under `booleanFilter`). Set `isOptional` `true` on the first deploy unless step 4 comes back zero.
4. **Count the violators** with the SOQL in `references/metadata-examples.md` §7 before flipping anything to required. A non-zero count is a backfill task, not a rounding error.
5. **Lint the tree:** `python3 skills/admin/lookup-filter-cross-object-patterns/scripts/check_lookup_filter_cross_object_patterns.py --manifest-dir force-app/main/default`. It fails on an active filter with no `filterItems`, an item carrying both `value` and `valueField`, and a `booleanFilter` index that points at no item; it warns on a required filter with no `errorMessage` and a `valueField` with no `$Source.` prefix.
6. **Deploy and verify as a non-admin.** Deploy with the command in `references/metadata-examples.md` §9, then open the picker as a user on a real profile and confirm both the narrowing and the `errorMessage` text. An empty picker is the failure mode that looks like success.
7. **Flip to required, and record the field dependency.** Change `isOptional` to `false`, redeploy, and add every field named in the filter to the change-impact list for the source and target objects — see `admin/custom-field-creation` for the surrounding field lifecycle.

---

## Review Checklist

- [ ] Every field named in a `filterItem` is readable by every profile that saves the source object
- [ ] `errorMessage` written for any filter with `isOptional` `false`; `infoMessage` written for any with `isOptional` `true`
- [ ] `booleanFilter` indices all resolve to an existing `filterItems` position, in document order
- [ ] No `filterItem` carries both `value` and `valueField`
- [ ] `filterItems` count is 10 or fewer (api_meta.txt:43883–43884)
- [ ] No compound (Address / Geolocation) field referenced except through a distance range (object_reference.txt:2934–2935)
- [ ] Violating records counted with SOQL and dealt with before `isOptional` became `false`
- [ ] Filter tested with a non-admin profile and with one API/Data Loader write
- [ ] Translations added to `CustomObjectTranslation` if the org runs more than one language
- [ ] Deletion of any referenced field is gated by impact analysis

---

## Salesforce-Specific Gotchas

1. **The metadata has no bypass switch** — the `LookupFilter` field list is complete at seven elements, so every exemption is an OR'd `filterItem` you wrote yourself.
2. **`booleanFilter` numbers positions, not names** — reordering `filterItems` in a diff rewrites the logic without touching the `booleanFilter` string.
3. **`within` is distance-only** — the enum accepts it everywhere, the platform accepts it only for DISTANCE criteria, and only through the Metadata API.

Deeper treatment, with the failure mode and the fix for each, in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `objects/<Object>/fields/<Lookup>__c.field-meta.xml` | The lookup field carrying its `lookupFilter` block |
| `package.xml` | `CustomField` (and `CustomObjectTranslation`, if translated) entries for the deploy |
| Violator count | The SOQL and its result, run before `isOptional` was set to `false` |
| Exemption log | Which `filterItem` exists only to let someone through, and why |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing a `lookupFilter` block, the `package.xml`, the retrieve/deploy commands, the violator SOQL, or the Apex describe check |
| `references/gotchas.md` | The picker is empty, the filter deployed but does nothing, a deploy failed on the filter, or the message came out in the wrong language |
| `references/examples.md` | Sizing a requirement: which constraints a filter can express and which one is the signal to reach for a validation rule instead |
| `references/llm-anti-patterns.md` | Reviewing AI-generated filter guidance before you act on it |
| `references/well-architected.md` | Justifying required-vs-optional against the pillars, or chasing the official source behind a claim here |
| `templates/lookup-filter-cross-object-patterns-template.md` | Capturing the decisions before any XML is written |
| `scripts/check_lookup_filter_cross_object_patterns.py` | Linting `objects/*/fields/*.field-meta.xml` in a DX tree before deploying |

---

## Related Skills

- admin/custom-field-creation — the rest of the `CustomField` element set the `lookupFilter` block sits inside
- admin/lookup-and-relationship-design — choosing lookup vs master-detail, before there is anything to filter
- admin/field-dependency-and-controlling — the picklist form of "this field narrows that field", which uses a different mechanism
- admin/validation-rules — the fallback when the constraint cannot be written as field / operator / field
- admin/formula-fields — how to flatten a deep path into a single field the filter can reference
- admin/multi-language-and-translation — `LookupFilterTranslation` for `errorMessage` and `informationalMessage`
- admin/duplicate-management — matching-rule criteria, which look similar and are a different component
- data/data-loader-and-tools — the write path a required filter is most likely to surprise
- data/soql-query-optimization — when the violator-count query on a large object needs an index
