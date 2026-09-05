# Code Examples — Wire Service Patterns

One deployable slice that exercises every decision this skill owns: a record-page
panel that reads its host record with `getRecord` on a reactive `$recordId`, chains
`getObjectInfo` → `getPicklistValues`, wires a **cacheable** Apex method in the
**function form** so `data` and `error` are handled separately and the provisioned
result is kept for `refreshApex()`, then performs an imperative write and refreshes
*both* caches — `refreshApex()` for the Apex wire, `notifyRecordUpdateAvailable()`
for the LDS wire — because they are two different caches.

| Piece | What it proves | Why it is here and not in a sibling skill |
|---|---|---|
| `accountHealthPanel.js` | property form vs function form, reactive `$` params, wire→wire chaining, spread-copy of provisioned data | `lwc/lwc-imperative-apex` owns the click-driven call; this owns the wire around it |
| `AccountHealthController.cls` | `cacheable=true` read + non-cacheable write in one class | the `cacheable=true` contract is what makes `@wire(apexMethod)` legal at all |
| `refreshApex` + `notifyRecordUpdateAvailable` | two caches, two refresh calls | `lwc/lwc-wire-refresh-patterns` owns RefreshView API and the cross-component story; this owns the after-my-own-DML case |
| `__tests__/accountHealthPanel.test.js` | `emit()` on the imported adapters | `lwc/lwc-testing` owns the Jest harness, `jest.config.js` and the `.forceignore` delta — read it for those |

Error text is reduced inline here to keep the bundle self-contained. In a real org,
import the shared `errorUtils` normaliser from `lwc/lwc-error-boundaries`
(`references/code-examples.md` § "Bundle 1") instead of re-implementing the
array-vs-object branch in every component.

---

## 1. The Apex controller

`force-app/main/default/classes/AccountHealthController.cls`

```apex
/**
 * AccountHealthController — the read half is cacheable so it can be wired;
 * the write half is not, so it must be called imperatively.
 *
 * "To use @wire to call an Apex method, you must set cacheable=true."
 *   -- lwc_guide apex-result-caching L7256
 * "To set cacheable=true, a method must only get data, it can't mutate (change) data."
 *   -- lwc_guide apex-result-caching L7254
 */
public with sharing class AccountHealthController {
    /**
     * A wired param that is null still calls the method; a param that is
     * undefined does not (lwc_guide apex-wire-method L7104). So this method
     * must tolerate null rather than assume the wire gated it out.
     */
    @AuraEnabled(cacheable=true)
    public static List<Case> getOpenCases(Id accountId) {
        if (accountId == null) {
            return new List<Case>();
        }
        return [
            SELECT Id, CaseNumber, Subject, Priority, Status
            FROM Case
            WHERE AccountId = :accountId AND IsClosed = false
            WITH USER_MODE
            ORDER BY CreatedDate DESC
            LIMIT 50
        ];
    }

    /**
     * Not cacheable: it mutates. Called imperatively from the component.
     * The component is then responsible for refreshing BOTH caches.
     */
    @AuraEnabled
    public static void closeCase(Id caseId) {
        Case toClose = new Case(Id = caseId, Status = 'Closed');
        update as user toClose;
    }
}
```

`force-app/main/default/classes/AccountHealthController.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

API 67.0 matters here: "In API version 67.0 and later, Apex runs in user mode by
default" (`lwc_guide apex-security L7433`). `WITH USER_MODE` and `update as user`
are written explicitly anyway so the class does not change behaviour if someone
lowers the API version.

`force-app/main/default/classes/AccountHealthControllerTest.cls`

```apex
@IsTest
private class AccountHealthControllerTest {
    @TestSetup
    static void makeData() {
        Account a = new Account(Name = 'Wire Test Co');
        insert a;
        List<Case> cases = new List<Case>();
        for (Integer i = 0; i < 5; i++) {
            cases.add(new Case(AccountId = a.Id, Subject = 'Open ' + i, Status = 'New'));
        }
        insert cases;
    }

