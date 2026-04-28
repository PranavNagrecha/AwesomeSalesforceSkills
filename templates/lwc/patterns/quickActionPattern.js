import { LightningElement, api } from 'lwc';
import { CloseActionScreenEvent } from 'lightning/actions';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { updateRecord } from 'lightning/uiRecordApi';

/**
 * quickActionPattern — canonical LWC for a Lightning Quick Action
 * (target = `lightning__RecordAction` with `actionType: ScreenAction`).
 *
 * Lifecycle contract enforced by the runtime:
 *  - `@api invoke()` is called when the action is invoked from a Headless action.
 *    Headless actions must NOT render UI — do the work and `dispatchEvent(new CloseActionScreenEvent())`.
 *  - Screen actions render the component normally. The user clicks Save / Cancel
 *    in the modal footer or in your own buttons. Either way, dispatch
 *    `CloseActionScreenEvent` to dismiss the modal.
 *
 * Do NOT:
 *  - Call `window.location.reload()` to refresh — fire `RefreshEvent` from
 *    `lightning/refresh` so the parent record page re-wires its data.
 *  - Block on long callouts in `invoke()` for headless actions — the spinner
 *    is the user's only feedback. Time-box and toast on completion.
 */
export default class QuickActionPattern extends LightningElement {
    @api recordId;
    @api objectApiName;

    isSaving = false;
    rationale = '';

    handleRationaleChange(event) {
        this.rationale = event.target.value;
    }

    async handleSave() {
        if (!this.rationale?.trim()) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Rationale required',
                variant: 'error'
            }));
            return;
        }
        this.isSaving = true;
        try {
            await updateRecord({
                fields: {
                    Id: this.recordId,
                    Approval_Rationale__c: this.rationale
                }
            });
            this.dispatchEvent(new ShowToastEvent({
                title: 'Saved',
                variant: 'success'
            }));
        } catch (err) {
            this.dispatchEvent(new ShowToastEvent({
                title: 'Save failed',
                message: err?.body?.message ?? err?.message,
                variant: 'error'
            }));
            return;
        } finally {
            this.isSaving = false;
        }
        this.dispatchEvent(new CloseActionScreenEvent());
    }

    handleCancel() {
        this.dispatchEvent(new CloseActionScreenEvent());
    }

    @api
    async invoke() {
        // Used by Headless Quick Actions only. For Screen actions this is a no-op.
        // Do not render UI in here — the runtime expects the action to complete and close.
    }
}
