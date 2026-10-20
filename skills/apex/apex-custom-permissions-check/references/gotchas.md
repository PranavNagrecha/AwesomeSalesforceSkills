# Gotchas — Apex Custom Permissions Check

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The LWC import is `true` or `undefined` — never `false`

**What happens:** A developer mirrors the Apex check in an LWC and writes `if (hasApprove === false) { showDenied(); }`. The denied branch never runs, for anyone. The Lightning Web Components Developer Guide (create-get-permissions.html, fetched 2026-10-20) states the contract exactly: "To check whether a user has a permission, import a static reference to the permission and evaluate whether it's `true` or `undefined`." There is no `false` value — an unassigned permission produces `undefined`.

**When it occurs:** Any strict-equality comparison (`=== false`, `!== true`), any `JSON.stringify` of the flag into a payload, and any place the value is passed to a child component through an `@api` property that a template then compares strictly.

**How to avoid:** Test truthiness only, and name the reference so the boolean intent is obvious — the guide recommends the `has{Permission}` form.

```js
import { LightningElement } from 'lwc';
import hasApproveBigDeals from '@salesforce/customPermission/Approve_Big_Deals';

export default class ApprovalPanel extends LightningElement {
    get canApprove() {
        return hasApproveBigDeals === true;   // normalise undefined -> false once
    }
    get showDeniedMessage() {
        return !this.canApprove;              // never compare === false
    }
}
```

---

## Gotcha 2: A client-side custom-permission check is a UI affordance, not an authorization boundary

**What happens:** The team hides the Approve button with `if:true={canApprove}` and considers the feature gated. Anyone can call the `@AuraEnabled` method directly from the browser console or a REST client and reach the privileged code path, because the Apex method never checked.

**When it occurs:** Every time the LWC check is written and the Apex check is skipped "because the button is hidden."

**How to avoid:** Gate in Apex at the service entry point with `FeatureManagement.checkPermission`, which "Checks whether a custom permission is enabled" (apexref 262 L215450), and treat the LWC import purely as a rendering hint. Note also that this check is orthogonal to CRUD/FLS: since API version 67.0 "Apex runs in user context by default, meaning that the current user's permissions and field-level security (FLS) are enforced during code execution" (system mode is the default in 66.0 and earlier; apex dev guide 264 L11928-11929, L45133-45135), but user mode does not know anything about your custom permission. You need both.

```apex
public with sharing class ApprovalService {
    @AuraEnabled
    public static void approve(Id opportunityId) {
        if (!FeatureManagement.checkPermission('Approve_Big_Deals')) {
            throw new AuraHandledException('You are not authorized to approve this record.');
        }
        // ... privileged work
    }
}
```

---

## Gotcha 3: `isLicensed` is required and read-only in the metadata

**What happens:** A developer authoring a `.customPermission` file by hand sets `<isLicensed>true</isLicensed>` expecting to bind the permission to a package license, or omits the element entirely. The Metadata API describes `isLicensed` as "Required. Read-only. Indicates whether the appropriate Salesforce license is required before accessing the permission (true) or not (false)." (api_meta 264 L49046-49049). UNVERIFIED (2026-10-20): that a missing element fails the deploy and that the platform derives the value — "read-only" is all the guide says.

**When it occurs:** Hand-authored metadata, and LLM-generated `.customPermission` files that guess at the field set.

**How to avoid:** Retrieve the component from an org rather than authoring it blind, and keep the retrieved `isLicensed` value as-is. Remember the component lives in the `customPermissions` folder with the `.customPermission` suffix, and the type is available in API version 31.0 and later (api_meta 264 L49023, L49027); UNVERIFIED (2026-10-20): that an older `sourceApiVersion` fails to recognise it.

---

## Gotcha 4: `requiredPermission` creates a dependency that assignment does not satisfy

**What happens:** `Approve_Big_Deals` is authored with a `requiredPermission` entry pointing at `Access_Deal_Desk`. An admin assigns a Permission Set granting only `Approve_Big_Deals`. The Metadata API documents `requiredPermission` as indicating "which custom permissions are required by the parent custom permission" (API version 32.0 and later, api_meta 264 L49054-49057) and adds "A required custom permission must be enabled when its parent is enabled" (L49062-49063). UNVERIFIED (2026-10-20): what `checkPermission` returns for the parent when the required permission is missing — the guide states the rule, not the runtime result.

**When it occurs:** Feature hierarchies where a coarse permission implies a finer one, typically introduced by a packaged app and then re-assigned by a customer admin who only sees the leaf permission in the Permission Set UI.

**How to avoid:** Grant the whole dependency chain in one Permission Set, and assert both checks in a test that runs under `System.runAs`. Document the chain next to the feature, because nothing in the Permission Set UI shows it.

---

## Gotcha 5: Managed-package permissions need the namespace prefix — in Apex and in the LWC import

**What happens:** Code installed from a managed package calls `FeatureManagement.checkPermission('Approve_Big_Deals')` and gets `false` for a user who plainly has the permission, because the API name in the subscriber org is `acme__Approve_Big_Deals`. The LWC side fails differently and more loudly: an unresolvable `@salesforce/customPermission/...` import is a compile-time module resolution error, not a runtime `undefined` (UNVERIFIED (2026-10-20): the LWC guide does not describe the failure mode).

**When it occurs:** Any consumer code written against a packaged permission, and any code moved from the packaging org into a subscriber org.

**How to avoid:** The LWC guide is explicit: "If the custom permission was installed from a managed package, prepend the namespace followed by `__` to the permission name" (create-get-permissions.html, fetched 2026-10-20) — `@salesforce/customPermission/acme__Approve_Big_Deals`. UNVERIFIED (2026-10-20): that the same prefix applies to the Apex string argument — apexref 262 L215460 shows only `'MyCustomPermission'`, and the changeProtection example (L215338-215339) uses a bare name. Inside the package's own namespace, use the bare name: "Don't use a namespace with the permission name if you reference a custom permission from a component in the same namespace as the permission, including the default namespace" (same page).