    @IsTest
    static void getOpenCasesReturnsOnlyOpenCases() {
        Account a = [SELECT Id FROM Account LIMIT 1];
        Test.startTest();
        List<Case> result = AccountHealthController.getOpenCases(a.Id);
        Test.stopTest();
        Assert.areEqual(5, result.size(), 'All five seeded cases are open');
        for (Case c : result) {
            Assert.isFalse(c.IsClosed, 'Closed cases must not be provisioned to the wire');
        }
    }

    @IsTest
    static void getOpenCasesToleratesNullAccountId() {
        // The wire calls the method when the param is null, not only when it is set.
        Test.startTest();
        List<Case> result = AccountHealthController.getOpenCases(null);
        Test.stopTest();
        Assert.areEqual(0, result.size(), 'A null param must return empty, not throw');
    }

    @IsTest
    static void closeCaseSetsStatusClosed() {
        Case c = [SELECT Id FROM Case LIMIT 1];
        Test.startTest();
        AccountHealthController.closeCase(c.Id);
        Test.stopTest();
        Case reloaded = [SELECT Id, IsClosed FROM Case WHERE Id = :c.Id];
        Assert.isTrue(reloaded.IsClosed, 'closeCase must actually close the case');
    }
}
```

---

## 2. The component JavaScript

`force-app/main/default/lwc/accountHealthPanel/accountHealthPanel.js`

```js
import { LightningElement, api, wire } from 'lwc';
import {
    getRecord,
    getFieldValue,
    notifyRecordUpdateAvailable
} from 'lightning/uiRecordApi';
import { getObjectInfo, getPicklistValues } from 'lightning/uiObjectInfoApi';
import { refreshApex } from '@salesforce/apex';

import getOpenCases from '@salesforce/apex/AccountHealthController.getOpenCases';
import closeCase from '@salesforce/apex/AccountHealthController.closeCase';

import ACCOUNT_OBJECT from '@salesforce/schema/Account';
import NAME_FIELD from '@salesforce/schema/Account.Name';
import INDUSTRY_FIELD from '@salesforce/schema/Account.Industry';
import RATING_FIELD from '@salesforce/schema/Account.Rating';

// Static config value. No "$", so it is never re-evaluated
// (lwc_guide data-wire-service-about L6445).
const ACCOUNT_FIELDS = [NAME_FIELD, INDUSTRY_FIELD];

export default class AccountHealthPanel extends LightningElement {
    /**
     * @api because the record page sets it. It is undefined on the very first
     * tick, and an undefined config property means the wire does not provision
     * at all -- data and error both stay undefined
     * (lwc_guide data-wire-service-about L6408).
     */
    @api recordId;

    /** Set in Lightning App Builder via the <property> in the js-meta.xml. */
    @api cardTitle = 'Account Health';

    // ---------------------------------------------------------------- wires

    /**
     * PROPERTY FORM. Correct when the template consumes {data, error} as-is.
     * The property is assigned {data: undefined, error: undefined} after
     * construction and before any other lifecycle event, so it is safe to read
     * in a getter on the first render (lwc_guide data-wire-service-about L6453-L6454).
     */
    @wire(getRecord, { recordId: '$recordId', fields: ACCOUNT_FIELDS })
    account;

    // Wire 2 feeds wire 3. Chaining works only because the intermediate value
    // is reactive: "make the property reactive so that the wire provisions new
    // data when the property's value changes" (lwc_guide apex-wire-method L7178).
    @wire(getObjectInfo, { objectApiName: ACCOUNT_OBJECT })
    wiredObjectInfo({ data, error }) {
        if (data) {
            this.defaultRecordTypeId = data.defaultRecordTypeId;
            this.objectInfoError = undefined;
        } else if (error) {
            this.objectInfoError = this.reduce(error);
            this.defaultRecordTypeId = undefined;
        }
    }

    defaultRecordTypeId;
    objectInfoError;

