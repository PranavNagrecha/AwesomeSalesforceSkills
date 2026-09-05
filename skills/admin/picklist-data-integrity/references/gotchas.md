# Gotchas — Picklist Data Integrity

Non-obvious picklist behaviors that bite real admin teams.

---

## Gotcha 1: Deactivating a value doesn't remove it from existing records

**What happens.** Admin deactivates a picklist value. The value is
removed from the value list shown in the Setup UI. But records that
had that value retain it; the field still shows the deactivated
value on those records.

**When it occurs.** Every value retirement.

**How to avoid.** Migrate records off the value before deactivating
(Pattern C). After deactivation, optionally use Setup → field →
Value → Replace to catch records you missed.

---

## Gotcha 2: Unrestricted picklist + API write = phantom values

**What happens.** An integration writes a value not in the picklist
definition. The write succeeds. Reports filtered on the picklist
don't surface the records (because the filter is keyed on current
values). The records appear missing from dashboards but exist in
the DB.

**When it occurs.** Source-system value list diverges from
Salesforce picklist; Unrestricted picklist permits the divergence.

**How to avoid.** Either keep the picklist Restricted (forcing
integration errors to surface to ops) or build a periodic
reconciliation report that finds records whose value isn't in the
current picklist.

---

## Gotcha 3: Renaming the label doesn't change the API name

**What happens.** Admin renames `Pending` to `Awaiting Review`. The
UI label changes. Reports show the new label. Apex / formulas /
validation rules that reference the value (`ISPICKVAL(Status,
"Pending")`) continue to work because they reference the API name,
not the label.

**When it occurs.** Cosmetic label changes.

**How to avoid.** Distinguish label rename (cosmetic, no Apex
impact) from API-name rename (treat as a value migration). Most
business-friendly renames are label-only.

---

## Gotcha 4: Dependent picklist with deactivated controller leaves dependent values orphaned

**What happens.** Controller value (e.g. Country = US) is
deactivated while records exist where Country = US AND State =
California. Records' State field is now unreachable from the UI —
no controlling-value path leads to California.

**When it occurs.** Restructuring dependent-picklist hierarchies.

**How to avoid.** Migrate records BEFORE deactivating the
controller. Pattern D in SKILL.md — mass-update Country and State
atomically, verify zero records on the retiring controller, then
deactivate.

---

## Gotcha 5: Global Value Set changes ripple to every consuming field

**What happens.** Renaming a value in a Global Value Set changes
the label on every picklist field that consumes it. Some
consumers may not have wanted the change.

**When it occurs.** Multi-stakeholder orgs where one BU's
"Industry Codes" decisions affect another BU's records.

**How to avoid.** Treat Global Value Set changes as coordinated
multi-stakeholder changes. Notify every consuming team before the
change. Or use local picklists for BU-specific lists where ripple
isn't desired.

---

## Gotcha 6: Per-record-type value subset is metadata, not a runtime filter

**What happens.** Admin expects the picklist to "filter by something
at runtime". The per-record-type value subset is determined by the
*record's* record type, not by the running user's profile.

**When it occurs.** Designing dynamic picklist behavior.

**How to avoid.** Per-record-type subsets work via record-type
metadata. For runtime / user-driven filtering, use field
visibility via permission sets or custom dependent-picklist logic
implemented as flow / validation.

---

## Gotcha 7: Inactive values still appear in some historical reports

**What happens.** Reports built on field-history tracking
(`<Object>History`, `FieldHistoryArchive`) can surface inactive
values that no longer appear in current-state reports. Admin sees
"On Hold" in a status-change-history report after they deactivated
it; thinks the deactivation was reverted.

**When it occurs.** Field-history reporting on a field where
values have been retired.

**How to avoid.** Document that historical-value visibility is
expected on history reports. The current-state picklist is the
source-of-truth for new edits; history is the audit trail.

---

## Gotcha 8: API write of a label vs API name

**What happens.** Integration writes the picklist *label* string
("In Progress") expecting it to map to the value. The platform
matches by API name, not label. Spaces, capitalization differences,
or label changes break the integration.

**When it occurs.** Integrations written by developers who saw the
label in Setup and assumed labels are the value identifier.

**How to avoid.** Document that integrations write API names. Have
a one-time reconciliation script: pull the picklist definition's
API names, ensure source-system value mapping uses those.

---

## Gotcha 9: "Sort alphabetically" sorts by label, not API name

**What happens.** Admin enables "Sort values alphabetically" on a
picklist. The displayed order changes. The label and API name may
diverge from the displayed sort — reports keyed on API name
continue to work, but UI users see a different order than the API
name suggests.

**When it occurs.** Picklists with non-matching labels and API
names.

**How to avoid.** Be deliberate when API names and labels diverge.
Alphabetical-sort and "use first value as default" interact in
non-obvious ways.

---

## Gotcha 10: An unrestricted picklist doesn't just store the string — it grows a new inactive value in the field definition, matched case-insensitively

**What happens.** Everyone describes phantom values as "the record holds
text that isn't in the picklist". That understates it. The Object
Reference is explicit: "The API doesn't enforce the list of values for
advisory (unrestricted) picklist fields on `create()` or `update()`.
When inserting an unrestricted picklist field that doesn't have a
PicklistEntry, the system creates an 'inactive' picklist value. This
value can be promoted to an 'active' picklist value by adding the
picklist value in the Salesforce user interface. When creating new,
inactive picklists, the API checks to see if there's a match. This
check is case-insensitive" (object_reference.txt:2363–2367). So the
*definition itself* accumulates entries nobody authored, and
`EMEA-North`, `emea-north` and `EMEA-NORTH` collapse onto whichever one
arrived first — the CSV's casing is not what ends up in the org.

