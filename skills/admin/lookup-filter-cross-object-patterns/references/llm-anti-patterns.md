# LLM Anti-Patterns — Lookup Filter Cross Object Patterns

Common mistakes AI coding assistants make when generating or advising on lookup filters.

## Anti-Pattern 1: Inventing function calls in the filter expression

**What the LLM generates:** `TRIM(Contact.Name) equals $Source.Display_Name__c` or `IF(... , ... , ...)` inside the filter.

**Why it happens:** The LLM transfers formula-field syntax onto lookup filters because both look like declarative expressions in the UI.

**Correct pattern:**

```text
Contact.AccountId  equals  $Source.AccountId
```

The grammar is strictly `field operator field-or-value`. To use a transformed value, build a formula field on the relevant object first, then reference that field in the filter.

**Detection hint:** Any open paren in the filter expression — `(`, `TRIM(`, `IF(`, `TEXT(` — is wrong.

---

## Anti-Pattern 2: Two-hop traversal on `$Source`

**What the LLM generates:** `User.Region__c equals $Source.Account.Owner.Region__c`

**Why it happens:** The LLM extrapolates from cross-object formula syntax where multi-hop traversal is fine.

**Correct pattern:** Add `Account.Owner_Region__c` (a formula on Account that resolves `Owner.Region__c`), then `User.Region__c equals $Source.Account.Owner_Region__c`.

**Detection hint:** Count segments after `$Source.` — more than two (e.g., `$Source.A.B.C`) should stop the review.

UNVERIFIED (2026-09-04): the Metadata API Developer Guide documents `valueField` only as specifying "if the final column in the filter contains a field or a field value" (api_meta.txt:43922–43924) and states no depth limit. One hop is the safe assumption to review against; a deeper path is a thing to prove with a `--dry-run` deploy, not a thing to assert.

---

## Anti-Pattern 3: Using the filter as a security boundary

**What the LLM generates:** "We can prevent users from selecting confidential accounts by filtering the Account lookup on `IsConfidential__c = false`."

**Why it happens:** The LLM treats UI affordances as security.

**Correct pattern:** Lookup filters are UX guidance, not access control. Confidential records should be hidden via OWD + sharing rules + field-level security. A user with the record ID can still paste it via API.

**Detection hint:** Any time the LLM frames a lookup filter as "preventing access," "blocking visibility," or "hiding records from unauthorized users."

---

## Anti-Pattern 4: Suggesting "Modify All Data" as the bypass

**What the LLM generates:** "Grant the integration user the 'Modify All Data' permission and the lookup filter will be skipped."

**Why it happens:** The LLM conflates the admin-bypass setting (profile-scoped) with broad permissions.

**Correct pattern:** There is no bypass to grant. `LookupFilter` has exactly seven fields — `active`, `booleanFilter`, `description`, `errorMessage`, `filterItems`, `infoMessage`, `isOptional` (api_meta.txt:43864–43891) — and none of them exempts anyone. The exemption has to be an extra `filterItem` OR'd in through `booleanFilter`, which costs one of the ten items and shows up in the diff.

**Detection hint:** Any mention of "Modify All Data," "View All Data," a permission set, or a profile name as the filter-bypass mechanism, and any recommendation that names an element not in the seven above.

---

## Anti-Pattern 5: Skipping the optional-first staging step

**What the LLM generates:** A required filter deployed straight to production with no migration plan.

**Why it happens:** The LLM treats the request as "implement this constraint" instead of "introduce this constraint to a system with existing data."

**Correct pattern:** Stage as optional → measure violators with a report → backfill or grant temporary bypass → flip to required.

**Detection hint:** Any "deploy this filter as required" recommendation without an explicit step that counts existing-record violations first.

---

## Anti-Pattern 6: Inventing a standalone file for the filter

**What the LLM generates:** A path like `lookupFilters/Case_Contact.lookupFilter-meta.xml`, or a revived `<NamedFilter>` component, or a `package.xml` entry with `<name>LookupFilter</name>`.

**Why it happens:** Most Salesforce configuration the LLM has seen is its own component with its own file, so it generalises. `NamedFilter` also *was* a standalone type until API version 30.0, so the pattern exists in older material.

**Correct pattern:** The filter is the `lookupFilter` element inside the lookup field's `CustomField` — "the metadata associated with a lookup filter is now represented by the lookupFilter field in the CustomField component" (api_meta.txt:44513–44514). The file is `objects/<Object>/fields/<Field>.field-meta.xml`, and the `package.xml` member is the object-qualified field name under `<name>CustomField</name>`.

**Detection hint:** Any file path, `package.xml` type, or `sf project retrieve --metadata` argument containing `LookupFilter` or `NamedFilter`.

---

## Anti-Pattern 7: Setting both `value` and `valueField` on one filter item

**What the LLM generates:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- WRONG - excerpt showing one malformed filterItems entry inside a field -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Billing_Contact__c</fullName>
    <lookupFilter>
        <active>true</active>
        <filterItems>
            <field>Contact.AccountId</field>
            <operation>equals</operation>
            <value>001xx000003DGb2AAG</value>
            <valueField>$Source.Account__c</valueField>
        </filterItems>
        <isOptional>false</isOptional>
    </lookupFilter>
</CustomField>
```

**Why it happens:** The LLM fills every documented field of `FilterItem` because they are all listed in the same table, and neither is marked "Required", so nothing in the table signals that they are alternatives.

**Correct pattern:** Exactly one of the two. `valueField` "specifies if the final column in the filter contains a field or a field value" (api_meta.txt:43922–43924) — it is the switch between the two modes, not a companion to `value`. Field-to-field comparison uses `valueField`; field-to-literal uses `value`.

**Detection hint:** Any `filterItems` block containing both `<value>` and `<valueField>`. `scripts/check_lookup_filter_cross_object_patterns.py` fails on this.
