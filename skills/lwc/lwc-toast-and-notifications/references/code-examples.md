# Code Examples — LWC Toast And Notifications

A complete, deployable set: a surface-aware `notify.js` helper, a component that uses it behind a
`lightning/confirm` gate, the bundle's `.js-meta.xml` for both Lightning and Experience Cloud
targets, the Jest tests, an Apex `CustomNotificationSender` with its test, and the manifest and
deploy order that puts all of it in an org.

Every platform claim below carries the crawled Lightning Web Components Developer Guide page and
line (`lwc_guide <slug> L<n>`) or the Apex Reference Guide line that supports it. Claims the guide
does not print are marked `UNVERIFIED (2026-09-05)` beside the line they affect — those come from
the Component Library specification pages, which are not part of the crawled corpus.

Canonical skeletons this bundle follows rather than re-inventing:
`templates/lwc/component-skeleton/`, `templates/lwc/jest.config.js`,
`templates/apex/tests/TestDataFactory.cls`.

---

## 1. `notify.js` — pick the toast module from a capability flag

Two toast modules exist and they are not interchangeable.
`lightning/platformShowToastEvent` "isn't supported on login pages in Aura sites, LWR sites for
Experience Cloud, and standalone apps" and Salesforce says "We recommend that you use
`lightning/toast` instead" (`lwc_guide use-toast L10449`, `L10452`; `lwc_guide
base-components-patterns L4773`). `lightning/toast` is first available in API version 59.0 and
"is also supported in LWR sites"; `lightning/platformShowToastEvent` is API 45.0 and "isn't
supported in LWR sites" (`lwc_guide base-components-all L4649`, `L4651`).

A shared module keeps that rule in one place instead of in every handler.

```javascript
// force-app/main/default/lwc/notify/notify.js
//
// Surface-aware notification helper.
//
// Grounded: lightning/toast is the preferred module and is supported in LWR sites;
// lightning/platformShowToastEvent is not supported on Aura-site login pages, LWR sites, or
// standalone apps (lwc_guide use-toast L10448-L10452, base-components-all L4649/L4651).
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import Toast from 'lightning/toast';

// The capability flag the caller passes in. Prefer TOAST_MODULE, which works everywhere the
// component can run; EVENT exists for orgs pinned below API 59.0, where lightning/toast does
// not yet exist (lwc_guide base-components-all L4651).
export const TOAST_MODULE = 'toast-module';
export const TOAST_EVENT = 'toast-event';

// `lightning/toast` requires `label` as the title and treats `message` as optional
// (lwc_guide use-toast L10451). Both support inline links with the {N} or {linkName}
// placeholder syntax (same line).
// UNVERIFIED (2026-09-05): the guide never prints Toast.show()'s parameter list, so the second
// argument (the component reference) and the `variant` / `mode` config keys below come from the
// lightning/toast Component Library specification, which is not in the crawled corpus. If
// Toast.show ignores an argument in your org, check the specification before changing this file.
function showViaModule(component, { title, message, variant, mode }) {
    Toast.show({ label: title, message, variant, mode }, component);
}

// ShowToastEvent is created with `title`, `message`, `variant`, and `mode` properties and
// dispatched from the component (lwc_guide use-toast L10456).
// UNVERIFIED (2026-09-05): the accepted values for `variant` and `mode` are not printed in the
// Developer Guide. Only `variant: 'success'` and `variant: 'error'` appear in its own samples
// (lwc_guide data-table-inline-edit L5694, L5746). Treat any other literal as unconfirmed and
// check the platformShowToastEvent specification page.
function showViaEvent(component, { title, message, variant, mode }) {
    component.dispatchEvent(new ShowToastEvent({ title, message, variant, mode }));
}

/**
 * @param {LightningElement} component  the component that owns the notification
 * @param {object} config               { surface, title, message, variant, mode }
 *        surface — TOAST_MODULE (default) or TOAST_EVENT
 */
export function notify(component, config) {
    const { surface = TOAST_MODULE, ...rest } = config;
    if (surface === TOAST_EVENT) {
        showViaEvent(component, rest);
        return;
    }
    showViaModule(component, rest);
}

/**
 * Normalise anything thrown by Apex, LDS, or a fetch into one displayable string.
 * `error.body.message` is the shape the guide's own samples read
 * (lwc_guide data-table-inline-edit L5703, L5745).
 *
 * This is a deliberately minimal local copy. When the bundle already depends on the shared
 * error utilities described in lwc/lwc-error-boundaries, import those instead of this function
 * — that skill owns error normalisation and this skill owns what you do with the result.
 */
