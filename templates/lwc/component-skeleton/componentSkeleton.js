import { LightningElement, api, track } from 'lwc';

/**
 * componentSkeleton — canonical shell for new LWC components.
 *
 * Conventions:
 *  - @api for every public reactive property; kebab-case in markup.
 *  - @track only when property is a mutable object and you need deep reactivity.
 *  - loading / error state always modelled; template renders them explicitly.
 *  - Errors dispatched as a custom `error` event for parents to observe.
 *  - Accessibility: never use div-onclick. Prefer `lightning-button` or proper role.
 */
export default class ComponentSkeleton extends LightningElement {
    @api recordId;
    @api title = 'Untitled';

    @track state = {
        loading: false,
        error: null,
        data: null
    };

    get hasError() {
        return !!this.state.error;
    }

    get isReady() {
        return !this.state.loading && !this.state.error && this.state.data;
    }

    connectedCallback() {
        this.load();
    }

    async load() {
        this.state = { ...this.state, loading: true, error: null };
        try {
            const data = await this.fetchData();
            this.state = { loading: false, error: null, data };
        } catch (error) {
            this.state = { loading: false, error: this.formatError(error), data: null };
            this.dispatchEvent(new CustomEvent('error', { detail: { error } }));
        }
    }

    // Override in subclass / replace with imperative Apex call.
    async fetchData() {
        return { placeholder: true };
    }

    formatError(error) {
        if (!error) return 'Unknown error';
        if (Array.isArray(error.body)) {
            return error.body.map((e) => e.message).join(', ');
        }
        if (error.body && typeof error.body.message === 'string') {
            return error.body.message;
        }
        return error.message || String(error);
    }

    handleRetry() {
        this.load();
    }
}
