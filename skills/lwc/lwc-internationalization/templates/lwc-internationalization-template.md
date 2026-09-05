# LWC Internationalization — Work Template

## Scope

**Skill:** `lwc-internationalization`
**Component:** `c-________`
**Request summary:**

## Language Matrix

| Language | Locale code | Enabled in target org? | RTL? | Translator / owner |
|---|---|---|---|---|
|  |  |  |  |  |

- Does this component also run on an LWR Experience Cloud site? ☐ yes ☐ no
  (if yes: `currency`, `number.currencySymbol`, `number.currencyFormat` are unsupported and
  `timeZone` comes from the browser — see `references/gotchas.md` Gotcha 8)
- Is the org multi-currency? ☐ yes ☐ no

## String Inventory

One row per user-visible string. A "sentence" is anything with a value embedded in it and
gets a single label with a `{0}` placeholder, never concatenated fragments.

| Label `fullName` | Kind (term / sentence) | Master value | Chars | ≤ 765? | Translated in |
|---|---|---|---:|---|---|
|  |  |  |  |  |  |

Anything in the 766–1,000 band deploys as a master value and can never be fully translated
(`CustomLabelTranslation.label` maximum is 765). Split it before writing the component.

## Field Type Split

The single most common defect in this domain. Fill this in before writing a formatter.

| Field | Type (Date / DateTime / Currency / Number / Percent) | Rendered by | Time zone used |
|---|---|---|---|
|  |  | `lightning-formatted-*` or `Intl.*` | user's / `'UTC'` / n/a |

- Every `Date` row must say `'UTC'`.
- Every Currency row must say where the currency code comes from: the record's
  `CurrencyIsoCode`, or `@salesforce/i18n/currency` as the fallback.

## i18n Properties Imported

☐ `lang` ☐ `dir` ☐ `locale` ☐ `currency` ☐ `timeZone` ☐ `firstDayOfWeek`
☐ other: ____________ (must be on the enumerated list in `references/code-examples.md`)

Where is `<div lang={lang} dir={dir}>` bound? ____________

## RTL Plan

- Stylesheet uses logical properties only: ☐
- No `[dir="rtl"]` selector anywhere (fails in native shadow DOM): ☐
- Directional icons come from `lightning-icon`, not inline SVG: ☐
- Behaviour branches on `DIR` where mirroring is not enough: ____________

## Test Plan

| Assertion | Mocked label / property | Fixture value |
|---|---|---|
|  |  |  |

- No assertion reads English text (an unmocked label evaluates to `c.LabelName`): ☐
- `locale`, `currency` and `timeZone` are pinned so CI matches the author's machine: ☐

## Deployment

- `package.xml` includes `CustomLabel` (singular, named members): ☐
- `package.xml` includes `Translations` for every active language: ☐
- Deploy order: labels → bundle → translations: ☐

## Checklist

- [ ] Questions to Ask table answered
- [ ] `references/gotchas.md` reviewed, especially 2, 8 and 10
- [ ] No LLM anti-pattern triggered
- [ ] `scripts/check_lwc_internationalization.py --manifest-dir <source> --strict` clean
- [ ] Verified as a user in a target language, including one RTL language

## Notes
