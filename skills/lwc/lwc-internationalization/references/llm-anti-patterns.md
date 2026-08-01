# LLM Anti-Patterns — LWC Internationalization

Scope: the component-side half — importing labels, reading locale, and letting base
components format. Creating and governing the labels themselves belongs to
`admin/custom-label-management`; enabling languages and running Translation Workbench
belongs to `admin/multi-language-and-translation`. This file assumes those exist and covers
what the LWC does with them.

## Anti-Pattern 1: Building a label name at runtime

The one that compiles in every other framework and cannot work here. `@salesforce/label`
imports are resolved when the component is compiled, so the label name must be a literal in
an `import` statement. Assistants produce a lookup keyed by a variable — a status, a record
type, a language code — because that is how a translation dictionary works everywhere else.

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
known at build time, which is exactly the property that lets the platform ship the right
translation to each user. If the set genuinely is not known at build time, the strings are
data and belong in records with a translatable field, not in labels.

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

## Anti-Pattern 5: Quoting the wrong custom-label limit

Assistants routinely cite 255 characters, which is a text-field limit, not this one. Custom
labels can be up to **1,000 characters**, and an org can have up to **5,000** of them
(labels from managed packages do not count against that). Getting this wrong pushes teams
into inventing a Custom Metadata workaround for paragraphs that would have fit, and losing
Translation Workbench support in the process.

❌ "Labels max out at 255 characters, so use Custom Metadata for anything longer."
✅ Use labels up to their real 1,000-character ceiling, because that is the only string
store the Translation Workbench covers. Move to another store only past that limit, and
accept that translation then becomes your problem.

Source: Custom Labels — up to 5,000 labels per org, up to 1,000 characters each — https://help.salesforce.com/s/articleView?id=platform.cl_about.htm&type=5

## Anti-Pattern 6: Treating right-to-left as a CSS problem to solve later

RTL is deferred because it looks like styling, and then it fails on the parts that are not
styling: inline SVG that does not mirror, chevrons and arrows that now point away from the
direction of travel, and any layout built with hard-coded `left`/`right` rather than logical
properties.

❌ `margin-left: 0.5rem` throughout, plus an inline `<svg>` arrow.
✅ Logical properties (`margin-inline-start`) so the platform's direction handling does the
work, `lightning-icon` rather than inline SVG so directional icons mirror with the document,
and `import DIR from '@salesforce/i18n/dir';` where a behaviour — not just a style — has to
branch on direction. Then actually load the component with an RTL language enabled; this is
not a defect class that survives code review, only testing.

## Anti-Pattern 7: Shipping labels without checking they are translated

Deploying a label creates the English value. It does not create a translation, and an
untranslated label falls back to English silently — so a "fully translated" component quietly
shows English to exactly the users the work was for. Assistants stop at the import, because
that is the part that lives in the repo.

❌ Treat "label exists and deploys" as done.
✅ Confirm the language is enabled in the org, that a translated value exists for each label
in each active language, and that the translation was exported and re-imported through the
Translation Workbench rather than typed once into the UI. Then verify by switching a test
user's language — every fallback in this system is a silent one, so English on screen is
the only signal you will get.
