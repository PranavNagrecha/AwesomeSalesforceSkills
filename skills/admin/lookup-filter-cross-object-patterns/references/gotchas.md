# Gotchas — Lookup Filter Cross Object Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Required filter does not retroactively invalidate stored data

**What happens:** You flip a filter to required. Reports of records "violating" the new rule keep running fine. Then weeks later, a user edits one and gets blocked.

**When it occurs:** Whenever existing records do not match the new filter at the time of deploy. Salesforce never re-evaluates filters against existing data — only the next save is checked.

UNVERIFIED (2026-09-04): neither the Metadata API Developer Guide nor the Object Reference states when a lookup filter is evaluated. The guide says only that `errorMessage` is "the error message that appears if the lookup filter fails" (api_meta.txt:43872), which describes a save-time event but does not rule out a retroactive sweep. Confirm in a sandbox by loading a violating record, deploying the required filter, and re-querying it before you promise this behaviour to a stakeholder.

**How to avoid:** Run the count query in `references/metadata-examples.md` §7 before flipping to required. Backfill the violators, or add an OR'd exemption item, before the change.

---

## Gotcha 2: `$Source` cannot traverse two parents

**What happens:** `$Source.Account.Owner.Region__c` is rejected at filter design time, even though the path is valid in formulas elsewhere.

**When it occurs:** Whenever your right-hand side needs a value two relationships away from the source.

UNVERIFIED (2026-09-04): the `FilterItem` table describes `valueField` only as specifying "if the final column in the filter contains a field or a field value" (api_meta.txt:43922–43924) and documents no traversal-depth limit. One hop is the safe working assumption; anything deeper has to be proved by an actual deploy, not by analogy with formula syntax.

**How to avoid:** Add a formula field on the *first* parent (e.g., `Account.Owner_Region__c`) that flattens the deep traversal, then reference `$Source.Account.Owner_Region__c`. `admin/formula-fields` covers the flattening field and its own recalculation cost.

---

## Gotcha 3: There is no bypass element, so every exemption is a filter item you wrote

**What happens:** A team plans a rollout around "admins can bypass the filter", then finds nothing in the metadata to set. The exemption never ships, and the data-migration user is blocked on every insert.

**When it occurs:** On any required filter whose rollout plan assumes an escape hatch exists.

**Why:** `LookupFilter` has exactly seven fields — `active`, `booleanFilter`, `description`, `errorMessage`, `filterItems`, `infoMessage`, `isOptional` (api_meta.txt:43864–43891). None of them is a bypass, an exempt-profile list, or a permission reference. Whatever the Setup UI offers, the deployable artefact has no such switch.

UNVERIFIED (2026-09-04): the widely-repeated claim that a bypass, where it exists in the UI, matches only the literal `System Administrator` profile and ignores permission sets carrying Modify All Data is not stated anywhere in the fetched guides. Treat it as unproven and design as if there is no bypass at all, which the metadata supports.

**How to avoid:** Express the exemption as an extra `filterItem` OR'd in through `booleanFilter` — see `references/metadata-examples.md` §5. It costs one of your ten items, and it shows up in a code review, which a Setup checkbox does not.

---

## Gotcha 4: Field deletion silently breaks the filter

**What happens:** Someone deletes the field referenced on the right-hand side. The filter shows as "broken" only when an admin opens it in Setup; saves keep going through, but the picker now returns *no* records, so users can't fill the lookup at all.

**When it occurs:** During cleanup PRs that remove "unused" custom fields without checking lookup filter dependencies. A field referenced only from inside a `lookupFilter` block does not appear in most "where is this field used" answers, because the reference is nested inside another field's definition rather than in a formula, layout, or Apex file.

UNVERIFIED (2026-09-04): the empty-picker symptom is a field-report, not a documented behaviour — the guides do not describe what a filter does when a referenced field disappears. The dependency itself is real and checkable in source; the symptom is what you should confirm before quoting it.

**How to avoid:** Grep the DX tree for the field name inside `<lookupFilter>` blocks before any deletion, and run `scripts/check_lookup_filter_cross_object_patterns.py`. `admin/custom-field-creation` covers the wider field-deletion checklist.

---

## Gotcha 5: Field-level security is enforced before the filter

**What happens:** A profile cannot read `Account.Region__c`. The lookup filter referencing that field returns zero records for those users — the picker is silently empty.

**When it occurs:** Whenever the running user lacks read access to any field cited on either side of the filter.

UNVERIFIED (2026-09-04): the ordering of FLS against filter evaluation is not documented in the Metadata API guide or the Object Reference. What is certain is that an admin testing the filter sees a different picker than a restricted user, so the test has to be run on a real profile either way.

**How to avoid:** Make every field referenced in a lookup filter readable to every profile that needs to save the source object, and record that requirement in the field's `description` so a later FLS tightening does not silently break the picker.

---

## Gotcha 6: Compound fields are unusable, and the one exception is Metadata-API-only

**What happens:** A filter written against `BillingAddress`, `MailingAddress`, or a geolocation field will not save in Setup, and a distance filter that does work cannot be edited in the UI afterwards.

