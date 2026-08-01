# Examples — LWC Internationalization

## Example 1: A component whose "Save" button stayed English in every language

**Context:** A quick-action component rolled out to an org with English, German and
Japanese enabled. Translation Workbench was already in use for field labels and picklist
values.

**Problem:** Every string in the component was in the template. The org's translators had
nothing to translate — the strings were not in any object the Translation Workbench can
see, because they were in HTML. The first fix made it worse: a JavaScript object keyed by
language code, maintained by developers, which put translation into the deployment cycle
and out of the translators' hands.

**Solution:** Labels imported as literals, aggregated into one object for the template.

```javascript
// caseQuickAction.js
import { LightningElement } from 'lwc';
import ACTION_SAVE from '@salesforce/label/c.Action_Save';
import ACTION_CANCEL from '@salesforce/label/c.Action_Cancel';
import HEADING_NEW_CASE from '@salesforce/label/c.Heading_New_Case';
import ERROR_REQUIRED from '@salesforce/label/c.Error_Subject_Required';

export default class CaseQuickAction extends LightningElement {
    // One object keeps the template readable; the imports stay literal, which is
    // what makes them resolvable when the component is compiled.
    label = {
        save: ACTION_SAVE,
        cancel: ACTION_CANCEL,
        heading: HEADING_NEW_CASE,
        subjectRequired: ERROR_REQUIRED
    };

    subject;
    errorMessage;

    handleSave() {
        if (!this.subject) {
            this.errorMessage = this.label.subjectRequired;   // translated, not hard-coded
            return;
        }
        this.dispatchEvent(new CustomEvent('save', { detail: { subject: this.subject } }));
    }
}
```

```html
<!-- caseQuickAction.html -->
<template>
    <lightning-card title={label.heading}>
        <div class="slds-var-p-around_medium">
            <lightning-input
                label={label.subjectLabel}
                value={subject}
                onchange={handleSubjectChange}>
            </lightning-input>

            <template lwc:if={errorMessage}>
                <p class="slds-text-color_error">{errorMessage}</p>
            </template>
        </div>
        <div slot="footer">
            <lightning-button label={label.cancel} onclick={handleCancel}></lightning-button>
            <lightning-button variant="brand" label={label.save} onclick={handleSave}>
            </lightning-button>
        </div>
    </lightning-card>
</template>
```

**Why it works:** the strings now live in the one store the Translation Workbench covers, so
translating the component becomes a translator task rather than a deployment. Custom labels
hold up to 1,000 characters and an org can have up to 5,000, which is enough for the UI
strings of a large application — the frequently repeated 255-character figure is a different
limit and has pushed teams into unnecessary Custom Metadata workarounds.

**The constraint that shapes the design:** every one of those imports is a literal. There
is no runtime label lookup, so a label name cannot be assembled from a variable. Where a
value has to select between strings, import all of them and map — see anti-pattern 1.

**What is still not done:** deploying the labels creates the English values only. Until a
translated value exists for each active language every one of these renders in English, and
nothing warns you.

---

## Example 2: A currency figure that meant different amounts to different users

**Context:** An opportunity summary tile showing amount and close date, used by sales teams
in the US, Germany and Japan in a multi-currency org.

**Problem:** The template did `${opportunity.Amount.toFixed(2)}` and
`new Date(closeDate).toLocaleDateString()`. Two separate defects. The hard-coded `$`
changed what the number *meant* rather than how it looked — a German user saw a EUR amount
labelled as dollars. And `toLocaleDateString` reads the browser's locale, not the user's
Salesforce locale, so a user with a US locale setting on a German-configured laptop saw
dates that disagreed with every report they ran.

**Solution:** Let base components format, and bind the currency to the record.

```html
<!-- opportunityTile.html -->
<template>
    <lightning-card title={label.heading}>
        <dl class="slds-dl_horizontal slds-var-p-around_medium">
            <dt class="slds-dl_horizontal__label">{label.amount}</dt>
            <dd class="slds-dl_horizontal__detail">
                <!-- currency-code comes from the record, never from the template -->
                <lightning-formatted-number
                    value={amount}
                    format-style="currency"
                    currency-code={currencyIsoCode}>
                </lightning-formatted-number>
            </dd>

            <dt class="slds-dl_horizontal__label">{label.closeDate}</dt>
            <dd class="slds-dl_horizontal__detail">
                <lightning-formatted-date-time
                    value={closeDate}
                    year="numeric" month="short" day="2-digit">
                </lightning-formatted-date-time>
            </dd>

            <dt class="slds-dl_horizontal__label">{label.probability}</dt>
            <dd class="slds-dl_horizontal__detail">
                <lightning-formatted-number value={probability} format-style="percent">
                </lightning-formatted-number>
            </dd>
        </dl>
    </lightning-card>
</template>
```

```javascript
// opportunityTile.js — platform locale read only where formatting must be manual
import { LightningElement, api } from 'lwc';
import LOCALE from '@salesforce/i18n/locale';   // user's Salesforce locale, not the browser's
import DIR from '@salesforce/i18n/dir';         // 'ltr' or 'rtl'
import HEADING from '@salesforce/label/c.Opportunity_Summary_Heading';
import LABEL_AMOUNT from '@salesforce/label/c.Field_Amount';
import LABEL_CLOSE_DATE from '@salesforce/label/c.Field_Close_Date';
import LABEL_PROBABILITY from '@salesforce/label/c.Field_Probability';

export default class OpportunityTile extends LightningElement {
    @api amount;
    @api currencyIsoCode;      // from the record, in a multi-currency org
    @api closeDate;
    @api probability;

    label = {
        heading: HEADING,
        amount: LABEL_AMOUNT,
        closeDate: LABEL_CLOSE_DATE,
        probability: LABEL_PROBABILITY
    };

    // Only for a chart library or similar that cannot accept a base component.
    get axisFormatter() {
        return new Intl.NumberFormat(LOCALE, {
            style: 'currency',
            currency: this.currencyIsoCode
        });
    }

    get arrowIcon() {
        // Direction changes behaviour here, not just styling.
        return DIR === 'rtl' ? 'utility:chevronleft' : 'utility:chevronright';
    }
}
```

**Why it works:** `lightning-formatted-number` and `lightning-formatted-date-time` follow
the user's Salesforce language, locale and time zone, so the tile agrees with the reports
and list views the same user is looking at. Binding `currency-code` to the record keeps the
symbol tied to the actual currency rather than to the developer's assumption.

**Why `@salesforce/i18n/locale` and not `navigator.language`:** they answer different
questions. The browser knows what the operating system was set to; the platform knows what
the user record says, and only the second is consistent with the rest of Salesforce.

**On the RTL branch:** a chevron is one of the few cases where direction changes behaviour
rather than appearance — pointing "forward" is left in an RTL layout. Prefer
`lightning-icon` over inline SVG so directional icons mirror with the document, and reserve
an explicit `DIR` check for the cases a stylesheet cannot express.