    /**
     * Until defaultRecordTypeId has a value this wire never fires -- which is
     * the intended gate, not a bug. getPicklistValues requires BOTH params
     * (lwc_guide reference-wire-adapters-picklist-values L14960).
     */
    @wire(getPicklistValues, {
        recordTypeId: '$defaultRecordTypeId',
        fieldApiName: RATING_FIELD
    })
    ratingPicklist;

    /**
     * FUNCTION FORM. Chosen for three reasons this skill cares about:
     *  1. data and error need different handling, not a raw dump to the template;
     *  2. the provisioned object must be retained so refreshApex() has something
     *     legal to receive -- "The parameter you refresh with refreshApex() must
     *     be an object that was previously emitted by an Apex @wire"
     *     (lwc_guide apex-result-caching L7264);
     *  3. the rows are copied before the component adds UI-only fields.
     */
    wiredCasesResult;   // the whole provisioned object, for refreshApex
    caseRows = [];      // our own array, safe to mutate
    casesError;

    @wire(getOpenCases, { accountId: '$recordId' })
    wiredCases(result) {
        this.wiredCasesResult = result;
        const { data, error } = result;
        if (data) {
            // Provisioned objects are read-only. "To mutate the data, a component
            // should make a shallow copy of the objects it wants to mutate"
            // (lwc_guide data-wire-service-about L6401). data.push(...) or
            // row.isUrgent = true on the provisioned rows throws
            // "Invalid mutation ... is read-only" (lwc_guide create-components-data-flow L2021).
            this.caseRows = data.map((row) => ({
                ...row,
                isUrgent: row.Priority === 'High'
            }));
            this.casesError = undefined;
        } else if (error) {
            this.casesError = this.reduce(error);
            this.caseRows = [];
        }
    }

    // ------------------------------------------------------------- template

    get accountName() {
        return getFieldValue(this.account.data, NAME_FIELD);
    }

    get industry() {
        return getFieldValue(this.account.data, INDUSTRY_FIELD);
    }

    get ratingOptions() {
        return this.ratingPicklist.data ? this.ratingPicklist.data.values : [];
    }

    /**
     * Loading is "no data and no error yet", not "no data". Before the wire
     * fires for the first time both are undefined and the wire is NOT in an
     * error state (lwc_guide data-error L6572).
     */
    get isLoading() {
        return !this.account.data && !this.account.error && !this.casesError;
    }

    get isEmpty() {
        return !!this.wiredCasesResult && !this.casesError && this.caseRows.length === 0;
    }

    get recordError() {
        return this.account.error ? this.reduce(this.account.error) : undefined;
    }

    // -------------------------------------------------------------- actions

    /**
     * Imperative write, then TWO refreshes, because there are two caches:
     *  - refreshApex() re-runs the Apex wire using its bound config
     *    (lwc_guide apex-result-caching L7263);
     *  - notifyRecordUpdateAvailable() tells LDS the record changed outside its
     *    own mechanisms so every wire on that record re-emits
     *    (lwc_guide reference-notify-record-update L15370).
     * refreshApex() on the getRecord wire would be the wrong tool: using it to
     * refresh a non-Apex wire adapter is deprecated
     * (lwc_guide data-guidelines L5355).
     */
    async handleCloseCase(event) {
        const caseId = event.target.dataset.caseId;
        this.casesError = undefined;
        try {
            await closeCase({ caseId });
            await Promise.all([
                refreshApex(this.wiredCasesResult),
                notifyRecordUpdateAvailable([{ recordId: this.recordId }])
            ]);
        } catch (error) {
            this.casesError = this.reduce(error);
        }
    }

    // ---------------------------------------------------------------- utils

