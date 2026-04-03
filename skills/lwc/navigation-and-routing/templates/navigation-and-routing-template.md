# Navigation Contract Worksheet

## Destination

- Destination type: record / object / component / web page / named site page
- Container: Lightning desktop / mobile / Aura site / LWR site
- Shareable URL needed: Yes / No
- Custom state needed: Yes / No

## PageReference Model

```js
const pageRef = {
    type: 'standard__recordPage',
    attributes: {
        recordId: 'REPLACE_ME',
        objectApiName: 'Account',
        actionName: 'view'
    },
    state: {
        c__view: 'open'
    }
};
```

## Read Path

- `CurrentPageReference` fields consumed:
- Default values when state is absent:
- State keys that must be namespaced:

## Navigation APIs

- Immediate navigation uses `Navigate`: Yes / No
- Link generation uses `GenerateUrl`: Yes / No
- External URL requires `standard__webPage`: Yes / No

## Validation Notes

- Container support confirmed:
- Action names confirmed:
- Fallback behavior if destination is unavailable:
