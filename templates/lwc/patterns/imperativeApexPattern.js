import { LightningElement, api } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

// Replace with your actual @AuraEnabled(cacheable=false) method.
// The Apex class MUST enforce CRUD/FLS — use `WITH USER_MODE` or SecurityUtils.
import recalculateTotals from '@salesforce/apex/OrderService.recalculateTotals';

/**
 * imperativeApexPattern — canonical call to @AuraEnabled Apex.
 *
 * Use when:
 *  - You are writing data (wire is read-only).
 *  - You need Apex business logic (not plain CRUD).
 *  - The call is user-initiated (button click) — not auto-reactive.
 *
 * Rules:
 *  - Always handle loading + error states.
 *  - Surface Apex errors to the user via `ShowToastEvent`, not console.
 *  - Never cache-bust via `cacheable=true` on write methods.
 */
export default class ImperativeApexPattern extends LightningElement {
    @api recordId;

    loading = false;
    error;

    async handleClick() {
        this.loading = true;
        this.error = undefined;
        try {
            const result = await recalculateTotals({ orderId: this.recordId });
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Totals updated',
                    message: `New total: ${result.total}`,
                    variant: 'success'
                })
            );
        } catch (e) {
            this.error = this.formatError(e);
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Update failed',
                    message: this.error,
                    variant: 'error'
                })
            );
        } finally {
            this.loading = false;
        }
    }

    formatError(error) {
        if (!error) return 'Unknown error';
        if (Array.isArray(error.body)) {
            return error.body.map((e) => e.message).join(', ');
        }
        if (error.body && error.body.message) {
            return error.body.message;
        }
        return error.message || String(error);
    }
}
