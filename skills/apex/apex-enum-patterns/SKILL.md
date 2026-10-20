---
name: apex-enum-patterns
description: "Apex enum patterns — enum-based dispatch instead of string switching, ordinal stability, enum values in Custom Metadata, package-global enums, and the limitations (no methods on enum constants, no associated data). Covers `Enum.values()`, `valueOf(String)` failures, and the right way to map an enum to/from a picklist value. NOT for picklist-field design and value-set management — use admin/picklist-and-value-sets. NOT for reading picklist values at runtime via describe — use apex/apex-schema-describe."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "apex enum dispatch instead of string switch"
  - "enum valueOf throws system exception"
  - "apex enum custom metadata mapping"
  - "global enum managed package compatibility"
  - "apex enum ordinal stable identifier"
  - "switch on apex enum exhaustive"
tags:
  - enum
  - dispatch
  - custom-metadata
  - managed-package
  - type-safety
inputs:
  - "What the enum is modeling: state machine, dispatch type, picklist mirror, message subtype"
  - "Whether the enum is in a managed package (global vs public)"
  - "Whether the enum is persisted (string serialization to a field)"
outputs:
  - "Enum declaration with documented intent"
  - "Switch / dispatch pattern that handles all values"
  - "Safe conversion to/from string with default branch"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Apex Enum Patterns

Apex enums are simpler than Java enums — "the enum type itself has no constructor syntax" and "you cannot add user-defined methods to enum values"
(apex dev guide 264 L1753, L1825) — but they still beat
unstructured strings for state-machine dispatch, message routing,
and any "one of N exhaustive options" code path.

The mistakes follow a predictable pattern: people serialize enum
values into Custom Metadata or a Long Text field, the picklist
gets renamed, and `Enum.valueOf(String)` starts throwing in production:
"an exception is thrown if the input string doesn't match an enum value"
(apexref 262 L214381-214382). UNVERIFIED (2026-10-20): that the type is
`System.NoSuchElementException` — the guide does not name it. Or someone
adds a new enum value and the `switch on` doesn't have a branch: with no
matching `when` and no `when else`, "no action is taken" (apex dev guide
264 L2865). The earlier "falls through silently" wording is CONTRADICTED —
Apex has no fall-through (L2867, L2936); the miss is a silent no-op, and
`when else` is recommended but not required (L2890-2893).

This skill covers the patterns that make enums useful in Apex
without the foot-gun.

## Recommended Workflow

1. **Decide if an enum is the right shape.** If you have <2 values
   or values change at runtime, use a Boolean or a Custom
   Metadata-driven string. Enums are for closed sets.
2. **Name the enum after intent, not type.** `RenewalAction`
   beats `EnumType1`.
3. **Use `switch on <Enum>` with a `when else` branch** that throws
   a clear exception. This is the only way to surface a missed
   case at runtime when the enum gains a new value.
4. **Wrap `Enum.valueOf(String)` in a safe converter** that returns
   a default or throws a typed exception with the offending input
   in the message.
5. **Document `global` vs `public` in managed packages.** Once
   shipped, you "can't remove or reorder global enum values, although you
   can add new enum values" (apex dev guide 264 L43920); you also can't
   rename the enum itself (L43903).
6. **Write a test that asserts the enum's `values()` matches the
   expected set.** `values()` returns the Enum's values as a list
   (apexref 262 L214378-214379); this is the cheapest exhaustiveness check
   Apex gives you.

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Where does the string that becomes the enum come from?" | `valueOf` throws on a non-matching string (gotcha 1) | A safe converter with a default or a typed exception |
| "What happens when a new value is added?" | A `switch` with no `when else` does nothing for it (gotcha 2) | A `when else` that throws, plus a `values()` test |
| "Is anything persisting `ordinal()`?" | Ordinals are positions and shift on reorder (gotcha 3) | `name()` persisted instead |
| "Does the design need data or behaviour per value?" | Enum values carry no user-defined methods (gotcha 4) | A parallel `Map<Enum, ...>` or a wrapper class |
| "Is the enum `global` in a managed package?" | Global enum values can't be removed or reordered (gotcha 5) | An append-only value list and a release note |
| "Is the enum serialized to JSON or sent to a client?" | Serialization and case behaviour are not documented (gotcha 6) | A string field converted at the boundary |
| "Is the enum nested, and does it mirror a picklist?" | Nesting rules and picklist mapping are unverified (gotchas 8-9) | A top-level enum and an explicit API-name map |

A proper configuration adds a closed set owned by the code, a safe conversion at each boundary and a `values()` test, where "just doing it" gives a silent no-op the first time someone adds a value.

---

## When To Reach For An Enum

The right places: trigger-handler dispatch keys, message-routing
discriminators, log-level enums, status machines that the app
itself owns end-to-end. Anywhere the set of values is a property
of the code, not the data, an enum is the cheaper, safer choice.

The wrong places: anything an admin should be able to add to. If
adding a new "approval reason" should not require a deployment,
do not put it in an enum. The enum becomes a maintenance ratchet
that pulls every dispatcher into the release pipeline.

## What This Skill Does Not Cover

- **Picklist-field design** — see `admin/picklist-and-value-sets`.
- **Custom Metadata as configuration store** — see `admin/custom-metadata-types` and `apex/custom-metadata-in-apex`.
- **State machines with side effects** — no dedicated skill exists in the library as of 2026-10-20; the earlier pointer to `architect/state-machine-patterns` did not resolve.
