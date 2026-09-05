# Well-Architected Notes — Multi-Language and Translation

## Relevant Pillars

- **User Experience** — Multi-language support directly enables a better user experience for non-English users. Untranslated labels, picklist values, and error messages degrade adoption and usability for international users.
- **Operational Excellence** — Centralized translation management via Translation Workbench (with export/import workflow) is more maintainable than ad-hoc custom label overrides or language-conditional formulas. A structured process ensures translations stay current as the org evolves.

## Architectural Tradeoffs

**Custom Labels vs. hardcoded strings in code:** Custom Labels are the correct architecture for all user-facing strings in Apex, Visualforce, and Flow. Hardcoded strings cannot be translated without code changes. The investment in converting existing hardcoded strings to Custom Labels pays off immediately when a new language is added.

**Translation Workbench vs. custom translation objects:** Translation Workbench is the native, supported mechanism. Custom "translation record" approaches (custom objects with translated values looked up by language at runtime) add complexity and are harder to maintain.

**Setup-first vs source-first translation:** every surface this skill covers has
a deployable metadata type — `LanguageSettings`, `Translations`,
`CustomObjectTranslation`, `GlobalValueSetTranslation`,
`StandardValueSetTranslation`. Entering translations in Setup is faster once and
untrackable forever: there is no diff, no reviewer, and no way to tell a
reworded English label from a stale German one. Source-first costs a
`package.xml` and buys the release process a place to hang the re-translation
review that the platform does not provide (metadata translations carry no
staleness flag; only *data* translations have `IsOutOfDate`,
`object_reference.txt:227916-227917`).

**Translating a validation message twice:** a rule's error text can be
translated either as a `$Label` merge field (translated in the label's
`Translations` file) or as a `ValidationRuleTranslation.errorMessage` in the
object's `objectTranslation` (`api_meta.txt:46245-46246`). Both work. Doing
both in one org produces two sources of truth for the same sentence, and only
one of them will be updated next time. Pick one per org and write the choice
into the config workbook.

## Anti-Patterns

1. **Hardcoded strings in validation rule formulas** — Use `$Label.*` references for all user-facing messages so translations work automatically.
2. **Comparing picklist values using translated labels in code** — Always use API values (default language). Translated labels are UI-only.
3. **Disabling Translation Workbench to debug** — Removes all translations immediately. Use a sandbox or remove a single language. (See `gotchas.md` Gotcha 2 for what is and is not grounded here; the documented, reversible lever is `Translation.IsActive` per language, `object_reference.txt:290205-290206`.)
4. **Bundling a translation deploy with a stale `objects/` folder** — a picklist value missing from the deployed component definition is deactivated, not ignored (`api_meta.txt:47482-47483`). Translations deploy last, alone.
5. **Enabling a platform-only language to serve one app** — it also switches on every end-user language org-wide (`api_meta.txt:120961-120964`). Language tiers are an org-level decision.
6. **Treating "translate the product catalogue" as part of the UI translation** — record data is `enableDataTranslation` plus the `*DataTranslation` sObjects, a separate feature with separate owners (`api_meta.txt:120918-120920`, `object_reference.txt:227889`).

## Official Sources Used

- Metadata API Developer Guide — *Translations* → *Language* (`api_meta.txt:135350-135572`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — (the fully supported / end-user / platform-only language code lists, the `<locale>.translation` file-naming rule, the Translations children table, and the retrieve caveat that translations come back only for types also named in `package.xml`)
- Metadata API Developer Guide — *CustomObjectTranslation* and its subtypes (`api_meta.txt:45881-46425`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — (the `<Object>-<lang>.objectTranslation` naming rule, the `fields` / `picklistValues` / `layouts` / `recordTypes` / `validationRules` element shapes, the 40-character field-label cap and the 765-character caps on its neighbours, `gender` / `startsWith` / `caseValues`, and the package-override note)
- Metadata API Developer Guide — *GlobalValueSet*, *GlobalValueSetTranslation* and *StandardValueSetTranslation* (`api_meta.txt:79344-79516`, `api_meta.txt:130831-130895`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — (the `__gvs` developer-name suffix from API 57.0, the `ValueSetName-lang` file names, the optional `<translation>`, and the untranslated-value-as-XML-comment convention)
- Metadata API Developer Guide — *LanguageSettings* (`api_meta.txt:120896-121009`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — (`enableTranslationWorkbench` defaulting to false, `enablePlatformLanguages` cascading into `enableEndUserLanguages`, `useLanguageFallback`, `enableDataTranslation`, `enableLocaleInsensitiveFiltering`, and the `Settings` / `Language` manifest form)
- Metadata API Developer Guide — *CustomValue* and *ListView* (`api_meta.txt:47474-47484`, `api_meta.txt:44352-44355`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf — (picklist values missing from a deployed component definition are deactivated; a list view filtered with `startsWith`/`contains` is bound to `ListView.language` once the Workbench is on)
- Object Reference for the Salesforce Platform — *Translation*, *User*, *Product2DataTranslation* (`object_reference.txt:290166-290215`, `object_reference.txt:295460-295474`, `object_reference.txt:227878-227945`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf — (edition and permission requirements for enabling a language, `IsActive` / `CanManage`, `User.LanguageLocaleKey` and its API-47 `PicklistEntry.active` semantics, and data translation's `IsOutOfDate` staleness flag)
- SOQL and SOSL Reference — toLabel() (SOQL SELECT) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_tolabel.htm — (the `toLabel()` projection, its fallback to the master value, and the `ORDER BY` / alias / `WHERE` restrictions in the SKILL.md section)
- SOQL and SOSL Reference — toLabel() (SOSL RETURNING) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl_tolabel.htm — (the SOSL `RETURNING`-clause form)
- Salesforce Help — Set Up Translation Workbench — https://help.salesforce.com/s/articleView?id=sf.workbench_overview.htm — (the Setup navigation paths and the export/import spreadsheet workflow, which have no Metadata API equivalent)
- Salesforce Help — Experience Cloud Language Support — https://help.salesforce.com/s/articleView?id=sf.networks_multilingual.htm — (the Language Switcher component and site-level default language)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview — (the pillar framing above)

Note on the cheat sheet: `grep -n -i "translation|language"` over the Salesforce
App Limits Cheat Sheet returns **nothing** as of 2026-09-05. There are no
edition-level numeric limits on translations or supported languages in that
document; every ceiling cited in this package is a per-element character
maximum from the Metadata API field tables, not an org limit.
