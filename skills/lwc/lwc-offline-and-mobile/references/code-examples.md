# Code Examples — LWC Offline And Mobile

Everything here is a complete, deployable artifact. Line cites of the form
`lwc_guide <page-slug> L<n>` refer to the crawled Lightning Web Components Developer Guide
(676 pages); the URL for each page is
`https://developer.salesforce.com/docs/platform/lwc/guide/<page-slug>.html`.

Scope note: this file builds the **component**. Briefcase Builder priming rules, the offline
sync/conflict pipeline, and Field Service offline priming are a different problem — see
`lwc/lwc-mobile-offline-and-briefcase` and `architect/fsl-offline-architecture`. GraphQL query
*shape* (cursors, `{value, displayValue}`, fragments) belongs to `lwc/lwc-graphql-wire`; this file
only makes the module choice that offline forces on you.

---

## 1. The module decision that has to happen first

| You need | Module | Why |
|---|---|---|
| The component to work in Mobile Offline | `lightning/uiGraphQLApi` (v1) | `lightning/uiGraphQLApi` supports Mobile Offline use cases, `lightning/graphql` doesn't (`lwc_guide reference-graphql-intro L13437`, restated on the v2 pages at `L13458`, `L13470`, `L13529`, `L13565`) |
| Optional fields, dynamic query construction, mutations, `refresh` on the emitted data | `lightning/graphql` (v2) | v2 feature list, `lwc_guide reference-graphql-intro L13435–13436`; v1 explicitly lacks them (`lwc_guide reference-graphql L13590`, limitation list at `L13634–13638`) |
| Single-record read, no relationships | `lightning/uiRecordApi` `getRecord` | Not this skill — see `lwc/wire-service-patterns` |

The trap: the guide marks `lightning/uiGraphQLApi` **deprecated** and tells you to move to
`lightning/graphql` (`lwc_guide reference-refreshgraphql L13651`), while the comparison page says v2
is the one that does *not* support Mobile Offline (`L13437`). Both statements are current. If offline
is a requirement, v1 is the module, deprecation notice and all — write that decision down in the
component header so the next reader does not "fix" it.

---

## 2. `mobileVisitCard` — the bundle

`force-app/main/default/lwc/mobileVisitCard/mobileVisitCard.js`

