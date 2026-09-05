# Code Examples — LWC Data Table

A complete, deployable `lightning-datatable` bundle: an `@wire`d Apex read, a column
definition, client-side sorting, inline edit through `draft-values` → `onsave` → Apex,
a row-action `CustomEvent`, a custom data type that extends `LightningDatatable`, the
Apex controller and its test, the `-meta.xml`, a `package.xml`, and a Jest test.

Every line marked **grounded** below cites the Lightning Web Components Developer Guide
page slug and the line in the extracted text used while authoring. `lightning-datatable`'s
full attribute and column-type catalogue lives in the **Component Library**, not the
developer guide — attributes the guide never names are flagged inline.

## How to read it

- **`key-field` is required.** "The required `key-field` attribute associates each row
  with a contact record" — grounded: `data-table-inline-edit` L5675.
- **The element's attributes are kebab-case; everything inside `columns` is camelCase.**
  JS property names are camelCase, HTML attribute names kebab-case — grounded:
  `js-props-names` L2338. So the markup carries `key-field` / `draft-values` /
  `enable-infinite-loading`, and the JS array carries `fieldName` / `typeAttributes` /
  `cellAttributes` / `standardCellLayout` / `editTemplate`.
- **`columns[].fieldName` must match a key on the row object**, not a field label —
  grounded: `data-table-custom-types` L5812 ("The `fieldName` property matches the `Name`
  field on the account object") and `data-table-inline-edit` L5675 ("the `columns`
  attribute assigns a record field to each column").
- **`editable: true` in the column definition is what turns inline edit on** — grounded:
  `data-table-inline-edit` L5678. Compound fields (`Name`) cannot be edited; use the
  component fields — same line.
- **Sorting is client-side here.** `onsort` gives you `event.detail.fieldName` —
  grounded: `data-table-custom-types` L5855. Re-ordering the rows is your code's job;
  nothing is re-queried unless you re-query. The paired `event.detail.sortDirection`
  and the `sorted-by` / `sorted-direction` / `default-sort-direction` attributes are
  documented only in the Component Library. UNVERIFIED (2026-09-05): not stated on any
  developer-guide page in `lwc_guide.txt`.
- **The save path is Apex here, deliberately.** The guide documents both: `updateRecord()`
  from `lightning/uiRecordApi` for the UI-API path (L5676, L5714 — "`updateRecord()`
  expects a single record only"), and an Apex controller for bulk — "For bulk record
  updates in a single transaction, we recommend using Apex" (L5717). Because Apex writes
  bypass Lightning Data Service, "you must notify Lightning Data Service (LDS) using the
  `notifyRecordUpdateAvailable(recordIds)` function" (L5718) and call it *after* the
  update completes, using `async`/`await` (L5721).
- **`refreshApex` is what re-provisions the wire.** "To refresh stale data, call
  `refreshApex()`, because Lightning Data Service doesn't manage data provisioned by
  Apex" — grounded: `apex-wire-method` L7098. Its argument "must be an object that was
  previously emitted by an Apex `@wire`" — `apex-result-caching` L7264, which is why the
  wired *function* stashes the whole result.
- **Row actions**: the guide shows the handler shape — `event.detail.action` and
  `event.detail.row` (`data-table-tree-grid` L5632–L5634; `data-table-a11y` L5978). The
  `onrowaction` attribute name and the `type: 'action'` column's `rowActions`
  typeAttribute are Component-Library-only. UNVERIFIED (2026-09-05): the guide lists
  `action` among the standard types (`data-table-custom-types` L5773) but never documents
  its type attributes.
- **`isLoading` / `is-loading`** on the datatable: UNVERIFIED (2026-09-05) —
  Component-Library-only; the guide names only `enable-infinite-loading` and `onloadmore`
  (`data-table-performance` L6313). The example below therefore drives its own spinner
  flag rather than reaching into `event.target`.
- **Deploy order**: Apex first, then the two LWC bundles (`contactDatatable` before
  `contactTable`, because the wrapper's markup references `c-contact-datatable`).

---

## 1. Apex controller — `ContactTableController.cls`

`@AuraEnabled(cacheable=true)` is mandatory for `@wire` — grounded: `apex-wire-method`
L7098 and `apex-result-caching` L7256 ("To use `@wire` to call an Apex method, you must
set `cacheable=true`"). The method must be `static` and `global` or `public` — L7111.
`cacheable=true` methods "must only get data, [they] can't mutate (change) data" — L7254,
which is why the writer method is a separate, non-cacheable one.

```apex
public with sharing class ContactTableController {
    /**
     * Read side. cacheable=true is required by @wire and forbids DML.
     * Bounded by design: the guide recommends loading a maximum of 50 rows at a
     * time (data-table-performance L6318).
     */
    @AuraEnabled(cacheable=true)
    public static List<Contact> getContacts(Id accountId, Integer pageSize) {
        Integer limitSize = (pageSize == null || pageSize <= 0 || pageSize > 50)
            ? 50
            : pageSize;
        return [
            SELECT Id, FirstName, LastName, Title, Email, Phone, AccountId
            FROM Contact
            WHERE AccountId = :accountId
            WITH USER_MODE
            ORDER BY LastName
            LIMIT :limitSize
        ];
    }

    /**
     * Write side. Not cacheable. One DML for the whole draft batch — this is the
     * "bulk record updates in a single transaction" path the guide recommends
     * over N calls to updateRecord() (data-table-inline-edit L5717).
     * Returns the updated Ids so the caller can pass them to
     * notifyRecordUpdateAvailable() (L5718).
     */
    @AuraEnabled
    public static List<Id> updateContacts(List<Contact> drafts) {
        if (drafts == null || drafts.isEmpty()) {
            return new List<Id>();
        }
        List<Id> touched = new List<Id>();
        for (Contact c : drafts) {
            if (c.Id == null) {
                throw new AuraHandledException(
                    'Every draft row must carry an Id; check the datatable key-field.'
                );
            }
            touched.add(c.Id);
        }
        // User mode so FLS and sharing are enforced on the write, matching the
        // WITH USER_MODE read above.
        Database.update(drafts, AccessLevel.USER_MODE);
        return touched;
    }
}
```

`ContactTableController.cls-meta.xml` — `apiVersion` matches
`templates/lwc/component-skeleton/componentSkeleton.js-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## 2. Custom data type — `contactDatatable` bundle

"You can extend from `LightningDatatable` only to create a datatable with custom data
types. Unless stated otherwise, extending any class besides `LightningElement` to create
a Lightning web component isn't supported" — grounded: `data-table-custom-types` L5795.

The `customTypes` object takes `template` (the imported HTML template),
`typeAttributes` (the list of attributes reachable as `typeAttributes.attributeName`)
and `standardCellLayout` — grounded: L5804–L5806. `standardCellLayout` defaults to
`false`, which selects the *bare* layout, and the bare layout "doesn't support
accessibility and keyboard navigation for editable types"
(`data-table-custom-types-styling` L6095). Set it to `true` — L6097.

`contactDatatable/contactDatatable.js`:

```js
import LightningDatatable from 'lightning/datatable';
import statusCell from './statusCell.html';
import statusEditCell from './statusEditCell.html';

export default class ContactDatatable extends LightningDatatable {
    // Registered custom types. Property names here are camelCase per
    // data-table-custom-types L5804-L5806.
    static customTypes = {
        contactStatus: {
            template: statusCell,
            editTemplate: statusEditCell, // data-table-custom-types-editable L6150
            standardCellLayout: true,     // required for a11y + keyboard nav (L6097, L6151)
            typeAttributes: ['tone', 'recordId', 'placeholder']
        }
    };

    // If you override connectedCallback in a class extending LightningDatatable you
    // must call super first, "to ensure the datatable is initialized correctly"
    // (data-table-custom-types L5857-L5859).
    connectedCallback() {
        super.connectedCallback();
        this.hasRegisteredCustomTypes = true;
    }
}
```

`contactDatatable/statusCell.html` — the display template. Keyboard participation is
opt-in: elements in a custom data type do not participate in navigation mode by default,
so pass `tabindex={internalTabIndex}` and `data-navigation="enable"` — grounded:
`data-table-a11y` L6234, L6239–L6240. The full keyboard-mode contract lives in
`lwc/lwc-accessibility` gotcha "`lightning-datatable` Has Two Keyboard Modes, And Custom
Cell Types Opt Out By Default"; read it before shipping a custom type.

```html
<template>
    <lightning-badge
        label={value}
        class={badgeClass}
        data-navigation="enable"
        tabindex={internalTabIndex}
    ></lightning-badge>
</template>
```

`contactDatatable/statusEditCell.html` — the edit template. "The edit template for a
custom type uses an input component that matches the output component in the custom type
template. The `lightning-input` component is recommended" — grounded:
`data-table-custom-types-editable` L6139. `data-inputable="true"` "is required for
accessibility support in the standard cell layout" — L6149. `lightning-input-field`
"isn't supported for use in a datatable" — L6170.

```html
<template>
    <lightning-input
        type="text"
        name="contactStatus"
        label={columnLabel}
        value={editedValue}
        required={required}
        placeholder={typeAttributes.placeholder}
        data-inputable="true"
    ></lightning-input>
</template>
```

`contactDatatable/contactDatatable.js-meta.xml` — a datatable extension is never dropped
on a page on its own, so `isExposed` is `false`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>false</isExposed>
</LightningComponentBundle>
```

---

## 3. Wrapper component — `contactTable` bundle

`contactTable/contactTable.html`. The element carries kebab-case attributes; the columns
array carries camelCase keys (`js-props-names` L2338).

```html
<template>
    <lightning-card title="Contacts" icon-name="standard:contact">
        <div class="slds-var-p-horizontal_small">
            <template lwc:if={showSpinner}>
                <lightning-spinner alternative-text="Loading contacts"></lightning-spinner>
            </template>

            <template lwc:if={error}>
                <p class="slds-text-color_error" role="alert">{error}</p>
            </template>

            <c-contact-datatable
                key-field="Id"
                data={rows}
                columns={columns}
                draft-values={draftValues}
                sorted-by={sortedBy}
                sorted-direction={sortDirection}
                onsort={handleSort}
                onsave={handleSave}
                oncancel={handleCancel}
                onrowaction={handleRowAction}
            ></c-contact-datatable>
        </div>
    </lightning-card>
</template>
```

UNVERIFIED (2026-09-05): `sorted-by`, `sorted-direction`, `oncancel` and `onrowaction`
are Component-Library attributes; no developer-guide page in `lwc_guide.txt` names them.
`key-field`, `data`, `columns`, `draft-values` and `onsave` are grounded at
`data-table-inline-edit` L5675–L5676; `onsort` at `data-table-custom-types` L5855.

`contactTable/contactTable.js`:

```js
import { LightningElement, api, wire } from 'lwc';
import { refreshApex } from '@salesforce/apex';
import { notifyRecordUpdateAvailable } from 'lightning/uiRecordApi';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import getContacts from '@salesforce/apex/ContactTableController.getContacts';
import updateContacts from '@salesforce/apex/ContactTableController.updateContacts';

const PAGE_SIZE = 50; // data-table-performance L6318: load at most 50 rows at a time.

const COLUMNS = [
    // fieldName must match a key on the row object, not a field label.
    { label: 'First Name', fieldName: 'FirstName', editable: true, sortable: true },
    { label: 'Last Name', fieldName: 'LastName', editable: true, sortable: true },
    { label: 'Title', fieldName: 'Title', sortable: true },
    {
        label: 'Email',
        fieldName: 'Email',
        type: 'email', // standard type, data-table-custom-types L5773-L5786
        sortable: true
    },
    {
        label: 'Status',
        fieldName: 'statusLabel', // a derived key, added by the shaping layer below
        type: 'contactStatus',    // the custom type registered in contactDatatable.js
        editable: true,
        cellAttributes: { class: { fieldName: 'statusClass' } }, // L6101-L6102
        typeAttributes: {
            tone: { fieldName: 'statusTone' },
            recordId: { fieldName: 'Id' },
            placeholder: 'Set a status'
        }
    },
    {
        type: 'action',
        typeAttributes: {
            rowActions: [
                { label: 'View', name: 'view' },
                { label: 'Assign to me', name: 'assign' }
            ]
        }
    }
];

export default class ContactTable extends LightningElement {
    @api recordId;

    columns = COLUMNS;
    rows = [];
    draftValues = [];
    sortedBy = 'LastName';
    sortDirection = 'asc';
    showSpinner = false;
    error;

    // Hold the whole provisioned result: refreshApex's argument "must be an object
    // that was previously emitted by an Apex @wire" (apex-result-caching L7264).
    wiredContactsResult;

    @wire(getContacts, { accountId: '$recordId', pageSize: PAGE_SIZE })
    wiredContacts(result) {
        // data / error are hardcoded API property names (apex-wire-method L7106-L7107).
        this.wiredContactsResult = result;
        const { data, error } = result;
        if (data) {
            this.rows = this.shape(data);
            this.error = undefined;
        } else if (error) {
            this.error = this.readError(error);
            this.rows = [];
        }
    }

    /**
     * Shaping layer. Adds the derived keys the column definitions reference and
     * returns a NEW array of NEW objects — "you must create a new object and assign
     * it to the field for the change to be detected" (reactivity-fields L2288).
     */
    shape(records) {
        return records.map((r) => {
            const statusLabel = r.Title ? 'Assigned' : 'Unassigned';
            return {
                ...r,
                statusLabel,
                statusTone: r.Title ? 'success' : 'warning',
                statusClass: r.Title ? '' : 'slds-text-color_weak'
            };
        });
    }

    /**
     * Client-side sort only. onsort gives event.detail.fieldName
     * (data-table-custom-types L5855). Nothing is re-queried: rows outside the
     * fetched page are not reordered because they are not here.
     */
    handleSort(event) {
        const { fieldName, sortDirection } = event.detail;
        const direction = sortDirection === 'desc' ? -1 : 1;
        // Sort a COPY. Array.prototype.sort mutates in place, and an in-place
        // mutation of this.rows is not observed (reactivity-fields L2288, L2311-L2315).
        const sorted = [...this.rows].sort((a, b) => {
            const left = a[fieldName] === undefined || a[fieldName] === null ? '' : a[fieldName];
            const right = b[fieldName] === undefined || b[fieldName] === null ? '' : b[fieldName];
            if (left === right) {
                return 0;
            }
            return (left > right ? 1 : -1) * direction;
        });
        this.rows = sorted;
        this.sortedBy = fieldName;
        this.sortDirection = sortDirection;
    }

    /**
     * Inline edit save. event.detail.draftValues holds "the edited field values and
     * the record Id as an array of objects" (data-table-inline-edit L5711).
     * One Apex DML for the whole batch (L5717), then notifyRecordUpdateAvailable
     * because Apex writes bypass LDS (L5718), awaited before the notify (L5721),
     * then refreshApex to re-provision the wire (apex-wire-method L7098).
     */
    async handleSave(event) {
        const drafts = event.detail.draftValues;
        if (!drafts || drafts.length === 0) {
            return;
        }
        this.showSpinner = true;
        try {
            // Strip the derived keys — only real Contact fields may reach Apex.
            const payload = drafts.map((d) => ({
                Id: d.Id,
                FirstName: d.FirstName,
                LastName: d.LastName
            }));
            const touched = await updateContacts({ drafts: payload });
            notifyRecordUpdateAvailable(touched.map((id) => ({ recordId: id })));
            await refreshApex(this.wiredContactsResult);
            // Clear drafts only once the server round trip succeeded; clearing
            // draftValues is also what hides the datatable footer
            // (data-table-inline-edit L5712).
            this.draftValues = [];
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Saved',
                    message: `${touched.length} contact(s) updated`,
                    variant: 'success'
                })
            );
        } catch (e) {
            // Drafts are deliberately NOT cleared: the user keeps their edits.
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Save failed',
                    message: this.readError(e),
                    variant: 'error'
                })
            );
        } finally {
            this.showSpinner = false;
        }
    }

    handleCancel() {
        this.draftValues = [];
    }

    /**
     * Row action -> CustomEvent for the parent. The guide shows the handler shape:
     * event.detail.action and event.detail.row (data-table-tree-grid L5632-L5634,
     * data-table-a11y L5978).
     */
    handleRowAction(event) {
        const action = event.detail.action;
        const row = event.detail.row;
        this.dispatchEvent(
            new CustomEvent('contactaction', {
                detail: { actionName: action.name, recordId: row.Id },
                bubbles: true,
                composed: false
            })
        );
    }

    readError(e) {
        if (e && e.body && e.body.message) {
            return e.body.message;
        }
        return 'Unexpected error';
    }
}
```

`contactTable/contactTable.js-meta.xml`:

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
            <objects>
                <object>Account</object>
            </objects>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

---

## 4. Jest test — `contactTable/__tests__/contactTable.test.js`

Tests live in a `__tests__` folder at the top level of the bundle and end in `.test.js` —
grounded: `unit-testing-using-jest-create-tests` L12328, L12331. The folder must be in
`.forceignore` so it is never deployed — L12329–L12330. `element.shadowRoot` is the
test-only API for querying across the shadow boundary — L12379. After `emit()`ing mock
wire data, resolve a promise so the assertion runs after the rerender —
`unit-testing-using-wire-utility` L12548–L12549. Config: `templates/lwc/jest.config.js`.

```js
import { createElement } from 'lwc';
import ContactTable from 'c/contactTable';
import getContacts from '@salesforce/apex/ContactTableController.getContacts';

// The Apex wire adapter mock "mimics calls to an Apex method and includes any error
// status" (unit-testing-using-wire-utility L12524).
jest.mock(
    '@salesforce/apex/ContactTableController.getContacts',
    () => {
        const { createApexTestWireAdapter } = require('@salesforce/sfdx-lwc-jest');
        return { default: createApexTestWireAdapter(jest.fn()) };
    },
    { virtual: true }
);

jest.mock(
    '@salesforce/apex/ContactTableController.updateContacts',
    () => ({ default: jest.fn(() => Promise.resolve([])) }),
    { virtual: true }
);

const MOCK_CONTACTS = [
    { Id: '003000000000001AAA', FirstName: 'Ada', LastName: 'Zeta', Title: 'CTO' },
    { Id: '003000000000002AAA', FirstName: 'Bo', LastName: 'Alpha', Title: null }
];

function build() {
    const element = createElement('c-contact-table', { is: ContactTable });
    element.recordId = '001000000000001AAA';
    document.body.appendChild(element);
    return element;
}

function table(element) {
    return element.shadowRoot.querySelector('c-contact-datatable');
}

describe('c-contact-table', () => {
    afterEach(() => {
        // The jsdom instance is shared across test cases in a file, so reset the DOM
        // (unit-testing-using-jest-create-tests L12336-L12339).
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('renders one row per wired record, keyed by Id', async () => {
        const element = build();
        getContacts.emit(MOCK_CONTACTS);
        await Promise.resolve();

        const dt = table(element);
        expect(dt).not.toBeNull();
        expect(dt.keyField).toBe('Id');
        expect(dt.data).toHaveLength(2);
        expect(dt.data.map((r) => r.Id)).toEqual([
            '003000000000001AAA',
            '003000000000002AAA'
        ]);
        // The shaping layer added the derived key the Status column references.
        expect(dt.data[0].statusLabel).toBe('Assigned');
        expect(dt.data[1].statusLabel).toBe('Unassigned');
    });

    it('reorders rows on sort and hands back a new array reference', async () => {
        const element = build();
        getContacts.emit(MOCK_CONTACTS);
        await Promise.resolve();

        const dt = table(element);
        const before = dt.data;
        expect(before.map((r) => r.LastName)).toEqual(['Zeta', 'Alpha']);

        dt.dispatchEvent(
            new CustomEvent('sort', {
                detail: { fieldName: 'LastName', sortDirection: 'asc' }
            })
        );
        await Promise.resolve();

        const after = table(element).data;
        expect(after.map((r) => r.LastName)).toEqual(['Alpha', 'Zeta']);
        // A new reference, not an in-place sort: reactivity-fields L2288.
        expect(after).not.toBe(before);
    });

    it('emits contactaction with the row Id when a row action fires', async () => {
        const element = build();
        getContacts.emit(MOCK_CONTACTS);
        await Promise.resolve();

        const handler = jest.fn();
        element.addEventListener('contactaction', handler);

        table(element).dispatchEvent(
            new CustomEvent('rowaction', {
                detail: { action: { name: 'assign' }, row: MOCK_CONTACTS[0] }
            })
        );
        await Promise.resolve();

        expect(handler).toHaveBeenCalledTimes(1);
        expect(handler.mock.calls[0][0].detail).toEqual({
            actionName: 'assign',
            recordId: '003000000000001AAA'
        });
    });

    it('surfaces a wire error instead of rendering stale rows', async () => {
        const element = build();
        getContacts.error({ body: { message: 'Insufficient access' } }, 403);
        await Promise.resolve();

        const alert = element.shadowRoot.querySelector('[role="alert"]');
        expect(alert.textContent).toBe('Insufficient access');
    });
});
```

---

## 5. Apex test — `ContactTableControllerTest.cls`

```apex
@IsTest
private class ContactTableControllerTest {
    @TestSetup
    static void makeData() {
        Account a = new Account(Name = 'Datatable Co');
        insert a;
        List<Contact> people = new List<Contact>();
        for (Integer i = 0; i < 200; i++) {
            people.add(new Contact(
                FirstName = 'First' + i,
                LastName = 'Last' + String.valueOf(i).leftPad(3, '0'),
                AccountId = a.Id
            ));
        }
        insert people;
    }

    @IsTest
    static void getContactsCapsThePageAtFifty() {
        Account a = [SELECT Id FROM Account LIMIT 1];
        Test.startTest();
        List<Contact> page = ContactTableController.getContacts(a.Id, 500);
        Test.stopTest();
        Assert.areEqual(50, page.size(), 'Page size must be clamped to 50 rows');
        Assert.isNotNull(page[0].Id, 'Id must be selected — it is the datatable key-field');
    }

    @IsTest
    static void getContactsDefaultsWhenPageSizeIsNull() {
        Account a = [SELECT Id FROM Account LIMIT 1];
        List<Contact> page = ContactTableController.getContacts(a.Id, null);
        Assert.areEqual(50, page.size(), 'A null pageSize must fall back to the default');
    }

    @IsTest
    static void updateContactsSavesTheWholeDraftBatchInOneDml() {
        List<Contact> drafts = [SELECT Id, Title FROM Contact LIMIT 200];
        for (Contact c : drafts) {
            c.Title = 'Edited';
        }
        Test.startTest();
        List<Id> touched = ContactTableController.updateContacts(drafts);
        Test.stopTest();
        Assert.areEqual(200, touched.size(), 'Every draft row must come back');
        Assert.areEqual(
            200,
            [SELECT COUNT() FROM Contact WHERE Title = 'Edited'],
            'A 200-row draft batch must persist in one transaction'
        );
    }

    @IsTest
    static void updateContactsRejectsADraftWithNoId() {
        Boolean threw = false;
        try {
            ContactTableController.updateContacts(
                new List<Contact>{ new Contact(LastName = 'NoId') }
            );
        } catch (AuraHandledException e) {
            threw = true;
        }
        Assert.isTrue(threw, 'A draft row without an Id means the key-field is wrong');
    }

    @IsTest
    static void updateContactsHandlesAnEmptyBatch() {
        Assert.areEqual(
            0,
            ContactTableController.updateContacts(new List<Contact>()).size(),
            'An empty draft batch is a no-op, not an error'
        );
    }
}
```

---

## 6. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>ContactTableController</members>
        <members>ContactTableControllerTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>contactDatatable</members>
        <members>contactTable</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 7. Deploy and verify

```bash
# 1. Keep Jest tests out of the org (unit-testing-using-jest-create-tests L12329-L12330).
grep -q '__tests__' .forceignore || echo '**/__tests__/**' >> .forceignore

# 2. Static check before deploying.
python3 skills/lwc/lwc-data-table/scripts/check_lwc_data_table.py \
    --manifest-dir force-app/main/default

# 3. Jest — the bundle must have at least one passing describe.
npm run test:unit -- contactTable

# 4. Deploy.
sf project deploy start --manifest package.xml --target-org <alias>

# 5. Apex tests.
sf apex run test --class-names ContactTableControllerTest \
    --result-format human --code-coverage --wait 10 --target-org <alias>

# 6. Confirm the read path returns a bounded page.
sf data query --target-org <alias> --query \
  "SELECT COUNT(Id) FROM Contact WHERE AccountId = '001xx000003DGb2AAG'"
```

**Verification step in the org:** open an Account record page, drop `contactTable` on it,
edit First Name in two rows, and confirm (a) the footer with Cancel/Save appears only
after you tab out of the cell (`data-table-inline-edit` L5712), (b) after Save the toast
reports 2 rows and the footer disappears, and (c) the related list on the same page shows
the new values without a browser refresh — that last one is what
`notifyRecordUpdateAvailable` bought you (L5718).

---

## Where to go next

| You need | Read |
|---|---|
| More custom cell types — progress bars, pickers, images | `lwc/lwc-custom-datatable-types` |
| Infinite scroll, row-level errors, deeper inline-edit variants | `lwc/lwc-datatable-advanced` |
| Keyboard modes and the a11y contract for custom cells | `lwc/lwc-accessibility` |
| `refreshApex` vs `RefreshView` vs `notifyRecordUpdateAvailable` | `lwc/lwc-wire-refresh-patterns` |
| More rows than the datatable should hold | `lwc/lwc-virtualized-lists` |
