# Well-Architected Notes — LWC LDS Writes

## Relevant Pillars

- **Security** — UI API enforces sharing, CRUD, FLS, and validation rules in the running user's context. Choosing LDS is choosing the user's full access stack — there is no `without sharing` opt-out. Any architecture that mutates records *as the user* should default to LDS.
- **Reliability** — LDS write errors come back in a structured envelope (`output.fieldErrors`, `output.errors`) that maps directly to UI affordances. Apex DML errors are flatter and require manual mapping. Reliable single-record write UX is cheaper to build on LDS.
- **User Experience** — `lightning-record-edit-form` honors compact-layout-driven field rendering (lookups, picklists, dependent picklists), inline error placement, and Trailhead-baked save/cancel patterns. Hand-rolled forms drift from these conventions and ship UX bugs.

Performance is *not* a primary pillar here — LDS writes are one record per call. Performance-critical bulk paths belong in Apex DML and surface in a different skill.

## Architectural Tradeoffs

### LDS write vs imperative Apex DML

| Dimension | LDS write | Apex DML |
|---|---|---|
| Sharing/CRUD/FLS | Always enforced (user context) | `without sharing` available; manual `Security.stripInaccessible` recommended |
| Cardinality | One record per call | Up to 200 records per chunk; 10k per transaction |
| Validation rule UX | Per-field error envelope | Flat `DmlException`; UI must rebuild placement |
| Cache invalidation | Auto for same-component `getRecord` | Manual via `notifyRecordUpdateAvailable` or `refreshApex` |
| Network calls | One UI API request per write | One controller call regardless of record count |
| Best for | User gestures on a single record | Multi-record, transaction, system context |

### Form base components vs imperative writes

| Dimension | `lightning-record-edit-form` | imperative `updateRecord` |
|---|---|---|
| Build cost | Markup + minimal JS | Full handler + error mapping JS |
| FLS/CRUD enforcement | Automatic per-field | Server enforces; client must surface errors |
| Field rendering | Compact-layout-aware | Dev rebuilds for each field type |
| Custom layout / wizard UX | Limited (form is its own layout container) | Full control |
| When to switch from form to imperative | The form layout cannot express the UX | — |

### LDS post-write refresh vs explicit refresh primitives

LDS auto-refreshes wired `getRecord` calls inside the same component after a successful LDS write. That's the entire scope of free refresh. Anything else is explicit:

- Apex-backed `@wire` → `refreshApex(wiredResult)`.
- Cross-component `getRecord` → `notifyRecordUpdateAvailable([{ recordId }])`.
- Multi-record / hierarchical refresh on a record page → `RefreshView` API event from `lightning/refresh`.

Building a write component that doesn't articulate which refresh path it owns is the most common bug class in this domain.

## Anti-Patterns

1. **"LDS writes are slow, switch to Apex"** — LDS is one HTTP call per record, exactly like an imperative `@AuraEnabled` Apex method that does one DML. Performance is comparable; the real reason to switch is cardinality or sharing context, not latency.
2. **"Suppress validation rules from the LWC"** — LDS writes have no validation-rule bypass; neither does Apex DML without an explicit context flag. Architectures that need to bypass rules should reconsider whether the rule is valid, not route around the platform.
3. **Building a form-per-page-layout component** — `lightning-record-form` already adapts to the layout. Reinventing it inside an LWC is sunk cost and drifts from admin-driven layout governance.

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- `lightning/uiRecordApi` Module Reference — https://developer.salesforce.com/docs/platform/lwc/guide/reference-lightning-ui-api-record.html
- `lightning-record-edit-form` Reference — https://developer.salesforce.com/docs/component-library/bundle/lightning-record-edit-form/documentation
- UI API Records Resource — https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_resources_record.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