```js
import { LightningElement, api, wire } from 'lwc';
import { gql, graphql, refreshGraphQL } from 'lightning/uiGraphQLApi';
import { getBarcodeScanner } from 'lightning/mobileCapabilities';
import FORM_FACTOR from '@salesforce/client/formFactor';

/**
 * mobileVisitCard — record-context card for the Salesforce mobile app.
 *
 * MODULE CHOICE (do not "modernise" this import):
 *   lightning/uiGraphQLApi (v1) is used deliberately. It is the only GraphQL wire
 *   module that supports Mobile Offline use cases (lwc_guide reference-graphql-intro
 *   L13437). lightning/graphql (v2) is newer and is what the refreshGraphQL page tells
 *   you to migrate to (lwc_guide reference-refreshgraphql L13651), but v2 does not
 *   support Mobile Offline (lwc_guide reference-lightning-graphql-module L13458).
 *
 * Based on templates/lwc/component-skeleton/ and templates/lwc/patterns/graphqlWirePattern.js.
 */
export default class MobileVisitCard extends LightningElement {
    @api recordId;

    // --- data -------------------------------------------------------------
    graphqlResult;          // held so refreshGraphQL() has the object it needs
    account;
    lastGoodAccount;        // last successfully provisioned snapshot
    dataError;

    // --- draft-aware UI state --------------------------------------------
    draftNote = '';
    draftSavedAt;
    isStale = false;        // showing lastGoodAccount, not fresh data

    // --- capability state -------------------------------------------------
    scanner;
    scannerAvailable = false;
    scanMessage;
    scannedValues = [];

    get isPhone() {
        // @salesforce/client/formFactor returns Large | Medium | Small
        // (lwc_guide create-client-form-factor L3960–3962). Medium is a tablet and is
        // NOT one of the values <supportedFormFactor> accepts, so treat it explicitly.
        return FORM_FACTOR === 'Small';
    }

    get isTablet() {
        return FORM_FACTOR === 'Medium';
    }

    get hasDraft() {
        return this.draftNote.trim().length > 0 && !this.draftSavedAt;
    }

    get displayAccount() {
        return this.account ?? this.lastGoodAccount;
    }

    connectedCallback() {
        // Feature-detect once. getBarcodeScanner() is a factory with no options
        // (lwc_guide reference-lightning-barcodescanner-factory L17322–17326).
        this.scanner = getBarcodeScanner();
        this.scannerAvailable = Boolean(this.scanner) && this.scanner.isAvailable();
        if (!this.scannerAvailable) {
            // Mobile capability APIs exist only inside a supported mobile app on a
            // mobile device (lwc_guide reference-lightning-mobilecapabilities L17179).
            this.scanMessage = 'Scanning is unavailable here — enter the code manually.';
        }
    }

    @wire(graphql, {
        query: gql`
            query VisitCard($recordId: ID) {
                uiapi {
                    query {
                        Account(where: { Id: { eq: $recordId } }, first: 1) {
                            edges {
                                node {
                                    Id
                                    Name { value }
                                    Phone { value }
                                    ShippingCity { value }
                                }
                            }
                        }
                    }
                }
            }
        `,
        variables: '$queryVariables'
    })
    handleGraphql({ data, errors }) {
        // The GraphQL wire adapter emits `errors` (plural), unlike every other LWC wire
        // adapter (lwc_guide reference-graphql L13602).
        this.graphqlResult = { data, errors };
        if (errors) {
            this.dataError = this.reduceErrors(errors);
            this.isStale = Boolean(this.lastGoodAccount);
            this.account = undefined;
            return;
        }
        if (data) {
            const edges = data?.uiapi?.query?.Account?.edges ?? [];
            this.account = edges.length ? edges[0].node : undefined;
            this.lastGoodAccount = this.account ?? this.lastGoodAccount;
            this.isStale = false;
            this.dataError = undefined;
        }
    }

    get queryVariables() {
        // A getter keeps the variables map stable and lets the adapter react to change
        // (lwc_guide reference-graphql L13613).
        return { recordId: this.recordId };
    }

    reduceErrors(errors) {
        // Error body shape is NOT uniform. UI API read operations return error.body as an
        // ARRAY of objects; network errors — including an offline error — return
        // error.body as an OBJECT (lwc_guide data-error L6568–6571). Handle both.
        const list = Array.isArray(errors) ? errors : [errors];
        return list
            .map((e) => e?.message ?? e?.body?.message ?? 'Unknown error')
            .join(', ');
    }

    // --- explicit, user-driven refresh -----------------------------------
    async handleRefresh() {
        // No polling. The guide tells you to refresh once after a mutation, or to give
        // the user an explicit refresh action, rather than setInterval
        // (lwc_guide reference-refreshgraphql L13657). A refresh button is also the only
        // refresh affordance you get: pull-to-refresh does not work for custom Lightning
        // web components in the Salesforce mobile app
        // (lwc_guide use-config-for-app-builder-tips L9910).
        try {
            await refreshGraphQL(this.graphqlResult);
        } catch (error) {
            this.dataError = this.reduceErrors(error);
            this.isStale = Boolean(this.lastGoodAccount);
        }
    }

    // --- draft handling ---------------------------------------------------
    handleNoteChange(event) {
        this.draftNote = event.target.value;
        this.draftSavedAt = undefined;
    }

    handleDiscardDraft() {
        this.draftNote = '';
        this.draftSavedAt = undefined;
    }

    // --- capability-gated scan -------------------------------------------
    handleScan() {
        if (!this.scannerAvailable) {
            return;
        }
        // scan() resolves to an ARRAY of Barcode objects; the legacy beginCapture()
        // resolved to a single Barcode (lwc_guide reference-lightning-barcodescanner-scan
        // L17345 vs reference-lightning-barcodescanner-begincapture L17397).
        this.scanner
            .scan({
                barcodeTypes: [
                    this.scanner.barcodeTypes.QR,
                    this.scanner.barcodeTypes.EAN_13
                ],
                instructionText: 'Scan the asset tag',
                successText: 'Captured'
            })
            .then((results) => {
                this.scannedValues = results.map((r) => r.value);
                this.scanMessage = `${results.length} code(s) captured`;
            })
            .catch((error) => {
                // A user tapping Cancel arrives HERE, not in then(). It is the normal way
                // a scan session ends (lwc_guide reference-lightning-barcodescanner-data-types
                // L17319). Do not render it as a failure.
                this.scanMessage = this.isUserCancel(error)
                    ? 'Scan cancelled.'
                    : `Scan failed: ${error?.message ?? 'unknown'}`;
            })
            .finally(() => {
                // The mobile OS scanner interface stays on screen after a success OR an
                // error until dismiss() is called
                // (lwc_guide reference-lightning-barcodescanner-scan L17366–17367).
                this.scanner.dismiss();
            });
    }

    isUserCancel(error) {
        // The guide prints this code both as USER_DISMISSED_SCANNER (failure-code table,
        // lwc_guide reference-lightning-barcodescanner-data-types L17313) and as
        // userDismissedScanner (prose, same page L17319 and scan page L17365). Compare
        // case-insensitively rather than betting on one spelling.
        return String(error?.code ?? '').toLowerCase() === 'userdismissedscanner';
    }
}
```

