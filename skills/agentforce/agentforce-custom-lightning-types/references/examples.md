# Examples — Agentforce Custom Lightning Types

All code below is illustrative scaffolding authored from the official Metadata API and
Lightning Types developer guides. Replace `c__` namespace, field names, and markup with
your own. API version target: `64.0`+.

## Example 1: Branded output card (renderer)

**Context:** an Employee agent has a "Search Flights" action whose Apex method returns a
`Flight` result. By default the agent shows the fields as a plain list. You want a styled
card with the airline, times, and price.

**Problem:** without a renderer, the typed result is rendered generically; presentation
can't be controlled without polluting the Apex contract with display strings.

**Solution:**

Apex output class (the source of truth the schema projects from):

```apex
global with sharing class Flight {
    @AuraEnabled global String airline;
    @AuraEnabled global String origin;
    @AuraEnabled global String destination;
    @AuraEnabled global String departISO;
    @AuraEnabled global Decimal priceUSD;
}
```

`lightningTypes/flightResponse/schema.json`:

```json
{
  "title": "Flight Response",
  "description": "A flight result returned by the Search Flights action",
  "lightning:type": "@apexClassType/c__Flight"
}
```

`lightningTypes/flightResponse/lightningDesktopGenAi/renderer.json`:

```json
{
  "renderer": {
    "componentOverrides": {
      "$": { "definition": "c/flightDetails" }
    }
  }
}
```

Renderer LWC `flightDetails`:

```javascript
// flightDetails.js
import { LightningElement, api } from 'lwc';
export default class FlightDetails extends LightningElement {
    @api value;   // the Flight payload
    @api schema;  // the projected type definition
    get price() { return this.value?.priceUSD; }
}
```

```xml
<!-- flightDetails.js-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>64.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__AgentforceOutput</target>
    </targets>
</LightningComponentBundle>
```

**Why it works:** the schema binds the type to the `Flight` Apex class via `@apexClassType`,
so the platform knows which fields exist; the `"$"` override hands the whole payload to
`flightDetails` through `@api value` on the matching channel.

---

## Example 2: Custom input form (editor)

**Context:** the same agent has a "Filter Flights" action that takes a `FlightRequestFilter`
input. You want a date-range picker and a non-stop toggle instead of the default fields.

**Problem:** the default editor can't express a date range or cross-field rules; validating
only in Apex surfaces errors after the user submits.

**Solution:**

`lightningTypes/flightFilter/lightningDesktopGenAi/editor.json`:

```json
{
  "editor": {
    "componentOverrides": {
      "$": { "definition": "c/flightFilter" }
    }
  }
}
```

Editor LWC `flightFilter` dispatches `valuechange` so the host binds input live:

```javascript
// flightFilter.js
import { LightningElement, api } from 'lwc';
export default class FlightFilter extends LightningElement {
    @api value;
    @api schema;
    handleChange(event) {
        const next = { ...this.value, nonStop: event.target.checked };
        this.dispatchEvent(new CustomEvent('valuechange', { detail: next }));
    }
}
```

```xml
<!-- flightFilter.js-meta.xml -->
<targets><target>lightning__AgentforceInput</target></targets>
```

**Why it works:** the editor target marks the LWC as an input surface; emitting `valuechange`
is the contract the host listens to for real-time data binding.

---

## Example 3: Deployment manifest

**Context:** ship the bundle and its LWCs to a sandbox.

`package.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>*</members>
    <name>LightningTypeBundle</name>
  </types>
  <types>
    <members>flightDetails</members>
    <members>flightFilter</members>
    <name>LightningComponentBundle</name>
  </types>
  <version>64.0</version>
</Package>
```

Deploy with the Salesforce CLI:

```bash
sf project deploy start --manifest package.xml
```

**Why it works:** `LightningTypeBundle` supports the wildcard `*` member and deploys like
any other source-format metadata; the LWCs must deploy alongside the bundle that references
them. Targeting `64.0` satisfies the type's minimum API version.

---

## Anti-Pattern: re-declaring projected fields in schema.json

**What practitioners do:** hand-write a full JSON-Schema `properties` block in `schema.json`
listing every field, in addition to the `@apexClassType` binding.

**What goes wrong:** the field list drifts from the Apex class (the real source of truth),
producing properties the renderer never receives or validation that contradicts the class.

**Correct approach:** bind with `"lightning:type": "@apexClassType/c__ClassName"` and let the
platform project the `@AuraEnabled` members; add schema constraints only where the docs
support layering them on top of the projection.
