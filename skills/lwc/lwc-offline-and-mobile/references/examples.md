# Examples — LWC Offline And Mobile

Worked scenarios with the reasoning attached. The full deployable bundle lives in
`references/code-examples.md`; these are the decisions that produced it.

## Example 1: Capability-Gated Barcode Scanner

**Context:** A warehouse component should scan barcodes in the Salesforce mobile app but still render safely elsewhere.

**Problem:** The original code assumes the scanner exists in every container, uses the legacy
`beginCapture()` API, and never closes the camera view — so on desktop it throws, and on a phone the
OS scanner interface stays on top of the app after the scan finishes.

**Solution:**

```js
import { getBarcodeScanner } from 'lightning/mobileCapabilities';

export default class ScanAsset extends LightningElement {
    scanner;
    canScan = false;
    message;

    connectedCallback() {
        this.scanner = getBarcodeScanner();
        this.canScan = Boolean(this.scanner) && this.scanner.isAvailable();
    }

    handleScan() {
        if (!this.canScan) {
            return; // the template renders a manual-entry input instead
        }
        this.scanner
            .scan({
                barcodeTypes: [this.scanner.barcodeTypes.QR],
                instructionText: 'Scan the asset tag',
                scannerSize: 'MEDIUM'
            })
            .then((results) => {
                this.tag = results[0]?.value; // scan() resolves an ARRAY
            })
            .catch((error) => {
                const cancelled =
                    String(error?.code ?? '').toLowerCase() === 'userdismissedscanner';
                this.message = cancelled ? 'Scan cancelled.' : error?.message;
            })
            .finally(() => this.scanner.dismiss());
    }
}
```

**Why it works:** four separate obligations are met — the factory runs once, the availability check
decides what renders, the `catch` distinguishes a user cancel from a real failure, and the `finally`
closes the OS scanner interface, which does not close itself
(`lwc_guide reference-lightning-barcodescanner-scan L17366`). `scannerSize: 'MEDIUM'` sizes the
camera view to 33% of the screen, one of the documented options
(`lwc_guide reference-lightning-barcodescanner-data-types L17292`).

---

## Example 2: Resume-Safe Mobile Task Form

**Context:** A field-service user fills out a short task form on a phone and may lose connectivity or background the app.

**Problem:** The form assumes a continuous session, discards progress when the app resumes, and has
no way for the user to ask for fresh data — the team assumed pull-to-refresh would cover it.

**Solution:** three pieces of state instead of one.

| State | Holds | Rendered as |
|---|---|---|
| `account` | The current wire emission, or `undefined` after an error | Normal card content |
| `lastGoodAccount` | The most recent successful emission, never cleared by an error | Fallback content behind a staleness banner |
| `draftNote` + `draftSavedAt` | The user's in-progress input | Textarea value plus an "unsaved on this device" hint |

The wire handler only overwrites `account`; it never touches `lastGoodAccount` on the error branch,
so an offline error degrades the card instead of blanking it. Refresh is a button, because pull to
refresh doesn't work for custom Lightning web components in the Salesforce mobile app
(`lwc_guide use-config-for-app-builder-tips L9910`). The full handler is
`references/code-examples.md` §2.

**Why it works:** the design assumes interruption and reconnect, which is normal in mobile
workflows, and it makes the interrupted state visible instead of silently stale.

---

## Example 3: Choosing The GraphQL Module Under An Offline Requirement

**Context:** A component reads an Account plus its open Cases and must render on a technician's
phone in a basement with no signal.

**Problem:** The team's first draft imported `lightning/graphql`, because the guide recommends v2
where possible and marks v1 deprecated. It worked in every desktop and simulator test — the
simulator had a network connection.

**Solution:** the decision table, applied in one line of the file.

| Requirement | v1 `lightning/uiGraphQLApi` | v2 `lightning/graphql` |
|---|---|---|
| Mobile Offline | Yes | No |
| Optional fields | No | Yes |
| Dynamic query construction | No | Yes |
| Mutations (`executeMutation`) | Exported by the module (`reference-lightning-graphql-api L13581`) | Yes, and the documented path (`reference-graphql-mutation L13527`) |
| Refresh call | `refreshGraphQL(result)` | `refresh` on the emitted data |
| Deprecation notice | Marked deprecated | Current |

Offline wins, so the import is v1 and the reason is written above it:

```js
// Offline requirement -> lightning/uiGraphQLApi (v1) deliberately.
// v1 supports Mobile Offline, v2 does not (lwc_guide reference-graphql-intro L13437),
// even though v1 is the module marked deprecated (reference-refreshgraphql L13651).
import { gql, graphql, refreshGraphQL } from 'lightning/uiGraphQLApi';
```

**Why it works:** the comment survives the next refactor. Without it, the deprecation notice wins
the argument every time, and the failure only shows up on a device with no signal — the hardest
place to reproduce.

---

## Anti-Pattern: Treating Mobile As Desktop On A Smaller Screen

**What practitioners do:** They reuse a dense desktop component with large tables, hover interactions, and no capability checks, and they validate it in Chrome's Device Mode.

**What goes wrong:** `lightning-datatable` and `lightning-tree-grid` aren't supported on mobile
devices at all (`lwc_guide data-table-vs-tree-grid L5600`) — this is a support boundary, not a
styling complaint. Device Mode simulates screen size, orientation, location, CPU and network
constraints (`lwc_guide debug-mobile L12214–12219`), so it reproduces none of it.

**Correct approach:** Start from the mobile interaction model, gate device APIs, replace the table
with an iterated card layout on the `Small` branch, and validate on a simulator with
`sf lightning dev app --device-type ios` — remembering that only a Lightning *app*, never a single
component, can be previewed in a mobile environment
(`lwc_guide get-started-test-components L467`).