    /**
     * Minimal inline normaliser. UI API READ errors carry error.body as an
     * ARRAY of objects; Apex read/write and network errors carry it as an
     * OBJECT (lwc_guide data-error L6568-L6571). Prefer the shared errorUtils
     * module from lwc/lwc-error-boundaries in a real org.
     */
    reduce(error) {
        if (!error || !error.body) {
            return 'Unknown error';
        }
        if (Array.isArray(error.body)) {
            return error.body.map((e) => e.message).join(', ');
        }
        if (typeof error.body.message === 'string') {
            return error.body.message;
        }
        return 'Unknown error';
    }
}
```

---

## 3. The template

`force-app/main/default/lwc/accountHealthPanel/accountHealthPanel.html`

```html
<template>
    <lightning-card title={cardTitle} icon-name="standard:account">
        <div class="slds-var-m-around_medium">

            <!-- Loading: neither data nor error has arrived. -->
            <template lwc:if={isLoading}>
                <lightning-spinner alternative-text="Loading" size="small"></lightning-spinner>
            </template>

            <template lwc:if={recordError}>
                <p data-id="record-error" class="slds-text-color_error">{recordError}</p>
            </template>

            <template lwc:if={account.data}>
                <p data-id="name">{accountName}</p>
                <p data-id="industry">{industry}</p>
            </template>

            <template lwc:if={casesError}>
                <p data-id="cases-error" class="slds-text-color_error">{casesError}</p>
            </template>

            <!-- Empty is a distinct state from loading: the wire HAS emitted. -->
            <template lwc:if={isEmpty}>
                <p data-id="cases-empty">No open cases.</p>
            </template>

            <template for:each={caseRows} for:item="row">
                <div key={row.Id} data-id="case-row" class="slds-var-p-vertical_xx-small">
                    <span>{row.CaseNumber} — {row.Subject}</span>
                    <lightning-button
                        label="Close"
                        data-case-id={row.Id}
                        onclick={handleCloseCase}
                    ></lightning-button>
                </div>
            </template>

            <template lwc:if={ratingOptions.length}>
                <lightning-combobox
                    label="Rating"
                    options={ratingOptions}
                    data-id="rating"
                ></lightning-combobox>
            </template>
        </div>
    </lightning-card>
</template>
```

`lightning-card`, `lightning-spinner`, `lightning-button` and `lightning-combobox`
attribute names come from the Component Library, which is not part of the crawled
Developer Guide. **UNVERIFIED (2026-09-05): the exact attribute set of these base
components is documented in the Component Library, not in the LWC Developer Guide
pages available here.** The wire-side behaviour above is grounded; the base-component
attributes are not.

---

## 4. The bundle configuration

`force-app/main/default/lwc/accountHealthPanel/accountHealthPanel.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordPage</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <property name="cardTitle" type="String" label="Card Title"
                      default="Account Health"/>
            <objects>
                <object>Account</object>
            </objects>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

Constraining `<objects>` to Account is what makes `recordId` an Account Id. The
`<property>` tag is not decoration: "The `targetConfig` tag includes at least one
`property` tag and can include an `objects` tag" (`lwc_guide targets-lightning-record-page
L19346`), and `<objects>` may appear only once inside a `targetConfig` (`L19364`). Note the
two-hour caveat: after a rename, "name changes don't cascade thoroughly into source
code for approximately two hours … this timing is also important if the component's
meta.xml file uses `<objects>` to constrain the object home or record home"
(`lwc_guide data-wire-service-about L6417`).

Copy `templates/lwc/component-skeleton/componentSkeleton.js-meta.xml` when you need
the multi-target variant with design attributes; it carries the same `apiVersion`.

---

## 5. The Jest suite

`force-app/main/default/lwc/accountHealthPanel/__tests__/accountHealthPanel.test.js`

```js
import { createElement } from 'lwc';
import AccountHealthPanel from 'c/accountHealthPanel';
import { getRecord, notifyRecordUpdateAvailable } from 'lightning/uiRecordApi';
import { refreshApex } from '@salesforce/apex';
import getOpenCases from '@salesforce/apex/AccountHealthController.getOpenCases';
import closeCase from '@salesforce/apex/AccountHealthController.closeCase';

import MOCK_GET_RECORD from './data/getRecord.json';

const RECORD_ID = '001xx000003DGg0AAG';

