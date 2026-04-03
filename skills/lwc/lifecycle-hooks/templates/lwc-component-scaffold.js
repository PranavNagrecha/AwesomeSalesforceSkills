/**
 * [componentName].js
 *
 * Purpose:    TODO: describe what this component does
 * Owner:      TODO: team / individual
 * Dependencies: TODO: Apex class, wire adapters, child components
 *
 * Lifecycle: connectedCallback → wire → renderedCallback (guarded)
 */

import { LightningElement, api, wire } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

// TODO: Import your Apex method
// import getMyData from '@salesforce/apex/MyService.getMyData';

export default class [ComponentName] extends NavigationMixin(LightningElement) {

    // ─── Public API ───────────────────────────────────────────────────────────
    @api recordId;
    // @api myProp;   // Never mutate @api props directly — clone before modifying

    // ─── Private State ────────────────────────────────────────────────────────
    _data;
    _error;
    _isLoading = true;
    _initialized = false;       // renderedCallback guard
    _resizeHandler;             // Bound event handler reference for cleanup

    // ─── Wire ─────────────────────────────────────────────────────────────────
    // TODO: Replace with your wire adapter
    // @wire(getMyData, { recordId: '$recordId' })
    // wiredData({ data, error }) {
    //     this._isLoading = false;
    //     if (data) {
    //         this._data = data;
    //         this._error = undefined;
    //     } else if (error) {
    //         this._error = error.body?.message ?? 'An unknown error occurred.';
    //         this._data = undefined;
    //     }
    // }

    // ─── Lifecycle ────────────────────────────────────────────────────────────

    connectedCallback() {
        // Add event listeners — store bound reference for cleanup
        // TODO: Uncomment and replace with your listener if needed
        // this._resizeHandler = this.handleResize.bind(this);
        // window.addEventListener('resize', this._resizeHandler);
    }

    disconnectedCallback() {
        // Remove ALL event listeners added in connectedCallback
        // TODO: Uncomment if you added listeners above
        // window.removeEventListener('resize', this._resizeHandler);
    }

    renderedCallback() {
        // One-time DOM setup only — guard prevents re-execution on every render
        if (this._initialized) return;
        this._initialized = true;

        // TODO: One-time DOM work here (e.g. third-party lib init, focus management)
    }

    // ─── Event Handlers ───────────────────────────────────────────────────────

    handleNavigate() {
        // Always use NavigationMixin — never window.location.href
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: {
                recordId: this.recordId,
                objectApiName: 'TODO_ObjectAPIName',
                actionName: 'view'
            }
        });
    }

    handleSave() {
        // TODO: Add save logic
        // Always use ShowToastEvent — never alert()
        this.dispatchEvent(new ShowToastEvent({
            title: 'Success',
            message: 'TODO: Record saved successfully.',
            variant: 'success'
        }));
    }

    handleError(error) {
        this.dispatchEvent(new ShowToastEvent({
            title: 'Error',
            message: error?.body?.message ?? 'An unexpected error occurred.',
            variant: 'error',
            mode: 'sticky'
        }));
    }

    // ─── Getters ──────────────────────────────────────────────────────────────

    get hasError() {
        return !!this._error;
    }

    get isLoaded() {
        return !this._isLoading && !!this._data;
    }

    get isLoading() {
        return this._isLoading;
    }
}
