---
name: multi-language-and-translation
description: "Configure Salesforce Translation Workbench and translate custom labels, picklist values, field labels, page layout sections, or the Experience Cloud language switcher. Triggers: 'how to add a language to Salesforce', 'translate custom labels', 'Translation Workbench setup', 'picklist value translation', 'RTL language support'. NOT for creating the Custom Label records or referencing them from Apex/LWC — use admin/custom-label-management. NOT for locale formatting and RTL layout inside a component — use lwc/lwc-internationalization. Also: CustomObjectTranslation, objectTranslation file, GlobalValueSetTranslation, StandardValueSetTranslation, LanguageSettings, enableTranslationWorkbench, locale code, end-user language, platform-only language, data translation."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
triggers:
  - "how do I translate custom labels and field labels into Spanish or French"
  - "my Experience Cloud site needs to support multiple languages with a language switcher"
  - "how do I enable Translation Workbench and add a new language to the org"
  - "picklist values are showing in English even after I added translations"
  - "how do I support right-to-left languages like Arabic or Hebrew in Salesforce"
  - "multi language isn't working"
  - "we're having issues with multi language"
  - "return translated picklist or record type values in a SOQL or SOSL query"
  - "use toLabel() to show picklist values in the running user's language"
  - "field labels are still in English for my German users after deploying translations"
  - "objectTranslation deployed successfully but nothing changed in the UI"
  - "what file name does a CustomObjectTranslation need"
  - "translate picklist values that come from a global value set"
  - "enable Translation Workbench through metadata with LanguageSettings"
  - "deploy translations from sandbox to production and they overwrite each other"
  - "a picklist translation came back blank after the vendor import"
  - "which languages are fully supported versus end-user versus platform-only"
tags:
  - translation
  - multi-language
  - translation-workbench
  - custom-labels
  - localization
  - experience-cloud
inputs:
  - "List of languages to support and their locale codes (e.g., es for Spanish)"
  - "List of components to translate: field labels, picklist values, custom labels, validation messages"
  - "Whether the org uses Experience Cloud sites with language switcher"
outputs:
  - "Translation Workbench configuration steps for each language"
  - "Export/import workflow for bulk translations via Translation Workbench spreadsheet"
  - "Custom label translation setup"
  - "Experience Cloud language switcher configuration"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Multi-Language and Translation

Use this skill when configuring Salesforce to support multiple languages for internal users or Experience Cloud site visitors. This covers enabling Translation Workbench, adding supported languages, translating custom labels, field labels, picklist values, page layout section names, and configuring the Experience Cloud language switcher.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org edition. The `Translation` object — the record that represents "the languages enabled for translation in your Salesforce org" — requires Enterprise, Performance, Unlimited, or Developer edition and the "View Setup and Configuration" permission (`object_reference.txt:290167-290185`). Some older localization sObjects (`ScontrolLocalization`, `WebLinkLocalization`) list Professional as well; the `Translation` object's rule is the one that governs enabling a language.
- Identify the languages by locale code **and by tier** — fully supported (`de`, `fr`, `es`, `ja`, …), end-user (`ar`, `iw`, `pl`, `tr`, …), or platform-only (`cy`, `hi`, `ur`, …). The three lists are in the Metadata API Developer Guide (`api_meta.txt:135356-135572`) and the tier decides how much Salesforce translates for you. Hebrew is `iw`, not `he`.
- Determine what needs translating, and classify each item by the metadata type that carries it — see *Where each translation actually lives* below. Each type is a different file with a different naming rule.
- For RTL languages, the guide's own instruction is to "review the right-to-left language support limitations" **before** enabling Arabic or Hebrew as end-user languages (`api_meta.txt:135407`) or Urdu as a platform-only language (`api_meta.txt:135569`). Treat native RTL as covering standard Lightning surfaces only; custom LWC and Experience Cloud templates are yours to test.

## Questions to Ask Before Configuring

