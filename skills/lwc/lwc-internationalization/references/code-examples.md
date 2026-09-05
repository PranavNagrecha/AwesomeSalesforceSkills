# Code Examples — LWC Internationalization

A complete, deployable bundle plus the label and translation metadata it depends on.
Everything here is one artifact set: `localizedCaseSummary` renders a heading, a
count sentence, a date-only field, a date/time field and a currency amount, all in
the running user's language, locale, time zone and currency, and it lays out
correctly in a right-to-left language.

Start from `templates/lwc/component-skeleton/` and copy `templates/lwc/jest.config.js`
rather than retyping the boilerplate; the files below are the i18n-specific deltas.

## How to read it

- **Labels are imported by literal specifier.** `@salesforce/label/c.Name` for a label in
  the default namespace, `@salesforce/label/ns.Name` for one in a managed package — the
  guide uses the `namespace.labelName` format "because it's the same format used in managed
  packages, in Visualforce, and in other Salesforce technologies" (`lwc_guide create-labels`
  L3768). Templates reference the imported value with the ordinary `{property}` syntax
  (L3770).
- **`@salesforce` modules resolve at runtime, per user.** "Modules scoped with `@salesforce`
  add functionality to Lightning web components at runtime"
  (`lwc_guide reference-salesforce-modules` L21986). One deployed bundle therefore serves
  every language; what is fixed at build time is the *specifier*, not the value.
- **Every i18n property used below is one the guide enumerates**: `lang`, `dir`, `locale`,
  `currency`, `timeZone`, `firstDayOfWeek` (`lwc_guide create-i18n` L3801–L3835). Values
  "are returned for the current user" (L3799).
- **Base components first, `Intl` second.** The guide's own recommendation is base
  components "as they adapt automatically to the language, locale, and time zone settings
  of the Salesforce org they run in" (L3795); it offers `Intl.DateTimeFormat` /
  `Intl.NumberFormat` with the imported `locale` for the cases a base component cannot
  cover (L3841, L3844–L3847). The bundle shows both, and says which is which.
- **`dir` and `lang` are not applied for you.** "To bind internationalization properties to
  HTML attributes, store them as private properties in your component's JavaScript file"
  (L3848). The wrapper `<div lang={lang} dir={dir}>` below is that binding.
- **The label file lives anywhere under the package directory.** "In a Salesforce DX
  project, label files can live in any subdirectory of `force-app/main/default`" (L3773).
- **Master values and translations are separate metadata.** "Master custom label values are
  stored in the `CustomLabels.labels` file. Translations for custom labels can be retrieved
  through `Translations` in Metadata API. Translations are stored in files under the
  `translations` folder with the name format of `localeCode.translation`"
  (`api_meta` L41165–L41167).

---

## 1. `force-app/main/default/lwc/localizedCaseSummary/localizedCaseSummary.html`

```html
<template>
    <!-- lang and dir are bound explicitly; the platform does not stamp them on your
         markup (lwc_guide create-i18n L3848-L3849). -->
    <div lang={lang} dir={dir} class="summary">
        <lightning-card title={label.heading} icon-name="standard:case">

            <div class="slds-var-p-around_medium">
                <p class="summary__count">{countSentence}</p>

                <dl class="slds-dl_horizontal">
                    <dt class="slds-dl_horizontal__label">{label.opened}</dt>
                    <dd class="slds-dl_horizontal__detail">
                        <!-- Date-only field. Formatted in JS so the formatter can be
                             pinned to UTC; see openedOn in the JS file. -->
                        <span>{openedOn}</span>
                    </dd>

                    <dt class="slds-dl_horizontal__label">{label.lastUpdated}</dt>
                    <dd class="slds-dl_horizontal__detail">
                        <!-- DateTime field. The base component reads the user's
                             settings itself, so prefer it here. -->
                        <lightning-formatted-date-time
                            value={lastModifiedDateTime}>
                        </lightning-formatted-date-time>
                    </dd>

                    <dt class="slds-dl_horizontal__label">{label.estimatedCost}</dt>
                    <dd class="slds-dl_horizontal__detail">
                        <!-- Preferred path: the base component. -->
                        <lightning-formatted-number
                            value={estimatedCost}
                            format-style="currency"
                            currency-code={resolvedCurrency}>
                        </lightning-formatted-number>
                    </dd>

                    <dt class="slds-dl_horizontal__label">{label.estimatedCost}</dt>
                    <dd class="slds-dl_horizontal__detail">
                        <!-- Fallback path, for a chart axis or an aria-label that
                             cannot host a base component. -->
                        <span data-id="cost-intl">{formattedCost}</span>
                    </dd>
                </dl>

                <lightning-button
                    label={label.refresh}
                    icon-name={forwardIcon}
                    icon-position="right"
                    onclick={handleRefresh}>
                </lightning-button>
            </div>

        </lightning-card>
    </div>
</template>
```