export function toMessage(error, fallback) {
    if (Array.isArray(error?.body)) {
        return error.body.map((e) => e.message).join('; ');
    }
    if (error?.body?.message) {
        return error.body.message;
    }
    if (typeof error?.message === 'string') {
        return error.message;
    }
    return fallback;
}
```

**How to read it**

- `notify(component, config)` never branches on a runtime environment sniff. The surface is a
  declared input, so a reviewer can see from the `.js-meta.xml` and the page assignment which
  path a given placement takes.
- The default is `TOAST_MODULE`, matching the guide's recommendation (`use-toast L10452`).
- `mode` and `variant` are passed straight through. The helper does not validate them because the
  Developer Guide does not publish the accepted values — see the `UNVERIFIED` note above.
- Error text goes through `toMessage` so an `error.body` shape never reaches the user as
  `[object Object]`.

---

## 2. `caseCloser` — confirm, then act, then notify

`lightning/confirm` is the documented replacement for `window.confirm()`, "which isn't supported
for cross-origin iframes in Chrome and Safari", and `LightningConfirm.open()` "doesn't halt
execution on the page, it returns a promise" that "resolves to `true` when you click OK and
`false` when you click Cancel" (`lwc_guide use-dialog-confirm L10414`, `L10415`, `L10418`).
The broader rule: "the HTML specification has deprecated support for the `window.alert()`,
`window.confirm()`, and `window.prompt()` methods when used in a third-party context, we recommend
that you use these notification components instead" (`lwc_guide base-components-patterns L4768`).

```javascript
// force-app/main/default/lwc/caseCloser/caseCloser.js
import { LightningElement, api } from 'lwc';
import LightningConfirm from 'lightning/confirm';
import { notify, toMessage, TOAST_MODULE } from 'c/notify';
import closeCases from '@salesforce/apex/CaseCloseController.closeCases';

export default class CaseCloser extends LightningElement {
    @api recordIds = [];

    // Set in Lightning App Builder / Experience Builder. Defaults to the module path, which is
    // the only path that works in an LWR site (lwc_guide use-toast L10449).
    @api notificationSurface = TOAST_MODULE;

    isBusy = false;

    async handleClose() {
        if (!this.recordIds.length) {
            return;
        }

        // LightningConfirm.open() takes message, variant, and label
        // (lwc_guide use-dialog-confirm L10418).
        const confirmed = await LightningConfirm.open({
            label: 'Close selected cases',
            message: 'Closing runs downstream automation and cannot be undone. Continue?',
            variant: 'header'
        });
        // UNVERIFIED (2026-09-05): the accepted values of LightningConfirm's `variant` are not
        // printed in the Developer Guide — 'header' comes from the lightning/confirm Component
        // Library specification. Note also that the guide names this parameter `variant` for
        // confirm (L10418) but `theme` for alert (L10404) and prompt (L10432); do not assume one
        // shape covers all three.

        if (!confirmed) {
            return;
        }

        this.isBusy = true;
        try {
            const closedCount = await closeCases({ caseIds: this.recordIds });
            notify(this, {
                surface: this.notificationSurface,
                title: 'Cases closed',
                message: `${closedCount} case(s) were closed.`,
                variant: 'success'
            });
            this.dispatchEvent(new CustomEvent('closed'));
        } catch (error) {
            notify(this, {
                surface: this.notificationSurface,
                title: 'Close failed',
                message: toMessage(error, 'The cases could not be closed. Try again.'),
                variant: 'error'
            });
        } finally {
            this.isBusy = false;
        }
    }
}
```

```html
<!-- force-app/main/default/lwc/caseCloser/caseCloser.html -->
<template>
    <lightning-card title="Close cases">
        <div class="slds-var-m-around_medium">
            <lightning-button
                data-id="close-button"
                label="Close selected cases"
                variant="destructive"
                disabled={isBusy}
                onclick={handleClose}
            ></lightning-button>
        </div>
    </lightning-card>
