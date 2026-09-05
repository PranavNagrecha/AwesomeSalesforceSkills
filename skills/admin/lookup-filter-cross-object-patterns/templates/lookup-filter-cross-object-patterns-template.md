# Lookup Filter Design — Work Template

Fill this in before writing any XML. Every row here becomes an element of the `lookupFilter` block or
a decision you will otherwise make by accident.

**Skill:** `lookup-filter-cross-object-patterns`
**Requested by / date:**
**Request summary:**

---

## 1. The field

| Item | Value |
|---|---|
| Source object (owns the lookup) | |
| Lookup field API name | |
| DX path | `objects/________/fields/________.field-meta.xml` |
| Target object (`referenceTo`) | |
| Field type (`Lookup` / `MasterDetail`) | |
| Filter already present on this field? | yes / no — if yes, paste the current block below |

Existing block, if any (paste the retrieved `<lookupFilter>` element verbatim):

```text
```

---

## 2. The seven questions

| Ask | Answer |
|---|---|
| Shaping the picker, or enforcing a rule? | |
| How many records already hold a value this filter would reject? | (paste the SOQL count) |
| Exact relationship path from the source record to the constraining value | |
| Who must be allowed through anyway? | |
| What should the user read on rejection (`errorMessage`)? | |
| What should the user read on the page (`infoMessage`)? | |
| Is this org multi-language? Which `CustomObjectTranslation` members? | |

---

## 3. The filter items

Number them in the order they will appear in the file. `booleanFilter` indexes them by position.

| # | `field` (on the target) | `operation` | `value` **or** `valueField` | Why this item exists |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

`booleanFilter`:
`isOptional`:
`active`:

Checks before moving on:

- [ ] No item has both `value` and `valueField`
- [ ] Item count is 10 or fewer
- [ ] No compound (Address / Geolocation) field referenced, except through a distance range
- [ ] Every `booleanFilter` index matches a row above
- [ ] Stored picklist values used, not labels

---

## 4. Rollout

| Step | Owner | Date | Evidence |
|---|---|---|---|
| Deploy with `isOptional` `true` | | | deploy id |
| Run the violator count | | | count = |
| Backfill or add exemption item | | | record count fixed = |
| Re-run the violator count | | | count = |
| Flip to `isOptional` `false` | | | deploy id |
| Remove any temporary exemption item | | | deploy id |

If an exemption item was added, name it and give it an end date. An exemption with no removal date is
a permanent hole in the constraint:

| Exemption item # | Condition | Added for | Remove by |
|---|---|---|---|
| | | | |

---

## 5. Verification

- [ ] `sf project deploy start --dry-run` succeeded
- [ ] Picker narrowed correctly when opened as a **non-admin** user on profile: ____________
- [ ] `infoMessage` visible in the lookup dialog
- [ ] `errorMessage` returned on an intentionally invalid API / Data Loader write
- [ ] `python3 skills/admin/lookup-filter-cross-object-patterns/scripts/check_lookup_filter_cross_object_patterns.py --manifest-dir force-app/main/default` returned no findings
- [ ] Fields referenced by the filter added to the change-impact list for both objects

---

## 6. Notes and deviations

Record anything that differs from `references/metadata-examples.md`, and why. In particular, record
the literal `valueField` string the org actually accepted — the guide does not document that grammar,
so a working example from this org is the most reliable reference you will have.