## 2. `.../localizedCaseSummary.js`

```js
import { LightningElement, api } from 'lwc';

// Labels: literal specifiers, one import each. There is no runtime label lookup,
// so a label name can never be assembled from a variable.
import HEADING from '@salesforce/label/c.Case_Summary_Heading';
import COUNT_SENTENCE from '@salesforce/label/c.Case_Summary_Count';
import FIELD_OPENED from '@salesforce/label/c.Case_Field_Opened';
import FIELD_LAST_UPDATED from '@salesforce/label/c.Case_Field_Last_Updated';
import FIELD_ESTIMATED_COST from '@salesforce/label/c.Case_Field_Estimated_Cost';
import ACTION_REFRESH from '@salesforce/label/c.Case_Action_Refresh';

// Internationalization properties, all returned for the current user
// (lwc_guide create-i18n L3799).
import LANG from '@salesforce/i18n/lang';               // 'en-US'      (L3801)
import DIR from '@salesforce/i18n/dir';                 // 'ltr'|'rtl'  (L3802)
import LOCALE from '@salesforce/i18n/locale';           // 'en-CA'      (L3803)
import CURRENCY from '@salesforce/i18n/currency';       // 'CAD'        (L3807)
import TIME_ZONE from '@salesforce/i18n/timeZone';      // 'America/Los_Angeles' (L3835)
import FIRST_DAY_OF_WEEK from '@salesforce/i18n/firstDayOfWeek'; // 1     (L3808)

export default class LocalizedCaseSummary extends LightningElement {
    /** Date field (no time component), e.g. Case.SLA_Start_Date__c. */
    @api openedDate;
    /** DateTime field, e.g. Case.LastModifiedDate. */
    @api lastModifiedDateTime;
    /** Currency field value. */
    @api estimatedCost;
    /** CurrencyIsoCode from the record in a multi-currency org; optional. */
    @api recordCurrency;
    /** Open-case count for the sentence label. */
    @api openCaseCount = 0;

    label = {
        heading: HEADING,
        count: COUNT_SENTENCE,
        opened: FIELD_OPENED,
        lastUpdated: FIELD_LAST_UPDATED,
        estimatedCost: FIELD_ESTIMATED_COST,
        refresh: ACTION_REFRESH
    };

    lang = LANG;
    dir = DIR;
    firstDayOfWeek = FIRST_DAY_OF_WEEK;

    /**
     * One label carries the whole sentence with a {0} placeholder, so the
     * translator decides where the number goes. Never concatenate fragments.
     */
    get countSentence() {
        return this.label.count.replace('{0}', this.formattedCount);
    }

    get formattedCount() {
        return new Intl.NumberFormat(LOCALE).format(this.openCaseCount);
    }

    /**
     * A Date field arrives as 'YYYY-MM-DD'. Parsing it and formatting in the
     * user's time zone moves it backwards for anyone west of UTC, so the
     * formatter is pinned to UTC while the *locale* still comes from the user.
     */
    get openedOn() {
        if (!this.openedDate) {
            return '';
        }
        return new Intl.DateTimeFormat(LOCALE, {
            dateStyle: 'medium',
            timeZone: 'UTC'
        }).format(new Date(`${this.openedDate}T00:00:00Z`));
    }

    /**
     * A DateTime field is a real instant, so it is rendered in the user's own
     * time zone. The template prefers <lightning-formatted-date-time>; this
     * getter exists for the cases that cannot host a base component.
     */
    get lastModifiedText() {
        if (!this.lastModifiedDateTime) {
            return '';
        }
        return new Intl.DateTimeFormat(LOCALE, {
            dateStyle: 'medium',
            timeStyle: 'short',
            timeZone: TIME_ZONE
        }).format(new Date(this.lastModifiedDateTime));
    }

    /** The record's currency wins; the user's currency is only the fallback. */
    get resolvedCurrency() {
        return this.recordCurrency || CURRENCY;
    }

    get formattedCost() {
        return new Intl.NumberFormat(LOCALE, {
            style: 'currency',
            currency: this.resolvedCurrency
        }).format(this.estimatedCost ?? 0);
    }

    /** Direction changes behaviour, not just styling: "forward" is left in RTL. */
    get forwardIcon() {
        return this.dir === 'rtl' ? 'utility:chevronleft' : 'utility:chevronright';
    }

    handleRefresh() {
        this.dispatchEvent(new CustomEvent('refresh'));
    }
}
```

