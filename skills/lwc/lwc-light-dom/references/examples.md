# Examples — LWC Light DOM

## Example 1: Experience Cloud FAQ Indexed By Google

**Context:** A public knowledge base on an Experience Cloud LWR site renders its FAQ entries in a custom LWC `faqAccordion`. Marketing reports that Google and Bing are not indexing the answers — the FAQ HTML is inside a shadow root so crawlers only see an empty custom element.

**Problem:** Shadow DOM hides the rendered content from crawlers that do not execute or do not fully traverse shadow trees, so the page does not rank for the question text.

**Solution:**

`faqAccordion.js`

```javascript
import { LightningElement, api } from 'lwc';

export default class FaqAccordion extends LightningElement {
    static renderMode = 'light';

    @api entries = []; // [{ id, question, answer }]

    handleToggle(event) {
        const id = event.currentTarget.dataset.id;
        const entry = this.entries.find((e) => e.id === id);
        if (entry) {
            entry.open = !entry.open;
            this.entries = [...this.entries];
        }
    }
}
```

`faqAccordion.html`

```html
<template lwc:render-mode="light">
    <section class="faq">
        <template for:each={entries} for:item="entry">
            <article key={entry.id} class="faq__item">
                <button
                    type="button"
                    class="faq__question"
                    data-id={entry.id}
                    onclick={handleToggle}
                    aria-expanded={entry.open}
                >
                    {entry.question}
                </button>
                <template lwc:if={entry.open}>
                    <div class="faq__answer">{entry.answer}</div>
                </template>
            </article>
        </template>
    </section>
</template>
```

`faqAccordion.scoped.css` (scoped — compiled with synthesized per-component selectors so rules do not bleed)

```css
.faq__item { border-bottom: 1px solid var(--dxp-s-border-color, #ccc); }
.faq__question { width: 100%; text-align: left; padding: 12px 0; font-weight: 600; }
.faq__answer { padding: 0 0 12px 0; line-height: 1.5; }
```

`faqAccordion.js-meta.xml` (Experience Cloud target + relaxed CSP capability where applicable)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>60.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>FAQ Accordion</masterLabel>
    <targets>
        <target>lightningCommunity__Default</target>
        <target>lightningCommunity__Page</target>
    </targets>
    <capabilities>
        <capability>
            <name>lightningCommunity__RelaxedCSP</name>
        </capability>
    </capabilities>
</LightningComponentBundle>
```

**Why it works:** Light DOM puts the question and answer text directly in the page HTML, so crawlers see it. The `*.scoped.css` file keeps component styles from bleeding into the rest of the site even though the DOM is un-encapsulated.

---

## Example 2: Third-Party Tooltip Library That Needs DOM Access

**Context:** A customer dashboard LWC embeds a third-party tooltip library (e.g. Tippy-style) that calls `document.querySelector('[data-tip]')` when the page loads. The library currently sees nothing because the dashboard renders inside a shadow root.

**Problem:** Shadow DOM hides the `[data-tip]` elements from the library's global querySelector, so no tooltips bind.

**Solution:**

`dashboardMetrics.js`

```javascript
import { LightningElement } from 'lwc';
import tooltipLib from '@salesforce/resourceUrl/tooltipLib';
import { loadScript } from 'lightning/platformResourceLoader';

export default class DashboardMetrics extends LightningElement {
    static renderMode = 'light';

    async connectedCallback() {
        await loadScript(this, tooltipLib);
        // Library can now scan the document for [data-tip] elements
        window.tooltipLib?.bindAll('[data-tip]');
    }
}
```

`dashboardMetrics.html`

```html
<template lwc:render-mode="light">
    <div class="metrics">
        <span class="metric" data-tip="Rolling 30-day count">Cases: {caseCount}</span>
        <span class="metric" data-tip="Weighted by stage">Pipeline: {pipeline}</span>
    </div>
</template>
```

`dashboardMetrics.scoped.css`

```css
.metrics { display: flex; gap: 16px; }
.metric { cursor: help; }
```

**Why it works:** The library's `document.querySelector` now finds the `[data-tip]` elements because they live directly in the document. Lightning Web Security still sandboxes the library's JS, so it cannot escape the LWS boundary — but the DOM lookup works.

---

## Anti-Pattern: Flipping A Managed-Package Component To Light DOM Because "One Query Failed"

**What practitioners do:** An AppExchange ISV ships a dashboard widget as a managed package. A consumer reports that their global CSS no longer applies, or an internal script cannot `querySelector` into the widget. The ISV's first response is to switch `renderMode = 'light'` to unblock the ticket.

**What goes wrong:** Every consumer org now receives a component whose styles leak into the host page. A rule like `.metric { color: red }` written for the ISV's design scope now paints random elements across the consumer's entire site. Consumers cannot scope the package's CSS after install because the package is managed. Accessibility regressions and visual bugs pile up across dozens of orgs, and the ISV cannot hotfix them without a new package version.

**Correct approach:** Keep managed-package components in shadow DOM. If the consumer legitimately needs global styling access, expose CSS custom properties (styling hooks) through the shadow boundary. If the consumer needs DOM access for their own script, provide a documented event-based or public-property API instead. Salesforce's docs explicitly warn against light DOM in managed packages for this reason.
