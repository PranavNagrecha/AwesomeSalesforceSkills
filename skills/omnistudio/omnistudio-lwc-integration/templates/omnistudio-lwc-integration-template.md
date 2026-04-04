# OmniStudio LWC Integration — Work Template

Use this template when building or reviewing components that cross the OmniStudio/LWC boundary.

---

## Scope

**Skill:** `omnistudio/omnistudio-lwc-integration`

**Request summary:** (describe what the user asked for — embedding, custom element, IP call, or other)

**Integration direction:** (choose one)
- [ ] LWC embedding OmniScript (host LWC renders OmniScript as child component)
- [ ] Custom LWC element inside OmniScript (LWC registered as OmniScript screen element)
- [ ] LWC calling Integration Procedure (via Apex bridge)
- [ ] LWC launching OmniScript via NavigationMixin

---

## Runtime Verification

| Check | Result |
|---|---|
| OmniStudio runtime | `native` (`enableOaForCore = true`) OR `managed package` (vlocity_cmt/ins/ps) |
| Correct component tag to use | `omnistudio-omni-script` (native) OR `c-omni-script` (managed) |
| OmniScript type | |
| OmniScript subtype | |

---

## Custom LWC Element Configuration Template

Use this JSON as a starting point for configuring a custom LWC element in the OmniScript designer.
Replace all placeholder values before use.

```json
{
  "elementType": "CustomLWCElement",
  "name": "MyCustomElement",
  "label": "My Custom Element Label",
  "lwcName": "c/myCustomLwcComponent",
  "inputMap": [
    {
      "source": "OmniScriptFieldName",
      "target": "lwcPropertyName"
    }
  ],
  "outputMap": [
    {
      "source": "lwcOutputPropertyName",
      "target": "OmniScriptOutputFieldName"
    }
  ]
}
```

**Field name rules:**
- `source` in `outputMap` must match the JavaScript property key used in `pubsub.fireEvent` exactly (case-sensitive)
- `target` in `outputMap` must match the OmniScript data model field name exactly (case-sensitive)
- Mismatches silently drop data — always validate in OmniScript debug mode (`?debug=true`)

---

## Seed Data Contract

Document the seed data JSON structure before implementation. Both sides (LWC and OmniScript) must agree on field names and nesting.

```json
{
  "OmniScriptFieldName1": "value-or-merge-field",
  "OmniScriptFieldName2": "value-or-merge-field",
  "NestedGroup": {
    "NestedField": "value"
  }
}
```

**Source of truth:** The OmniScript's internal data model (inspect via `?debug=true` or the OmniScript designer's data panel).

---

## Embedding Checklist

- [ ] OmniStudio runtime confirmed (native vs managed package)
- [ ] Correct component tag selected (`omnistudio-omni-script` or `c-omni-script`)
- [ ] Seed data JSON structure documented and validated against OmniScript data model
- [ ] Seed data bound as a reactive template expression (not set imperatively after mount)
- [ ] `oncomplete` event handler implemented in parent LWC
- [ ] `hide-nav-bar` setting decided (true if parent LWC provides navigation, false to use built-in)
- [ ] Checker script run: `python3 scripts/check_omnistudio_lwc.py --manifest-dir <path>`

---

## Custom LWC Element Checklist

- [ ] `@api omniJsonData` declared to receive OmniScript context
- [ ] `@api omniOutputMap` declared to receive output field mapping
- [ ] `connectedCallback` implemented to restore state from `omniJsonData`
- [ ] `disconnectedCallback` implemented to clean up listeners
- [ ] Pubsub `fireEvent` call uses field name that exactly matches OmniScript output mapping (case-sensitive)
- [ ] No `@wire` adapters inside the custom element (use imperative Apex instead)
- [ ] OmniScript designer configured with correct component API name, input mapping, and output mapping
- [ ] Validated in OmniScript debug mode (`?debug=true`) that output data is captured correctly

---

## Integration Procedure Bridge Checklist

- [ ] Apex class uses `with sharing` and `@AuraEnabled` annotation
- [ ] Integration Procedure name matches the deployed procedure name exactly
- [ ] Input map keys match the Integration Procedure's expected input element names
- [ ] Output map parsed correctly in LWC (handle null/empty result gracefully)
- [ ] Direct REST calls to Integration Procedure endpoints are absent in LWC JavaScript

---

## Notes

Record any deviations from the standard patterns and why they were made:

(fill in)
