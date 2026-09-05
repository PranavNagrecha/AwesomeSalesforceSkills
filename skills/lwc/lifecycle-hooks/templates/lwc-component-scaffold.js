/**
 * [componentName].js
 *
 * Purpose:      <<REPLACE: what this component does>>
 * Owner:        <<REPLACE: team / individual>>
 * Dependencies: <<REPLACE: Apex class, wire adapters, child components>>
 *
 * Lifecycle contract (see references/code-examples.md for the worked version):
 *   constructor        parent -> child, super() first, no DOM, no @api reads
 *   connectedCallback  parent -> child, can fire MORE THAN ONCE, synchronous
 *   render             returns a template reference, nothing else
 *   renderedCallback   child -> parent, runs after EVERY render, guard one-time work
 *   disconnectedCallback  parent -> child, undoes connectedCallback line for line
 */

import { LightningElement, api, wire } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

// <<REPLACE: import your Apex method>>
// import getMyData from '@salesforce/apex/MyService.getMyData';

export default class ComponentName extends NavigationMixin(LightningElement) {

    // ─── Public API ───────────────────────────────────────────────────────────
    @api recordId;
    // @api myProp;   // Never mutate @api props directly — a nested write throws
    //                // "Invalid mutation"; make a shallow copy first.

    // ─── Private State ────────────────────────────────────────────────────────
    _data;
    _error;
    _isLoading = true;
    _hasRendered = false;       // renderedCallback one-time guard
    _resizeHandler;             // bound handler reference; removeEventListener needs
                                // the SAME object, so bind once and store it
    _subscription = null;       // existence guard for re-entrant connectedCallback

    // ─── Wire ─────────────────────────────────────────────────────────────────
    // <<REPLACE: your wire adapter>>
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
        // Environment work only — child elements do not exist yet.
        // Keep this synchronous: the framework does not await a returned promise.
        // <<REPLACE or delete: window/document listener>>
        // this._resizeHandler = this.handleResize.bind(this);
        // window.addEventListener('resize', this._resizeHandler);

        // <<REPLACE or delete: message-channel subscription, guarded>>
        // if (!this._subscription) {
        //     this._subscription = subscribe(this.messageContext, CHANNEL,
        //         (message) => this.handleMessage(message));
        // }
    }

    disconnectedCallback() {
        // One line here for every setup line above. Delete both or keep both.
        // window.removeEventListener('resize', this._resizeHandler);
        // unsubscribe(this._subscription);
        // this._subscription = null;
    }

    renderedCallback() {
        // One-time DOM setup only. Every field on this class is reactive, so an
        // ungated assignment here re-enters this hook.
        if (this._hasRendered) {
            return;
        }
        this._hasRendered = true;

        // <<REPLACE or delete: one-time DOM work — focus, measure, library init>>
    }

    // ─── Event Handlers ───────────────────────────────────────────────────────

    handleNavigate() {
        // Always use NavigationMixin — never window.location.href
        this[NavigationMixin.Navigate]({
            type: 'standard__recordPage',
            attributes: {
                recordId: this.recordId,
                objectApiName: '<<REPLACE: ObjectApiName>>',
                actionName: 'view'
            }
        });
    }

    handleSave() {
        // <<REPLACE: save logic>>
        // Always use ShowToastEvent — never alert()
        this.dispatchEvent(new ShowToastEvent({
            title: 'Success',
            message: '<<REPLACE: Record saved successfully.>>',
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
