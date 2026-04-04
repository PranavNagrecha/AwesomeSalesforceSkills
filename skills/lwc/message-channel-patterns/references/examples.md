# Examples — Message Channel Patterns

## Example 1: Master-Detail Page with Independent LWC Regions

**Context:** A service console Lightning App page has two columns: a `caseList` component on the left that lists open cases, and a `caseDetail` component on the right that shows case details. Both components are placed as independent regions in App Builder — they share no common LWC ancestor. The team needs the detail panel to refresh when the user selects a row in the list.

**Problem:** Custom events from `caseList` cannot reach `caseDetail` because they are siblings in the DOM with no shared parent LWC component to catch and re-dispatch events. Using a global variable or a shared Apex call on every row click would introduce unnecessary server round-trips and coupling.

**Solution:**

1. Create the message channel metadata:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/messageChannels/CaseSelected.messageChannel-meta.xml -->
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>CaseSelected</masterLabel>
    <isExposed>false</isExposed>
    <description>Published when a case row is clicked in the case list component.</description>
    <lightningMessageFields>
        <fieldName>caseId</fieldName>
        <description>Salesforce record ID of the selected case</description>
    </lightningMessageFields>
</LightningMessageChannel>
```

2. Publisher — `caseList.js`:

```javascript
import { LightningElement, wire } from 'lwc';
import { publish, MessageContext } from 'lightning/messageService';
import CASE_SELECTED_CHANNEL from '@salesforce/messageChannel/CaseSelected__c';

export default class CaseList extends LightningElement {
    @wire(MessageContext)
    messageContext;

    handleRowClick(event) {
        const payload = { caseId: event.currentTarget.dataset.caseId };
        publish(this.messageContext, CASE_SELECTED_CHANNEL, payload);
    }
}
```

3. Subscriber — `caseDetail.js`:

```javascript
import { LightningElement, wire, track } from 'lwc';
import { subscribe, unsubscribe, MessageContext } from 'lightning/messageService';
import CASE_SELECTED_CHANNEL from '@salesforce/messageChannel/CaseSelected__c';

export default class CaseDetail extends LightningElement {
    @wire(MessageContext)
    messageContext;

    subscription = null;
    @track selectedCaseId;

    connectedCallback() {
        this.subscription = subscribe(
            this.messageContext,
            CASE_SELECTED_CHANNEL,
            (message) => { this.selectedCaseId = message.caseId; }
        );
    }

    disconnectedCallback() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }
}
```

**Why it works:** Both components live on the same Lightning page and share the same LMS message bus. The default scope (no `APPLICATION_SCOPE`) is sufficient here because both components are in the same navigation context — neither is in a workspace tab that can go inactive independently.

---

## Example 2: Visualforce-to-LWC Bridge on a Mixed Lightning Page

**Context:** A legacy `productPricingVF` Visualforce page is embedded as an iframe inside a Lightning App page via a standard Visualforce component. A modern `orderSummaryLwc` LWC component sits next to it on the same page. When the pricing table in the VF page recalculates a total, the LWC component must update its displayed discount and tax fields without a full page reload.

**Problem:** The VF page is inside an iframe. Standard LWC-to-LWC message passing cannot cross the iframe boundary. Polling the server from LWC on an interval is wasteful and creates race conditions.

**Solution:**

1. Deploy the `PricingUpdated__c` message channel to the org:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/messageChannels/PricingUpdated.messageChannel-meta.xml -->
<LightningMessageChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>PricingUpdated</masterLabel>
    <isExposed>false</isExposed>
    <description>Published by VF pricing table when totals are recalculated.</description>
    <lightningMessageFields>
        <fieldName>netTotal</fieldName>
        <description>Net order total after discounts</description>
    </lightningMessageFields>
    <lightningMessageFields>
        <fieldName>taxAmount</fieldName>
        <description>Calculated tax amount</description>
    </lightningMessageFields>
</LightningMessageChannel>
```

2. Publisher inside the Visualforce page (uses `sforce.one` — the only supported LMS API from VF):

```javascript
// Inside productPricingVF.page <script> block
function onRecalculate(netTotal, taxAmount) {
    // APPLICATION scope is required to cross the iframe boundary
    sforce.one.publish('PricingUpdated__c', {
        netTotal: netTotal,
        taxAmount: taxAmount
    });
}
```

3. LWC subscriber — `orderSummaryLwc.js`:

```javascript
import { LightningElement, wire, track } from 'lwc';
import { subscribe, unsubscribe, MessageContext, APPLICATION_SCOPE } from 'lightning/messageService';
import PRICING_UPDATED_CHANNEL from '@salesforce/messageChannel/PricingUpdated__c';

export default class OrderSummaryLwc extends LightningElement {
    @wire(MessageContext)
    messageContext;

    subscription = null;
    @track netTotal = 0;
    @track taxAmount = 0;

    connectedCallback() {
        // APPLICATION_SCOPE is required because the publisher is inside a VF iframe
        this.subscription = subscribe(
            this.messageContext,
            PRICING_UPDATED_CHANNEL,
            (msg) => {
                this.netTotal = msg.netTotal;
                this.taxAmount = msg.taxAmount;
            },
            { scope: APPLICATION_SCOPE }
        );
    }

    disconnectedCallback() {
        unsubscribe(this.subscription);
        this.subscription = null;
    }
}
```

**Why it works:** `sforce.one.publish()` is the only supported way to publish LMS messages from inside a Visualforce iframe. The subscriber must use `APPLICATION_SCOPE` because the message originates outside the active navigation area. Without `APPLICATION_SCOPE`, the LWC component would never receive the message, regardless of whether the components are visually co-located.

---

## Anti-Pattern: Subscribing in the Constructor

**What practitioners do:** Place the `subscribe()` call inside the LWC component constructor, before `@wire` has resolved `MessageContext`, because the constructor runs earlier and feels like an init hook.

**What goes wrong:** `MessageContext` is injected by the wire service, which runs after construction. Calling `subscribe()` in the constructor with an unresolved context either throws an error or silently creates a broken subscription that never receives messages. The component appears to work on first render because the error is silent, but messages never arrive.

**Correct approach:** Always call `subscribe()` in `connectedCallback()`, after the wire service has had a chance to inject `MessageContext`. Unsubscribe in `disconnectedCallback()`. Never subscribe in the constructor or in a `@wire` handler that may run before the component is attached to the DOM.