Ask these before the first `<fields>` element is written. Every row traces to a
gotcha in `references/gotchas.md` — skip it and the translation deploys green
and changes nothing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which exact locale codes, and is each fully supported, end-user, or platform-only?" | Enabling one platform-only language also enables *all* end-user languages (`api_meta.txt:120961-120964`); the tier also decides how much standard UI stays English | The `LanguageSettings` flags to set, and a written expectation of what will still read English |
| "For each string, which metadata type carries it — custom label, field label, local picklist, global value set, standard picklist, validation message, layout section?" | Each lands in a different file with a different naming rule; a global-value-set value translated per field deploys clean and shows nothing (Gotcha 6) | A file inventory: which `objectTranslation`, `globalValueSetTranslation` and `<locale>.translation` files this change creates |
| "Is the ask to translate the UI, or the record data?" | Metadata translation and `enableDataTranslation` are separate features with separate objects (Gotcha 10) | Whether `Product2DataTranslation` and friends are in scope at all, and who owns that half |
| "How long is the longest field label, in the longest target language?" | `CustomFieldTranslation.label` caps at 40 characters while its neighbours cap at 765 (Gotcha 7) | Per-element ceilings in the vendor brief instead of one number for the whole job |
| "Does anything filter on a translated value — a list view using contains/startsWith, a report filter, Apex?" | `ListView.language` binds such filters to one language once the Workbench is on (Gotcha 9), and picklist API values never change (Gotcha 1) | The list of filters to re-point at API values, plus a `<language>` decision per affected list view |
| "How stale will the object metadata be by the time translations come back from the vendor?" | A picklist value missing from a `CustomObject` payload is deactivated, not ignored (Gotcha 5) | A deploy split: translations alone, never bundled with a weeks-old `objects/` folder |
| "Who re-translates when an English label is reworded, and what triggers them?" | Metadata translations carry no staleness flag — only *data* translations have `IsOutOfDate` (Gotcha 10) | A named owner and a review step in the release process, not a hope |

What a proper configuration adds over just entering translations in Setup: every string lands in the right metadata type, the file names match what the platform expects, the deploy runs in an order that cannot deactivate values or overwrite a colleague's work, and each language is verified as a user in that language rather than assumed.

---

## Core Concepts

### Translation Workbench Architecture

Translation Workbench (Setup > Translation Workbench > Translation Settings) is the central management tool for Salesforce UI translations. Key concepts:

- **Default language**: The org's default language. All metadata is authored in this language.
- **Supported languages**: Languages you enable in Translation Workbench. Only supported languages are available to users and translatable via the Workbench.
- **Translation override vs. auto-translation**: Translations for standard Salesforce UI elements are provided by Salesforce for supported languages. Custom components (custom labels, custom field labels, picklist values) require manual entry or import.
- **Language tiers**: fully supported languages get the whole UI; end-user languages get standard objects and pages "except admin pages, Setup, and Help" and the guide warns "Don't use end-user languages as corporate languages" (`api_meta.txt:135382-135387`); platform-only languages leave "all standard Salesforce labels default to English or, in select cases, to an end-user or fully supported language" (`api_meta.txt:135412-135413`). Arabic and Hebrew are end-user, not fully supported.
- **Enablement is metadata**: `LanguageSettings` lives in `settings/Language.settings` and carries `enableTranslationWorkbench` (default `false`), `enableEndUserLanguages`, `enablePlatformLanguages`, `enableDataTranslation` and `useLanguageFallback` (default `true`, which is why a missing translation renders as source-language text with no error) — `api_meta.txt:120903`, `api_meta.txt:120911-120971`.

### Where each translation actually lives

The single most useful thing to know before touching a translation: the type of
thing you are translating decides the file, and the file name is part of the
contract.

| What you are translating | Metadata type | File name | Grounding |
|---|---|---|---|
| Custom label, custom app, custom tab, report type, flow definition, global quick action, In-App Guidance prompt | `Translations` | `translations/<locale>.translation` — e.g. `de.translation` | `api_meta.txt:135574-135575`, children at `api_meta.txt:135605-135666` |
| Object name, field label, field help, **local** picklist values, layout sections, record types, validation-rule messages, web links, sharing reasons, workflow tasks, object-scoped quick actions | `CustomObjectTranslation` | `objectTranslations/<Object>-<lang>.objectTranslation` — e.g. `Account-de.objectTranslation` | `api_meta.txt:45899-45908` |
| Values inherited from a global value set | `GlobalValueSetTranslation` | `globalValueSetTranslations/<ValueSet>-<lang>.globalValueSetTranslation` (note the `__gvs` suffix on sets created in API 57.0+) | `api_meta.txt:79446-79448`, `api_meta.txt:79419-79421` |
| Standard picklist values (Lead Source, Account Rating, …) | `StandardValueSetTranslation` | `standardValueSetTranslations/<ValueSet>-<lang>.standardValueSetTranslation` | `api_meta.txt:130842-130844` |
| Whether the Workbench and each language tier are on | `LanguageSettings` | `settings/Language.settings`, deployed as `Settings` member `Language` | `api_meta.txt:120903`, `api_meta.txt:120988-120997` |
| Record *data* (product names, territory names) | `Product2DataTranslation` and three sibling sObjects — not metadata | data load, gated by `enableDataTranslation` | `object_reference.txt:227889`, `api_meta.txt:120918-120920` |

