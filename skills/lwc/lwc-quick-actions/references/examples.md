# Examples — LWC Quick Actions

## Example 1: Screen Quick Action — Edit Opportunity Close Plan

**Context:** Sales ops wants a "Close Plan" button on the Opportunity record page that opens a modal with three text areas (risks, next steps, decision criteria), saves the result to custom fields, and closes the modal.

**Problem:** Developers ship the save and the `CloseActionScreenEvent` dispatch in the same synchronous click handler. The modal closes before the imperative Apex promise resolves, the component is torn down, the promise chain runs on a detached instance, and the user sees no toast — sometimes no save either.

**Solution:**

`closePlanEdit.js-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
  <apiVersion>63.0</apiVersion>
  <isExposed>true</isExposed>
  <targets>
    <target>lightning__RecordAction</target>
  </targets>
  <targetConfigs>
    <targetConfig targets="lightning__RecordAction" actionType="ScreenAction">
      <objects>
        <object>Opportunity</object>
      </objects>
    </targetConfig>
  </targetConfigs>
</LightningComponentBundle>
```

`closePlanEdit.js`:

```javascript
import { LightningElement, api } from 'lwc';
import { CloseActionScreenEvent } from 'lightning/actions';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { getRecordNotifyChange } from 'lightning/uiRecordApi';
import saveClosePlan from '@salesforce/apex/ClosePlanController.save';

export default class ClosePlanEdit extends LightningElement {
  @api recordId;
  risks = '';
  nextSteps = '';
  criteria = '';
  isSaving = false;

  handleChange(event) {
    this[event.target.name] = event.target.value;
  }

  async handleSave() {
    this.isSaving = true;
    try {
      await saveClosePlan({
        opportunityId: this.recordId,
        risks: this.risks,
        nextSteps: this.nextSteps,
        criteria: this.criteria,
      });
      getRecordNotifyChange([{ recordId: this.recordId }]);
      this.dispatchEvent(new ShowToastEvent({
        title: 'Close plan saved',
        variant: 'success',
      }));
      this.dispatchEvent(new CloseActionScreenEvent());
    } catch (error) {
      this.isSaving = false;
      this.dispatchEvent(new ShowToastEvent({
        title: 'Could not save close plan',
        message: error?.body?.message ?? 'Unknown error',
        variant: 'error',
      }));
    }
  }

  handleCancel() {
    this.dispatchEvent(new CloseActionScreenEvent());
  }
}
```

**Why it works:** `await` gates the close on the actual save result. The toast is dispatched while the component is still alive. `getRecordNotifyChange` refreshes the record page without a hard reload. On failure, the modal stays open so the user can retry.

---

## Example 2: Headless Quick Action — Mark Case As Read

**Context:** Service agents want a "Mark as Read" button on Case that flips a `IsAcknowledged__c` flag, shows a toast, and does nothing visual otherwise.

**Problem:** Developers build it as a screen action with an auto-submitting template. The modal flashes, focus jumps, and the agent sees a visual glitch for a non-UI operation.

**Solution:**

`markCaseRead.js-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
  <apiVersion>63.0</apiVersion>
  <isExposed>true</isExposed>
  <targets>
    <target>lightning__RecordAction</target>
  </targets>
  <targetConfigs>
    <targetConfig targets="lightning__RecordAction" actionType="Action">
      <objects>
        <object>Case</object>
      </objects>
    </targetConfig>
  </targetConfigs>
</LightningComponentBundle>
```

`markCaseRead.js` (no HTML file):

```javascript
import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { getRecordNotifyChange } from 'lightning/uiRecordApi';
import markRead from '@salesforce/apex/CaseAcknowledgementController.markRead';

export default class MarkCaseRead extends LightningElement {
  @api recordId;

  @api async invoke() {
    try {
      await markRead({ caseId: this.recordId });
      getRecordNotifyChange([{ recordId: this.recordId }]);
      this.dispatchEvent(new ShowToastEvent({
        title: 'Case marked as read',
        variant: 'success',
      }));
    } catch (error) {
      this.dispatchEvent(new ShowToastEvent({
        title: 'Could not mark case as read',
        message: error?.body?.message ?? 'Unknown error',
        variant: 'error',
      }));
    }
  }
}
```

**Why it works:** No template, so nothing visual happens. `invoke()` awaits the save before returning — the platform only dismisses the action after the promise resolves. Toasts render on the host record page because the event bubbles out of the action surface.

---

## Anti-Pattern: Headless Action That Opens A Modal Internally

**What practitioners do:** Declare `actionType="Action"` but then attempt to open a custom modal from inside `invoke()` using a `lightning-overlay-library`-style call, expecting the "headless" nature to keep the button from rendering its own frame.

**What goes wrong:** The component has no template and no supported place to host modal markup from an `invoke()` call. The modal either never appears or appears detached from focus/keyboard handling. The action closes as soon as `invoke()` resolves, destroying the modal mid-interaction.

**Correct approach:** If the user must see or confirm anything, use `actionType="ScreenAction"` and render the UI in the quick-action modal. If the only confirmation needed is a yes/no, use `LightningConfirm.open({ ... })` from inside `invoke()` — it is a platform dialog that works headlessly — and branch on its result before resolving.
