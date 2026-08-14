# Gotchas — EDA Data Model and Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

All object, field and error strings below are taken from the EDA managed
package source (`SalesforceFoundation/EDA`, BSD-3-Clause, `main`). EDA installs
under the **`hed` namespace**, so every packaged component is prefixed `hed__`
in a subscriber org — `hed__Affiliation__c`, `hed__Term__c`, `hed__Course__c`.
Guidance written against unprefixed names does not compile or query.

---

## Gotcha 1: The object labelled "Course Connection" is `hed__Course_Enrollment__c`

**What happens:** Enrollment records show up in the UI, reports, and list views
as **Course Connection**, but the API name is `hed__Course_Enrollment__c`.
Anything typed from the label — SOQL, Apex, a Data Loader mapping, a Flow Get
Records element, an external ETL job — targets an object that does not exist in
the org and fails at compile or run time.

**When it occurs:** Every time someone writes integration or reporting code from
a screenshot, a data dictionary generated from labels, or an LLM's guess. It is
the single most common EDA integration bug.

**How to avoid:** Build the field map from Object Manager API names, never from
labels. Add `hed__Course_Enrollment__c` to the project glossary alongside its
label so both spellings resolve. Same class of trap: the "Affiliation Mappings"
setting is `hed__Affl_Mappings__c`, and the "Reciprocal Relationships" setting
is `hed__Relationship_Lookup__c`.

---

## Gotcha 2: Affiliation Mappings is a List custom setting, so its rows do not deploy

**What happens:** `hed__Affl_Mappings__c` is declared `<customSettingsType>List</customSettingsType>`
— it is a custom **setting**, not a custom object. Its two load-bearing fields
are `hed__Account_Record_Type__c` (an Account record type) and
`hed__Primary_Affl_Field__c` (the API name of an Account lookup field on
Contact). The setting *definition* travels in a change set or package; the
**rows do not**. A sandbox that works perfectly promotes to production with an
empty mapping table.

**When it occurs:** First release after an EDA build, and again after every full
sandbox refresh.

**How to avoid:** Treat mapping rows as post-deployment data, not metadata. Load
them with a scripted step (Data Loader, `sf data import`, or an install script)
and add a smoke check that counts rows in `hed__Affl_Mappings__c` before
declaring the release green. When a mapping is missing, saving an Affiliation
fails with:

> We can't save this record because of an Account record type error in Affiliation Mappings. Ask your administrator to verify that Account Record Types are correctly mapped to Contact Primary Affiliations.

and a mapping pointing at a record type that no longer exists produces:

> We can't save this record because {1} isn't a valid Account record type. Ask your admin to check Affiliation Mappings in EDA Settings and set the value for {0} to the API name of a valid Account record type instead of {1}.

---

## Gotcha 3: Four of the six Primary Affiliation fields on Contact are *not* namespaced

**What happens:** `hed__Primary_Household__c` and `hed__Primary_Organization__c`
ship inside the managed package and carry the `hed__` prefix. The other four —
`Primary_Academic_Program__c`, `Primary_Educational_Institution__c`,
`Primary_Department__c`, `Primary_Sports_Organization__c` — are deployed to the
subscriber org as **unmanaged** org-level fields and have **no prefix at all**.
EDA's own install script makes the split explicit: it namespace-wraps the first
two and writes the other four as bare API names into the default mapping rows.

**When it occurs:** Writing SOQL, a Flow formula, an integration field map, or a
`hed__Affl_Mappings__c` row. Prefixing all six "for consistency" silently
targets fields that do not exist; the mapping row then fails validation with
"The Primary Affiliation field {0} isn't valid."

**How to avoid:** Never infer the prefix — read it off Object Manager per field.
The same asymmetry means the unmanaged four can be renamed or deleted by an
admin, which the package cannot prevent, so include them in field-deletion impact
analysis. For reference, the record type *developer names* EDA maps by default
are `Academic_Program`, `Business_Organization`, `HH_Account` (not
`Household_Account`), `Educational_Institution`, `University_Department`, and
`Sports_Organization`.

---

## Gotcha 4: One Account record type maps to exactly one Contact Primary Affiliation field

