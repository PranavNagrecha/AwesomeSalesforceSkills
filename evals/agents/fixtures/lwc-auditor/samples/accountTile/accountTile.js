/**
 * accountTile.js — synthetic sample for lwc-auditor eval.
 * Carries:
 *   P0 innerHTML-without-sanitize — sets innerHTML from a server string
 *   P1 imperative-in-render        — imperative Apex in connectedCallback, no caching
 *   P3 untagged-console            — raw console.log
 *   P2 querySelector-over-ref      — DOM lookup that should use lwc:ref
 */
import { LightningElement, api } from 'lwc';
import getOpps from '@salesforce/apex/AccountController.getOpps';

export default class AccountTile extends LightningElement {
    @api recordId;
    @api logoUrl;
    opps = [];
    hasOpps = false;

    connectedCallback() {
        getOpps({ accountId: this.recordId })
            .then((result) => {
                this.opps = result;
                this.hasOpps = result && result.length > 0;
                console.log(result);
                const host = this.template.querySelector('.raw-html');
                host.innerHTML = '<b>' + (result[0] && result[0].Description || '') + '</b>';
            });
    }

    handleSelect() {
        this.dispatchEvent(new CustomEvent('select', { detail: this.recordId }));
    }

    handleEdit() {
        this.dispatchEvent(new CustomEvent('edit', { detail: this.recordId }));
    }
}