**When it occurs.** Every API or Data Loader write of an unfamiliar
value to an unrestricted picklist. It is silent: no error, no row in a
failure file, nothing in the deploy log.

**How to avoid.** Two consequences to design around. First, the
Setup "Inactive Values" list on a long-lived unrestricted picklist is
an inbound-data audit log — read it before assuming the value list is
what someone designed. Second, when you later flip the field to
restricted, the case-insensitive collapse means your source system's
casing may no longer match the stored key; normalise casing on the
source side before the flip
(`references/metadata-examples.md` §5).

---

## Gotcha 11: `getPicklistValues()` cannot see the values you retired, so a describe-based audit finds nothing

**What happens.** An agent writes the obvious audit: describe the field,
loop the entries, flag the ones where `isActive()` is false. It reports
a clean field. Meanwhile 1,800 records carry a value retired last year.
`getPicklistValues()` "Returns a list of active `PicklistEntry` objects…
Only active picklist values are returned"
(apexrefguide.txt:190848–190849). The inactive entries were filtered out
before the loop began, so the `!isActive()` branch is unreachable — a
test that always passes.

**When it occurs.** Any Apex or LLM-authored audit that treats describe
as the inventory of what the field has ever held. `PicklistValueInfo`
has the same shape: it "Represents the active picklist values for a
given picklist field" (object_reference.txt:219760–219761).

**How to avoid.** Orphaned values are only visible as a **set
difference**: what is stored (a `GROUP BY` on the field) minus what is
defined (describe). Neither side alone can produce the list.
`references/metadata-examples.md` §1 is that computation. The one thing
`PicklistEntry.isActive()` is genuinely useful for is a value set you
built yourself in memory, not one from `getPicklistValues()`.

---

## Gotcha 12: Restricted rejects the write, but nobody has told you which error code to catch

**What happens.** Turning `restricted` on is documented as a hard stop:
a restricted picklist is one "whose values are restricted to those
values defined by a Salesforce admin. Users can't load unapproved values
through the API" (object_reference.txt:2463–2464), and the element means
"Whether the picklist's values are limited to only the values defined by
a Salesforce admin" (api_meta.txt:45847–45849). What is *not* documented
in the guides is the status code string. Middleware written to branch on
a specific code — retry, dead-letter, alert — is branching on a string
somebody remembered.

**When it occurs.** The first inbound message carrying an unlisted value
after the field is made restricted. Which is often weeks later, when the
source system adds a value.

**How to avoid.** **UNVERIFIED (2026-09-04):** the code named elsewhere
in this skill, `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`, does not
appear in api_rest.txt, apexdev.txt, api_meta.txt, object_reference.txt,
api_asynch.txt or apexrefguide.txt. Provoke the failure in a sandbox,
capture the real `errorCode` and `message` from the response, and put
those strings in the integration runbook. Do not ship error handling
keyed on a code you have not seen an org emit.

---

## Gotcha 13: Data Loader stopped truncating oversized picklist values at version 15.0 — it fails the row instead

**What happens.** A migration that worked for years starts rejecting
rows. "Allow field truncation" covers "Email, Multi-select Picklist,
Phone, Picklist, Text, and Text (Encrypted)". "In Data Loader versions
14.0 and earlier, Data Loader truncates values for fields of those types
if they're too large. In Data Loader version 15.0 and later, the load
operation fails if a value is specified that is too large"
(salesforce_data_loader.txt:437–452, 1863–1877). The setting is
`sfdc.truncateFields` in `config.properties` and is selected by default,
which is why nobody remembers deciding it.

**When it occurs.** Bulk value-replacement runs (this skill's Pattern C
and `references/metadata-examples.md` §4), especially on multi-select
picklists where the stored string is the semicolon-joined set and
therefore grows with every additional selection.

**How to avoid.** Before a replacement run, check the replacement
value's length against the field, and for multi-selects check the
longest *combination* rather than the longest single value. Failed rows
land in the error file, not the log — and the failed-rows file is a
different file from the unprocessed-rows file
(`admin/data-import-and-management` → `references/gotchas.md`,
"Failed Rows and Unprocessed Rows Are Different Files").

---

## Gotcha 14: A label rename survives in formulas and breaks in reports — the two references are not the same reference

**What happens.** `ISPICKVAL(Status__c, "Tier_1")` keeps working after
the label becomes "Gold", because the formula compares the stored key
and "the `query()` call always returns the value, not the label"
(object_reference.txt:2372–2374). A report filter typed as
`Support Tier equals Tier 1` does not, because a report filter on a
picklist is bound to a value the admin picked from a list — and the list
no longer offers that entry. The admin concludes the rename was partial
and starts changing things.

**When it occurs.** Any label rename on a field with saved reports,
dashboards, or list views. The identical trap on record types is
documented in `admin/record-types-and-page-layouts` →
`references/gotchas.md` § 4, "Reports Filter by Record Type Label —
Labels Are Not Stable"; picklist values behave the same way and for the
same reason.

**How to avoid.** Treat a label rename as a change with a dependency
list, not a cosmetic edit. The `rename-label` action exists in the
governance record for exactly this
(`references/metadata-examples.md` §6): formulas, validation rules and
Apex are greppable in retrieved source and usually need nothing; reports,
dashboards, list views and hand-typed integration mappings are not
greppable and usually do. An API-name rename is the opposite problem —
see § 3 and `admin/picklist-and-value-sets` → `references/gotchas.md`
§ 3 for the add-Replace-deactivate sequence it actually requires.