**What happens:** Admins try to map, say, `Educational Institution` to two
Contact lookups so a student's institution lands in both. EDA refuses:

> We can't map this Affiliation because it references a record type that is already referenced by another Affiliation Mapping. If you want to add this mapping so the Affiliation is translated, click Edit to modify the existing mapping.

EDA's own health check reports the inverse case too — "The {0} ({1}) field is
mapped to multiple Account record types."

**When it occurs:** Multi-campus and multi-program models, where one person
legitimately affiliates to several Accounts of the same record type.

**How to avoid:** Model the second relationship as an additional
`hed__Affiliation__c` record with `hed__Primary__c = false`, not as a second
mapping. Primary Affiliation is a *single* denormalised convenience lookup; the
Affiliation records are the system of record. Attempting to make a second
Affiliation primary against the same Account produces:

> This Contact already has a Primary Affiliation to the specified Account. Either deselect the Primary setting for the other Affiliation so you can designate this one as Primary, or create this Affiliation without the Primary value.

---

## Gotcha 5: EDA automation is table-driven, and bulk loads must be told to skip it

**What happens:** EDA does not ship one trigger per object. It ships a TDTM
(Table-Driven Trigger Management) dispatcher driven by rows in the
`hed__Trigger_Handler__c` **custom object**, with fields `hed__Class__c`,
`hed__Object__c`, `hed__Trigger_Action__c`, `hed__Load_Order__c`,
`hed__Active__c`, `hed__Asynchronous__c`, and `hed__Usernames_to_Exclude__c`. A
naïve student/enrollment load fires every handler for every row: household
maintenance, address maintenance, reciprocal relationship creation, primary
affiliation rollups. Load times blow out and CPU/DML limits trip.

**When it occurs:** Any initial migration or nightly SIS sync above a few
thousand rows.

**How to avoid:** Do not comment out triggers — there are none to comment out.
Either set `hed__Active__c = false` on the specific handler rows you need
quiet, or put the integration user's username in `hed__Usernames_to_Exclude__c`
so that user bypasses the handler while interactive users keep it. The
username-exclusion route is safer because it cannot be left switched off for
everyone. Whichever you pick, script the restore and verify it — a handler left
inactive silently stops maintaining Primary Affiliation and Household data, and
nothing errors.

---

## Gotcha 6: Affiliations require the Account to have a record type at all

**What happens:** With EDA's Record Type Validation setting on, an Affiliation
whose Account carries no record type is rejected:

> We can't create this Affiliation because the specified Account doesn't have a record type.

EDA describes the setting as: "Require Accounts specified as a Contact's Primary
Affiliation use a record type. Also ensure that all Account record types are
mapped to Primary Affiliation fields on the Contact object. If validation fails,
the Affiliation isn't saved."

**When it occurs:** Accounts created by an integration user whose profile has no
default Account record type assigned, or Accounts that predate the EDA install.

**How to avoid:** Assign Account record types in the integration user's profile
or permission set and set a default; audit for `Account.RecordTypeId = null`
before migrating Affiliations. Related install-time failure — EDA expects an
Administrative Account record type and reports its absence as:

> We can't find the Administrative Account record type in your org. Following installation, use Object Manager to create a new record type named 'Administrative' for the Account object.

---

## Gotcha 7: Turning on Course Connection record types after data exists needs a backfill job

**What happens:** Course Connection record types are off by default. Switch them
on in an org that already holds enrollment data and every existing record keeps
a null record type, so the student/faculty split silently excludes historical
rows from every record-type-filtered report and layout.

**When it occurs:** Phase-two EDA builds that add faculty tracking to an org
already carrying student enrollments.

**How to avoid:** EDA ships the fix and says to run it first: "Before enabling
Course Connections for the first time, run this Apex job to update Faculty
Course Connection records to the Default Faculty Record Type value. Also updates
remaining Course Connections to the Default Student Record Type value." It is
asynchronous — the confirmation reads "We're updating Course Connection record
types. Check the status of the job under Apex Jobs in Setup." Wait for the job
to finish before validating reports, and confirm Default Student Record Type and
Default Faculty Record Type are set to *different* record types; EDA's health
check flags them when they match.