## 3. `.../localizedCaseSummary.css`

```css
/*
 * Logical properties, not left/right. The LWC guide's own RTL review tooling
 * describes its output as "code-level fixes for CSS logical properties,
 * bidirectional text, keyboard semantics, and RTL-aware SLDS class usage"
 * (lwc_guide mcp-testing L12765).
 */
.summary__count {
    margin-block-end: 0.75rem;
    padding-inline-start: 0.5rem;
    border-inline-start: 3px solid #0176d3;
    text-align: start;
}

.summary .slds-dl_horizontal__detail {
    padding-inline-start: 0.5rem;
}

/*
 * Do NOT reach for [dir="rtl"] here. The guide notes that the [dir=""]
 * attribute selector "only works in synthetic shadow DOM"
 * (lwc_guide create-components-shadow-dom L3517: the selector "only works in
 * synthetic shadow DOM"). Where a real direction
 * branch is needed, use :dir() if the browser supports it, or branch in JS on
 * the imported dir value as forwardIcon does.
 */
```

## 4. `.../localizedCaseSummary.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <property name="openCaseCount" type="Integer" label="Open Case Count" default="0"/>
            <property name="recordCurrency" type="String" label="Record Currency ISO Code"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

The `label` attribute on `<property>` is what an admin sees in Lightning App Builder.
UNVERIFIED (2026-09-05): the LWC Developer Guide documents `<property>` and its `label`
attribute (`lwc_guide reference-configuration-tags` L18979 — "label String Displays as a label for the attribute in Lightning App Builder" — and L8397) but nowhere states that
design-attribute labels are translatable or picked up by the Translation Workbench, and no
`Translations` sub-type for `LightningComponentBundle` appears in the `Translations` field
table (`api_meta` L135600–L135700, scanned). Treat App Builder property labels as untranslated
until proven otherwise, and do not put user-facing runtime strings in them.

## 5. `force-app/main/default/labels/CaseSummary.labels-meta.xml`

Shaped from the guide's own sample definition (`api_meta` L41231–L41248,
`lwc_guide create-labels` L3773–L3784). `fullName`, `language`, `protected`,
`shortDescription` and `value` are all listed Required for `CustomLabel`
(`api_meta` L41191–L41220).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomLabels xmlns="http://soap.sforce.com/2006/04/metadata">
    <labels>
        <fullName>Case_Summary_Heading</fullName>
        <categories>caseSummary,ui</categories>
        <language>en_US</language>
        <protected>false</protected>
        <shortDescription>Case Summary Heading</shortDescription>
        <value>Open Cases</value>
    </labels>
    <labels>
        <fullName>Case_Summary_Count</fullName>
        <categories>caseSummary,ui</categories>
        <language>en_US</language>
        <protected>false</protected>
        <shortDescription>Case Summary Count Sentence</shortDescription>
        <value>You have {0} open cases.</value>
    </labels>
    <labels>
        <fullName>Case_Field_Opened</fullName>
        <categories>caseSummary,ui</categories>
        <language>en_US</language>
        <protected>false</protected>
        <shortDescription>Case Field Opened</shortDescription>
        <value>Opened</value>
    </labels>
    <labels>
        <fullName>Case_Field_Last_Updated</fullName>
        <categories>caseSummary,ui</categories>
        <language>en_US</language>
        <protected>false</protected>
        <shortDescription>Case Field Last Updated</shortDescription>
        <value>Last Updated</value>
    </labels>
    <labels>
        <fullName>Case_Field_Estimated_Cost</fullName>
        <categories>caseSummary,ui</categories>
        <language>en_US</language>
        <protected>false</protected>
        <shortDescription>Case Field Estimated Cost</shortDescription>
        <value>Estimated Cost</value>
    </labels>
    <labels>
        <fullName>Case_Action_Refresh</fullName>
        <categories>caseSummary,ui</categories>
        <language>en_US</language>
        <protected>false</protected>
        <shortDescription>Case Action Refresh</shortDescription>
        <value>Refresh</value>
    </labels>
