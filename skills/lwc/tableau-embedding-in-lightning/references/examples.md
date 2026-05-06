# Examples — Tableau Embedding in Lightning

## Example 1 — Custom LWC with JWT-based SSO

**HTML.**

```html
<template>
    <div class="tableau-container" lwc:dom="manual"></div>
</template>
```

**JavaScript.**

```javascript
import { LightningElement, api } from 'lwc';
import { loadScript } from 'lightning/platformResourceLoader';
import tableauApi from '@salesforce/resourceUrl/tableauEmbeddingApiV3';
import generateJwt from '@salesforce/apex/TableauJwtService.generate';

export default class TableauDashboard extends LightningElement {
    @api recordId;
    isInitialized = false;

    async renderedCallback() {
        if (this.isInitialized) return;
        this.isInitialized = true;
        await loadScript(this, tableauApi);

        const token = await generateJwt({ contextRecordId: this.recordId });
        const viz = document.createElement('tableau-viz');
        viz.src = 'https://prod-eu-a.online.tableau.com/#/site/acme/views/Sales/Dashboard';
        viz.token = token;
        viz.toolbar = 'bottom';
        viz.hideTabs = true;

        // Pass record context as a Tableau filter parameter.
        const filter = document.createElement('viz-filter');
        filter.field = 'AccountId';
        filter.value = this.recordId;
        viz.appendChild(filter);

        this.template.querySelector('.tableau-container').appendChild(viz);
    }
}
```

**Apex.** `TableauJwtService.generate(String contextRecordId)`
returns a short-lived JWT signed with the Tableau-side Connected
App's secret. The exact JWT shape is in Tableau's docs; key claims
include `iss` (Connected App Client Id), `sub` (the Salesforce
user's email), `aud` (Tableau site URL), `exp` (expiry, e.g. 5
minutes from now), and a `scp` claim listing required scopes (e.g.
`tableau:views:embed`).

---

## Example 2 — CSP Trusted Sites configuration

Setup -> CSP Trusted Sites -> New:

- Trusted Site Name: `Tableau_Production`
- Trusted Site URL: `https://prod-eu-a.online.tableau.com`
- Active: checked
- Context: `All` (or `Lightning Experience`)
- Frame-Source: checked
- Connect-Source: checked (if Apex fetches the Tableau API)
- Image-Source / Style-Source / etc.: per Tableau's documented
  CSP requirements

Without this, the embedded `<iframe>` is blocked silently and the
component renders empty.

---

## Example 3 — Row-level security configuration on the Tableau side

**Data source filter (Tableau).**

```
[Owner_Email] = USERNAME()
```

Where:

- `[Owner_Email]` is a column in the Tableau data source carrying
  the email of the row's owner.
- `USERNAME()` returns the identity Tableau resolved from the
  embedded session (set by the JWT `sub` claim).

**Salesforce-side requirement.** The JWT generated in Apex must
have `sub` set to the Salesforce user's email AND that email must
match the email Tableau provisioned for the user. A mismatch
silently filters everything out.

---

## Example 4 — Tableau Viz LWC (drag-and-drop, no code)

App Builder -> Add Component -> "Tableau Viz" (the platform-
provided LWC) -> drop on the page -> configure the View URL.

Use this when:

- You don't need programmatic filters / parameters.
- SSO is already working at the org level (e.g. SAML SSO into
  Tableau Cloud is set up identically to Salesforce).
- The dashboard is generic (not record-context-aware).

Use a custom LWC when:

- You need to pass `recordId` as a Tableau filter.
- You need to listen to viz events.
- You need to dynamically swap views.

---

## Example 5 — Tableau Pulse (insights / metric) embedding

Tableau Pulse provides AI-driven metric summaries; embedding is
similar to dashboard embedding but uses Pulse-specific URLs and
the Embedding API supports a `<pulse-metric>` element.

**Pattern.**

```javascript
const pulse = document.createElement('pulse-metric');
pulse.metricId = '<metric-uuid>';
pulse.token = token;  // same JWT pattern
this.template.querySelector('.pulse-container').appendChild(pulse);
```

**Why this matters.** Pulse summaries are succinct and well-suited
to Lightning record pages where a full dashboard is too dense.

---

## Example 6 — Auth: JWT vs SAML vs anonymous

| Auth | Use when | Tradeoffs |
|---|---|---|
| JWT (Connected App in Tableau) | Programmatic, per-request token | Best for embedded SaaS; required for fine-grained RLS |
| SAML SSO (org-level into Tableau) | User has separate Tableau session via SAML | Simplest if SAML already in place; less control of identity claim |
| Anonymous (no auth) | Fully public dashboard | Almost never appropriate; data is exposed |

Default for most embedding scenarios: JWT. SAML works if the user is
already SAML-SSO'd into Tableau and you accept whatever identity
Tableau resolves them as.
