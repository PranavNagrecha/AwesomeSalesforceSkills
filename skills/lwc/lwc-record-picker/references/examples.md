# Examples — LWC Record Picker

Two worked scenarios and one anti-pattern showing how to configure
`lightning-record-picker` for real-world lookup needs. The scenarios
target the two most common shapes: a single-object picker bound to
matching/display info that captures the selected Id, and a filtered
picker that scopes results via the GraphQL-style `filter` criteria
while presenting richer secondary context with `display-info`. The
anti-pattern shows what breaks when practitioners reach for a
hand-rolled `lightning-combobox` + imperative SOQL instead of the
platform base component.

---

## Example 1: Account picker with matching on Name + Industry, capturing the selected Id

**Context:** A "Log Visit" LWC on a custom site-visit object needs the
field rep to pick the Account they visited. The org is large (200K+
Accounts) so a plain pick-list won't fit; the rep usually knows the
Account name but sometimes only remembers the industry vertical they
were calling on. The selected Account Id is then passed into an Apex
controller that creates the visit record.

**Problem:** A first attempt sets only `object-api-name="Account"` and
`label="Account"` with no `matching-info`. The picker works, but
matching is limited to the object's primary name field — reps who
type "Tech" looking for the technology accounts they covered get
zero hits because nothing in the Account *name* contains "Tech". The
parent's change handler also reads `event.target.value` and gets
`undefined` instead of the Id.

**Solution:** Configure `matching-info` so the picker queries both
`Name` (primary) and `Industry` (additional). Configure `display-info`
so the dropdown shows the matched Account name as the primary line
with `Industry` as the secondary context line. Read the selection
from `event.detail.recordId`.

```javascript
// logVisit.js
import { LightningElement, api, wire } from 'lwc';
import { createRecord } from 'lightning/uiRecordApi';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class LogVisit extends LightningElement {
    @api recordId;          // current rep context
    selectedAccountId;

    matchingInfo = {
        primaryField:   { fieldPath: 'Name' },
        additionalFields: [{ fieldPath: 'Industry' }]
    };

    displayInfo = {
        primaryField:     'Name',
        additionalFields: ['Industry']
    };

    handleAccountChange(event) {
        // event.detail.recordId — NOT event.target.value
        // value is null when the user clears the picker
        this.selectedAccountId = event.detail.recordId;
    }

    async handleSubmit() {
        if (!this.selectedAccountId) {
            this.dispatchEvent(new ShowToastEvent({
                title:   'Pick an Account first',
                variant: 'warning'
            }));
            return;
        }
        await createRecord({
            apiName: 'Site_Visit__c',
            fields:  {
                Account__c: this.selectedAccountId,
                Visit_Date__c: new Date().toISOString().slice(0, 10),
                Rep__c: this.recordId
            }
        });
        // reset the picker by toggling value back to null
        this.selectedAccountId = null;
    }
}
```

```html
<!-- logVisit.html -->
<template>
    <lightning-record-picker
        label="Account"
        placeholder="Search by name or industry"
        object-api-name="Account"
        matching-info={matchingInfo}
        display-info={displayInfo}
        value={selectedAccountId}
        required
        onchange={handleAccountChange}>
    </lightning-record-picker>
    <lightning-button
        label="Log Visit"
        variant="brand"
        onclick={handleSubmit}>
    </lightning-button>
</template>
```

**Why it works:** `matching-info.additionalFields` extends the search
beyond the primary name field, so typing "Tech" matches Accounts whose
`Industry = 'Technology'` even when the Account name doesn't contain
the substring. `display-info.additionalFields` adds the matched
secondary value as a subtitle row in the dropdown, so the rep can
disambiguate between two "Acme" entries (one Manufacturing, one
Retail) without opening each record. `event.detail.recordId` is the
documented payload of the `change` event — `event.target.value` is
`undefined` because the picker exposes the selection through the
event detail, not as a DOM attribute. Binding `value={selectedAccountId}`
back to the component gives a one-line reset path: setting the bound
property to `null` clears the chip.

---

## Example 2: Filtered Contact picker scoped to one Account, with `display-info` icon + secondary text

**Context:** A "Send Quote" LWC on an Opportunity record page needs the
sales rep to pick a Contact, but only Contacts who (a) belong to the
Opportunity's parent Account, (b) have an email address on file, and
(c) have not been opted out of marketing. The dropdown should show
each Contact's name as primary, the Contact's Title as secondary,
and the standard Contact icon so the rep visually distinguishes a
Contact picker from an Account picker on the same page.

**Problem:** Practitioners often build this as `object-api-name="Contact"`
with no filter and rely on the rep to remember which Contacts belong
to which Account — wrong Account's Contacts show up in the dropdown.
The other common miss is passing the filter as a SOQL-string
("AccountId = '001...'") and getting silent zero-result behavior with
no error: `lightning-record-picker` filters use the UI API filter
JSON shape, not SOQL.

**Solution:** Build the `filter` reactively from `this.accountId`
using the documented `criteria` array shape (`fieldPath`, `operator`,
`value`). Use `filterLogic` to combine three conditions with explicit
AND. Set `display-info.additionalFields: ['Title']` and let the
picker auto-render the Contact entity icon based on `object-api-name`.

