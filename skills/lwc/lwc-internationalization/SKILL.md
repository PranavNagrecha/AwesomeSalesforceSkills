---
name: lwc-internationalization
description: "Build LWCs that support translation, locale-aware formatting, and RTL layouts. NOT for Translation Workbench setup."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
triggers:
  - "lwc translate label"
  - "custom labels lwc"
  - "lwc internationalization rtl"
  - "rtl layout lwc"
tags:
  - i18n
  - custom-labels
  - locale
inputs:
  - "target locales"
  - "strings to translate"
outputs:
  - "component using custom labels + locale-aware components"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# LWC Internationalization

LWC internationalization uses `@salesforce/label/c.MyLabel` to import translated strings from Custom Labels and `@salesforce/i18n/locale` + `lightning-formatted-*` for locale-aware formatting. RTL is supported via the platform's dir attribute; most SLDS styles already mirror correctly. This skill walks through label extraction, locale-aware number/date/currency formatting, pluralization patterns, and RTL audit checklist that together ensure a component works the same for users in every active language and locale without string concatenation pitfalls.

## When to Use

Any LWC used in an org with multiple active locales.

Typical trigger phrases that should route to this skill: `lwc translate label`, `custom labels lwc`, `lwc internationalization rtl`, `rtl layout lwc`.

## Recommended Workflow

1. Extract every user-visible string into Custom Labels; translate via Translation Workbench.
2. Import with `import MY_LABEL from '@salesforce/label/c.MyLabel'`.
3. Format numbers/dates with `<lightning-formatted-number>`, `<lightning-formatted-date-time>` — they honor user locale.
4. Audit for hard-coded punctuation / date formats (e.g., `MM/DD/YYYY` string-concat).
5. Test in at least one LTR + RTL locale (e.g., en-US + he-IL).

## Key Considerations

- Custom Labels have a 255-char limit — long paragraphs need Custom Metadata or content service.
- Pluralization is not built-in; template a simple singular/plural Custom Label pair.
- Date formatting differences (US vs EU) silently cause misread reports.
- RTL testing reveals icon/chevron directionality bugs.

## Worked Examples (see `references/examples.md`)

- *Hardcoded strings audit* — New component 'Save' label
- *Locale-aware number* — Currency display

## Common Gotchas (see `references/gotchas.md`)

- **String concat dates** — 'MM/DD/YYYY' reads as DD/MM in EU.
- **Label over 255 chars** — Deploy fails.
- **RTL icon mirroring** — Chevron points wrong way.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Hard-coded English strings
- Concatenating dates/numbers
- Skipping RTL test

## Official Sources Used

- Lightning Web Components Developer Guide — https://developer.salesforce.com/docs/platform/lwc/guide/
- Lightning Data Service — https://developer.salesforce.com/docs/platform/lwc/guide/data-wire-service-about.html
- LWC Recipes — https://github.com/trailheadapps/lwc-recipes
- SLDS 2 — https://www.lightningdesignsystem.com/2e/
