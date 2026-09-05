# LLM Anti-Patterns — LWC Internationalization

Scope: the component-side half — importing labels, reading locale, and letting base
components format. Creating and governing the labels themselves belongs to
`admin/custom-label-management`; enabling languages and running Translation Workbench
belongs to `admin/multi-language-and-translation`. This file assumes those exist and covers
what the LWC does with them.

## Anti-Pattern 1: Building a label name at runtime

The one that compiles in every other framework and cannot work here. The label *specifier*
must be a literal in a static `import` statement; only the *value* behind it is supplied per
user. "Modules scoped with `@salesforce` add functionality to Lightning web components at
runtime" (`reference-salesforce-modules` L21986), which is exactly why one deployed bundle
can serve every language — but the module identifier itself is still fixed in source.
Assistants produce a lookup keyed by a variable — a status, a record type, a language code —
because that is how a translation dictionary works everywhere else.

**Wrong** — there is no runtime label resolution to hook into:

```javascript
import { LightningElement, api } from 'lwc';

export default class StatusBadge extends LightningElement {
    @api status;                                   // 'Open' | 'Closed' | 'Escalated'

    get statusLabel() {
        // No such API. Nothing resolves this, and nothing warns you either.
        return import(`@salesforce/label/c.Status_${this.status}`);
    }
}
```

**Right** — import every literal you might need, then map:

```javascript
import { LightningElement, api } from 'lwc';
import STATUS_OPEN from '@salesforce/label/c.Status_Open';
import STATUS_CLOSED from '@salesforce/label/c.Status_Closed';
import STATUS_ESCALATED from '@salesforce/label/c.Status_Escalated';

const STATUS_LABELS = {
    Open: STATUS_OPEN,
    Closed: STATUS_CLOSED,
    Escalated: STATUS_ESCALATED
};

export default class StatusBadge extends LightningElement {
    @api status;

    get statusLabel() {
        return STATUS_LABELS[this.status] ?? this.status;
    }
}
```

The map is the design, not a workaround: the set of translatable strings is finite and
declared in source, which is what lets the platform resolve each one to the running user's
language at runtime. If the set genuinely is not known when the component is written, the
strings are data and belong in records with a translatable field, not in labels.

Source: `@salesforce/label` scoped module, label reference format `namespace.labelName` — https://developer.salesforce.com/docs/platform/lwc/guide/create-labels.html

## Anti-Pattern 2: Assembling a sentence out of translated fragments

The habit that produces grammatically broken output in every language whose word order is
not English. Assistants concatenate a label, a value and another label because each piece is
individually translated, and the result reads as nonsense wherever the verb does not sit in
the middle.

❌ `` `${LABEL_YOU_HAVE} ${count} ${LABEL_OPEN_CASES}` `` — fixes the word order in English
and imposes it everywhere.
✅ One label per whole sentence with a placeholder, and substitute into it:

```javascript
import { LightningElement, api } from 'lwc';
import CASES_SUMMARY from '@salesforce/label/c.Cases_Open_Summary';   // 'You have {0} open cases'

export default class CaseSummary extends LightningElement {
    @api count = 0;

    get summary() {
        return CASES_SUMMARY.replace('{0}', this.formattedCount);
    }
}
```

The translator then controls where `{0}` goes in their language, which is the whole point.
Plural forms are not handled for you either — languages with more than two plural
categories need a label per form and a rule to select between them, so keep the number of
count-dependent sentences deliberately small.

## Anti-Pattern 3: Formatting dates and numbers by hand

`toLocaleString()` reads the *browser's* locale. Salesforce users have a locale on their
user record, and the two disagree constantly — a user in Frankfurt with an English (US)
locale setting, or a browser set to a language the org has never enabled. The result is a
component whose dates disagree with every report the same user runs.

❌ `new Date(value).toLocaleDateString()` and `value.toFixed(2)`.
✅ Base components, which follow the user's Salesforce settings rather than the browser's:

```html
<template>
    <lightning-formatted-date-time value={closeDate} year="numeric" month="short" day="2-digit">
    </lightning-formatted-date-time>

    <lightning-formatted-number value={amount} format-style="currency" currency-code={currencyCode}>
    </lightning-formatted-number>

    <lightning-formatted-number value={winRate} format-style="percent">
    </lightning-formatted-number>
</template>
```

Hard-coding a currency symbol has the same defect in a more damaging form: it changes the
meaning of the number rather than its appearance. Bind `currency-code` to the record's
currency in a multi-currency org instead of prefixing a symbol in the template.