</CustomLabels>
```

- `categories` is "a comma-separated list of categories for the label … Maximum of 255
  characters" (`api_meta` L41191–L41193) — it is a list-view filter, not a namespace.
- `protected`: "Protected components can't be linked to or referenced by components created
  in the installing organization" (`api_meta` L41203–L41205). Set it deliberately before a
  label ships in a managed package; `false` is the right answer for a label an installing
  org is expected to override or reference.
- `value` is capped at 1,000 characters (`api_meta` L41219–L41220, and L41152–L41153:
  "custom text values, up to 1,000 characters in length").

## 6. `force-app/main/default/translations/de.translation-meta.xml`

A `Translations` file, one per language. This is a complete, deployable file for German
holding only the custom-label section — the `Translations` type carries many other
sub-lists (`customApplications`, `customTabs`, `bots` …) that this component does not use
(`api_meta` L135605–L135612). `CustomLabelTranslation` has exactly two fields, both
Required: `label` (the translated text) and `name` (the label's `fullName`)
(`api_meta` L135930–L135937).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Translations xmlns="http://soap.sforce.com/2006/04/metadata">
    <customLabels>
        <label>Offene Fälle</label>
        <name>Case_Summary_Heading</name>
    </customLabels>
    <customLabels>
        <label>Sie haben {0} offene Fälle.</label>
        <name>Case_Summary_Count</name>
    </customLabels>
    <customLabels>
        <label>Geöffnet</label>
        <name>Case_Field_Opened</name>
    </customLabels>
    <customLabels>
        <label>Zuletzt aktualisiert</label>
        <name>Case_Field_Last_Updated</name>
    </customLabels>
    <customLabels>
        <label>Geschätzte Kosten</label>
        <name>Case_Field_Estimated_Cost</name>
    </customLabels>
    <customLabels>
        <label>Aktualisieren</label>
        <name>Case_Action_Refresh</name>
    </customLabels>
</Translations>
```

- The Metadata API file name is `localeCode.translation` — "For example, the file name for
  German translations is `de.translation`" (`api_meta` L135574–L135575). Packaged
  translations use `pkgNamespace__localeCode.translation` (L135576–L135577).
  UNVERIFIED (2026-09-05): the `-meta.xml` suffix shown above is Salesforce DX **source
  format**, documented in the Salesforce DX Developer Guide, which is not in the extracted
  set. In an MDAPI-format deployment the file is `translations/de.translation`.
- The `{0}` placeholder must survive translation. That is the whole reason the sentence is
  one label rather than three.
- `CustomLabelTranslation.label` is "Maximum of 765 characters" (`api_meta`
  L135934–L135935) — 235 fewer than the master `value`. A master label between 766 and
  1,000 characters deploys, and then cannot be fully translated into any language.

## 7. `.../localizedCaseSummary/__tests__/localizedCaseSummary.test.js`

