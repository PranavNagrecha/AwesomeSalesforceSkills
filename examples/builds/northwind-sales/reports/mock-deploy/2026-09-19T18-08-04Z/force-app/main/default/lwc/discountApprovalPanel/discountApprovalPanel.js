import { LightningElement, api, wire } from 'lwc';
import {
    getRecord,
    getFieldValue,
    notifyRecordUpdateAvailable
} from 'lightning/uiRecordApi';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

import submitForApproval from '@salesforce/apex/OpportunityApprovalController.submitForApproval';

import DISCOUNT_FIELD from '@salesforce/schema/Opportunity.Discount__c';
import APPROVAL_STATUS_FIELD from '@salesforce/schema/Opportunity.Approval_Status__c';

/**
 * discountApprovalPanel - build northwind-sales, step M3-S04.
 *
 * Shows the Opportunity discount and its approval status, and submits the deal into the
 * `Discount_Approval` approval process. The Submit button is enabled only when the discount
 * is above the policy threshold and nothing is already Pending or Approved (Q35).
 *
 * DATA STRATEGY (skills/lwc/wire-service-patterns, "Decision Guidance"):
 *   read  -> UI API, twice over, and no Apex at all. `lightning-record-view-form` in the
 *            template renders the two fields with the platform's own labels, formatting and
 *            field-level security; `@wire(getRecord)` here provisions the same two fields so
 *            the button rule can be computed in JavaScript. Both go through Lightning Data
 *            Service and share its cache, so this is one read model, not two.
 *            "Standard record read with strong platform security defaults -> UI API wire
 *            adapter or LDS base component."
 *   write -> imperative Apex. "User clicks Save or Submit and writes data -> Imperative call
 *            ... Writes cannot be cacheable=true, so they cannot be wired." The shape is
 *            templates/lwc/patterns/imperativeApexPattern.js, copy-renamed.
 *   refresh -> notifyRecordUpdateAvailable([{ recordId }]), never refreshApex: the stale read
 *            is a UI API wire, and "refreshApex() on a non-Apex wire adapter is deprecated"
 *            (wire-service-patterns gotcha 7). This is Q34's "the component refreshes the
 *            record after submit".
 *
 * WHY THE CONTROLLER AND NOT THE INVOCABLE (plan decision D6, step M3-S03):
 *   An LWC can only import an @AuraEnabled method, and @InvocableMethod cannot be stacked
 *   with it - "Stackable annotations: @Deprecated only"
 *   (skills/apex/invocable-methods/SKILL.md). `OpportunityApprovalSubmitAction` is Flow's
 *   entry point; `OpportunityApprovalController.submitForApproval(Id opportunityId)` is
 *   this component's. Both delegate to `OpportunityApprovalService.submitOne`.
 *
 * THE FAILED-RESULT SHAPE:
 *   `submitForApproval` returns an `OpportunityApprovalService.SubmitOutcome`
 *   ({ opportunityId, success, message, instanceStatus }) and refuses by returning
 *   `success = false` with a `message` rather than by throwing - that is Q30's answer, and
 *   the reason the controller does not raise AuraHandledException. Both paths are handled
 *   below; only the thrown path would reach `catch`.
 *
 * DECISION TREE: standards/decision-trees/automation-selection.md Q8 - "Can the action
 *   complete in under 10s without custom UI? No -> LWC calling imperative Apex (see
 *   templates/lwc/patterns/imperativeApexPattern.js)" - recorded as plan decision D5.
 */

/** Static config: no `$`, so it is never re-evaluated (lwc_guide L6445). */
const FIELDS = [DISCOUNT_FIELD, APPROVAL_STATUS_FIELD];

/**
 * Approval_Status__c is a restricted picklist with exactly Pending / Approved / Rejected,
 * and is blank until a rep submits (artefacts/M1-S01/objects/Opportunity/fields/
 * Approval_Status__c.field-meta.xml). Q35: the button is disabled for Pending and Approved;
 * Rejected and blank both leave it available, so a rejected deal can be re-submitted.
 */
const BLOCKING_STATUSES = ['Pending', 'Approved'];

/** Matches the js-meta.xml design attribute default. Both are the plain number, not 0.20. */
const DEFAULT_THRESHOLD = 20;

/** Bundle-scoped log tag - agents/lwc-builder/AGENT.md Step 3, "Diagnosability". */
const LOG_TAG = '[discountApprovalPanel]';

