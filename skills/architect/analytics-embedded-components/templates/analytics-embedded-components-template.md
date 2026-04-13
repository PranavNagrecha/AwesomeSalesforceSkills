# Analytics Embedded Components — Work Template

Use this template when embedding a CRM Analytics dashboard on a Lightning or Experience Cloud page, or when embedding a custom LWC inside an Analytics dashboard canvas.

## Scope

**Skill:** `analytics-embedded-components`

**Request summary:** (fill in what the user asked for)

**Embedding direction:** (choose one)
- [ ] Pattern A — Dashboard embedded IN a Lightning/Experience page
- [ ] Pattern B — Custom LWC embedded INSIDE an Analytics dashboard canvas

---

## Context Gathered

Answer these before writing any code:

| Question | Answer |
|---|---|
| Target surface | Lightning record/app/home page / Experience Cloud page / Analytics dashboard canvas |
| Correct component for surface | `wave-wave-dashboard-lwc` / `wave-community-dashboard` / `analytics__Dashboard` target |
| Dashboard identifier | Developer name: `___________` OR 18-char ID (0FK): `___________` |
| Record context needed? | Yes / No — if Yes, record ID source: `{!recordId}` / `@api recordId` / other |
| Pre-loaded filter state needed? | Yes / No — if Yes, state JSON: `___________` |
| CRM Analytics license confirmed for all target users? | Yes / No / Unknown |

---

## Pattern A: Dashboard on a Page

Fill this section for Pattern A (dashboard embedded IN a Lightning or Experience Cloud page).

### Component Markup

```html
<!-- Replace placeholders. Use wave-wave-dashboard-lwc for Lightning pages,
     wave-community-dashboard for Experience Cloud pages.
     Use EITHER developer-name OR dashboard (0FK ID) — never both. -->

<wave-wave-dashboard-lwc
    developer-name="[DEVELOPER_API_NAME]"
    record-id={recordId}
    show-title="[true|false]"
    show-sharing-button="[true|false]">
</wave-wave-dashboard-lwc>
```

### js-meta.xml Target

```xml
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <!-- Choose the correct target for the surface: -->
        <target>lightning__RecordPage</target>
        <!-- <target>lightning__AppPage</target> -->
        <!-- <target>lightning__HomePage</target> -->
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <property name="recordId" type="String" label="Record ID" />
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

### JavaScript (if wrapping in a custom LWC)

```javascript
import { LightningElement, api } from 'lwc';

export default class DashboardHost extends LightningElement {
    @api recordId; // populated by Lightning runtime on record pages

    // If building state dynamically:
    get dashboardState() {
        // Always use JSON.stringify() — never string concatenation
        const stateObj = {
            // myFilterStep: { selections: [this.someValue] }
        };
        return JSON.stringify(stateObj);
    }
}
```

---

## Pattern B: Custom LWC Inside an Analytics Dashboard Canvas

Fill this section for Pattern B (custom LWC embedded INSIDE an Analytics dashboard).

### js-meta.xml with analytics__Dashboard Target

```xml
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>analytics__Dashboard</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="analytics__Dashboard">
            <!-- Define properties the dashboard designer can configure per widget instance -->
            <property name="[PROPERTY_NAME]"
                      type="[String|Integer|Boolean]"
                      label="[Human-readable label]"
                      default="[default value]" />
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

### Deployment and Dashboard Setup

- [ ] LWC deployed to org with `analytics__Dashboard` target in js-meta.xml
- [ ] Dashboard opened in Analytics Studio edit mode
- [ ] Custom component visible in widget picker under "Custom Components"
- [ ] Component dragged onto canvas and widget properties configured
- [ ] Dashboard saved and tested in preview mode

---

## Checklist

Work through these before marking complete:

- [ ] Embedding direction confirmed: Pattern A (dashboard-in-page) or Pattern B (LWC-in-dashboard)
- [ ] Correct component selected: `wave-wave-dashboard-lwc` (Lightning) / `wave-community-dashboard` (Experience Cloud) / `analytics__Dashboard` target (Pattern B)
- [ ] Only ONE of `developer-name` or `dashboard` (0FK ID) is set — never both
- [ ] `record-id` binding is correct (`{!recordId}` in App Builder, `@api recordId` in LWC)
- [ ] `state` JSON built with `JSON.stringify()`, not string concatenation — validated before use
- [ ] Dashboard-side bindings confirmed if relying on `record-id` for context filtering
- [ ] CRM Analytics license confirmed for target users
- [ ] Component renders on target page in test/sandbox environment
- [ ] Context filtering verified end-to-end with a test record

---

## Notes

Record any deviations from the standard pattern and why:

(fill in here)
