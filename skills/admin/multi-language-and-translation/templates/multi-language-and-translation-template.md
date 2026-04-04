# Multi-Language and Translation — Setup Checklist

## Languages to Support

| Language | Locale Code | Status |
|---|---|---|
| ___ | ___ | Enabled / In Progress |

## Translation Workbench Setup

- [ ] Translation Workbench enabled: Setup > Translation Workbench > Translation Settings > Enable
- [ ] Each language added as Supported Language with active status
- [ ] Default language confirmed (org default = ___

## Components to Translate

### Custom Labels
- [ ] All user-facing strings in Apex/Visualforce/Flow use Custom Labels (not hardcoded)
- [ ] Translations entered for each label per supported language
- [ ] Bulk export/import used for >20 labels

### Field Labels
- [ ] Custom field labels translated via Translation Workbench > Custom Field Labels
- [ ] Section names on page layouts translated

### Picklist Values
- [ ] Picklist values translated via Translation Workbench > Picklist Values
- [ ] Confirmed: API values (stored values) are unchanged — only display labels translated
- [ ] Apex/SOQL code confirmed to use API values, not translated labels

### Validation Rule Messages
- [ ] All validation rule error messages reference `$Label.*` not hardcoded strings

### Experience Cloud (if applicable)
- [ ] Language Switcher component added to site header
- [ ] Site default language configured
- [ ] Content tested in each supported language via language switcher

## Testing Checklist

For each supported language:
- [ ] Test user with correct `LanguageLocaleKey` set
- [ ] Logged in as test user — field labels display in target language
- [ ] Picklist values display in target language
- [ ] Validation rule fires in target language — error message is in target language
- [ ] Custom Labels display in target language in Apex/VF/Flow contexts