Deployable examples of every one of these, with the `package.xml`, the deploy
order and the verification queries, are in `references/metadata-examples.md`.
The `CustomLabels` master file itself belongs to `admin/custom-label-management`;
this skill owns the `<locale>.translation` file that carries its translated
value.

### Custom Label Translations

Custom Labels (`Setup > Custom Labels`) are the standard mechanism for translatable string constants used in Apex, Visualforce, and Flow. Each label supports translations per language:

1. Create the Custom Label with the English value.
2. Open the label, click "New Local Translations/Overrides".
3. Select the language, enter the translated value.

In Apex: `System.Label.My_Label` returns the translation for the running user's language.
In Visualforce: `{!$Label.My_Label}` returns the translation.
In Flow: Use the `{!$Label.My_Label}` merge field in text elements.

### Picklist Value Translation

Picklist values are translated via Translation Workbench > Translate:
1. Select the entity type: "Picklist Value"
2. Select the object and picklist field
3. Enter translated values for each language

**Critical rule**: The picklist value API value (the stored database value) does not change when you add translations. Only the displayed label changes. Validation rules and Apex should use the API value, not the translated label.

**Classify the picklist first** — the same UI step writes to three different metadata types, and picking wrong deploys cleanly and shows nothing:

| Picklist kind | Metadata type | Deployed element |
|---|---|---|
| Local custom picklist (inline `<valueSetDefinition>`) | `CustomFieldTranslation.picklistValues` inside the object's `objectTranslation` | `<masterLabel>` + `<translation>`, both Required (`api_meta.txt:46186-46189`) |
| Field inheriting a global value set (`<valueSetName>`) | `GlobalValueSetTranslation` — once per value set, not per field | `<masterLabel>` Required, `<translation>` optional (`api_meta.txt:79466-79470`) |
| Standard picklist (Lead Source, Account Rating, …) | `StandardValueSetTranslation` — "In API version 38.0, use StandardValueSetTranslation instead" (`api_meta.txt:45982-45983`) | same `valueTranslation` shape |

`masterLabel` matches the value's **label** as shown on the setup page, not a guess at its API name (`api_meta.txt:46186-46188`). Full XML in `references/metadata-examples.md`.

### Querying Translated Labels with `toLabel()`

Translation Workbench and custom labels translate what users see in the standard UI, but query results return the master (default-language) value by default. So an LWC or Apex controller that renders values from its own SOQL — a custom console list, a report-style component, an Experience Cloud data table — will show English to a Spanish user even when the translations exist. The `toLabel()` SOQL/SOSL function returns the translation for the running user's language instead.

- Wrap the field in the `SELECT` clause: `SELECT Company, toLabel(Status) FROM Lead`.
- Supported fields: regular, multiselect, division, and currency-code picklists; data category group and data category unique-name fields; and record type names (`toLabel(RecordType.Name)`).
- Any org can use `toLabel()`; it is most useful once Translation Workbench is enabled. When a value has no translation, it falls back to the master (default-language) value, so a single query serves every language.
- The SOSL equivalent lives in the `RETURNING` clause: `FIND {Joe} RETURNING Lead(Company, toLabel(RecordType.Name))`.