export default class DiscountApprovalPanel extends LightningElement {
    /**
     * Set by the record page. Undefined on the first tick, and an undefined reactive
     * parameter means the wire is not evaluated at all (lwc_guide L6408) - which is why
     * `isSubmitDisabled` is true until the record arrives rather than defaulting open.
     * @type {string}
     */
    @api recordId;

    /**
     * The discount percentage above which manager approval is required, surfaced in
     * Lightning App Builder rather than hard-coded (plan decision D8, assumption A35).
     *
     * App Builder hands design-attribute values to the component as STRINGS even when the
     * property is declared `type="Integer"`, so every read goes through `this.threshold`,
     * which coerces. Comparing `'20' > 20` untouched would be a silent false.
     * @type {number|string}
     */
    @api discountThreshold = DEFAULT_THRESHOLD;

    // ------------------------------------------------------------------ internal state

    /** True from the click until the Apex promise settles. Never exposed with @api. */
    isSubmitting = false;

    /** The live-region sentence: the outcome of the last submit, success or failure. */
    outcomeMessage = '';

    /** Styles and wording of the live region; never the only signal - the text says it too. */
    outcomeIsError = false;

    // ------------------------------------------------------------------------- the wire

    /**
     * PROPERTY FORM. Correct here because nothing needs the provisioned object retained:
     * the refresh path is `notifyRecordUpdateAvailable`, not `refreshApex`, and that takes
     * record ids rather than a wire result (wire-service-patterns, "Property Form Versus
     * Function Form" and "Two Data Sources Means Two Caches").
     */
    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    opportunity;

    // --------------------------------------------------------------------------- getters

    /**
     * UNVERIFIED (2026-09-19) - assumption A35. A Percent field carries the fraction in
     * FORMULA context (0.20 for 20%) and the plain number outside it (20). Only the formula
     * half is grounded in this library, which is why the validation rule and the approval
     * entry criteria compare against 0.20 while this component compares against 20. If a
     * retrieved Opportunity shows the UI API returning 0.25 for a 25% discount, this getter
     * and the threshold are the only things that change - the Jest suite pins the reading
     * in both directions so the change fails a test rather than shipping silently.
     */
    get discount() {
        return getFieldValue(this.opportunity?.data, DISCOUNT_FIELD);
    }

    get approvalStatus() {
        return getFieldValue(this.opportunity?.data, APPROVAL_STATUS_FIELD);
    }

    /** The design attribute, coerced. Anything unparseable falls back to the default. */
    get threshold() {
        const parsed = Number(this.discountThreshold);
        return Number.isFinite(parsed) ? parsed : DEFAULT_THRESHOLD;
    }

    get isAboveThreshold() {
        return typeof this.discount === 'number' && this.discount > this.threshold;
    }

    get isApprovalUnderway() {
        return BLOCKING_STATUSES.includes(this.approvalStatus);
    }

    /**
     * The one rule the requester described, in one place. Q35: "button disabled when
     * Discount__c <= 20 or Approval_Status__c in (Pending, Approved); enabled otherwise".
     * The first two terms are this component's own safety: no record id and no provisioned
     * discount both mean the rule cannot be evaluated, and an unevaluated rule is closed,
     * not open.
     */
    get isSubmitDisabled() {
        return (
            this.isSubmitting ||
            !this.recordId ||
            !this.isAboveThreshold ||
            this.isApprovalUnderway
        );
    }

    /**
     * Why the button is in the state it is in, as visible text. A disabled control that does
     * not say why is the accessibility failure this panel would otherwise ship
     * (skills/lwc/lwc-accessibility, "Validation feedback is programmatic and not
     * color-only" and the focus-contract question).
     */
    get submitHint() {
        if (this.isSubmitting) {
            return 'Submitting this opportunity for approval.';
        }
        if (!this.recordId) {
            return 'This panel needs to be placed on an opportunity record page.';
        }
        if (this.recordError) {
            return 'The discount is unavailable, so nothing can be submitted from here.';
        }
        if (this.isApprovalUnderway) {
            return `An approval is already ${String(this.approvalStatus).toLowerCase()} for this deal, so there is nothing to submit.`;
        }
        if (!this.isAboveThreshold) {
            return `Approval is only needed when the discount is above ${this.threshold}%.`;
        }
        return `A discount above ${this.threshold}% needs manager approval before this deal can be closed won.`;
    }

