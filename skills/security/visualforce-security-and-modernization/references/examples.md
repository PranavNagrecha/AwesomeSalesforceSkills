# Examples — Visualforce Security And Modernization

Concrete before/after examples for hardening, modernization, and interop. Apply in priority order — fix CSRF and FLS gaps before any rewrite work, because an exposed page does not stop being a problem while it waits for migration.

---

## Example 1 — VF page with FLS guards on a custom-controller getter

**Symptom:** Customer Community user opens an Experience Cloud Visualforce page and sees an `Annual_Salary__c` field even though their permission set explicitly removes FLS read for that field. The page binds the field via `<apex:outputField value="{!emp.Annual_Salary__c}"/>` and the controller queries the record without enforcement.

**Before (vulnerable controller):**

```apex
public with sharing class EmployeeViewController {
    public Id empId { get; set; }
    public Employee__c emp { get; private set; }

    public EmployeeViewController() {
        this.empId = ApexPages.currentPage().getParameters().get('id');
        // No FLS enforcement — Salary__c is returned regardless of FLS
        this.emp = [
            SELECT Id, Name, Department__c, Annual_Salary__c
            FROM Employee__c
            WHERE Id = :this.empId
            LIMIT 1
        ];
    }
}
```

The `with sharing` keyword enforces record sharing only. The user has access to the *record* (community sharing rule), but not to the `Annual_Salary__c` *field*. The query returns the field anyway, and `<apex:outputField>` renders whatever the controller hands it.

