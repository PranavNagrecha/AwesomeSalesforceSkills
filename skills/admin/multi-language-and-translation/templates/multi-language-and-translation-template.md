# Multi-Language and Translation — Setup Checklist

## Languages to Support

Tier decides how much Salesforce translates for free, and whether enabling one
language enables seventeen others. Codes and tiers: `api_meta.txt:135356-135572`.

| Language | Locale Code | Tier (fully supported / end-user / platform-only) | `Translation.IsActive` | Status |
|---|---|---|---|---|
| ___ | ___ | ___ | Yes / No | Enabled / In Progress |

## Translation Workbench Setup

- [ ] `settings/Language.settings-meta.xml` authored, with `enableTranslationWorkbench` = `true`
- [ ] `enableEndUserLanguages` = ___ (required if any locale above is end-user tier)
- [ ] `enablePlatformLanguages` = ___ (setting this true also forces `enableEndUserLanguages` true)
- [ ] `useLanguageFallback` = ___ (default `true`; leaving it on is why missing translations render as source-language text with no error)
- [ ] `enableDataTranslation` = ___ (record data, a separate feature — only if product/territory *names* are in scope)
- [ ] Deployed alone as `Settings:Language` before any translation file
- [ ] Default language confirmed (org default = ___ )

## String Classification (fill before writing any XML)

One row per translatable item. The metadata type column decides the file, and
the file name is part of the contract.

| Source string / item | Metadata type | Target file | Char ceiling | Owner | es | fr | de |
|---|---|---|---|---|---|---|---|
| ___ | CustomLabel / field label / local picklist / global value set / standard picklist / validation message / layout section | `translations/es.translation` or `objectTranslations/Account-es.objectTranslation` or `globalValueSetTranslations/X__gvs-es.globalValueSetTranslation` | 40 / 80 / 765 | ___ | ☐ | ☐ | ☐ |

## Components to Translate

### Custom Labels
- [ ] All user-facing strings in Apex/Visualforce/Flow use Custom Labels (not hardcoded)
- [ ] Translations entered for each label per supported language
- [ ] Bulk export/import used for >20 labels

### Field Labels
- [ ] Custom field labels translated via Translation Workbench > Custom Field Labels
- [ ] Section names on page layouts translated

### Picklist Values
- [ ] Every picklist classified: local custom / inherits a global value set / standard
- [ ] Local values translated in the object's `objectTranslation` (`masterLabel` matches the value's setup-page label)
- [ ] Global-value-set values translated once in `globalValueSetTranslations/<ValueSet>-<lang>` — with the `__gvs` suffix if the set was created in API 57.0 or later
- [ ] Standard picklist values translated in `standardValueSetTranslations/<ValueSet>-<lang>`
- [ ] Confirmed: API values (stored values) are unchanged — only display labels translated
- [ ] Apex/SOQL code confirmed to use API values, not translated labels

### List Views and Report Filters
- [ ] List views using `contains` / `startsWith` audited and given an explicit `<language>` — those filters become language-bound once the Workbench is on
- [ ] Report filters on picklists confirmed to use API values

### Validation Rule Messages
- [ ] One mechanism chosen org-wide: `$Label.*` merge field **or** `ValidationRuleTranslation.errorMessage` — never both for the same rule
- [ ] Chosen mechanism recorded here: ___

### Experience Cloud (if applicable)
- [ ] Language Switcher component added to site header
- [ ] Site default language configured
- [ ] Content tested in each supported language via language switcher

## Pre-Deploy Gate

- [ ] `python3 scripts/check_multi_language_and_translation.py --manifest-dir <dir> --active-locales <codes>` reports 0 ERROR
- [ ] Every WARN reviewed — blank translated elements are silent no-ops on deploy
- [ ] INFO coverage lines triaged into the classification table above
- [ ] Metadata being translated retrieved *immediately* before this deploy, not weeks ago
- [ ] Deploy split: translation folders only, no stale `objects/` or `globalValueSets/` in the same payload
- [ ] `--dry-run` clean against the target org

## Testing Checklist

For each supported language:
- [ ] `SELECT Language, IsActive FROM Translation` confirms the language is active
- [ ] Test user with correct `LanguageLocaleKey` **and** a matching `LocaleSidKey` (language and locale are different settings)
- [ ] Logged in as test user — field labels display in target language
- [ ] Picklist values display in target language, and `toLabel()` in a query run as that user returns the translation
- [ ] Field-level help text checked, not just labels
- [ ] Validation rule fires in target language — error message is in target language
- [ ] Custom Labels display in target language in Apex/VF/Flow contexts
- [ ] Layout section headings and record type names checked on a real record page