Query-clause restrictions (these are the ones that fail silently or won't compile):

- **No `ORDER BY` on a `toLabel()` field** — SOQL always sorts by the picklist's defined order, never by the translated text.
- **Alias required when the same field appears twice** — e.g. returning both the raw value (for logic) and the translated value (for display): `SELECT Status, toLabel(Status) translatedStatus FROM Lead`.
- **You can filter a picklist on its label** — `WHERE toLabel(Status) = 'le Draft'` matches the translated label. But `LIKE` only matches the label text, never the API name.
- **You cannot filter on a translated record type name** — filter on the master value or the record type Id instead.
- **No `toLabel()` in a `WHERE` clause for division or currency ISO-code picklists.**

This is the display-side complement to the API-value rule above: use the API value wherever a comparison drives behavior (Apex, validation rules, routing filters), and reach for `toLabel()` only when the goal is to *show* translated values in query output.

### Experience Cloud Language Switcher

For Experience Cloud sites:
1. Enable Translation Workbench and add supported languages.
2. In Experience Builder, add the Language Switcher component to the site header.
3. In Site Settings, set the default language and enable language-specific content.
4. Translated content for Experience Cloud pages is managed via Content Management or by creating language variants of the site.

### RTL Language Support

Arabic is `ar` and Hebrew is `iw` — both **end-user** languages, not fully supported ones (`api_meta.txt:135382-135387`). Urdu (`ur`) is platform-only. For all three the guide's instruction is the same and it comes before enablement, not after: "review the right-to-left language support limitations" (`api_meta.txt:135407`, `api_meta.txt:135569`).

- Salesforce Lightning Experience supports RTL layout natively when the user's language is set to a RTL locale.
- Custom LWC components may need CSS `direction: rtl` and `text-align: start` adjustments — see `lwc/lwc-internationalization`.
- Experience Cloud sites support RTL via the site-level language setting.
- The checker flags every RTL locale it finds in a translation file, so the review prompt fires on the deploy rather than on a bug report.

---

## Common Patterns

### Bulk Export/Import via Translation Workbench Spreadsheet

**When to use:** Large orgs with hundreds of custom labels, picklist values, or field labels to translate.

**How it works:**
1. Translation Workbench > Export Translations: select the language and metadata types to export.
2. The export generates a ZIP containing a bilingual tab-delimited text file.
3. Send the file to a translation service. They fill the translation column.
4. Import via Translation Workbench > Import Translations: upload the completed file.

**Why not manual entry:** Manual entry is impractical for large translation sets. The export/import workflow enables external translation vendors and version control of translated strings.

### Validation Rule Error Message Translation

**When to use:** Validation rule error messages must display in the user's language.

**How it works:**
1. Write the validation rule error message using a Custom Label merge field: `$Label.Account_Name_Required`.
2. Create translations for that label in each supported language.
3. When the validation rule fires, the error message displays in the user's language.

**Why not hardcode the message in the formula:** A hardcoded message string in a validation rule formula cannot be translated.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Translating standard field labels | Translation Workbench > Standard Field Labels | Native mechanism |
| Translating custom field labels | Translation Workbench > Custom Field Labels | Native mechanism |
| Translating picklist values | Translation Workbench > Picklist Values | API value unchanged; only label translated |
| Translating strings in Apex/VF/Flow | Custom Labels with per-language translations | Labels are the standard translation mechanism for code strings |
| Large-scale translation (100+ items) | Export/import via Translation Workbench spreadsheet | Enables vendor translation workflow |
| Experience Cloud multi-language | Language Switcher component + Translation Workbench | Native Experience Cloud localization |
| Returning translated picklist / record-type values in a query | `toLabel(field)` in SOQL `SELECT` or SOSL `RETURNING` | Returns the running user's language; falls back to master value when untranslated |
| RTL support | Enable RTL language, test custom components | Custom LWC may need CSS direction adjustments |
| Translating a value shared by several objects | One `GlobalValueSetTranslation`, not one entry per field | `PicklistValueTranslation` covers only local custom picklists (`api_meta.txt:46182-46183`) |
| Turning the Workbench on as part of a pipeline | `settings/Language.settings`, deployed alone as `Settings:Language` first | `enableTranslationWorkbench` defaults to `false` (`api_meta.txt:120965-120967`); nothing else lands until it is true |
| Translating product or territory *names* stored on records | Data translation: `enableDataTranslation` + the `*DataTranslation` sObjects | A different feature from the Workbench; the sObjects require both flags (`object_reference.txt:227889`) |
| Removing a translation | Overwrite it with the wanted value | A blank is skipped on deploy with no error (`api_meta.txt:135789-135790`) |

---

## Recommended Workflow

1. **Classify every string before writing any XML.** Fill
   `templates/multi-language-and-translation-template.md` with the answers to
   *Questions to Ask Before Configuring* and one row per item, each row naming
   the metadata type that will carry it (see *Where each translation actually
   lives*). Strings that belong to Apex, LWC or Flow leave here for
   `admin/custom-label-management`.
2. **Enable the Workbench and the language tiers first, on their own.** Author
   `settings/Language.settings-meta.xml` from `references/metadata-examples.md`
   §1 and deploy `Settings:Language` by itself. `enableTranslationWorkbench`
   defaults to `false` and `enablePlatformLanguages` drags
   `enableEndUserLanguages` with it (`references/gotchas.md` Gotcha 8).
3. **Retrieve the metadata being translated immediately before authoring** —
   objects, fields, global value sets, labels, record types, validation rules.
   Not at the start of the vendor cycle: a stale `CustomObject` payload
   deactivates picklist values on deploy (`references/gotchas.md` Gotcha 5).
4. **Author the translation files** using the shapes in
   `references/metadata-examples.md` §2–§4 — one `objectTranslation` per object
   per language, one `globalValueSetTranslation` per shared value set per
   language, one `<locale>.translation` for everything org-level. Get the file
   names right; they are the type's primary key.
5. **Lint before every deploy.** Run
   `python3 scripts/check_multi_language_and_translation.py --manifest-dir force-app/main/default --active-locales de,fr`.
   Clear every `ERROR` (unknown locale, orphan field or picklist value, wrong
   `__gvs` naming, over-length label, `flowDefinitions` using `<name>`); triage
   `WARN` (blank translations, which deploy silently) and read the `INFO`
   coverage lines as your untranslated-item list.
6. **Deploy in the order in `references/metadata-examples.md` → "Deploy order"**,
   with `--dry-run` first. Translation metadata is a set of pointers by name, so
   it goes last, and never in the same payload as a weeks-old `objects/` folder.
7. **Verify per locale, as a user in that locale.** Run the three checks in
   `references/metadata-examples.md` → "Verification": `Translation.IsActive`
   for the language, `toLabel()` in a query run as the target user, and a
   `LanguageLocaleKey` / `LocaleSidKey` pair on the test user. A missing
   translation renders as source-language text with no error, so "it looks
   fine" is not evidence.

---

## Review Checklist

- [ ] `settings/Language.settings` sets `enableTranslationWorkbench` true, and the end-user / platform-only flags match the locale tiers actually in scope
- [ ] Every locale code appears in the guide's language lists and is `IsActive = true` on the `Translation` object
- [ ] Each translation file name matches its type's rule — `<Object>-<lang>`, `<ValueSet>-<lang>` (with `__gvs` where the set was created in API 57.0+), bare `<locale>` for `Translations`
- [ ] Every picklist classified local / global value set / standard, and translated in the matching file
- [ ] All custom labels used for user-facing strings have translations for each supported language
- [ ] Picklist values translated — API values confirmed unchanged
- [ ] Validation rule error messages translated exactly once — either a `$Label` merge field or a `ValidationRuleTranslation`, never both
- [ ] No field-label translation over 40 characters; no other label over its element's ceiling
- [ ] No blank translated element anywhere in the payload
- [ ] `scripts/check_multi_language_and_translation.py` reports 0 ERROR, and every WARN is deliberate
- [ ] Translations deployed *after* the metadata they name, and not bundled with a stale `objects/` folder
- [ ] Tested by logging in as a user whose `LanguageLocaleKey` is each supported language, with `LocaleSidKey` set to match
- [ ] Experience Cloud language switcher configured and tested (if applicable)
- [ ] RTL languages tested in relevant UI contexts — custom components checked for direction issues

---

## Salesforce-Specific Gotchas

1. **Picklist API value does NOT change with translation** — Translations only affect the displayed label. Validation rules, Apex conditions, and SOQL WHERE clauses must use the API value (the English/default language value), not the translated label.
2. **Translation Workbench export includes metadata you may not intend to translate** — The export for a language includes all translatable metadata. Review the export carefully before sending to a vendor to avoid including internal/system labels that should not change.
3. **RTL support requires more than enabling the language** — Native Lightning Experience and standard components support RTL. Custom LWC components and Experience Cloud custom templates may need explicit CSS `direction: rtl` adjustments.
4. **`toLabel()` has query-clause restrictions** — see the *Querying Translated Labels with `toLabel()`* section above for the full list (no `ORDER BY`, no record-type-name filter, no `WHERE` on division/currency ISO-code picklists, alias-when-duplicated, `LIKE` matches label only). Treat it as a display-only projection.
5. **A blank translation is skipped, not applied** — "If a translation label is left blank, it's skipped during deployment, and no error will be shown" (`api_meta.txt:135789-135790`). Blank never means "revert to English".
6. **A picklist value absent from a deployed `CustomObject` is deactivated** (`api_meta.txt:47482-47483`), which is why a stale retrieve destroys the values you were about to translate.
7. **A global value set's values cannot be translated per field** — `PicklistValueTranslation` covers only "a local, custom picklist field" (`api_meta.txt:46182-46183`).

Deeper treatment, with the deploy-order and list-view consequences, in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `settings/Language.settings-meta.xml` | Workbench and language-tier flags, deployed alone as `Settings:Language` before anything else |
| `objectTranslations/<Object>-<lang>.objectTranslation-meta.xml` | Per object per language: object name, field labels and help, local picklist values, layout sections, record types, validation messages |
| `globalValueSetTranslations/<ValueSet>-<lang>.globalValueSetTranslation-meta.xml` | Shared picklist values, once per value set per language |
| `translations/<locale>.translation-meta.xml` | Org-level: custom labels, apps, tabs, report types, flow definitions, global quick actions |
| Translation classification sheet | One row per string: source text, metadata type, target file, character ceiling, translated value, status per language |
| Per-locale verification evidence | `Translation.IsActive` query, a `toLabel()` result run as the target-language user, and the test user's `LanguageLocaleKey`/`LocaleSidKey` pair |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing any of the five files — `Language.settings`, `<locale>.translation`, `<Object>-<lang>.objectTranslation`, `<ValueSet>-<lang>.globalValueSetTranslation`, `<ValueSet>-<lang>.standardValueSetTranslation` — or the `package.xml`, the deploy order, or the three verification checks |
| `references/gotchas.md` | The translation deployed cleanly and something is still wrong — labels still English, a picklist untranslated, values vanished from a picklist, a list view returning nothing for some users, product names untranslated |
| `references/examples.md` | Three end-to-end walkthroughs — a vendor bulk round-trip, translatable validation messages, and `toLabel()` in a custom component — plus the translated-label-in-code anti-pattern |
| `references/llm-anti-patterns.md` | Reviewing translation guidance, `toLabel()` queries, or translation metadata an AI assistant produced |
| `references/well-architected.md` | Choosing between Custom Labels, Translation Workbench and a home-grown translation object, or chasing the official source behind a claim here |
| `templates/multi-language-and-translation-template.md` | Workflow step 1 — the per-string classification and the language/testing checklist, before any XML exists |
| `scripts/check_multi_language_and_translation.py` | Workflow step 5, before every deploy that touches `objectTranslations/`, `translations/`, `globalValueSetTranslations/` or `standardValueSetTranslations/` |

---

## Related Skills

- `admin/custom-label-management` — owns the `CustomLabels` master file, the 1,000-character `value` cap, and `System.Label` / `$Label` consumers; this skill owns the `<locale>.translation` file that carries the translated value
- `admin/picklist-and-value-sets` — picklist and global-value-set design, upstream of every picklist translation decision
- `admin/validation-rules` — the rules whose `errorMessage` you translate, either here via `ValidationRuleTranslation` or there via a `$Label` merge field (pick one per org)
- `admin/record-types-and-page-layouts` — the record type names and layout section names that `CustomObjectTranslation` translates
- `admin/experience-cloud-site-setup` — the site-level language settings behind the language switcher
- `security/experience-cloud-security` — Experience Cloud configuration, including language/region settings for external users
- `lwc/lwc-internationalization` — locale formatting, `direction: rtl` and RTL layout inside a component
- `devops/metadata-api-retrieve-deploy` — retrieve/deploy mechanics for the org-wide files this skill edits
