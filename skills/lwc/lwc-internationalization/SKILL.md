---
name: lwc-internationalization
description: "Build LWCs with translation, locale-aware formatting, and RTL layouts. Triggers: LWC i18n, custom labels LWC, RTL layout, @salesforce/label import, @salesforce/i18n locale, timeZone, currency, Intl.NumberFormat in LWC, Translations metadata, date off by one day, mock a label in Jest. NOT for Translation Workbench admin setup — use admin/custom-label-management. NOT for org-wide multi-language config — use admin/multi-language-and-translation."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
triggers:
  - "lwc translate label"
  - "custom labels lwc"
  - "lwc internationalization rtl"
  - "rtl layout lwc"
  - "import a custom label into a lightning web component"
  - "my lwc shows english for german users"
  - "format a currency amount in the user's locale in lwc"
  - "date shows a day earlier in my lwc"
  - "why does tolocaledatestring show the wrong format in lwc"
  - "mock a custom label in a jest test"
  - "deploy custom label translations with package.xml"
  - "custom label not found when deploying lwc"
  - "make my lwc layout work in arabic or hebrew"
  - "picklist label not translated in my lwc"
  - "custom label value too long to deploy"
  - "get the user's time zone in a lightning web component"
tags:
  - i18n
  - custom-labels
  - locale
inputs:
  - "target locales"
  - "strings to translate"
  - "which fields are Date versus DateTime versus Currency"
  - "whether the component also runs on an LWR Experience Cloud site"
outputs:
  - "component using custom labels + locale-aware components"
  - "CustomLabels and Translations metadata plus the package.xml that deploys both"
  - "Jest suite with mocked labels and a pinned locale"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# LWC Internationalization

`@salesforce/label/c.MyLabel` imports a translated string; `@salesforce/i18n/*` exposes the
running user's language, direction, locale, currency and time zone; `lightning-formatted-*`
and `Intl.*` turn a raw value into something that user can read. This skill covers the
component half: which value comes from the user and which from the record, where a base
component beats `Intl`, why a Date field loses a day and a DateTime field does not, and how
to test any of it when Jest never sees the org.

---

## Before Starting

Gather this context before writing markup:

- Which languages are actually enabled in the target org, and is any of them right-to-left?
- Which of the values on screen are `Date`, which are `DateTime`, and which are Currency?
- Does this component also have to run on an LWR Experience Cloud site?
- Is the org multi-currency, and does the record carry a `CurrencyIsoCode`?

---

## Questions to Ask Before Configuring