UNVERIFIED (2026-09-05): the attribute names in that markup — `format-style`,
`currency-code`, and `lightning-formatted-date-time`'s `year`/`month`/`day` — come from the
Lightning Component Library, which is not in the extracted document set. The LWC Developer
Guide names the components and their purpose ("`lightning-formatted-number` displays numbers
in a specified format", `data-wire-service-about` L6630–L6631) and recommends them for
locale adaptation, but does not publish their attribute tables. Check the Component Library
before copying attribute spellings.

Source: Internationalization — the recommendation to use base components that adapt to the user's language, locale and time zone — https://developer.salesforce.com/docs/platform/lwc/guide/create-i18n.html

## Anti-Pattern 4: Reading `navigator.language` instead of the platform's locale

When formatting genuinely has to be manual, the browser is still the wrong source. The
platform exposes the running user's settings through scoped modules, and those are the ones
consistent with the rest of the org.

❌ `const locale = navigator.language;`
✅ `import LOCALE from '@salesforce/i18n/locale';` for formatting, and
`import LANG from '@salesforce/i18n/lang';` when behaviour depends on the user's language
rather than their number and date conventions. These are distinct settings on the user
record — a user can read English and format numbers German-style, and conflating them
produces a component that is correct for neither.

Source: `@salesforce/i18n` scoped module — https://developer.salesforce.com/docs/platform/lwc/guide/reference-salesforce-modules.html

## Anti-Pattern 5: Quoting the wrong custom-label limit, in either direction

Assistants routinely cite 255 characters. The Metadata API guide gives `CustomLabel.value`
as "Maximum of 1000 characters" (`api_meta` L41219–L41220); the 255-character field on
`CustomLabel` is `categories`, the list-view filter (L41191–L41193), which is a plausible
source of the confusion. Quoting 255 pushes teams into a Custom Metadata workaround for a
paragraph that would have fit.

The correction that assistants then miss is the ceiling in the other direction:
`CustomLabelTranslation.label` is "Maximum of 765 characters" (`api_meta` L135934–L135935).
A 900-character master value deploys and can never be fully translated.

❌ "Labels max out at 255 characters, so use Custom Metadata for anything longer."
❌ "Labels hold 1,000 characters, so write the whole disclaimer as one label."
✅ Write to a 765-character budget for anything that will be translated, and split longer
text across labels. Move to another store only when the text is genuinely not UI copy.

UNVERIFIED (2026-09-05): the frequently quoted "5,000 custom labels per org, managed-package
labels excluded" figure appears in Salesforce Help, which cannot be fetched, and is not
present in the Metadata API guide, the Object Reference, or the App Limits Cheat Sheet.
Do not state it as a checked number.

Source: `CustomLabel` field table — `value` Maximum of 1000 characters, `categories` Maximum of 255 characters; `CustomLabelTranslation.label` Maximum of 765 characters — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

## Anti-Pattern 6: Treating right-to-left as a CSS problem to solve later

RTL is deferred because it looks like styling, and then it fails on the parts that are not
styling: inline SVG that does not mirror, chevrons and arrows that now point away from the
direction of travel, and any layout built with hard-coded `left`/`right` rather than logical
properties.

❌ `margin-left: 0.5rem` throughout, plus an inline `<svg>` arrow.
❌ `[dir="rtl"] .thing { ... }` as the fix — that attribute selector "only works in synthetic
shadow DOM" (`create-components-shadow-dom` L3517), so it stops applying the moment the
component runs under a native-shadow subtree, with no error.
✅ Logical properties (`margin-inline-start`, `padding-inline-end`, `text-align: start`) so
no direction selector is needed, `:dir()` where the browser supports it, `lightning-icon`
rather than inline SVG so directional icons mirror with the document, and
`import DIR from '@salesforce/i18n/dir';` where a behaviour — not just a style — has to
branch on direction. Then actually load the component with an RTL language enabled; this is
not a defect class that survives code review, only testing.

Source: mixed shadow mode and the `[dir=""]` selector — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-shadow-dom.html

## Anti-Pattern 7: Shipping labels without checking they are translated

Deploying a label creates the English value. It does not create a translation, and an
untranslated label falls back to English silently — so a "fully translated" component quietly
shows English to exactly the users the work was for. Assistants stop at the import, because
that is the part that lives in the repo.

❌ Treat "label exists and deploys" as done.
✅ Confirm the language is enabled in the org and that a `<customLabels>` entry exists for
each label in each `<locale>.translation` file — the master values and the translations are
separate metadata in separate folders (`api_meta` L41165–L41167). Then verify by switching a
test user's language; "users can set their individual language, locale, and time zone on
their personal settings pages" (`create-i18n` L3794). Every fallback in this system is a
silent one, so English on screen is the only signal you will get.

UNVERIFIED (2026-09-05): the Translation Workbench export/import workflow itself — enabling
it, assigning translators, the bilingual export file — is documented only in Salesforce
Help, which cannot be fetched. The declarative side is owned by
`admin/multi-language-and-translation`; do not restate its mechanics from here.

## Anti-Pattern 8: Asserting on English text in a Jest test

The test that is green for the wrong reason. Assistants write
`expect(el.textContent).toBe('Save')` because that is what the label says in the org — but
Jest never reaches the org. "In Jest tests, we use a jest-transformer to convert the
`@salesforce/label` import statement into a variable declaration. The value is set to the
label path. By default, `myImport` is assigned a string value of `c.specialLabel`"
(`unit-testing-using-jest-patterns` L12650).

❌ `expect(button.label).toBe('Save');` — fails, so the assistant "fixes" it to
`expect(button.label).toBe('c.Action_Save');`, which passes and proves nothing about
translation.
✅ Mock the import and assert on the fixture, which is the guide's own instruction — "you
can use `jest.mock()` to provide your own value for an import" (L12650):

```javascript
jest.mock(
    '@salesforce/label/c.Action_Save',
    () => ({ default: 'FIXTURE_SAVE' }),
    { virtual: true }
);
```

Do the same for `@salesforce/i18n/locale`, `currency` and `timeZone`, or a currency
assertion passes on the author's machine and fails in CI. The rest of the Jest harness —
config, wire mocks, coverage — belongs to `lwc/lwc-testing`.

Source: Jest Test Patterns and Mock Dependencies — https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-patterns.html
