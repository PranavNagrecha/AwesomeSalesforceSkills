# Examples — Multi-Language and Translation

## Example 1: Bulk Translation of Custom Labels via Export/Import

**Context:** A global Financial Services org has 200 custom labels used in Visualforce pages and Flow messages. They need Spanish (es) and Portuguese (pt_BR) translations.

**Problem:** Entering translations manually one by one for 200 labels in two languages would take days.

**Solution:**
1. Setup > Translation Workbench > Translation Settings — confirm both `es` and `pt_BR` are enabled.
2. Setup > Translation Workbench > Export: select "Custom Label", select language "Spanish". Export produces a ZIP with a bilingual TSV file.
3. Send the TSV to the translation vendor. They fill the Spanish translation column (column 3) for each row.
4. Import the completed file via Translation Workbench > Import.
5. Repeat for `pt_BR`.

**What the vendor actually receives.** The Workbench export is a bilingual
tab-delimited file, and the shape below is what a translator's tooling reads —
one row per string, the source column locked, the translation column empty. The
`LABEL` metadata type here is the Workbench's own name for a custom label; the
`KEY` is the label's `fullName`, which is what the import matches on.

```text
# Translation file for: Spanish
# Version: 62.0
Metadata Type	Key	Label	Translation	Out of Date
LABEL	Quote_Save_Button	Save Quote		-
LABEL	Error_Amount_Must_Be_Positive	{0} must be greater than zero.		-
LABEL	Toast_Quote_Submitted	Quote submitted for approval.		-
```

UNVERIFIED (2026-09-05): the exact column order and header text of the
Translation Workbench export (STF) file are described in Salesforce Help, which
is not in the extracted corpus used for this revision; the Metadata API
Developer Guide documents only the XML equivalents. Treat the block above as the
*shape* of the round-trip — one row per string, keyed on the label's API name,
with an empty translation column — and open one real export before writing a
vendor spec against it. The three columns that matter are grounded in the
`CustomLabelTranslation` field table: `name` (Required, the label's API name)
and `label` (Required, "Maximum of 765 characters") — `api_meta.txt:135934-135937`.

**Three constraints to put in the vendor brief, not discover on import:**

- The translated value caps at **765** characters even though the English
  source may be up to 1,000 (`api_meta.txt:135934-135935`). Flag any source
  string over 765 before it ships.
- A row returned **blank** does not clear the existing translation. "If a
  translation label is left blank, it's skipped during deployment, and no error
  will be shown" (`api_meta.txt:135789-135790`). Blank cells are silent no-ops,
  so ask the vendor to return the source string rather than an empty cell for
  "leave as English".
- Placeholders like `{0}` are `String.format` positions, not platform syntax.
  A translator who reflows the sentence may move them — correct — or drop them
  — silently wrong. Say which is which in the brief.

**Why it works:** The export format is a structured bilingual text file that translation vendors can work with directly. The import maps translations back to the exact label records. No manual UI entry required.

**Metadata equivalent.** The same round-trip in source control is a
`translations/es.translation-meta.xml` file reviewed as a pull request — see
`references/metadata-examples.md` §2 and `admin/custom-label-management`, which
owns the `CustomLabels` master file the keys above point at.

---

## Example 2: Translatable Validation Rule Error Messages

**Context:** A healthcare org has users in English and Spanish. Validation rules on the Patient record display error messages in English, confusing Spanish-speaking users.

**Problem:** Validation rule error message formulas use hardcoded English strings:
`'Date of birth is required for adult patients'`

**Solution:**
1. Create a Custom Label `Patient_DOB_Required` with value `'Date of birth is required for adult patients'`.
2. Add a Spanish translation via the label's detail page: value `'La fecha de nacimiento es obligatoria para pacientes adultos'`.
3. Update the validation rule formula to reference the label:
   `$Label.Patient_DOB_Required`
4. When the validation fires for a Spanish-language user, the error message displays in Spanish automatically.

**Why it works:** Custom Labels automatically return the translation for the running user's language. No conditional logic needed — the platform handles the language lookup.

---

## Example 3: Showing Picklist and Record Type Values in the User's Language with `toLabel()`

**Context:** A support console LWC lists Cases with their Status and Record Type. Its Apex controller runs its own SOQL. Translation Workbench already has Spanish translations for the Case Status picklist and the record types, but Spanish agents still saw English text in the component.

**Problem:** SOQL returns the master (default-language) value by default. The custom query bypassed the standard UI translation path, so the component rendered English regardless of the agent's language.

**Solution:**
1. Wrap the display fields in `toLabel()` in the controller query:
   ```sql
   SELECT CaseNumber,
          toLabel(Status) translatedStatus,
          toLabel(RecordType.Name) translatedRecordType
   FROM Case
   WHERE Status = 'Escalated'
   ```
2. Note the aliases (`translatedStatus`, `translatedRecordType`) — they give the columns readable names in the result. An alias becomes *required* only when the raw field is also in the `SELECT` list (e.g. both `Status` and `toLabel(Status)`).
3. Keep the `WHERE` clause on the API value (`Status = 'Escalated'`), never on `toLabel(Status)`, so the routing/filter logic stays language-independent.

**Why it works:** `toLabel()` returns the running user's translation and falls back to the master value when no translation exists, so a single query serves every language without any conditional logic. Because filtering still uses the API value, the query returns the same rows for every agent — only the displayed labels differ.

---

## Anti-Pattern: Using Picklist Translated Label in Apex or Validation Rules

**What practitioners do:** Reference the translated label of a picklist value in an Apex condition or validation rule formula:
```apex
if (account.Industry == 'Tecnología') { /* ... */ } // Spanish translation — breaks for every other language
```

**What goes wrong:** The picklist API value (the stored database value) is always the default language value (`Technology`), not the translation. The comparison always returns false for Spanish-language users, breaking the logic.

**Correct approach:** Always use the picklist API value in Apex and validation rule formulas, regardless of user language:
```apex
if (account.Industry == 'Technology') { /* ... */ } // API value, always works
```
Translations only affect the UI display label. They never change the stored value.