```javascript
// sendQuoteContactPicker.js
import { LightningElement, api, wire } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import OPP_ACCOUNT_ID from '@salesforce/schema/Opportunity.AccountId';

export default class SendQuoteContactPicker extends LightningElement {
    @api recordId;          // Opportunity Id (record page context)
    accountId;

    matchingInfo = {
        primaryField:     { fieldPath: 'Name' },
        additionalFields: [{ fieldPath: 'Email' }]
    };

    displayInfo = {
        primaryField:     'Name',
        additionalFields: ['Title']
    };

    @wire(getRecord, { recordId: '$recordId', fields: [OPP_ACCOUNT_ID] })
    wiredOpportunity({ data }) {
        if (data) {
            this.accountId = getFieldValue(data, OPP_ACCOUNT_ID);
        }
    }

    // Reactive getter: filter rebuilds whenever this.accountId changes.
    get filter() {
        if (!this.accountId) {
            // Filter that never matches anything — clean empty state.
            return {
                criteria: [
                    { fieldPath: 'Id', operator: 'eq', value: '000000000000000000' }
                ]
            };
        }
        return {
            criteria: [
                { fieldPath: 'AccountId',      operator: 'eq', value: this.accountId },
                { fieldPath: 'Email',          operator: 'ne', value: null },
                { fieldPath: 'HasOptedOutOfEmail', operator: 'eq', value: false }
            ],
            filterLogic: '1 AND 2 AND 3'
        };
    }

    handleContactChange(event) {
        this.dispatchEvent(new CustomEvent('contactselect', {
            detail: { contactId: event.detail.recordId }
        }));
    }
}
```

```html
<!-- sendQuoteContactPicker.html -->
<template>
    <lightning-record-picker
        label="Recipient Contact"
        placeholder="Search Contacts on this Account"
        object-api-name="Contact"
        matching-info={matchingInfo}
        display-info={displayInfo}
        filter={filter}
        onchange={handleContactChange}>
    </lightning-record-picker>
</template>
```

**Why it works:** The `filter` object uses the UI API filter shape
that `lightning-record-picker` consumes — each criterion is a JS
object with three required keys (`fieldPath`, `operator`, `value`)
and the optional `filterLogic` string composes them with `AND` / `OR`
/ `NOT` / parentheses. The operator vocabulary (`eq`, `ne`, `lt`,
`gt`, `lte`, `gte`, `in`, `nin`, `like`, `includes`, `excludes`) is
the same set the GraphQL wire adapter uses under the hood. The
reactive getter (`get filter()`) rebuilds the object whenever
`this.accountId` is reassigned, which retriggers the picker's
internal query. The `display-info` icon comes free: when
`object-api-name` is set, the picker renders the entity icon from
the standard SLDS icon set — no manual `icon-name` needed and no CSP
nightmare around static-resource icon URLs. Returning the selection
through a typed custom event (`contactselect`, detail
`{ contactId }`) keeps the parent's contract explicit.

---

## Anti-Pattern: Hand-rolled `lightning-combobox` + imperative Apex SOQL "lookup"

**What practitioners do:**

```javascript
// DON'T DO THIS — handRolledLookup.js
import { LightningElement, track } from 'lwc';
import searchAccounts from '@salesforce/apex/AccountSearchController.searchAccounts';

export default class HandRolledLookup extends LightningElement {
    @track searchTerm = '';
    @track options    = [];
    @track selected;

    async handleType(event) {
        this.searchTerm = event.target.value;
        if (this.searchTerm.length < 2) return;
        const results = await searchAccounts({ term: this.searchTerm });
        this.options = results.map(r => ({ label: r.Name, value: r.Id }));
    }

    handleSelect(event) {
        this.selected = event.detail.value;
    }
}
```

```html
<!-- handRolledLookup.html -->
<template>
    <lightning-input
        label="Account"
        type="text"
        value={searchTerm}
        onchange={handleType}>
    </lightning-input>
    <lightning-combobox
        label="Matches"
        options={options}
        onchange={handleSelect}>
    </lightning-combobox>
</template>
```

**What goes wrong:**

1. **No typeahead optimization.** Every keystroke fires an imperative
   Apex call. With 200K Accounts, a SOQL LIKE on the unindexed `Name`
   field times out under load. `lightning-record-picker` runs the
   same logical query through the GraphQL wire adapter, which uses
   the SOSL search index — far faster and cap-free against record
   volume.
2. **No "recent items" list.** Out of the box, `lightning-record-picker`
   shows the user's most-recently-viewed records of the target object
   before they type anything. The hand-rolled version shows an empty
   dropdown until the user types two characters, then a list with no
   context. Reps complain it "feels slower" even when underlying
   latency is similar.
3. **Broken focus management and keyboard nav.** The two-component
   combo (input + combobox) needs custom JS to forward arrow keys
   from the input into the combobox option list and to manage focus
   trap during open/close. Practitioners ship without this; keyboard
   users tab past the dropdown entirely.
4. **CSP-unsafe and inconsistent entity icons.** To render the
   account/contact icon, the hand-rolled version either hardcodes
   the SLDS icon URL (breaks under strict CSP in Experience Cloud
   sites) or omits the icon (visual inconsistency with every other
   lookup on the page). `lightning-record-picker` reads
   `object-api-name`, fetches the entity's icon from the platform's
   internal registry, and stays inside the CSP contract.
5. **No `change` event contract.** Parents that consume the
   hand-rolled lookup have to subscribe to two events (input + combo)
   and stitch the state together. Practitioners get the bookkeeping
   wrong and ship parents that retain stale Ids when the user clears
   the input.

**Correct approach:** Use `lightning-record-picker`. Bind
`object-api-name`, set `matching-info`/`display-info`, optionally
add a `filter`, and read `event.detail.recordId` on `change`. The
component already includes typeahead debouncing, recent-items, focus
trap and keyboard nav per SLDS Global Focus Guidelines, the entity
icon, and a single typed event. The only legitimate reason to build
a custom lookup is a documented gap — multi-select (use
`lwc-multi-select-lookup`), external objects (the picker doesn't
support them), or a need to query non-UI-API objects. For everything
else, the correct line count for a custom lookup is zero.
