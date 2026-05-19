# Examples — Custom Label Management

Two worked scenarios plus one anti-pattern showing how to externalize
strings through Custom Labels, surface them in Apex and LWC code, and
push them through the Translation Workbench. Examples assume the org
default language is `en_US` and the target locales are Spanish (`es`)
and French (`fr`).

---

## Example 1: Replace a hard-coded Apex error and an LWC toast with a single Custom Label

**Context:** A bulk-import Apex trigger currently calls
`record.addError('Amount must be positive')` and a related LWC quote
form shows the same wording via a hard-coded `<p>` tag. Sales ops
wants the message localized for the French-Canadian rollout in Q3,
and they don't want the translator chasing the same English string in
two places.

**Step 1 — Create the label once in Setup.**

```
Setup > Custom Labels > New Custom Label
  Short Description: Validation error when amount field is non-positive
  Name:              Error_Amount_Must_Be_Positive
  Categories:        Errors;Quote
  Language:          English (default)
  Value:             Amount must be greater than zero.
```

The `Name` is the API handle — pick it carefully because Apex code
breaks if it changes. Categories are free-text and act as filterable
tags inside Translation Workbench exports; `Errors;Quote` lets the
translator slice the export by feature area.

**Step 2 — Reference from Apex.** Replace the literal in the trigger
handler:

```apex
// Before
opportunity.Amount.addError('Amount must be positive');

// After
opportunity.Amount.addError(System.Label.Error_Amount_Must_Be_Positive);
```

`System.Label.<Name>` is resolved at apex-compile time — the
compiler verifies the label exists in the org before the class will
save. Misspell the name and the class fails to compile with
`Variable does not exist: Error_Amount_Must_Be_Positive`. At runtime
the platform returns the value matched to the current user's
`LanguageLocaleKey`, falling back to the source-language value if no
translation exists for the user's locale.

**Step 3 — Reference from LWC.** The import path
`@salesforce/label/c.<Name>` uses the `c` namespace prefix for any
label in an unpackaged or unlocked-package context. For labels
delivered by a 1GP managed package, replace `c` with the package
namespace (for example `acme.Error_Amount_Must_Be_Positive`):

```javascript
// quoteForm.js
import { LightningElement } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import AMOUNT_ERROR from '@salesforce/label/c.Error_Amount_Must_Be_Positive';

export default class QuoteForm extends LightningElement {
    labels = { amountError: AMOUNT_ERROR };

    validate(amount) {
        if (amount <= 0) {
            this.dispatchEvent(new ShowToastEvent({
                title: this.labels.amountError,
                variant: 'error'
            }));
        }
    }
}
```

```html
<!-- quoteForm.html -->
<template>
    <p if:true={isInvalid}>{labels.amountError}</p>
</template>
```

Convention: collect all label imports into a single `labels` object
exposed on the component so the template stays clean and refactors
(renaming variables, swapping labels) touch one place.

**Why it works:** One label, one canonical English value, one
translator workflow. When the French-Canadian rollout arrives the
translator updates one row in Translation Workbench and both the
Apex error and the LWC toast pick up the new wording on the next
deploy/refresh — without a code change.

---

## Example 2: Add Spanish and French translations via the Translation Workbench bulk export

**Context:** The quote-form rollout above is going live in Mexico
(`es`) and France (`fr`) next sprint. Marketing has 47 customer-
facing labels (Errors, Toasts, EmailBody categories) that need
translated values, and they want to hand the work to a third-party
translation vendor rather than typing each value into Setup.

**Step 1 — Enable Translation Workbench and the target languages.**

```
Setup > Translation Workbench > Translation Settings > Enable
Setup > Translation Workbench > Supported Languages > Add
  - Spanish (es)              Active: true
  - French   (fr)             Active: true
```

Enabling a language makes it available to users (via personal
language settings) and makes its translation columns appear in the
Translation Workbench UI.

**Step 2 — Export the source file.**

```
Setup > Translation Workbench > Export
  Export Type:    Bilingual
  Languages:      Spanish, French
```

`Bilingual` produces one `.stf` file per language containing both
the source-language value and an empty target column for each
translatable element. The export is delivered by email when complete
(large orgs can take several minutes). Files are UTF-8 encoded; do
not re-save them in any other encoding or the import will reject
extended characters.

A `.stf` snippet looks like:

