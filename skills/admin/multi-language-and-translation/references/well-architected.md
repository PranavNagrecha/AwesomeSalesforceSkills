# Well-Architected Notes — Multi-Language and Translation

## Relevant Pillars

- **User Experience** — Multi-language support directly enables a better user experience for non-English users. Untranslated labels, picklist values, and error messages degrade adoption and usability for international users.
- **Operational Excellence** — Centralized translation management via Translation Workbench (with export/import workflow) is more maintainable than ad-hoc custom label overrides or language-conditional formulas. A structured process ensures translations stay current as the org evolves.

## Architectural Tradeoffs

**Custom Labels vs. hardcoded strings in code:** Custom Labels are the correct architecture for all user-facing strings in Apex, Visualforce, and Flow. Hardcoded strings cannot be translated without code changes. The investment in converting existing hardcoded strings to Custom Labels pays off immediately when a new language is added.

**Translation Workbench vs. custom translation objects:** Translation Workbench is the native, supported mechanism. Custom "translation record" approaches (custom objects with translated values looked up by language at runtime) add complexity and are harder to maintain.

## Anti-Patterns

1. **Hardcoded strings in validation rule formulas** — Use `$Label.*` references for all user-facing messages so translations work automatically.
2. **Comparing picklist values using translated labels in code** — Always use API values (default language). Translated labels are UI-only.
3. **Disabling Translation Workbench to debug** — Removes all translations immediately. Use a sandbox or remove a single language.

## Official Sources Used

- Salesforce Help — Set Up Translation Workbench — https://help.salesforce.com/s/articleView?id=sf.workbench_overview.htm
- Salesforce Help — Translate Custom Labels — https://help.salesforce.com/s/articleView?id=sf.cl_translate.htm
- Salesforce Help — Experience Cloud Language Support — https://help.salesforce.com/s/articleView?id=sf.networks_multilingual.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
