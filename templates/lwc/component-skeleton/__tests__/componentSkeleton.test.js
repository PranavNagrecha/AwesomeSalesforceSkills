import { createElement } from 'lwc';
import ComponentSkeleton from 'c/componentSkeleton';

async function flushPromises() {
    return Promise.resolve();
}

describe('c-component-skeleton', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('renders the card title', async () => {
        const element = createElement('c-component-skeleton', { is: ComponentSkeleton });
        element.title = 'Test Title';
        document.body.appendChild(element);
        await flushPromises();

        const card = element.shadowRoot.querySelector('lightning-card');
        expect(card.title).toBe('Test Title');
    });

    it('shows loading then ready state', async () => {
        const element = createElement('c-component-skeleton', { is: ComponentSkeleton });
        document.body.appendChild(element);

        const spinnerBeforeResolve = element.shadowRoot.querySelector('lightning-spinner');
        expect(spinnerBeforeResolve).not.toBeNull();

        await flushPromises();
        await flushPromises();

        const spinnerAfterResolve = element.shadowRoot.querySelector('lightning-spinner');
        expect(spinnerAfterResolve).toBeNull();
    });

    it('dispatches error on fetchData rejection', async () => {
        class FailingComponent extends ComponentSkeleton {
            async fetchData() {
                throw new Error('boom');
            }
        }
        FailingComponent.delegatesFocus = false;

        const element = createElement('c-component-skeleton', { is: FailingComponent });
        const errorHandler = jest.fn();
        element.addEventListener('error', errorHandler);
        document.body.appendChild(element);

        await flushPromises();
        await flushPromises();

        expect(errorHandler).toHaveBeenCalled();
        const alert = element.shadowRoot.querySelector('[role="alert"]');
        expect(alert.textContent).toContain('boom');
    });
});
