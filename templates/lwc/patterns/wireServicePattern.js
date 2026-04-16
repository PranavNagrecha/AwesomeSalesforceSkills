import { LightningElement, api, wire } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';

import NAME_FIELD from '@salesforce/schema/Account.Name';
import INDUSTRY_FIELD from '@salesforce/schema/Account.Industry';

/**
 * wireServicePattern — canonical reactive read of a record via LDS.
 *
 * Preferred over imperative Apex when:
 *  - You only need to READ data the UI Record API already provides.
 *  - Reactivity on record change is desired.
 *  - FLS + sharing must be automatic (LDS enforces both).
 *
 * Do NOT use wire adapters for:
 *  - Writes (use `uiRecordApi.updateRecord` imperatively).
 *  - Anything requiring Apex business logic — use `imperativeApexPattern.js`.
 */
const FIELDS = [NAME_FIELD, INDUSTRY_FIELD];

export default class WireServicePattern extends LightningElement {
    @api recordId;

    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    record;

    get name()     { return getFieldValue(this.record.data, NAME_FIELD); }
    get industry() { return getFieldValue(this.record.data, INDUSTRY_FIELD); }

    get hasError() {
        return !!(this.record && this.record.error);
    }

    get isReady() {
        return !!(this.record && this.record.data);
    }
}