**When it occurs:** On any "same city as the account" or "within 50 km of the site" requirement.

**Why:** "You can't use compound fields in lookup filters, except to filter distances that are within or not within given ranges. You can use distance lookup filters only in the Metadata API" (object_reference.txt:2934–2935). The Object Reference repeats the point from the other side: DISTANCE formulas are supported in "Lookup filters (in the Metadata API only)" (object_reference.txt:2957–2961). This is also why `within` carries the parenthetical "(DISTANCE criteria only)" in the `FilterOperation` enum (api_meta.txt:43916).

**How to avoid:** Filter on the component field (`BillingCity`, `BillingCountry`) rather than the compound one. If the requirement really is distance, accept that the filter becomes source-only — it must be deployed from the DX tree every time, and anyone who edits that field in Setup risks dropping it.

---

## Gotcha 7: `FilterItem` is a shared type, so the enum promises more than lookup filters deliver

**What happens:** An operation that is documented in `FilterOperation` is rejected for a lookup filter, or a `valueField` that works in one component fails in another.

**When it occurs:** When the filter is copied from an approval process, a workflow rule, or a report filter, all of which use the same `FilterItem` shape.

**Why:** The `FilterItem` table carries two restrictions that belong to specific consumers, not to the type: `within` is "(DISTANCE criteria only)" (api_meta.txt:43916), and "approval processes don't support valueField entries in filter criteria" (api_meta.txt:43923–43924). The enum is the union across every component that embeds `FilterItem`, so membership in it is not proof that a lookup filter accepts it.

**How to avoid:** Treat the enum as a candidate list and prove each operation with a `--dry-run` deploy. Do not lift a `filterItems` block from an `approvalProcess` file without re-checking `valueField` — see `admin/approval-processes` for what that component supports instead.

---

## Gotcha 8: Ten filter items is a hard cap, and the tenth arrives late

**What happens:** A filter that grew one condition per sprint stops accepting new ones.

**When it occurs:** On filters that encode business rules incrementally — an exemption here, a status exclusion there — rather than being designed once.

**Why:** "You can have up to 10 FilterItems per lookup filter" (api_meta.txt:43883–43884).

**How to avoid:** Budget the ten from the start, and remember that each exemption (Gotcha 3) spends one of them. When you need an eleventh, collapse two conditions into a formula or checkbox field on the target object and filter on that single field instead. That also makes the condition reportable, which a filter item is not.

---

## Gotcha 9: The translated messages live in a different component, under a different element name

**What happens:** A French user gets a narrowed picker and an English rejection message.

**When it occurs:** In any multi-language org where the field was deployed without its object translation.

**Why:** `errorMessage` and `infoMessage` are English strings inside the `CustomField`. Their translations sit on `CustomObjectTranslation`, in a `lookupFilter` element of type `LookupFilterTranslation` whose two fields are `errorMessage` and `informationalMessage` (api_meta.txt:46011–46014, 46075–46087). Note the rename: `infoMessage` in the field, `informationalMessage` in the translation (api_meta.txt:43886, 46083). Copying the element name across is a deploy failure; forgetting the component entirely is a silent one.

**How to avoid:** Add the `CustomObjectTranslation` members to the same `package.xml` as the field — see `references/metadata-examples.md` §6 and §9. `admin/multi-language-and-translation` covers the wider translation deploy.

---

## Gotcha 10: A dependent lookup filter on a standard restricted picklist compares the stored code, not the label

**What happens:** The filter is written against the value the user sees, matches nothing, and the picker comes back empty.

**When it occurs:** When the controlling field is a standard restricted picklist whose stored values differ from their labels.

**Why:** The Object Reference documents exactly this case for Field Service: "To create a dependent lookup filter with ServiceResource.ResourceType, use only the first letter of the picklist value, for example T for Technician" (object_reference.txt:259743–259744). `ResourceType` is a restricted picklist storing single-letter codes — Technician (T), Dispatcher (D), Crew (C), Asset (S), Agent (A), Planner (P) (object_reference.txt:259736–259739).

**How to avoid:** For any standard picklist on either side of a filter, look up the stored values in the Object Reference entry for that field before writing the `value`. Custom picklists have the same split whenever the API name was edited after creation.

---

## Gotcha 11: `booleanFilter` numbers positions, so reordering the items rewrites the logic

**What happens:** A merge or a formatter reorders the `filterItems` blocks. The XML still deploys, `booleanFilter` is untouched, and the filter now enforces a different rule.

**When it occurs:** On any filter with three or more items, particularly after a conflict resolution in the field's `.field-meta.xml`.

UNVERIFIED (2026-09-04): the guide describes `booleanFilter` only as "specifies advanced filter conditions" (api_meta.txt:43868) and never states that its numbers index `filterItems` by document position. The positional reading matches every other Salesforce filter-logic surface, but it is an inference here — confirm it by retrieving a three-item filter built in Setup and checking which item each number lands on.

**How to avoid:** Never reorder `filterItems`. When you must, rewrite `booleanFilter` in the same commit, and put the intent in `description` — that field exists precisely so the logic string has a plain-English partner (api_meta.txt:43870).
