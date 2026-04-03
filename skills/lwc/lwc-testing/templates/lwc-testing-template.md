# LWC Jest Test Skeleton

```js
import { createElement } from 'lwc';
import ComponentUnderTest from 'c/componentUnderTest';

const flushPromises = () => Promise.resolve();

describe('c-component-under-test', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    function buildElement(props = {}) {
        const element = createElement('c-component-under-test', {
            is: ComponentUnderTest
        });
        Object.assign(element, props);
        document.body.appendChild(element);
        return element;
    }

    it('renders the default state', async () => {
        const element = buildElement();
        await flushPromises();
        expect(element).toBeTruthy();
    });

    it('handles the primary user interaction', async () => {
        const element = buildElement();
        element.shadowRoot.querySelector('[data-id=\"primary-action\"]').click();
        await flushPromises();

        expect(
            element.shadowRoot.querySelector('[data-id=\"result\"]')
        ).not.toBeNull();
    });

    it('renders the error state', async () => {
        const element = buildElement();
        // Arrange failure path for wire or imperative Apex mock here.
        await flushPromises();

        expect(
            element.shadowRoot.querySelector('[data-id=\"error\"]')
        ).not.toBeNull();
    });
});
```

## Add-On Sections

- Wire adapter registration:
- Imperative Apex mock:
- Navigation mock assertions:
- Accessibility smoke checks:
