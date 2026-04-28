# Examples — LWC Locker → LWS Migration

Three realistic before/after examples covering the most common migration scenarios: a library that broke under Locker and works under LWS, a deep-clone shim that becomes harmful, and an in-house chart component built around `SecureElement` quirks.

---

## Example 1 — Chart.js (or jsPDF / D3) shim removal

### Before — Locker-era component with a patched library and a deep-clone shim

A custom component that renders a Chart.js chart from server-fetched data. Under Locker, Chart.js 2.x didn't see real `<canvas>` nodes (it got a `SecureElement` proxy), so the team:

1. Forked Chart.js to a "Locker-compatible" fork stored as a static resource.
2. Deep-cloned the data on the way in to "escape the proxy."
3. Mocked `HTMLCanvasElement` in Jest because canvas operations through the proxy didn't work.

```js
// myChart.js (Locker-era)
import { LightningElement, api } from 'lwc';
import { loadScript } from 'lightning/platformResourceLoader';
import CHARTJS from '@salesforce/resourceUrl/chartjs_locker_fork'; // patched fork

export default class MyChart extends LightningElement {
    @api chartData;
    chart;

    async renderedCallback() {
        if (this.chart) return;
        await loadScript(this, CHARTJS + '/Chart.min.js');

        // LOCKER WORKAROUND: deep-clone to escape SecureElement proxy on the data.
        const safeData = JSON.parse(JSON.stringify(this.chartData));

        const canvas = this.template.querySelector('canvas');
        // LOCKER WORKAROUND: canvas is a SecureElement proxy; Chart.js 2.x fork
        // pre-unwraps it via this fork's getRawNode() shim.
        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: safeData,
            options: { responsive: true }
        });
    }
}
```

```js
// jest.config.js (Locker-era)
module.exports = {
    moduleNameMapper: {
        '^@salesforce/resourceUrl/(.+)$': '<rootDir>/__mocks__/static-resource-mock.js',
    },
    setupFiles: ['jest-canvas-mock'], // LOCKER: canvas calls failed through proxy in tests
    setupFilesAfterEach: ['./test-utils/secure-window-stub.js'], // LOCKER: stub SecureWindow
};
```

Symptoms after flipping LWS in a sandbox: `chart` renders **twice** for some users, animations stutter on rerender, console shows `Cannot read properties of undefined (reading 'getRawNode')` from the patched fork (LWS no longer exposes `getRawNode`).

### After — Upstream Chart.js, no shims

Under LWS, `canvas` is a real `HTMLCanvasElement`, the upstream Chart.js build runs unmodified, and the deep-clone is now a structured-clone-style copy that strips function references the chart options expected (e.g., a custom `tooltip.callbacks.label` function).

```js
// myChart.js (LWS-clean)
import { LightningElement, api } from 'lwc';
import { loadScript } from 'lightning/platformResourceLoader';
import CHARTJS from '@salesforce/resourceUrl/chartjs'; // upstream build, no fork

export default class MyChart extends LightningElement {
    @api chartData;
    chart;

    async renderedCallback() {
        if (this.chart) return;
        await loadScript(this, CHARTJS + '/chart.umd.js');

        const canvas = this.template.querySelector('canvas');
        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: this.chartData,    // pass through — no deep clone
            options: { responsive: true }
        });
    }

    disconnectedCallback() {
        this.chart?.destroy();
    }
}
```

```js
// jest.config.js (LWS-clean)
module.exports = {
    moduleNameMapper: {
        '^@salesforce/resourceUrl/(.+)$': '<rootDir>/__mocks__/static-resource-mock.js',
    },
    // jest-canvas-mock removed — Jest still runs in jsdom, but the component-side
    // workaround (deep-clone shim) is gone, so test setup is simpler.
    // If charts are still rendered in tests you may keep jest-canvas-mock for jsdom,
    // but the SecureWindow stub is unconditionally retired.
};
```

Result: smaller static-resource bundle (drops the fork), simpler component (~10 fewer lines), faster rerender (no deep clone), and `tooltip.callbacks.label` callbacks now actually fire.

---

## Example 2 — In-house signature-pad component built around `SecureElement`

### Before — Component that reaches for `SecureElement` features

A signature-capture component used `SecureElement`-specific behaviour to detect whether a touch event came through the proxy and adapt its coordinate math:

```js
// signaturePad.js (Locker-era)
import { LightningElement } from 'lwc';

export default class SignaturePad extends LightningElement {
    onPointerDown(evt) {
        // LOCKER: evt.target is a SecureElement; raw coords need adjustment.
        const isSecure = (typeof SecureElement !== 'undefined') &&
                         (evt.target instanceof SecureElement);
        const rect = isSecure
            ? evt.target.getBoundingClientRect() // proxy hides margin in Locker — adjust below
            : evt.target.getBoundingClientRect();
        const x = isSecure ? evt.clientX - rect.left - 2 : evt.clientX - rect.left;
        const y = isSecure ? evt.clientY - rect.top - 2  : evt.clientY - rect.top;
        this.startStroke(x, y);
    }
}
```

