# Path Configuration — Work Template

Use this template when configuring or reviewing a Salesforce Path for any object.

---

## Scope

**Object:** (e.g., Opportunity, Lead, Case, custom object API name)

**Record Type:** (developer name, or `Master` — "All Record Types" in the UI is the `Master` record type, and it consumes the one-and-only path slot for this object just like any other)

**Picklist Field:** (e.g., StageName, Status, Custom_Stage__c)

**Request summary:** (describe what the user or stakeholder wants to achieve)

---

## Context Gathered

Answer these before building:

- **Org-level Path toggle enabled?** Yes / No / Unknown
- **Path component on the Lightning page?** Yes / No / Unknown (check Lightning App Builder)
- **Existing paths on this object?** List any active paths and their record types. Get the real answer with `sf project retrieve start --metadata "PathAssistant:*"` — one path per object + record type is the platform maximum, so an existing path on your target record type means you are editing, not adding
- **Sales Process assigned (Opportunity only)?** Name of Sales Process — this controls available stages
- **Stages in scope:** List all picklist values that should appear in the path
- **Confetti needed?** Yes (on which stage?) / No
- **Mobile in scope?** Yes / No

---

## Stage Content Plan

Fill in one row per stage. Add or remove rows as needed.

| Stage | Key Fields (max 5) | Guidance Text Summary | Confetti? |
|---|---|---|---|
| (Stage 1) | Field1, Field2, Field3 | (1–2 sentence summary of guidance) | No |
| (Stage 2) | Field1, Field2 | (1–2 sentence summary) | No |
| (Stage 3) | Field1, Field2, Field3, Field4 | (summary) | No |
| (Closed Won / Final) | Field1, Field2 | (summary) | Yes |

**Field type check — confirm all key fields are a supported type:**

- [ ] No long text area fields (Description, rich text fields)
- [ ] No encrypted fields
- [ ] No cross-object dotted references (`Contact.Phone`) — `fieldNames` must name fields on the path's own object
- [ ] No fields the running user's FLS restricts (they will silently not appear)
- [ ] Every custom field in the list exists in the deployment package, not only in the source org

---

## Path Setup Steps

1. Go to Setup > Path Settings
2. Confirm the org-level Enable Path toggle is ON
3. Click "New" to create a path, or click an existing path to edit
4. Select: Object = `[object]`, Field = `[field]`, Record Type = `[record type]`
5. For each stage listed above:
   a. Click the stage chevron
   b. Add key fields from the "Fields" picklist (left panel)
   c. Enter guidance text in the rich-text editor
   d. If confetti needed: toggle "Celebration Animation" on
6. Click "Activate" when configuration is complete
7. Open Lightning App Builder for the `[object]` record page
8. Confirm the Path standard component is present in a full-width region at the top
9. Save and activate the Lightning page if changes were made

**If this is being deployed rather than clicked, the package needs five types, not one** — see `references/metadata-examples.md`:

| # | Type | File |
|---|---|---|
| 1 | `StandardValueSet` (only if a stage value is new) | `standardValueSets/<Name>.standardValueSet-meta.xml` |
| 2 | `CustomField` (every custom key field) | `objects/<Object>/fields/<Field>.field-meta.xml` |
| 3 | `BusinessProcess` + `RecordType` | inside the object definition |
| 4 | `PathAssistant` | `pathAssistants/<Name>.pathAssistant-meta.xml` |
| 5 | `PathAssistantSettings` + `FlexiPage` | `settings/PathAssistant.settings-meta.xml`, `flexipages/<Page>.flexipage-meta.xml` |

Run `python3 scripts/check_path_and_guidance.py --manifest-dir <dir>` before every deploy.

**Manual post-deploy step, every org, every time:** re-enable the celebration animation. It has no element in `PathAssistant` and does not travel with the package.

---

## Test Checklist

Test as a non-admin user (representative of the end users):

- [ ] Path component renders on the record page with all expected stages in the chevron bar
- [ ] Clicking each stage chevron shows the correct key fields for that stage
- [ ] Guidance text is visible and formatted correctly (bullets, links work)
- [ ] Key fields are editable inline where expected (check FLS for the test user)
- [ ] Confetti fires when advancing to the designated stage via "Mark Stage as Complete"
- [ ] Confetti does NOT fire when the stage is changed via the picklist directly or via automation (confirm expectation is set)
- [ ] Mobile rendering checked: stage labels readable, key fields visible, guidance accessible

---

## Deviations and Notes

Record any decisions that differ from the standard pattern:

- (e.g., "Guidance text for Negotiation stage links to an external tool — URL confirmed working as of 2026-04-04")
- (e.g., "Confetti intentionally not enabled — stage advance is always via integration, not UI")
- (e.g., "Key fields for New Business record type differ from Renewal record type — two separate paths maintained")
- (e.g., "Celebration re-enabled by hand in PROD on <date> by <name> — confirm after every deploy")
- (e.g., "canOverrideAutoPathCollapseWithUserPref left false on purpose — <reason>")
