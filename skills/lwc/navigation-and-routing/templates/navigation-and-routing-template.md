# Navigation Contract Worksheet

Fill this in before writing the component. Every line maps to a rule in
`references/gotchas.md` or a check in `scripts/check_navigation_and_routing.py`.

## Destination

- Destination type: record / object / record relationship / custom tab / component / named page / web page
- Container(s) that must work: Lightning Experience / Salesforce mobile app / Lightning console app / Aura site / LWR site
- Unsupported containers acknowledged (Lightning Out, LWC for Visualforce): Yes / No
- Shareable URL needed: Yes / No
- Custom state needed: Yes / No

## PageReference Model

```js
const pageRef = {
    type: 'standard__recordPage',
    attributes: {
        recordId: 'REPLACE_ME',
        // send objectApiName even where optional — required in LWR sites
        objectApiName: 'Account',
        actionName: 'view'
    },
    state: {
        c__view: 'open' // string value, namespaced key
    }
};
```

## Read Path

- `CurrentPageReference` fields consumed:
- Default values when state is absent:
- State keys that must be namespaced:
- State read through a getter over the wired reference (not cached in the wire callback): Yes / No
- Any state value that identifies a person (must be moved out of the URL): Yes / No

## Navigation APIs

- Immediate navigation uses `Navigate`: Yes / No
- `replace: true` for state-only navigations: Yes / No
- Link generation uses `GenerateUrl`, promise resolved with `.then` / `await`: Yes / No
- Class applies the mixin — `extends NavigationMixin(LightningElement)`: Yes / No
- Navigation originates inside a `LightningModal` subclass (must be delegated to the parent): Yes / No
- External URL requires `standard__webPage`: Yes / No

## Deployment Unit

- Target bundle declares `lightning__UrlAddressable` (only if using `standard__component`):
- Target component declares `lightning__Tab` (only if using `standard__navItemPage`):
- `CustomTab` member included in `package.xml`:
- All destinations ship in the same manifest as the navigating component: Yes / No

## Validation Notes

- Container support confirmed per page type:
- Action names confirmed against the PageReference Types table:
- Jest asserts the PageReference object via `getNavigateCalledWith()`: Yes / No
- `check_navigation_and_routing.py --manifest-dir <lwc source>` clean: Yes / No
- Fallback behavior if destination is unavailable (see `lwc/lightning-navigation-dead-link-handling`):