`force-app/main/default/lwc/mobileVisitCard/mobileVisitCard.html`

```html
<template>
    <lightning-card title="Visit" icon-name="standard:account">
        <div class="slds-var-p-horizontal_medium">

            <template lwc:if={isStale}>
                <div class="slds-notify slds-notify_alert slds-theme_warning" role="alert">
                    Showing the last data this device loaded. Tap Refresh when you are back online.
                </div>
            </template>

            <template lwc:if={displayAccount}>
                <p class="slds-text-heading_small">{displayAccount.Name.value}</p>
                <p>{displayAccount.Phone.value}</p>
                <p>{displayAccount.ShippingCity.value}</p>
            </template>
            <template lwc:else>
                <template lwc:if={dataError}>
                    <p class="slds-text-color_error">{dataError}</p>
                </template>
                <template lwc:else>
                    <lightning-spinner alternative-text="Loading"></lightning-spinner>
                </template>
            </template>

            <lightning-textarea
                label="Visit note"
                value={draftNote}
                onchange={handleNoteChange}
            ></lightning-textarea>

            <template lwc:if={hasDraft}>
                <p class="slds-text-body_small slds-text-color_weak">
                    Unsaved note kept on this device.
                </p>
                <lightning-button
                    label="Discard note"
                    onclick={handleDiscardDraft}
                ></lightning-button>
            </template>

            <template lwc:if={scannerAvailable}>
                <lightning-button
                    class="scan-button"
                    variant="brand"
                    label="Scan asset tag"
                    onclick={handleScan}
                ></lightning-button>
            </template>
            <template lwc:else>
                <lightning-input
                    label="Asset tag"
                    placeholder="Type the code"
                ></lightning-input>
            </template>

            <template lwc:if={scanMessage}>
                <p class="scan-message">{scanMessage}</p>
            </template>

            <lightning-button
                class="refresh-button"
                label="Refresh"
                onclick={handleRefresh}
            ></lightning-button>
        </div>
    </lightning-card>
</template>
```

`force-app/main/default/lwc/mobileVisitCard/mobileVisitCard.js-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Visit Card</masterLabel>
    <description>Record-context visit card for the Salesforce mobile app.</description>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
        <target>lightning__Tab</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <objects>
                <object>Account</object>
            </objects>
            <supportedFormFactors>
                <supportedFormFactor type="Large"/>
                <supportedFormFactor type="Small"/>
            </supportedFormFactors>
        </targetConfig>
        <targetConfig targets="lightning__AppPage">
            <supportedFormFactors>
                <supportedFormFactor type="Small"/>
            </supportedFormFactors>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**How to read the `-meta.xml`**

- `lightning__RecordPage` is what gives the component `recordId` on a record page in Lightning
  App Builder (`lwc_guide reference-configuration-tags L18744`). Without it the `@api recordId`
  is never populated and the wire never fires.
- `lightning__Tab` is the target that makes the component reachable as a custom tab **in the
  Salesforce mobile app** as well as Lightning Experience (`lwc_guide reference-configuration-tags
  L18746`; the walkthrough is `lwc_guide use-config-custom-tab-intro L7974` and `use-config-custom-tab-lex L7994–8014`).
- `lightning__HomePage` is deliberately absent: Home pages support only the `Large` form factor
  (`lwc_guide use-config-form-factors L9795`), so a mobile-first card there is dead weight.
- `lightning__RecordAction` is deliberately absent: `Small` is not supported for that target
  because LWC quick actions do not appear in the Salesforce mobile app
  (`lwc_guide targets-lightning-record-action L19313`, and `lwc_guide use-config-for-quick-actions L10561`).
- `<supportedFormFactor type="…">` accepts only `Large` and `Small`
  (`lwc_guide targets-lightning-record-action L19311–19313`). There is no `Medium`, even though
  `@salesforce/client/formFactor` returns `Medium` for a tablet
  (`lwc_guide create-client-form-factor L3961`). A tablet is served by the `Large` declaration
  while the JS reports `Medium` — which is why `isPhone` and `isTablet` are separate getters.
- Adding form factors later is fine; **removing** one is not. Once the component is in use on a
  Lightning page you can only increase supported form factors, not decrease them
  (`lwc_guide use-config-form-factors L9806`, repeated at `use-config-for-app-builder-tips L9909`).

---

## 3. Jest test

The wire adapter is mocked with the `@salesforce/sfdx-lwc-jest` test utility, which is the
documented way to test a component that uses the wire service
(`lwc_guide unit-testing-using-wire-utility L12519–12522`). The test imports **the same wire
adapter the component imports** and calls `.emit()` on it (`L12533`, `L12535`).

`force-app/main/default/lwc/mobileVisitCard/__tests__/mobileVisitCard.test.js`

```js
import { createElement } from 'lwc';
import MobileVisitCard from 'c/mobileVisitCard';
import { graphql } from 'lightning/uiGraphQLApi';
import { getBarcodeScanner } from 'lightning/mobileCapabilities';
import mockVisitCard from './data/graphql.json';

// Flush the microtask queue so the DOM reflects the emitted data.
const flush = () => Promise.resolve();

describe('c-mobile-visit-card', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    function build() {
        const element = createElement('c-mobile-visit-card', { is: MobileVisitCard });
        element.recordId = '001xx000003DGb2AAG';
        document.body.appendChild(element);
        return element;
    }

    it('renders the account once the wire emits', async () => {
        const element = build();
        graphql.emit(mockVisitCard);
        await flush();
        expect(element.shadowRoot.textContent).toContain('Northern Trail Outfitters');
    });

    it('keeps the last good snapshot and flags staleness when the wire errors', async () => {
        const element = build();
        graphql.emit(mockVisitCard);
        await flush();

        // A network/offline error arrives with error.body as an OBJECT, not an array
        // (lwc_guide data-error L6571).
        graphql.emit({ errors: { message: 'Network error', body: { message: 'offline' } } });
        await flush();

        expect(element.shadowRoot.textContent).toContain('Northern Trail Outfitters');
        expect(element.shadowRoot.textContent).toContain('last data this device loaded');
    });

    it('hides the scan button and offers manual entry when the capability is absent', async () => {
        getBarcodeScanner.mockReturnValue({ isAvailable: () => false });
        const element = build();
        await flush();
        expect(element.shadowRoot.querySelector('.scan-button')).toBeNull();
        expect(element.shadowRoot.querySelector('lightning-input')).not.toBeNull();
    });

    it('dismisses the scanner interface after a user cancel', async () => {
        const dismiss = jest.fn();
        getBarcodeScanner.mockReturnValue({
            isAvailable: () => true,
            barcodeTypes: { QR: 'qr', EAN_13: 'ean13' },
            scan: () => Promise.reject({ code: 'userDismissedScanner' }),
            dismiss
        });
        const element = build();
        await flush();

        element.shadowRoot.querySelector('.scan-button').click();
        await flush();
        await flush();

        // dismiss() must run even on the cancel path — the OS scanner UI stays up
        // otherwise (lwc_guide reference-lightning-barcodescanner-scan L17366).
        expect(dismiss).toHaveBeenCalled();
        expect(element.shadowRoot.querySelector('.scan-message').textContent)
            .toContain('cancelled');
    });
});
```

`force-app/main/default/lwc/mobileVisitCard/__tests__/data/graphql.json` — the guide's convention
is a `data` folder inside `__tests__` holding one JSON file per wire adapter
(`lwc_guide unit-testing-using-wire-utility L12528–12529`).

```json
{
  "data": {
    "uiapi": {
      "query": {
        "Account": {
          "edges": [
            {
              "node": {
                "Id": "001xx000003DGb2AAG",
                "Name": { "value": "Northern Trail Outfitters" },
                "Phone": { "value": "(415) 555-0100" },
                "ShippingCity": { "value": "San Francisco" }
              }
            }
          ]
        }
      }
    }
  },
  "errors": null
}
```

`jest.config.js` — the `moduleNameMapper` entry is the documented way to point an import at a
mock you control (`lwc_guide unit-testing-using-jest-patterns L12637–12647`; the shape of the
block is `lwc_guide unit-testing-using-jest-create-tests L12430–12456`). Start from
`templates/lwc/jest.config.js` and add the mobile entry.

```js
const { jestConfig } = require('@salesforce/sfdx-lwc-jest/config');