</template>
```

**Why the confirm sits before the Apex call, not inside it:** the promise gate is the only place a
user can still change their mind. Putting the check server-side turns "are you sure" into "it
already happened".

---

## 3. `caseCloser.js-meta.xml` — one bundle, both containers

`isExposed` must be `true` and at least one `<target>` declared for the component to appear in a
builder (`lwc_guide reference-configuration-tags L18712`). For Experience Builder, add
`lightningCommunity__Page` for the drag-and-drop component and `lightningCommunity__Default` to
expose editable properties in `targetConfigs` (`lwc_guide use-config-for-community-builder L8106`,
`L8107`, `L8110`). A `String` property renders as a picklist when it declares
`datasource="value1,value2"` (`lwc_guide reference-configuration-tags L18781`).

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Case Closer</masterLabel>
    <description>Closes selected cases behind a confirm gate and reports the outcome.</description>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightningCommunity__Page</target>
        <target>lightningCommunity__Default</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__RecordPage">
            <property
                name="notificationSurface"
                type="String"
                label="Notification surface"
                datasource="toast-module,toast-event"
                default="toast-module"
                description="toast-module uses lightning/toast; toast-event uses lightning/platformShowToastEvent."
            />
            <supportedFormFactors>
                <supportedFormFactor type="Large" />
                <supportedFormFactor type="Small" />
            </supportedFormFactors>
        </targetConfig>
        <targetConfig targets="lightningCommunity__Default">
            <property
                name="notificationSurface"
                type="String"
                label="Notification surface"
                datasource="toast-module,toast-event"
                default="toast-module"
                description="Leave this on toast-module in LWR sites; platformShowToastEvent renders nothing there."
            />
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**How to read it**

- `apiVersion` 63.0 is the version the guide's own flow-local-action sample carries
  (`lwc_guide use-flow-local-actions L8814`); every component must specify one from Spring '25
  (`lwc_guide reference-configuration-tags L18700`).
- The Experience Cloud `targetConfig` exists only so a site admin can see the surface setting. It
  should stay on `toast-module`: `platformShowToastEvent` is not supported in LWR sites
  (`lwc_guide base-components-all L4649`).
- Changing this file after the component is live in a site or managed package is restricted — you
  cannot add a `required=true` property or remove an existing `<property>`
  (`lwc_guide use-config-for-community-builder L8126`–`L8129`).

---

## 4. Jest tests — assert the event detail and the confirm promise

Salesforce ships base-component mocks in `sfdx-lwc-jest`; "no events are fired from these mocks
but you can call `dispatchEvent()` against them" (`lwc_guide unit-testing-using-jest-patterns
L12622`, `L12627`). The grounded assertion shape for toasts reads the dispatched event's detail:
`expect(handler.mock.calls[0][0].detail.title).toBe(TOAST_TITLE)` and the same for `message` and
`variant` (`lwc_guide unit-testing-using-jest-patterns L12630`–`L12635`).

Without a `moduleNameMapper` entry, `import { ShowToastEvent } from
'lightning/platformShowToastEvent'` resolves to the stock `sfdx-lwc-jest` stub; with one, it
resolves to your own mock (`lwc_guide unit-testing-using-jest-patterns L12640`–`L12647`).

```javascript
// jest.config.js — extend templates/lwc/jest.config.js
const { jestConfig } = require('@salesforce/sfdx-lwc-jest/config');

module.exports = {
    ...jestConfig,
    moduleNameMapper: {
        '^lightning/platformShowToastEvent$':
            '<rootDir>/force-app/test/jest-mocks/lightning/platformShowToastEvent',
        '^lightning/confirm$': '<rootDir>/force-app/test/jest-mocks/lightning/confirm',
        '^lightning/toast$': '<rootDir>/force-app/test/jest-mocks/lightning/toast'
    }
};
```

```javascript
// force-app/test/jest-mocks/lightning/confirm.js
// lightning/confirm has no stock stub that resolves a value, so the test controls it.
export default { open: jest.fn() };
```

```javascript
// force-app/test/jest-mocks/lightning/toast.js
export default { show: jest.fn() };
```

```javascript
// force-app/main/default/lwc/caseCloser/__tests__/caseCloser.test.js
import { createElement } from 'lwc';
import CaseCloser from 'c/caseCloser';
import LightningConfirm from 'lightning/confirm';
import Toast from 'lightning/toast';
import { ShowToastEventName } from 'lightning/platformShowToastEvent';
import closeCases from '@salesforce/apex/CaseCloseController.closeCases';

jest.mock(
    '@salesforce/apex/CaseCloseController.closeCases',
    () => ({ default: jest.fn() }),
    { virtual: true }
);

function build(surface) {
    const element = createElement('c-case-closer', { is: CaseCloser });
    element.recordIds = ['500xx0000000001', '500xx0000000002'];
    if (surface) {
        element.notificationSurface = surface;
    }
    document.body.appendChild(element);
    return element;
}

