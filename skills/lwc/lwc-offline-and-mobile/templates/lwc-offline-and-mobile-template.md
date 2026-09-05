# LWC Mobile And Offline Review Template

Fill this in before writing the component, and keep it with the bundle. Rows marked
**one-way door** cannot be reversed after the component is live on a Lightning page.

## Runtime Context

| Item | Value |
|---|---|
| Component name | |
| Containers it must run in | Salesforce mobile app / desktop LEX / mobile browser / Experience Cloud |
| Offline requirement | None / read-tolerant / must render with no connection |
| Device capabilities needed | barcode / location / biometrics / contacts / calendar / NFC / document scan / none |
| Records that must already be on the device | (Briefcase rule owner: ______) |

## Decisions

| Decision | Choice | Reason recorded in |
|---|---|---|
| GraphQL module | `lightning/uiGraphQLApi` (v1, Mobile Offline) / `lightning/graphql` (v2) / not GraphQL | Comment above the import |
| Data path per record | LDS wire only / Apex only / mixed (justify) | |
| `<supportedFormFactor>` set — **one-way door** | Large / Small / both | `-meta.xml` |
| Tablet (`Medium`) behaviour | Desktop layout / phone layout / its own branch | JS getter |
| Targets | `lightning__RecordPage` / `lightning__AppPage` / `lightning__Tab` / other | `-meta.xml` |
| Refresh affordance | Button / post-mutation refresh / none (justify) | |
| Fallback when the capability is absent | Manual input / hidden section / disabled control | Template |

## Checklist

- [ ] Every capability call has factory + `isAvailable()` + `.catch()` + `.finally(dismiss)`.
- [ ] User-cancel failure code is branched on separately from real errors.
- [ ] Unsupported containers render a real alternative.
- [ ] The GraphQL module matches the offline requirement and the reason is in the file.
- [ ] A last-known-good snapshot survives a wire error, behind a staleness signal.
- [ ] An explicit refresh control exists; no polling timer.
- [ ] `supportedFormFactors` declared, only `Large`/`Small`, tablet handled in JS.
- [ ] No `lightning-datatable` / `lightning-tree-grid` on a `Small`-capable bundle.
- [ ] `__tests__` covers capability-absent, offline-error, and cancel paths.
- [ ] `check_lwc_offline_and_mobile.py --manifest-dir <source>` is clean.
- [ ] Verified on a simulator via `sf lightning dev app --device-type ios|android`, and on hardware for anything using the camera, location, or biometrics.

## Notes

Document whether the component fits the Salesforce mobile app or should move to another mobile
architecture, and record any conflict between the offline requirement and features only the v2
GraphQL module provides.
