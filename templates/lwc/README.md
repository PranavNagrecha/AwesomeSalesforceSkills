# LWC shared templates

## What's here

- `jest.config.js` — canonical Jest config, wired to `@salesforce/sfdx-lwc-jest`
  with module mocks for `@salesforce/apex`, `lightning/navigation`, and
  `lightning/platformShowToastEvent`. 75% coverage threshold.
- `component-skeleton/` — full LWC bundle (`.js`, `.html`, `.css`,
  `-meta.xml`, `__tests__/`). Copy, rename, adapt.
- `patterns/wireServicePattern.js` — reactive `@wire` with `refreshApex`.
- `patterns/imperativeApexPattern.js` — button-driven imperative call with
  loading / error / toast handling.
- `patterns/ldsRecordEditForm.html` — `lightning-record-edit-form` when you
  just need CRUD on one record with zero Apex.

## Copy-rename workflow

```bash
# Example: create a new "accountTile" LWC from the skeleton
cp -r templates/lwc/component-skeleton force-app/main/default/lwc/accountTile
cd force-app/main/default/lwc/accountTile

# Rename files
mv componentSkeleton.js accountTile.js
mv componentSkeleton.html accountTile.html
mv componentSkeleton.css accountTile.css
mv componentSkeleton.js-meta.xml accountTile.js-meta.xml
mv __tests__/componentSkeleton.test.js __tests__/accountTile.test.js

# Rename references inside files (sed/ripgrep)
find . -type f -exec sed -i '' 's/componentSkeleton/accountTile/g' {} +
find . -type f -exec sed -i '' 's/ComponentSkeleton/AccountTile/g' {} +
find . -type f -exec sed -i '' 's/Component Skeleton/Account Tile/g' {} +
```

## Conventions the skeleton enforces

| Concern | How the skeleton handles it |
|---|---|
| Async errors | `try/catch` + `extractMessage(e)` + toast. No `console.error`. |
| Loading state | `isLoading` flag gates `<lightning-spinner>` |
| Empty state | Explicit `lwc:else` branch — never "white screen" |
| Parent communication | `CustomEvent` with typed `detail` payload — never `dispatchEvent(new CustomEvent('x'))` with unstructured data |
| Accessibility | `role="alert"` on error notices, visible labels on buttons |
| Variant validation | Setter validates against allow-list and falls back — fail-safe, not fail-loud |

## Testing rules

- Every Jest test queries the shadow DOM via `el.shadowRoot.querySelector`.
- Use `await flushPromises()` (just `Promise.resolve()` twice) between a
  state change and the assertion — LWC re-renders are microtasks.
- Use `jest.fn()` for event listener assertions; assert both call count and
  `detail` shape.
- Tear down the DOM in `afterEach` — leftover elements between tests leak
  state.