Each question decides a branch that is expensive to reverse, and each traces to a gotcha in
`references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which of these fields is a `Date` and which is a `DateTime`?" | A `Date` has no time component, so formatting it in the user's time zone renders the previous day for anyone west of UTC — the same code that is correct for the `DateTime` next to it (Gotcha 10) | The list of fields that must be formatted with `timeZone: 'UTC'` while still taking the locale from the user |
| "Is the org multi-currency, and does the record carry its own `CurrencyIsoCode`?" | `@salesforce/i18n/currency` returns the *user's* currency code (`create-i18n` L3807); using it for a record amount changes what the number means, not how it looks | Whether the currency binds to the record or to the user, decided once rather than per component |
| "Will any of this text be translated, and how long is the longest string?" | The master value caps at 1,000 characters but a translation caps at 765 (Gotcha 2) — the 766–1,000 band deploys and can never be fully translated | A 765-character budget, and a decision to split long help text before a translator hits the wall |
| "Which languages are enabled, and is one of them right-to-left?" | RTL fails on inline SVG, directional icons and hard-coded `left`/`right`; the obvious `[dir="rtl"]` CSS fix works only in synthetic shadow DOM (Gotcha 3) | A logical-properties stylesheet and a JS branch on `@salesforce/i18n/dir`, rather than an RTL pass bolted on later |
| "Does this component also run on an LWR Experience Cloud site?" | On LWR, `currency`, `number.currencySymbol` and `number.currencyFormat` are unsupported and `timeZone` comes from the browser (Gotcha 8) | Either "internal only", or a design that reads currency from the record and does not trust `timeZone` |
| "Does any sentence embed a number, name or date?" | Concatenated fragments fix English word order everywhere; one label with a `{0}` placeholder lets the translator move it (anti-pattern 2) | The list of whole-sentence labels, written before the strings are hard-coded into a getter |
| "Who owns the labels — this repo, or the admins?" | Master values and translations are separate metadata in separate folders, and `CustomLabels` cannot be retrieved by name or with a namespace (Gotchas 4, 5, 6) | A source-of-truth decision, and a `package.xml` that ships `CustomLabel` *and* `Translations` in the same change |

What a proper configuration adds over just doing it: every user-visible string reaches a
translator instead of a developer, every formatted value agrees with the reports and list
views the same user is looking at, and the three failures that are otherwise invisible —
an untranslated label, a date shifted by a day, a translation that will not fit — are
caught by the checker and the Jest suite before anyone in the target language sees them.

---

## Adoption Signals

Any LWC used in an org with multiple active locales.

- Required when string concatenation, plural forms, or relative-time formatting hard-codes English in the template.
- Required when the layout must support RTL languages (Arabic, Hebrew) — bidirectional CSS is non-trivial.
- Required when the org is multi-currency and the component renders an amount.
- Required when the same bundle is reused on an LWR Experience Cloud site.

---

## Core Concepts

### Two Modules, Two Different Questions

`@salesforce/label/*` answers "what does this string say in the running user's language".
`@salesforce/i18n/*` answers "what conventions does the running user read numbers, dates and
text direction by". They are independent settings on the user record — a user can read
English and format numbers German-style — so conflating them produces a component correct
for neither.

### The Specifier Is Static, the Value Is Not

The module identifier must be a literal in a static `import`. The value behind it is
supplied per user at runtime, which is why one deployed bundle serves every language. That
split is the whole design; trying to build a label name from a variable defeats the static
half and gets you nothing dynamic in return.

### Base Component First, `Intl` Second, Raw Never

The guide's own recommendation is `lightning-formatted-*` and `lightning-input`, which read
the platform settings themselves. `Intl.DateTimeFormat` / `Intl.NumberFormat` with the
imported `locale` is the documented fallback for what a base component cannot host — a
chart axis, an `aria-label`, a string passed to a third-party library.
`toLocaleDateString()` with no argument is neither: it reads the browser.

### The Enumerated i18n Property Set

`lang`, `dir`, `locale`, `defaultCalendar`, `defaultNumberingSystem`, `calendarData`,
`currency`, `firstDayOfWeek`, `isEasternNameStyle`, `common.calendarData`, `common.digits`,
the seven `dateTime.*` format patterns, the fourteen `number.*` symbols and patterns,
`showJapaneseCalendar`, and `timeZone`. All are documented in
`references/code-examples.md` with their sample values, and all are returned for the current
user. Anything not on that list does not exist as an `@salesforce/i18n` identifier.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Rendering a `DateTime` field | `<lightning-formatted-date-time>` | Reads the user's language, locale and time zone without you wiring it |
| Rendering a `Date` field | `Intl.DateTimeFormat(LOCALE, { timeZone: 'UTC' })` | The value has no instant; the user's time zone would shift the day |
| Rendering a currency amount | `<lightning-formatted-number format-style="currency" currency-code={recordCurrency}>` | The record's currency, not the user's, is what the number means |
| Formatting for a chart axis or `aria-label` | `Intl.NumberFormat(LOCALE, …)` | Nothing there can host a base component |
| A sentence containing a value | One label with `{0}`, then `.replace()` | The translator controls word order |
| A string that varies by status or record type | Import every literal, map by key | There is no runtime label lookup to hook |
| Direction-dependent styling | CSS logical properties | Works in both shadow modes; `[dir]` selectors do not |
| Direction-dependent *behaviour* | Branch in JS on `@salesforce/i18n/dir` | An icon that points "forward" points left in RTL |

---

## Recommended Workflow

1. **Answer the Questions table**, then write the string inventory: every user-visible
   string, tagged as a whole sentence or a standalone term, with its longest expected
   translation. Anything over 765 characters gets split now, not later.
2. **Create the labels first.** Copy the `CustomLabels` block from
   `references/code-examples.md` § 5 — `fullName`, `language`, `protected`,
   `shortDescription`, `value` are all Required — and add a `<customLabels>` entry to each
   `translations/<locale>.translation-meta.xml` (§ 6) in the same commit.
3. **Build the bundle from `references/code-examples.md` §§ 1–4.** Start from
   `templates/lwc/component-skeleton/`; the i18n-specific parts are the literal label
   imports, the `<div lang={lang} dir={dir}>` wrapper, the `openedOn` / `lastModifiedText`
   split between `timeZone: 'UTC'` and the user's zone, and the logical-properties CSS.
   Check the base-component path before reaching for `Intl`.
4. **Write the Jest suite from § 7**, mocking every label with
   `jest.mock(..., { virtual: true })` and pinning `@salesforce/i18n/locale`, `dir`,
   `currency` and `timeZone`. Copy `templates/lwc/jest.config.js` and add the i18n mapper
   from § 8. Harness questions beyond this belong to `lwc/lwc-testing`.
5. **Run the checker**:
   `python3 skills/lwc/lwc-internationalization/scripts/check_lwc_internationalization.py --manifest-dir force-app/main/default --strict`
   then `npx sfdx-lwc-jest`. Fill in `templates/lwc-internationalization-template.md` as you go.
6. **Deploy in the order in § 10** — labels, then bundle, then translations — using the
   `package.xml` in § 9. Note the singular `CustomLabel` type; the plural one with named
   members retrieves nothing.
7. **Verify as a user in the target language** using the six steps in § 11, including the
   Pacific-time-zone check for the `Date` field and one right-to-left language. Every
   failure in this domain is silent, so nothing else counts as evidence.

---

## Review Checklist

- [ ] No literal user-facing text node remains in any HTML template.
- [ ] Every `@salesforce/label` import resolves to a label defined in the repo.
- [ ] Every sentence containing a value is one label with a `{0}` placeholder.
- [ ] `Date` fields format with `timeZone: 'UTC'`; `DateTime` fields format in the user's zone.
- [ ] Currency binds to the record's `CurrencyIsoCode` where the org is multi-currency.
- [ ] No `toLocaleDateString()` / `toLocaleString()` without an explicit locale.
- [ ] The stylesheet uses logical properties, not `left`/`right` or `[dir="rtl"]`.
- [ ] `lang` and `dir` are bound onto a wrapper element.
- [ ] Every label has a `<customLabels>` entry in every active `<locale>.translation` file.
- [ ] No master label value sits in the 766–1,000 character band.
- [ ] The Jest suite mocks its labels and pins its locale; no assertion on English text.
- [ ] `package.xml` ships `CustomLabel` (singular, named members) and `Translations`.
- [ ] `scripts/check_lwc_internationalization.py --manifest-dir <source> --strict` is clean.

---

## Common Gotchas (see `references/gotchas.md`)

- **Two ceilings** — a label value holds 1,000 characters; its translation holds 765.
- **`CustomLabels` by name retrieves nothing** — the plural type takes only `*`.
- **No namespace retrieval** — `CustomLabels` cannot be retrieved with a namespace at all.
- **Labels ship without translations** — separate type, separate folder, no warning.
- **Jest labels are paths** — an unmocked label evaluates to `c.MyLabel`, not its text.
- **LWR drops three properties** — `currency`, `currencySymbol`, `currencyFormat`.
- **Picklist `label` is translated; `value` never is** — never compare on the label.
- **Date-only fields lose a day** — the user's time zone shifts an assumed UTC midnight.
- **`[dir]` selectors fail in native shadow DOM** — use logical properties or `:dir()`.
- **`lang` and `dir` are yours to bind** — the platform does not stamp them for you.

---

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Building a label name at runtime from a variable
- Assembling a sentence out of translated fragments
- Formatting dates and numbers by hand with `toLocaleString()`
- Reading `navigator.language` instead of `@salesforce/i18n/locale`
- Quoting 255 (or 1,000) as the label limit that matters
- Treating right-to-left as a CSS problem to solve later
- Shipping labels and calling the component translated
- Asserting on English text in a Jest test

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Component bundle | HTML, JS, CSS and `js-meta.xml` using label imports, i18n properties and locale-aware formatting |
| Label metadata | `CustomLabels` file with the master values, plus one `Translations` file per active language |
| Jest suite | Tests with mocked labels and a pinned locale, currency and time zone |
| Deploy manifest | `package.xml` covering `CustomLabel`, `Translations` and `LightningComponentBundle`, with the deploy order |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are writing the bundle: full component (html/js/css/meta), `CustomLabels` XML, a German `Translations` file, the Jest suite with label and i18n mocks, `jest.config.js`, `package.xml`, deploy order, and six verification steps |
| `references/gotchas.md` | Something renders in English, on the wrong day, or in the wrong direction, and nothing errored — the eleven silent failures with their grounded citations |
| `references/examples.md` | You want the narrative of two real defects: a component no translator could see, and a currency figure that meant different amounts to different users |
| `references/llm-anti-patterns.md` | You are reviewing generated i18n code, or want the detection hints the checker implements |
| `references/well-architected.md` | You need the pillar framing, the sourced claims list, and the explicit list of sources this skill could *not* verify |
| `templates/lwc-internationalization-template.md` | You are recording the string inventory, the field-type split, and the language matrix for review |
| `scripts/check_lwc_internationalization.py` | Before deploy: run it with `--manifest-dir` over the source tree, `--strict` in CI |

---

## Related Skills

- `admin/custom-label-management` - owns the declarative side: creating, categorising and governing labels in Setup.
- `admin/multi-language-and-translation` - owns enabling languages and running the Translation Workbench; this skill assumes both are done.
- `lwc/lwc-accessibility` - owns `lang` semantics for screen readers and the rest of the accessibility surface; use alongside this skill's `dir` handling.
- `lwc/lwc-testing` - owns the Jest harness, config and wire mocks; this skill covers only the label and locale mocks.
- `lwc/lwc-forms-and-validation` - use when the translated strings are field labels and validation messages in a form.
- `lwc/lwc-data-table` - owns column-level formatting and cell types; use it for a table rather than formatting each cell here.
- `lwc/lwc-css-and-styling` - use for the styling mechanics behind the logical-properties stylesheet.