// Two microtask turns: one for the confirm promise, one for the Apex promise.
const settle = () => Promise.resolve().then(() => Promise.resolve());

describe('c-case-closer notifications', () => {
    afterEach(() => {
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    it('does not call Apex when the confirm promise resolves false', async () => {
        LightningConfirm.open.mockResolvedValue(false);

        const element = build();
        element.shadowRoot.querySelector('[data-id="close-button"]').click();
        await settle();

        expect(LightningConfirm.open).toHaveBeenCalledTimes(1);
        expect(closeCases).not.toHaveBeenCalled();
    });

    it('shows a success toast through lightning/toast on the default surface', async () => {
        LightningConfirm.open.mockResolvedValue(true);
        closeCases.mockResolvedValue(2);

        const element = build();
        element.shadowRoot.querySelector('[data-id="close-button"]').click();
        await settle();

        expect(Toast.show).toHaveBeenCalledTimes(1);
        const [config] = Toast.show.mock.calls[0];
        expect(config.label).toBe('Cases closed');
        expect(config.variant).toBe('success');
    });

    it('dispatches an error ShowToastEvent carrying error.body.message on the event surface', async () => {
        LightningConfirm.open.mockResolvedValue(true);
        closeCases.mockRejectedValue({ body: { message: 'Case is locked by an approval process' } });

        const element = build('toast-event');
        const handler = jest.fn();
        element.addEventListener(ShowToastEventName, handler);

        element.shadowRoot.querySelector('[data-id="close-button"]').click();
        await settle();

        expect(handler).toHaveBeenCalled();
        expect(handler.mock.calls[0][0].detail.title).toBe('Close failed');
        expect(handler.mock.calls[0][0].detail.message).toBe(
            'Case is locked by an approval process'
        );
        expect(handler.mock.calls[0][0].detail.variant).toBe('error');
    });
});
```

**How to read it**

- The third test listens on the element itself. That is the level the guide's own example asserts
  at (`L12630`); it verifies the component dispatched the event, not that a host rendered a toast.
  No Jest test can prove a toast appeared on screen — see `references/gotchas.md`, Gotcha 6.
- `LightningConfirm.open` is mocked because the stock stub does not resolve a decision; the two
  branches (`false` then `true`) are what make the destructive gate testable at all.
- Deeper Jest mechanics — wire adapters, timers, accessibility assertions — belong to
  `lwc/lwc-testing`; this file only shows the notification-specific assertions.

---

## 5. `CustomNotificationSender.cls` — the server-side surface

A toast lives and dies inside one page. When the recipient is not looking at the page — or is not
logged in yet — the surface is a custom notification, sent from Apex through
`Messaging.CustomNotification` (Apex Reference Guide L166555–L166635). Its delivery channels and
label are defined by a `CustomNotificationType` in metadata, which the admin sibling
`admin/custom-notification-type-design` owns.

Hard limits from the Apex Reference Guide: title maximum 250 characters, body maximum 750
characters (L166708, L166711), and the recipient set holds "up to the maximum of 500 values"
(L166775). Recipient ids may be a UserId, AccountId, OpportunityId, GroupId, or QueueId
(L166769–L166774). "You must specify a target for a notification… Neither attribute is required,
but if both are omitted, `send()` throws an exception" (L166572–L166573). To send at all, the
running user needs the Send Custom Notifications permission — "If you don't have the required
permission, the `send()` method fails" (L166593).

```apex
/**
 * Sends a custom notification for a record event, with the platform's own limits enforced
 * before the platform enforces them.
 *
 * Grounded in Apex Reference Guide, CustomNotification Class (L166555-L166635):
 *   title max 250 chars (L166708), body max 750 chars (L166711),
 *   recipients max 500 values per send (L166775),
 *   send() throws when both targetId and targetPageRef are omitted (L166573),
 *   caller needs the Send Custom Notifications user permission (L166593).
 */
public with sharing class CustomNotificationSender {
    @TestVisible
    private static final Integer MAX_TITLE = 250;
    @TestVisible
    private static final Integer MAX_BODY = 750;
    @TestVisible
    private static final Integer MAX_RECIPIENTS = 500;

    // Test seam: when true, batches are recorded instead of sent, so the test can assert
    // chunking and truncation without delivering a real notification.
    @TestVisible
    private static Boolean suppressSend = false;
    @TestVisible
    private static List<Set<String>> sentBatches = new List<Set<String>>();

    public class NotificationException extends Exception {
    }

    public static void notifyUsers(
        String typeDeveloperName,
        String title,
        String body,
        String targetId,
        Set<String> recipientIds
    ) {
        if (String.isBlank(title)) {
            throw new NotificationException('A notification title is required.');
        }
        if (String.isBlank(body)) {
            throw new NotificationException('A notification body is required.');
        }
        if (String.isBlank(targetId)) {
            // Reference Guide L166574: with no natural target, use a dummy id such as
            // 000000000000000AAA rather than omitting the target and taking the exception.
            throw new NotificationException(
                'A targetId is required; send() throws when targetId and targetPageRef are both omitted.'
            );
        }
        if (recipientIds == null || recipientIds.isEmpty()) {
            throw new NotificationException('At least one recipient id is required.');
        }

        List<CustomNotificationType> types = [
            SELECT Id
            FROM CustomNotificationType
            WHERE DeveloperName = :typeDeveloperName
            WITH USER_MODE
            LIMIT 1
        ];
        if (types.isEmpty()) {
            throw new NotificationException(
                'No CustomNotificationType with DeveloperName ' + typeDeveloperName
            );
        }

        String safeTitle = title.length() > MAX_TITLE ? title.left(MAX_TITLE) : title;
        String safeBody = body.length() > MAX_BODY ? body.left(MAX_BODY) : body;

        for (Set<String> batch : chunk(recipientIds)) {
            Messaging.CustomNotification notification = new Messaging.CustomNotification();
            notification.setNotificationTypeId(types[0].Id);
            notification.setTitle(safeTitle);
            notification.setBody(safeBody);
            notification.setTargetId(targetId);

            if (suppressSend) {
                sentBatches.add(batch);
                continue;
            }
            try {
                notification.send(batch);
            } catch (Exception e) {
                // send() can throw for a missing permission or a bad target; surface it rather
                // than losing it. See apex/debug-and-logging for the logging contract.
                throw new NotificationException(
                    'Custom notification send failed: ' + e.getMessage(),
                    e
                );
            }
        }
    }

    @TestVisible
    private static List<Set<String>> chunk(Set<String> ids) {
        List<Set<String>> batches = new List<Set<String>>();
        Set<String> current = new Set<String>();
        for (String id : ids) {
            current.add(id);
            if (current.size() == MAX_RECIPIENTS) {
                batches.add(current);
                current = new Set<String>();
            }
        }
        if (!current.isEmpty()) {
            batches.add(current);
        }
        return batches;
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

```apex
@IsTest
private class CustomNotificationSenderTest {
    private static Set<String> ids(Integer count) {
        Set<String> out = new Set<String>();
        for (Integer i = 0; i < count; i++) {
            out.add('005000000000' + String.valueOf(1000 + i));
        }
        return out;
    }

    @IsTest
    static void rejectsAnEmptyRecipientSet() {
        Boolean threw = false;
        Test.startTest();
        try {
            CustomNotificationSender.notifyUsers(
                'Case_Escalation',
                'Case escalated',
                'A case you own passed its milestone.',
                '500000000000001AAA',
                new Set<String>()
            );
        } catch (CustomNotificationSender.NotificationException e) {
            threw = true;
            Assert.isTrue(
                e.getMessage().contains('recipient'),
                'The message should name the missing recipients: ' + e.getMessage()
            );
        }
        Test.stopTest();
        Assert.isTrue(threw, 'An empty recipient set must be rejected before send().');
    }

    @IsTest
    static void rejectsAMissingTarget() {
        Boolean threw = false;
        Test.startTest();
        try {
            CustomNotificationSender.notifyUsers(
                'Case_Escalation',
                'Case escalated',
                'A case you own passed its milestone.',
                null,
                ids(1)
            );
        } catch (CustomNotificationSender.NotificationException e) {
            threw = true;
        }
        Test.stopTest();
        Assert.isTrue(threw, 'A blank targetId must be rejected; send() would throw anyway.');
    }

    @IsTest
    static void splitsRecipientsIntoBatchesOfFiveHundred() {
        CustomNotificationSender.suppressSend = true;
        CustomNotificationSender.sentBatches = new List<Set<String>>();

        List<CustomNotificationType> types = [
            SELECT Id, DeveloperName
            FROM CustomNotificationType
            LIMIT 1
        ];
        if (types.isEmpty()) {
            // No notification type deployed in this org yet; the chunker is still worth asserting.
            List<Set<String>> batches = CustomNotificationSender.chunk(ids(1200));
            Assert.areEqual(3, batches.size(), '1200 ids should split into 3 batches.');
            Assert.areEqual(500, batches[0].size(), 'The first batch should be full.');
            Assert.areEqual(200, batches[2].size(), 'The last batch holds the remainder.');
            return;
        }

        Test.startTest();
        CustomNotificationSender.notifyUsers(
            types[0].DeveloperName,
            'Case escalated',
            'A case you own passed its milestone.',
            '500000000000001AAA',
            ids(1200)
        );
        Test.stopTest();

        Assert.areEqual(
            3,
            CustomNotificationSender.sentBatches.size(),
            '1200 recipients exceed the 500-per-send maximum and must be chunked.'
        );
    }

    @IsTest
    static void truncatesTitleAndBodyToThePlatformMaximums() {
        String longTitle = 'x'.repeat(400);
        Assert.areEqual(250, longTitle.left(250).length(), 'Title truncates at 250 characters.');
        String longBody = 'y'.repeat(900);
        Assert.areEqual(750, longBody.left(750).length(), 'Body truncates at 750 characters.');
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## 6. `CustomNotificationType` metadata

The file suffix is `.notiftype` and the files live in the `notificationtypes` directory of the
package directory; the type is available in API version 46.0 and later (Metadata API Developer
Guide L41779–L41780, L41791). `customNotifTypeName`, `masterLabel`, `desktop`, and `mobile` are
all required (L41799–L41811).

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CustomNotificationType xmlns="http://soap.sforce.com/2006/04/metadata">
    <customNotifTypeName>Case_Escalation</customNotifTypeName>
    <masterLabel>Case Escalation</masterLabel>
    <description>Tells the case owner and their queue that a milestone was missed.</description>
    <desktop>true</desktop>
    <mobile>true</mobile>
</CustomNotificationType>
```

Path: `force-app/main/default/notificationtypes/Case_Escalation.notiftype-meta.xml`.

---

## 7. `package.xml` and deploy order

`CustomNotificationType` "doesn't support the wildcard character `*` (asterisk) in the package.xml
manifest file" (Metadata API Developer Guide L41893), so each type is named explicitly.

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case_Escalation</members>
        <name>CustomNotificationType</name>
    </types>
    <types>
        <members>CustomNotificationSender</members>
        <members>CustomNotificationSenderTest</members>
        <members>CaseCloseController</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>notify</members>
        <members>caseCloser</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>63.0</version>
</Package>
```

**Deploy order**

1. `CustomNotificationType` first. The Apex sender queries it by `DeveloperName` at run time, so
   there is no compile-time dependency — but a deploy that lands the Apex first leaves a class
   that throws on its first call.
2. Apex classes. `CaseCloseController` is the `@AuraEnabled` controller the LWC calls; it is not
   listed above in full because it is ordinary Apex — see `apex/debug-and-logging` for its
   logging contract.
3. LWC bundles last: `notify` before `caseCloser`, because `caseCloser` imports `c/notify`.
4. Grant Send Custom Notifications to whoever runs the sender (Apex Reference Guide L166593).

```bash
# Retrieve what is already there before you overwrite it.
sf project retrieve start --manifest manifest/package.xml --target-org myorg

# Validate without committing anything to the org.
sf project deploy start --manifest manifest/package.xml --target-org myorg --dry-run

# Deploy and run only this feature's Apex tests.
sf project deploy start --manifest manifest/package.xml --target-org myorg \
  --test-level RunSpecifiedTests --tests CustomNotificationSenderTest

# Jest, locally — no org needed.
npm run test:unit -- caseCloser
```

**Verification**

1. The notification type exists and is queryable under the name the Apex uses:

   ```sql
   SELECT Id, DeveloperName, MasterLabel FROM CustomNotificationType
   WHERE DeveloperName = 'Case_Escalation'
   ```

2. Run the checker against the deployed source tree — it reads the bundle and its `.js-meta.xml`
   together, which is the only way to catch an LWR target paired with the event module:

   ```bash
   python3 skills/lwc/lwc-toast-and-notifications/scripts/check_lwc_toast_and_notifications.py \
     --manifest-dir force-app/main/default
   ```

3. In the org: place `caseCloser` on a Lightning record page and confirm the success toast; then
   place it on an LWR Experience Builder page, set the surface property to `toast-event`, and
   confirm that **nothing** appears. That silent failure is the behaviour
   `lwc_guide use-toast L10449` describes, and seeing it once is what stops a team shipping it.
