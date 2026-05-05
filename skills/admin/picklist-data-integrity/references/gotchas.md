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