module.exports = {
    ...jestConfig,
    moduleNameMapper: {
        '^lightning/navigation$':
            '<rootDir>/force-app/test/jest-mocks/lightning/navigation',
        '^lightning/mobileCapabilities$':
            '<rootDir>/force-app/test/jest-mocks/lightning/mobileCapabilities'
    },
    testTimeout: 10000
};
```

<!-- UNVERIFIED (2026-09-05): whether sfdx-lwc-jest ships a built-in lightning-stubs entry for
     lightning/mobileCapabilities. The guide names a stub only for platformShowToastEvent
     (lwc_guide unit-testing-using-jest-patterns L12646). Supplying your own mock through
     moduleNameMapper is documented and works either way, so that is what this file does. -->

`force-app/test/jest-mocks/lightning/mobileCapabilities.js`

```js
// Hand-written mock. The real module is only resolvable inside a supported mobile app
// (lwc_guide reference-lightning-mobilecapabilities L17179), so Jest must be told what
// getBarcodeScanner() returns. Default = capability absent, which is the desktop reality.
export const getBarcodeScanner = jest.fn(() => ({ isAvailable: () => false }));
export const getLocationService = jest.fn(() => ({ isAvailable: () => false }));
export const getBiometricsService = jest.fn(() => ({ isAvailable: () => false }));
```

---

## 4. package.xml

`LightningComponentBundle` is the Metadata API type for a Lightning web component
(`lwc_guide get-started-with-your-tools L559`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>mobileVisitCard</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 5. Deploy order

Deploy in this order; each step depends on the one before it.

1. **Fields and object access.** The GraphQL wire runs under the current user's object- and
   field-level security (`lwc_guide reference-graphql L13593`, and for v2 `reference-graphql-wire L13472`). Grant FLS on `Phone` and
   `ShippingCity` before the component ships, or the fields silently do not come back.
2. **The bundle.**
   ```bash
   sf project deploy start --source-dir force-app/main/default/lwc/mobileVisitCard
   ```
3. **The Lightning record page.** Add the component in Lightning App Builder to the Account
   record page and confirm the phone form factor is selected in the page's activation. The
   component's `<supportedFormFactor type="Small"/>` only permits it — the page still has to
   include it.
4. **Offline priming (separate skill).** If this component must render with no connection, the
   records it reads have to be on the device already. That is a Briefcase Builder rule, not a
   component change — see `lwc/lwc-mobile-offline-and-briefcase`. The GraphQL query itself may
   also need metaschema directives to survive prefetch: the guide states that a query failing
   prefetch in the Salesforce mobile app, Salesforce Field Service, or Mobile Offline must keep
   metaschema directives for referential integrity and priming
   (`lwc_guide reference-graphql L13639`).
   <!-- UNVERIFIED (2026-09-05): the exact metaschema directive names and syntax. The LWC guide
        states the requirement but does not print an example; the directive list lives in the
        Mobile and Offline Developer Guide / the linked known-issue article, neither of which is
        in the crawled corpus. Do not copy a directive from memory into a shipped query — read
        the known-issue article first. -->

---

## 6. Verification

```bash
# 1. Unit tests, including the capability-absent and offline-error paths.
npm run test:unit -- mobileVisitCard

# 2. Static check of the bundle against this skill's rules.
python3 skills/lwc/lwc-offline-and-mobile/scripts/check_lwc_offline_and_mobile.py \
    --manifest-dir force-app/main/default

# 3. Run the real thing on a simulator/emulator. Live Preview supports previewing only
#    Lightning APPS in a mobile environment — a single-component preview is browser-only
#    (lwc_guide get-started-test-components L467). --device-type accepts desktop | ios | android
#    (lwc_guide get-started-test-components L464).
sf lightning dev app --target-org myOrg --name "Sales" --device-type ios
```

Then, on the device:

| Check | Expected |
|---|---|
| Open the Account record in the Salesforce mobile app | Card renders, name/phone/city populated |
| Put the device in airplane mode, background the app, reopen it | The stale banner appears and the last snapshot is still on screen — not a blank card |
| Type a note, background the app, reopen | The note is still in the textarea and the "Unsaved note" hint shows |
| Tap **Scan asset tag**, then tap Cancel in the OS scanner | The scanner UI closes (proves `dismiss()` ran) and the message reads "Scan cancelled." |
| Open the same page on desktop | No scan button; the manual-entry input is shown instead |
| Pull down on the page to refresh | Nothing happens — this is expected (`lwc_guide use-config-for-app-builder-tips L9910`); the **Refresh** button is the affordance |