    /**
     * Loading is "no data and no error yet" and is NOT an error state
     * (wire-service-patterns gotcha 8), so this reads `error` and nothing else.
     * UI API READ errors carry `body` as an ARRAY; Apex read/write and network errors carry
     * it as an OBJECT (lwc_guide data-error L6568-L6571) - `reduceError` branches on both.
     */
    get recordError() {
        return this.opportunity?.error ? this.reduceError(this.opportunity.error) : undefined;
    }

    get outcomeClass() {
        const base = 'slds-text-body_small slds-var-m-top_x-small';
        return this.outcomeIsError ? `${base} slds-text-color_error` : base;
    }

    // -------------------------------------------------------------------------- handlers

    /**
     * The imperative write, shaped after templates/lwc/patterns/imperativeApexPattern.js:
     * loading state set before the call, errors surfaced through ShowToastEvent rather than
     * the console, and the flag cleared in `finally` so a rejected promise cannot leave a
     * spinner running.
     *
     * The guard is not decoration. A disabled `lightning-button` fires no click on a real
     * page, but the sfdx-lwc-jest stub has no behaviour at all and `click()` on it calls
     * straight through - so without this line the "does not call Apex while disabled" test
     * would pass on a component that does.
     */
    async handleSubmit() {
        if (this.isSubmitDisabled) {
            return;
        }

        this.isSubmitting = true;
        this.outcomeMessage = '';
        this.outcomeIsError = false;

        try {
            const outcome = await submitForApproval({ opportunityId: this.recordId });

            if (outcome && outcome.success) {
                this.outcomeMessage = outcome.instanceStatus
                    ? `Submitted for approval. Approval status: ${outcome.instanceStatus}.`
                    : 'Submitted for approval.';
                this.toast('Submitted for approval', this.outcomeMessage, 'success');
                // One refresh call, for one stale cache. The read is a UI API wire, so this
                // is the documented function; it also reaches the record detail and any
                // other LDS wire on this record, which refreshApex would not.
                await notifyRecordUpdateAvailable([{ recordId: this.recordId }]);
            } else {
                // Q30's shape: a refusal comes back as success = false with a message, not
                // as an exception. Nothing is refreshed, because nothing changed.
                const message =
                    (outcome && outcome.message) ||
                    'The submission was refused and no reason was returned.';
                this.failWith(message);
                console.warn(`${LOG_TAG} submit refused: ${message}`);
            }
        } catch (error) {
            // Reached only when the call itself fails - a platform error, a lost session,
            // or an exception the service did not convert into an outcome.
            const message = this.reduceError(error);
            this.failWith(message);
            // Never log the wired value or the raw error object here: a @wire proxy logged
            // directly is unreadable in DevTools (agents/lwc-builder/AGENT.md Step 3).
            console.error(`${LOG_TAG} submit failed: ${message}`);
        } finally {
            this.isSubmitting = false;
            // The live region is always mounted, so it is focusable in this same tick - the
            // "focus lands nowhere after a state flip" trap only applies to a node the flip
            // itself renders (skills/lwc/lwc-accessibility). `lwc:ref` rather than
            // `this.template.querySelector` per skills/lwc/lwc-template-refs.
            this.refs.outcome?.focus();
        }
    }

    // --------------------------------------------------------------------------- helpers

    failWith(message) {
        this.outcomeIsError = true;
        this.outcomeMessage = `Submit failed. ${message}`;
        this.toast('Submit failed', message, 'error');
    }

    /**
     * ShowToastEvent is legal on this bundle's surfaces and only there: assumption A17 fixes
     * the targets at Lightning Experience desktop and the Salesforce mobile app, with no
     * Experience Cloud target. `lightning/platformShowToastEvent` "is not supported in LWR
     * sites" (lwc_guide L4649, L4773) - adding `lightningCommunity__*` to the js-meta.xml
     * means switching this to `lightning/toast`.
     */
    toast(title, message, variant) {
        this.dispatchEvent(new ShowToastEvent({ title, message, variant }));
    }

    reduceError(error) {
        if (Array.isArray(error?.body)) {
            return error.body.map((entry) => entry.message).join(', ');
        }
        if (typeof error?.body?.message === 'string') {
            return error.body.message;
        }
        return error?.message ?? 'Unknown error';
    }
}