const MOCK_CASES = Object.freeze([
    Object.freeze({ Id: '500xx0000000001', CaseNumber: '00001', Subject: 'Broken', Priority: 'High', Status: 'New' }),
    Object.freeze({ Id: '500xx0000000002', CaseNumber: '00002', Subject: 'Slow', Priority: 'Low', Status: 'New' })
]);

// UNVERIFIED (2026-09-05): the crawled guide documents emit() on the imported
// adapter (unit-testing-using-wire-utility L12554) but says nothing about
// mocking refreshApex or notifyRecordUpdateAvailable. These two jest.mock
// factories are a local convention, not a documented platform API.
jest.mock(
    '@salesforce/apex',
    () => ({ refreshApex: jest.fn(() => Promise.resolve()) }),
    { virtual: true }
);
jest.mock('lightning/uiRecordApi', () => {
    const actual = jest.requireActual('lightning/uiRecordApi');
    return { ...actual, notifyRecordUpdateAvailable: jest.fn(() => Promise.resolve()) };
});
jest.mock(
    '@salesforce/apex/AccountHealthController.closeCase',
    () => ({ default: jest.fn(() => Promise.resolve()) }),
    { virtual: true }
);

function build(props = {}) {
    const element = createElement('c-account-health-panel', { is: AccountHealthPanel });
    Object.assign(element, props);
    document.body.appendChild(element);
    return element;
}

describe('c-account-health-panel', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('shows the loading state before any wire emits', () => {
        const element = build({ recordId: RECORD_ID });
        // Before the wire fires, data and error are both undefined and the wire
        // is not in an error state (lwc_guide data-error L6572).
        expect(element.shadowRoot.querySelector('lightning-spinner')).not.toBeNull();
        expect(element.shadowRoot.querySelector('[data-id="record-error"]')).toBeNull();
    });

    it('renders record fields once getRecord emits', async () => {
        const element = build({ recordId: RECORD_ID });
        // "The component receives updates about data only when the component is
        // connected to the DOM" -- emit AFTER appendChild
        // (lwc_guide unit-testing-using-wire-utility L12548).
        getRecord.emit(MOCK_GET_RECORD);
        await Promise.resolve();

        expect(element.shadowRoot.querySelector('[data-id="name"]').textContent).toBe('Acme');
    });

    it('copies wired Apex rows instead of mutating them', async () => {
        const element = build({ recordId: RECORD_ID });
        getOpenCases.emit(MOCK_CASES);
        await Promise.resolve();

        const rows = element.shadowRoot.querySelectorAll('[data-id="case-row"]');
        expect(rows.length).toBe(2);
        // Object.freeze is the test-side stand-in for the read-only membrane.
        // A component that pushed or assigned into the provisioned array would
        // have thrown before reaching this assertion.
        expect(MOCK_CASES[0].isUrgent).toBeUndefined();
    });

    it('distinguishes empty from loading', async () => {
        const element = build({ recordId: RECORD_ID });
        getRecord.emit(MOCK_GET_RECORD);
        getOpenCases.emit([]);
        await Promise.resolve();

        expect(element.shadowRoot.querySelector('[data-id="cases-empty"]')).not.toBeNull();
        expect(element.shadowRoot.querySelector('lightning-spinner')).toBeNull();
    });

    it('renders the Apex error shape (body as an object)', async () => {
        const element = build({ recordId: RECORD_ID });
        // UNVERIFIED (2026-09-05): error() on a wire adapter stub is documented
        // in the wire-service-jest-util README, not in the crawled Developer Guide.
        // Apex read and write operations return error.body as an OBJECT
        // (lwc_guide data-error L6570) -- this payload matches that shape.
        getOpenCases.error({ body: { message: 'Insufficient access' }, status: 403 });
        await Promise.resolve();

        expect(
            element.shadowRoot.querySelector('[data-id="cases-error"]').textContent
        ).toBe('Insufficient access');
    });

    it('refreshes both caches after an imperative close', async () => {
        const element = build({ recordId: RECORD_ID });
        getOpenCases.emit(MOCK_CASES);
        await Promise.resolve();

        element.shadowRoot.querySelector('lightning-button').click();
        await Promise.resolve();
        await Promise.resolve();

        expect(closeCase).toHaveBeenCalledWith({ caseId: MOCK_CASES[0].Id });
        // refreshApex must receive the whole provisioned object, never .data
        // (lwc_guide apex-result-caching L7264).
        expect(refreshApex).toHaveBeenCalledTimes(1);
        expect(refreshApex.mock.calls[0][0]).toHaveProperty('data');
        expect(notifyRecordUpdateAvailable).toHaveBeenCalledWith([{ recordId: RECORD_ID }]);
    });
});
```

`force-app/main/default/lwc/accountHealthPanel/__tests__/data/getRecord.json` — a
trimmed UI API record response. "The best practice is to grab a snapshot of data
using a REST client that accesses the UI API" (`lwc_guide
unit-testing-using-wire-utility L12544`), not to hand-author it.

```json
{
  "apiName": "Account",
  "childRelationships": {},
  "fields": {
    "Industry": { "displayValue": "Technology", "value": "Technology" },
    "Name": { "displayValue": null, "value": "Acme" }
  },
  "id": "001xx000003DGg0AAG",
  "recordTypeId": "012000000000000AAA",
  "recordTypeInfo": null
}
```

Read `recordTypeId`, never `recordTypeInfo`: "In the Record response, don't use the
`recordTypeInfo` property. Instead, use the `recordTypeId` property, which is
returned for every record" (`lwc_guide reference-wire-adapters-record L15153`).

For the `jest.config.js`, the `moduleNameMapper` entries and the `.forceignore`
delta, read `lwc/lwc-testing` § "The `jest.config.js` delta" — this skill does not
restate the harness. `templates/lwc/jest.config.js` is the canonical config.

---

## 6. Deploy order

The Apex class must exist before the component that imports it, or the deploy fails
resolving `@salesforce/apex/AccountHealthController.getOpenCases`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>AccountHealthController</members>
        <members>AccountHealthControllerTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>accountHealthPanel</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>67.0</version>
</Package>
```

