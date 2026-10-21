# Gotchas — Record Type Id Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `getRecordTypeInfosByDeveloperName()` returns record types the running user cannot use

**What happens:** A developer writes an "available record types" picker by iterating the describe map, and users see record types they are not assigned. The Apex Reference Guide is explicit for every one of the four accessors: "The current user is not required to have access to a record type to see it in this map" (list for `getRecordTypeInfos()`; apexref 262 L192544, L192557, L192570, L192589). The map is a schema view, not an access-control view.

**When it occurs:** Any picker, LWC combobox, or Flow choice set built from `getRecordTypeInfosByDeveloperName()`, `getRecordTypeInfosByName()`, `getRecordTypeInfosById()`, or `getRecordTypeInfos()` without filtering. UNVERIFIED (2026-10-21): that a deactivated record type stays in the map — the guide provides `isActive()` (apexref 262 L193848) but does not say what the maps contain.

**How to avoid:** Filter on both `Schema.RecordTypeInfo.isAvailable()` — "Returns true if this record type is available to the current user" (apexref 262 L193867) — and `isActive()`. Resolution code that only needs an Id for a known DeveloperName can skip the filter; anything user-facing cannot.

```apex
List<Schema.RecordTypeInfo> pickable = new List<Schema.RecordTypeInfo>();
for (Schema.RecordTypeInfo rti : Account.SObjectType.getDescribe().getRecordTypeInfos()) {
    if (rti.isAvailable() && rti.isActive() && !rti.isMaster()) {
        pickable.add(rti);
    }
}
```

---

## Gotcha 2: The Master record type is in the map and its Id is not what callers expect

**What happens:** Code loops the describe map and assigns "the first record type" to new records, and picks up Master. The Apex Reference Guide is explicit: `isMaster()` "Returns true if this is the master record type and false otherwise. The master record type is the default record type that's used when a record has no custom record type associated with it" (apexref 262 L193892-193893). Assigning it is not the same as assigning a real record type — downstream logic that compares the record type by DeveloperName will not match the business type the author intended.

**When it occurs:** Generic "clone this record into object X" utilities, data-load default logic, and LLM-generated pickers that iterate without an `isMaster()` guard.

**How to avoid:** Always exclude `isMaster()` from user-facing lists, and never treat Master as a resolvable business record type. If your object genuinely has one record type, resolve that one by DeveloperName rather than falling back to the map's first entry.

---

## Gotcha 3: Changing a record type's `fullName` in source is not a rename (UNVERIFIED that it creates a second record type)

**What happens:** The Metadata API `RecordType` type documents `fullName` as the "Record type name. The fullName can contain only underscores and alphanumeric characters" (api_meta 264 L47382-47383) — the same character rules as `RecordType.DeveloperName` (obj 264 L246998-246999), and the component key. Change it in source and the deploy addresses a different component. UNVERIFIED (2026-10-21): that the deploy then creates a new record type, leaves the old one active with every existing record, and raises no error — the corpus does not describe a deploy of a changed `fullName`.

**When it occurs:** Any refactor that "cleans up" record-type API names, and any copy-paste of a record type definition between objects.

**How to avoid:** Treat `fullName` as immutable after the first deploy. Change the `label` — "Required. Descriptive label for the record type" (api_meta 264 L47396) — when the business name changes; leave `fullName` alone. If the API name genuinely must change, plan a data migration that re-stamps `RecordTypeId` on existing records, then deactivate the old type with `<active>false</active>` rather than deleting it.

---

## Gotcha 4: `businessProcess` must NOT be prefixed with the object name, and a missing DeveloperName surfaces as a null

**What happens:** A hand-written Opportunity `RecordType` file writes `<businessProcess>Opportunity.Bulk Orders</businessProcess>`. The guide says this field takes "the bare process name ... not object-qualified. As the record type is already defined within the object, don't prefix the object name (Opportunity. Bulk Orders)", and that it is "required in record types for lead, opportunity, solution, and case, and not allowed otherwise" (api_meta 264 L47367-47373). That instruction is about `businessProcess`, not the record type's own `fullName` — and the guide's two samples differ on `fullName`: the declarative sample inside a `CustomObject` writes it bare (`<fullName>My_First_Recordtype</fullName>`, api_meta 264 L47474), while the Java API sample sets an object-qualified `edit.setFullName("ExpenseReport__c.Edit")` (api_meta 264 L47429). When a record type fails to deploy, `getRecordTypeInfosByDeveloperName().get('Bulk_Orders')` returns `null`, and `.getRecordTypeId()` on it throws "Attempt to de-reference a null object" (apexdev 264 L40297), far from the real cause.

**When it occurs:** Hand-authored metadata for Lead, Opportunity, Solution or Case record types, and copy-paste of `package.xml` member names (`Opportunity.Bulk_Orders`) into element values.

**How to avoid:** Write `businessProcess` bare; retrieve record-type files from an org rather than hand-authoring them. And null-guard every describe lookup — a missing DeveloperName is a deployment defect that should fail loudly:

```apex
Schema.RecordTypeInfo rti = Account.SObjectType.getDescribe()
    .getRecordTypeInfosByDeveloperName().get('Business_Account');
if (rti == null) {
    throw new IllegalArgumentException(
        'Record type Business_Account is not deployed to this org');
}
Id rtId = rti.getRecordTypeId();
```

---

## Gotcha 5: `getName()` is a translatable label, so name-based lookups are language-sensitive

**What happens:** Code resolves via `getRecordTypeInfosByName()` and works for the developer; it can return `null` for a user whose language is French (UNVERIFIED, see below). `Schema.RecordTypeInfo.getName()` "Returns the UI label of this record type. The label can be translated into any language that Salesforce supports" (apexref 262 L193824), and `getRecordTypeInfosByName()` "matches record labels to their associated record type" (apexref 262 L192589). UNVERIFIED (2026-10-21): that the map is keyed on the *running user's* translated label, so a French user gets `null` — the guide pairs the two facts but does not say which language keys the map.

**When it occurs:** Multi-language orgs, and any org where Translation Workbench is enabled for record types (`RecordTypeLocalization` holds the translated label, obj 264 L247090). It is invisible in single-language sandboxes, so it ships.

**How to avoid:** Use `getRecordTypeInfosByDeveloperName()` for every resolution. Reserve `getName()` for display only. The same rule applies in SOQL: filter `RecordType.DeveloperName`, never `RecordType.Name` (the label, obj 264 L247039).