```js
import { createElement } from 'lwc';
import LocalizedCaseSummary from 'c/localizedCaseSummary';

// In Jest, "we use a jest-transformer to convert the @salesforce/label import
// statement into a variable declaration. The value is set to the label path.
// By default, myImport is assigned a string value of c.specialLabel. You can
// use jest.mock() to provide your own value for an import."
// (lwc_guide unit-testing-using-jest-patterns L12650)
//
// So an unmocked label import evaluates to the STRING 'c.Case_Summary_Count',
// not to "You have {0} open cases." Assert against a mocked value, never
// against English text.
jest.mock(
    '@salesforce/label/c.Case_Summary_Count',
    () => ({ default: 'OPEN_COUNT {0}' }),
    { virtual: true }
);
jest.mock(
    '@salesforce/label/c.Case_Summary_Heading',
    () => ({ default: 'HEADING' }),
    { virtual: true }
);

// Locale is pinned so the assertions are deterministic on every machine.
jest.mock('@salesforce/i18n/locale', () => ({ default: 'de-DE' }), { virtual: true });
jest.mock('@salesforce/i18n/dir', () => ({ default: 'rtl' }), { virtual: true });
jest.mock('@salesforce/i18n/currency', () => ({ default: 'EUR' }), { virtual: true });
jest.mock(
    '@salesforce/i18n/timeZone',
    () => ({ default: 'Europe/Berlin' }),
    { virtual: true }
);

describe('c-localized-case-summary', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    function build(props = {}) {
        const element = createElement('c-localized-case-summary', {
            is: LocalizedCaseSummary
        });
        Object.assign(element, props);
        document.body.appendChild(element);
        return element;
    }

    it('substitutes the count into the sentence label instead of concatenating', () => {
        const element = build({ openCaseCount: 3 });
        const p = element.shadowRoot.querySelector('.summary__count');
        expect(p.textContent).toBe('OPEN_COUNT 3');
    });

    it('renders a date-only field on its own calendar day regardless of time zone', () => {
        // 2026-03-01 must stay 1 March for every user. Formatting it in the
        // user's time zone would render 28 February anywhere west of UTC.
        const element = build({ openedDate: '2026-03-01' });
        return Promise.resolve().then(() => {
            const dd = element.shadowRoot.querySelectorAll('dd')[0];
            expect(dd.textContent).toContain('2026');
            expect(dd.textContent).not.toContain('28');
        });
    });

    it('prefers the record currency over the user currency', () => {
        const element = build({ estimatedCost: 1234.5, recordCurrency: 'JPY' });
        return Promise.resolve().then(() => {
            const span = element.shadowRoot.querySelector('[data-id="cost-intl"]');
            expect(span.textContent).toContain('¥');
        });
    });

    it('falls back to the user currency when the record carries none', () => {
        const element = build({ estimatedCost: 1234.5 });
        return Promise.resolve().then(() => {
            const span = element.shadowRoot.querySelector('[data-id="cost-intl"]');
            expect(span.textContent).toContain('€');
        });
    });

    it('mirrors the directional icon and stamps dir on the wrapper in RTL', () => {
        const element = build({});
        const wrapper = element.shadowRoot.querySelector('div.summary');
        expect(wrapper.getAttribute('dir')).toBe('rtl');
        const button = element.shadowRoot.querySelector('lightning-button');
        expect(button.iconName).toBe('utility:chevronleft');
    });
});
```

## 8. `jest.config.js`

Copy `templates/lwc/jest.config.js` and add the i18n mappers. The
`moduleNameMapper` mechanism is the guide's ("To create references to mock components for
more control over component behavior, add `moduleNameMapper` settings in the
`jest.config.js` file" — `lwc_guide unit-testing-using-jest-patterns` L12637; the shape of
the map is shown at `unit-testing-using-jest-create-tests` L12434–L12453).

```js
const { jestConfig } = require('@salesforce/sfdx-lwc-jest/config');

module.exports = {
    ...jestConfig,
    moduleNameMapper: {
        '^lightning/navigation$':
            '<rootDir>/force-app/test/jest-mocks/lightning/navigation',
        // One shared i18n mock keeps every suite on the same fixed locale.
        // Per-suite jest.mock() calls still override it.
        '^@salesforce/i18n/(.+)$':
            '<rootDir>/force-app/test/jest-mocks/i18n/$1'
    },
    testTimeout: 10000
};
```