```bash
# 1. Apex first, with its tests.
sf project deploy start \
  --source-dir force-app/main/default/classes \
  --test-level RunSpecifiedTests \
  --tests AccountHealthControllerTest \
  --target-org myOrg

# 2. Then the bundle.
sf project deploy start \
  --source-dir force-app/main/default/lwc/accountHealthPanel \
  --target-org myOrg

# 3. Jest, before or after -- it needs no org.
npm run test:unit -- accountHealthPanel

# 4. This skill's checker over the source tree.
python3 skills/lwc/wire-service-patterns/scripts/check_wire_service_patterns.py \
  --manifest-dir force-app --strict
```

---

## 7. Verification

| Check | How | Expected |
|---|---|---|
| The wire gate is real, not theoretical | Drop the component on an App Page (no `recordId`) instead of a record page | The panel shows loading and never errors — an undefined config property means no provisioning and no error (`data-wire-service-about L6408`) |
| `cacheable=true` is load-bearing | Temporarily remove `(cacheable=true)` from `getOpenCases` and redeploy | The wire fails; only imperative calls are legal without it (`apex-result-caching L7256`) |
| The Apex refresh works | Close a case, watch the row disappear without a page reload | `refreshApex()` re-queries with the bound config and re-emits (`apex-result-caching L7275`) |
| The LDS refresh works | Put `lightning-record-form` on the same page over a field the Apex write touches; close a case | The form updates too — that is `notifyRecordUpdateAvailable()` reaching every wire on the record (`reference-notify-record-update L15371`), which `refreshApex` alone would not do |
| Immutability is enforced, not just intended | In a sandbox with debug mode on, change `data.map(...)` to `data[0].isUrgent = true` | Browser console: `Invalid mutation … is read-only` (`create-components-data-flow L2021`) |
| Nothing polls | `grep -rn "setInterval\|setTimeout" force-app/main/default/lwc/accountHealthPanel` | No hits — "Don't use refresh functions in a polling pattern" (`data-wire-service-about L6478`) |