This "before" holds when `EmployeeViewController.cls-meta.xml` pins `apiVersion` at 66.0 or below. At 67.0+ (Summer '26) the same unqualified query runs in user mode and enforces FLS on its own — the symptom above is impossible there, and this community user gets the `System.QueryException` described below instead of a salary. The "after" is then stating intent rather than closing a hole. Check the meta XML before writing the finding up — the gate is the class's pinned version, not the org's release. See [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version*.

**After (FLS-enforced via `WITH USER_MODE`):**

```apex
public with sharing class EmployeeViewController {
    public Id empId { get; set; }
    public Employee__c emp { get; private set; }

    public EmployeeViewController() {
        this.empId = ApexPages.currentPage().getParameters().get('id');
        this.emp = [
            SELECT Id, Name, Department__c, Annual_Salary__c
            FROM Employee__c
            WHERE Id = :this.empId
            WITH USER_MODE
            LIMIT 1
        ];
    }
}
```

`WITH USER_MODE` enforces FLS and CRUD for the running user, and it does so all-or-nothing: one inaccessible field in the `SELECT` list throws `System.QueryException` and the whole query fails, so the community user gets a page error rather than a redacted field. That is the intended fail-closed behaviour, but it is not a drop-in swap — either select only the fields that audience can read, or run `Security.stripInaccessible(AccessType.READABLE, records).getRecords()` where rendering the record without the salary is acceptable.

**Verification:** Log in as a community user and load the page. Either the page surfaces the `QueryException` (fail-closed), or — on the `stripInaccessible` variant — it renders with the salary absent from the HTML entirely (not merely hidden via CSS).

---

## Example 2 — CSRF-safe form with state-changing action

**Symptom:** Audit flags `<apex:page>` with `action="{!processSubmission}"` where `processSubmission()` performs DML. A crafted external page can hit the URL via `<img src="https://my-org.my.salesforce.com/apex/MyPage?id=001xxx">` and trigger the DML on behalf of any logged-in user.

**Before (CSRF-vulnerable, GET-triggered DML):**

```html
<apex:page controller="OrderProcessor" action="{!processSubmission}">
    <h1>Order processed!</h1>
</apex:page>
```

```apex
public class OrderProcessor {
    public PageReference processSubmission() {
        Id orderId = ApexPages.currentPage().getParameters().get('id');
        // DML on GET — no CSRF token required
        update new Order__c(Id = orderId, Status__c = 'Processed');
        return null;
    }
}
```

**After (DML moved to POST inside an `<apex:form>`):**

```html
<apex:page controller="OrderProcessor">
    <apex:form>
        <apex:pageMessages/>
        <p>Confirm processing of Order: <apex:outputText value="{!orderId}"/></p>
        <apex:commandButton value="Process Order" action="{!processSubmission}"/>
    </apex:form>
</apex:page>
```

```apex
public with sharing class OrderProcessor {
    public Id orderId { get { return ApexPages.currentPage().getParameters().get('id'); } }

    public PageReference processSubmission() {
        // POST inside <apex:form> — CSRF token verified by the platform automatically
        update new Order__c(Id = this.orderId, Status__c = 'Processed');
        ApexPages.addMessage(new ApexPages.Message(ApexPages.Severity.CONFIRM, 'Order processed.'));
        return null;
    }
}
```

The `<apex:form>` automatically embeds the anti-CSRF token. A `commandButton` POST submission carries the token; an external `<img>` GET cannot forge one.

**Note:** Do *not* "fix" this by setting `csrfProtection="false"` — that is a regression, not a fix. The form-based pattern shown above is the platform-correct answer.

---

## Example 3 — Hosting an LWC inside a Visualforce page (Lightning Out)

**Symptom:** A 1,800-line VF page does most of its work via legacy `<apex:pageBlockTable>`, but the team wants to replace one section — a real-time inventory table — with a modern LWC without rewriting the entire page.

**Step 1 — Lightning Out wrapper app** (`c:LegacyShellOutApp.app`):

```xml
<aura:application access="GLOBAL" extends="ltng:outApp">
    <aura:dependency resource="c:inventoryTable"/>
</aura:application>
```

**Step 2 — LWC component** (`c/inventoryTable`):

```javascript
import { LightningElement, api, wire } from 'lwc';
import getInventory from '@salesforce/apex/InventoryController.getInventory';

export default class InventoryTable extends LightningElement {
    @api warehouseId;
    @wire(getInventory, { warehouseId: '$warehouseId' }) inventory;
}
```

**Step 3 — Visualforce page hosts the LWC:**

```html
<apex:page controller="LegacyShellController" sidebar="false" standardStylesheets="false">
    <apex:includeLightning/>

    <h1>Warehouse Console</h1>
    <!-- legacy VF content remains above -->
    <apex:pageBlock title="Customer Info">
        <!-- existing markup -->
    </apex:pageBlock>

    <!-- LWC mount point -->
    <div id="inventory-container"></div>

    <script>
        $Lightning.use("c:LegacyShellOutApp", function() {
            $Lightning.createComponent(
                "c:inventoryTable",
                { warehouseId: "{!JSENCODE(warehouseId)}" },
                "inventory-container",
                function(cmp) {
                    console.log("inventoryTable mounted");
                }
            );
        });
    </script>
</apex:page>
```

**Why this matters for security:** the LWC runs inside Lightning Web Security with its own session and Locker-equivalent isolation. `@AuraEnabled` methods called from the LWC have FLS enforced if the methods use `WITH USER_MODE` or `Database.query(..., AccessLevel.USER_MODE)`. The legacy VF controller is *not* the data path for the LWC — they coexist but read separately.

**`{!JSENCODE(...)}`** is the Visualforce JS-encoding function — required when interpolating Apex values into a JS context to prevent injection.

---

## Example 4 — Navigating from a Visualforce page to an LWC tab

**Symptom:** A button on a legacy VF page should take the user to a new LWC-based page (e.g., a modernized record-detail view). Using `window.location` works in Salesforce Classic but breaks in Lightning Experience because the VF page runs in an iframe with a different origin.

**Before (Classic-only):**

```html
<apex:commandButton value="Open New View" onclick="window.location='/lightning/n/MyLwcTab'; return false;"/>
```

This does not work in LEX — the iframe's `window.location` points at `*.visualforce.com`, not the Lightning host.

**After (LEX-compatible via `sforce.one`):**

```html
<apex:page>
    <apex:includeScript value="/support/console/61.0/integration.js"/>
    <apex:commandButton value="Open New View" onclick="navigateToLwcTab(); return false;"/>
    <script>
        function navigateToLwcTab() {
            if (typeof sforce !== 'undefined' && sforce.one) {
                sforce.one.navigateToURL('/lightning/n/MyLwcTab');
            } else {
                // Fallback for Classic / standalone VF
                window.location = '/lightning/n/MyLwcTab';
            }
        }
    </script>
</apex:page>
```

`sforce.one.navigateToURL()` is the documented LEX navigation API. It uses the Lightning navigation stack and survives the iframe-to-host transition. The fallback covers Classic and standalone VF page URL access.

For navigating to a record (not a tab):

```javascript
sforce.one.navigateToSObject(recordId);
```

---

## Example 5 — Secure view-state-free pattern for a read-heavy page

**Symptom:** A read-heavy reporting Visualforce page hits the 170 KB view state ceiling for users with large data sets. Marking everything `transient` only goes so far — the real fix is to skip view state entirely.

**Before (view-state-bound, hits the ceiling):**

```apex
public with sharing class ReportController {
    public List<Account_Snapshot__c> snapshots { get; private set; }

    public ReportController() {
        this.snapshots = [
            SELECT Id, Name, Revenue__c, Region__c, Snapshot_Date__c
            FROM Account_Snapshot__c
            WHERE Snapshot_Date__c = LAST_N_MONTHS:12
            WITH USER_MODE
            LIMIT 5000
        ];
    }
}
```

**After (JavaScript Remoting — no view state):**

```html
<apex:page controller="ReportController" sidebar="false">
    <apex:includeScript value="{!URLFOR($Resource.ReportRenderer)}"/>
    <h1>Account Snapshots</h1>
    <div id="report-table"></div>
    <script>
        ReportController.getSnapshots(function(result, event) {
            if (event.status) {
                ReportRenderer.render(result, document.getElementById('report-table'));
            } else {
                console.error(event.message);
            }
        });
    </script>
</apex:page>
```

```apex
public with sharing class ReportController {
    @RemoteAction
    public static List<Account_Snapshot__c> getSnapshots() {
        return [
            SELECT Id, Name, Revenue__c, Region__c, Snapshot_Date__c
            FROM Account_Snapshot__c
            WHERE Snapshot_Date__c = LAST_N_MONTHS:12
            WITH USER_MODE
            LIMIT 5000
        ];
    }
}
```

Remote actions execute server-side over their own AJAX channel; no view state is round-tripped. FLS is still enforced via `WITH USER_MODE`. The page never accumulates state in controller properties — every load is a fresh fetch.

**Caveat:** Remote actions do not use the standard CSRF form token. They have their own session-based protection but if the action performs DML, treat it like any authenticated AJAX endpoint and validate inputs server-side. Read-only remote actions like the example above are low risk.

---

## Example 6 — Retire-or-harden inventory output

For a triage exercise, output looks like a per-page disposition table. Example for a 12-page inventory:

| Page Name | Audience | Last Modified | Issues Found | Disposition | Sunset |
|---|---|---|---|---|---|
| `AccountSummary` | Internal admin | 2018-03-12 | None | leave-alone | n/a |
| `CommunityAccountSummary` | Customer Community | 2019-08-04 | FLS gap on Salary__c via custom getter | harden-in-place | n/a |
| `CommunityOrderSubmit` | Customer Community guest | 2017-11-22 | `csrfProtection="false"`, page-action DML | rewrite-lwc | 2026-08-01 |
| `InvoicePDF` | Internal | 2020-01-09 | None — `renderAs="pdf"` | leave-alone | n/a |
| `LegacyDashboard` | Internal | 2016-04-30 | `<apex:dynamicComponent>` for permission UI, broken in LEX | rewrite-lwc | 2026-09-01 |
| `MassUpdateAccounts` | Internal admin | 2022-06-15 | None — works fine | leave-alone | n/a |
| `OrderDetail` | Internal sales | 2023-10-04 | `<apex:actionFunction>` rerender side effects but secure | harden-in-place | n/a |
| `PartnerPortalHome` | Partner Community | 2020-07-19 | View state ceiling near limit, controller without USER_MODE | harden-in-place | n/a |
| `QuoteAccept` | External signer (guest) | 2018-12-03 | Page-action DML, no FLS, no CSRF awareness | rewrite-lwc | 2026-07-01 |
| `ReportRenderer` | Internal | 2019-05-22 | None — uses remoting, no view state | leave-alone | n/a |
| `SetupWizard` | Internal admin | 2021-02-14 | Multi-step view state heavy but admin-only | leave-alone | n/a |
| `SiteContactForm` | Public guest | 2017-01-08 | `csrfProtection="false"`, no input sanitization | rewrite-lwc | 2026-06-01 |

The pattern: external-facing pages with security findings go to `rewrite-lwc` first; internal-only pages with findings go to `harden-in-place`; everything working stays.
