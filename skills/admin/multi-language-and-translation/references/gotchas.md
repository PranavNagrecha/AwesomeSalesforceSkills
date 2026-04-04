# Gotchas — Multi-Language and Translation

## Gotcha 1: Picklist API Values Never Change — Only Labels Do

**What happens:** An admin adds Spanish translations for picklist values and notices that existing records still show English values in some contexts — specifically in reports filtered by picklist value or in Apex conditions.

**When it occurs:** Any code or formula that references picklist values by their stored value. Since the API value (stored value) does not change, comparisons using translated labels fail.

**How to avoid:** Always use the API value (default language value) in Apex, SOQL, validation rule formulas, and report filters. Translations only affect the displayed label in the UI. Document this clearly for developers joining the project.

---

## Gotcha 2: Disabling Translation Workbench Removes All Translations

**What happens:** An admin disables Translation Workbench to troubleshoot a UI issue. All translations disappear immediately for all users. When Translation Workbench is re-enabled, the translations return — but the org experienced a translation outage.

**When it occurs:** Setup > Translation Workbench > Translation Settings > Disable.

**How to avoid:** Never disable Translation Workbench in production. Use a sandbox to troubleshoot translation issues. If a specific language is causing problems, remove just that language rather than disabling the entire workbench.

---

## Gotcha 3: Export/Import Translation Files Are Language-Specific

**What happens:** An admin exports translations for all languages at once, expecting a single file to contain all translations. The export actually creates language-specific files in the ZIP. Importing the wrong language's file overwrites translations.

**When it occurs:** Translation Workbench > Export > select all languages. Each language has its own tab-delimited file in the export ZIP.

**How to avoid:** Process one language at a time in export/import workflows. Label each file clearly with the language code before sending to a vendor or importing. Always import the file for the correct language.