Symptom under LWS: `SecureElement` is `undefined`, so `typeof SecureElement !== 'undefined'` is always `false`, the `isSecure` branch is dead, and the existing fallback `else` math runs — which on this codebase happened to be correct for LWS by accident. **But** the dead `instanceof SecureElement` line is a `ReferenceError` waiting to be triggered the day someone refactors the guard.

### After — Standards-based code, no Locker probe

```js
// signaturePad.js (LWS-clean)
import { LightningElement } from 'lwc';

export default class SignaturePad extends LightningElement {
    onPointerDown(evt) {
        const rect = evt.target.getBoundingClientRect();
        const x = evt.clientX - rect.left;
        const y = evt.clientY - rect.top;
        this.startStroke(x, y);
    }
}
```

The Locker-era branch is deleted; `evt.target` is a real `HTMLElement`, so the standard DOM math is correct.

---

## Example 3 — Cross-namespace component passing a callback (silent break)

### Before — Parent passes a callback to a child component in a different namespace

`acme__Dashboard` (custom-namespace dashboard) hosts `widgets__MetricCard` (a packaged component). Under Locker, the namespaces saw filtered proxies of each other but functions could still cross via the shared SecureWindow.

```js
// acme__/dashboard/dashboard.js (Locker-era — works)
import { LightningElement } from 'lwc';

export default class Dashboard extends LightningElement {
    formatValue = (n) => `$${n.toLocaleString()}`;
}
```

```html
<!-- acme__/dashboard/dashboard.html -->
<template>
    <c-widgets--metric-card value={total} formatter={formatValue}></c-widgets--metric-card>
</template>
```

```js
// widgets__/metricCard/metricCard.js (Locker-era — works)
import { LightningElement, api } from 'lwc';

export default class MetricCard extends LightningElement {
    @api value;
    @api formatter; // a function passed from the parent namespace

    get displayValue() {
        return this.formatter ? this.formatter(this.value) : this.value;
    }
}
```

Symptom after flipping LWS in a sandbox: `displayValue` returns `undefined` (or throws `TypeError: this.formatter is not a function`) because `formatter` crossed a realm boundary — the function does not transfer.

### After — Event-based pattern with structured-cloneable detail

The parent owns the formatting; the child publishes raw values via an event and the parent listens (or the parent passes a primitive flag the child interprets locally).

Cleanest fix: move formatting to the parent and pass the already-formatted string.

```js
// acme__/dashboard/dashboard.js (LWS-clean)
import { LightningElement } from 'lwc';

export default class Dashboard extends LightningElement {
    get totalDisplay() {
        return `$${this.total.toLocaleString()}`;
    }
}
```

```html
<!-- acme__/dashboard/dashboard.html -->
<template>
    <c-widgets--metric-card value={total} display-value={totalDisplay}></c-widgets--metric-card>
</template>
```

```js
// widgets__/metricCard/metricCard.js (LWS-clean)
import { LightningElement, api } from 'lwc';

export default class MetricCard extends LightningElement {
    @api value;
    @api displayValue;

    get rendered() {
        return this.displayValue ?? this.value;
    }
}
```

The hop now carries strings (structured-cloneable), not functions. This pattern is forward-compatible regardless of LWS realm boundaries.

---

## Official Sources Used

- **Salesforce Help — Lightning Web Security**: <https://help.salesforce.com/s/articleView?id=sf.security_lws_intro.htm&type=5> — defines LWS, the Session Settings toggle, the Locker → LWS comparison, and the GA timeline.
- **LWC Developer Guide — Lightning Web Security and Lightning Locker**: <https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-intro.html> — official compatibility guidance for third-party libraries and the "what changes" list (no `SecureElement` proxies, real DOM, realm-based isolation).
- **Spring '23 Release Notes — Lightning Web Security GA for LWC**: <https://help.salesforce.com/s/articleView?id=release-notes.rn_security_lws_ga.htm&type=5> — confirms the GA milestone referenced in the SKILL.
- **LWS Distortion Viewer**: <https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-distortions.html> — the official tool that lists per-API differences between native browser behaviour and LWS-distorted behaviour. Required reading when triaging a third-party-library regression.
- **Trailhead — Lightning Web Security Module**: <https://trailhead.salesforce.com/content/learn/modules/lightning-web-security> — Salesforce's own walkthrough of the migration mechanics.
- **MDN — JavaScript Realms**: <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Memory_management> and the TC39 realms proposal — background for the realm-boundary semantics that determine why functions don't transfer across namespaces under LWS.