```
# Salesforce.com Internationalization
# Export Date: 2026-05-19
Language: es
Type: CustomLabel
--------------------------------
"Error_Amount_Must_Be_Positive","Amount must be greater than zero.",""
"Toast_Quote_Saved","Quote saved.",""
```

**Step 3 — Send to vendor, receive translated file.** The vendor
fills the third column. Final row:

```
"Error_Amount_Must_Be_Positive","Amount must be greater than zero.","El monto debe ser mayor que cero."
```

**Step 4 — Import.**

```
Setup > Translation Workbench > Import
  File: Bilingual_es_2026-05-19.stf
```

Import is delta — only rows where the translated column is filled
get applied. Existing translations not present in the file are not
deleted. The platform parses errors row-by-row and emails a summary
including any rows that failed (typical failures: encoding
corruption, source value drift since export, untranslatable
markup tags).

**Step 5 — Verify with a test user.** Create a user whose
`LanguageLocaleKey` is `es` and log in as that user. The LWC toast
and the Apex `addError` should both render the Spanish translation.
If you see English instead, the translation didn't import (re-check
the file) or the user's language is set to the default rather than
`es` — switching `Locale` alone does not change the UI language.

**Why it works:** The export/import workflow scales linearly with
label count instead of the O(N × M) clicks of manual Setup entry.
Vendors work in a familiar `.stf`/CSV-like format and Translation
Workbench enforces the file format on import — encoding errors and
malformed rows are caught at upload time, not weeks later when an
end user sees a blank string.

---

## Anti-Pattern: Hard-coding user-facing strings inline in Apex and LWC

**What practitioners do:**

```apex
// Apex trigger handler
trigger OpportunityTrigger on Opportunity (before insert, before update) {
    for (Opportunity o : Trigger.new) {
        if (o.Amount == null || o.Amount <= 0) {
            o.Amount.addError('Amount must be greater than zero');
        }
        if (o.CloseDate < Date.today()) {
            o.CloseDate.addError('Close date cannot be in the past');
        }
        if (String.isBlank(o.AccountId)) {
            o.AccountId.addError('Account is required for opportunities');
        }
    }
}
```

```html
<!-- quoteForm.html -->
<template>
    <h1>Submit a Quote</h1>
    <p>Please complete all fields marked with an asterisk.</p>
    <button>Save Draft</button>
    <button>Submit</button>
</template>
```

**What goes wrong — the i18n debt explosion:**

The team starts in English-only and ships fast. Eighteen months
later, a sales VP closes a deal in Quebec on the condition that the
internal sales UI is bilingual French. Engineering audits the
codebase and finds:

- ~400 hard-coded strings across ~120 Apex classes (`addError`,
  email body templates, exception messages re-thrown to the UI,
  `System.debug` statements that ended up customer-facing through
  a Lightning component).
- ~280 strings inline in LWC `.html` and `.js` files (button text,
  empty-state messages, toast titles, modal headers).
- ~60 strings inside Validation Rule formulas.
- ~30 strings inside Email Templates.

Every one of these needs:
1. A label created with a stable `Name`, filled `Short Description`,
   and assigned category.
2. The source code refactored to reference the label
   (`System.Label.X`, `@salesforce/label/c.X`, `$Label.X`).
3. A Spanish/French translation entered via Translation Workbench.
4. Regression-test pass per locale.

In a real org with 770 strings, this is a 4–6 week project that
must ship as one PR (intermediate states leak English text). The
risk profile during that window is enormous — any regression touches
nearly every user-facing surface — and the work would have been
trivial if labels had been used from day one.

Worse second-order effects:

- **Validation rule strings can't be reused** between the rule
  and the LWC that displays the same error inline — duplication
  silently grows.
- **Toast messages drift** as different developers paraphrase the
  same concept ("Saved", "Quote saved", "Successfully saved",
  "Saved!") — translators see four entries for the same idea and
  produce four French variants, which marketing then complains
  about as inconsistent voice.
- **Renaming the product** requires a global codebase search-and-
  replace; with labels, you change one value in Setup.

**Correct approach from day one:**

Treat any string that touches a user (toast title, modal header,
button text, error message, empty-state hint, email body) as a
candidate for a Custom Label even when the org is currently
English-only. The cost on day one is trivial — one Setup record per
string — and the future cost of i18n drops from "multi-week
project" to "one Translation Workbench export." If you must keep
some strings inline (logging, internal debug, developer-facing
error codes never shown to a user), document the boundary in
`CLAUDE.md` so it survives team turnover.