```js
// force-app/test/jest-mocks/i18n/locale.js
export default 'de-DE';
```

Labels need no mapper entry: the sfdx-lwc-jest transformer already resolves
`@salesforce/label/c.X` to the string `c.X`, and `jest.mock(..., { virtual: true })`
overrides it per suite (L12650). Add a mapper only if you want one shared translated
fixture across many suites.

## 9. `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case_Summary_Heading</members>
        <members>Case_Summary_Count</members>
        <members>Case_Field_Opened</members>
        <members>Case_Field_Last_Updated</members>
        <members>Case_Field_Estimated_Cost</members>
        <members>Case_Action_Refresh</members>
        <name>CustomLabel</name>
    </types>
    <types>
        <members>de</members>
        <name>Translations</name>
    </types>
    <types>
        <members>localizedCaseSummary</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>67.0</version>
</Package>
```

Note the singular `CustomLabel`. "Use `CustomLabels` with the wildcard character (\*) for
members in the `package.xml` manifest file to retrieve all custom labels that are defined
in your organization. `CustomLabels` doesn't support retrieving one or more custom labels
by name. To retrieve specific labels by name, use `CustomLabel` and specify the label names
as members" (`api_meta` L41225–L41227). The plural type with a named member retrieves
nothing and reports no error.

## 10. Deploy order

Labels must exist before the component that imports them, and translations must be
deployed separately from the master values.

```bash
# 1. Master label values first — the component's imports resolve against these.
sf project deploy start \
  --source-dir force-app/main/default/labels \
  --target-org myOrg

# 2. The component bundle.
sf project deploy start \
  --source-dir force-app/main/default/lwc/localizedCaseSummary \
  --target-org myOrg

# 3. Translations last. Deploying steps 1-2 leaves every language on the master
#    English value, silently.
sf project deploy start \
  --source-dir force-app/main/default/translations \
  --target-org myOrg

# Retrieve what the org actually has (note: CustomLabels cannot be retrieved
# with a namespace — api_meta L41289-L41291).
sf project retrieve start --manifest manifest/package.xml --target-org myOrg
```

## 11. Verification

1. **The labels landed with the values you meant.** In Setup, Custom Labels; or by query:

   ```sql
   SELECT Name, MasterLabel, Value, Category, Language, IsProtected
   FROM ExternalString
   WHERE Name LIKE 'Case_%'
   ORDER BY Name
   ```

   UNVERIFIED (2026-09-05): `ExternalString` is the Tooling API object behind custom labels;
   it is not documented in the extracted Object Reference or Metadata API guide, so run this
   with `sf data query --use-tooling-api` and fall back to the Setup list if it errors.

2. **A translation actually exists for every label, in every active language.** Retrieve the
   translation files and compare names against the label file — the count is the check, and
   nothing in the platform will raise this for you:

   ```bash
   sf project retrieve start --metadata Translations --target-org myOrg
   grep -c '<name>Case_' force-app/main/default/labels/CaseSummary.labels-meta.xml
   grep -c '<name>Case_' force-app/main/default/translations/de.translation-meta.xml
   ```

3. **The component renders in the target language.** Set a test user's Language to German
   and their Locale to `de_DE` in personal settings — "Users can set their individual
   language, locale, and time zone on their personal settings pages"
   (`lwc_guide create-i18n` L3794) — then load the page as that user. English on screen is
   the only failure signal you will get.

4. **The date-only field did not move.** Set the same user's time zone to
   `(GMT-08:00) Pacific Time`, reload, and confirm the Opened date still shows the stored
   day. If it shows the day before, the formatter is reading the user's time zone instead
   of UTC.

5. **RTL.** Enable a right-to-left language in the org, switch the test user to it, and
   confirm the layout mirrors and the button chevron points left. Note the Metadata API
   guide's own caution for platform-only RTL languages: "Before enabling Urdu as a
   platform-only language, review the right-to-left language support limitations"
   (`api_meta` L135569).

6. **The checker is clean:**

   ```bash
   python3 skills/lwc/lwc-internationalization/scripts/check_lwc_internationalization.py \
     --manifest-dir force-app/main/default --strict
   ```
