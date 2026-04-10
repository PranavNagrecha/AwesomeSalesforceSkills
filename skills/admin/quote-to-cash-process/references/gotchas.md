# Gotchas — Quote-to-Cash Process (CPQ + Revenue Cloud)

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Contract Is the Required Pivot — Skipping It Silently Breaks Billing

**What happens:** Orders activate successfully, Order status shows "Activated", but `blng__BillingSchedule__c` records are never created for recurring subscription products. The billing run completes without generating invoices. No error is surfaced to the user.

**When it occurs:** When an Order is created directly from an approved `SBQQ__Quote__c` without first creating a Contract. This can happen via a custom Flow, Apex code, or manual Order creation from the Quote's related list. The Order is created and can be activated, but `SBQQ__Subscription__c` records are never generated because Subscriptions are created by the Contract creation step — not by the Quote-to-Order path. Without Subscriptions, the Revenue Cloud Billing trigger has no Subscription anchor to create billing schedules from.

**How to avoid:** Always contract a Quote before or alongside creating Orders for recurring products. Set `SBQQ__Quote__c.SBQQ__Contracted__c = true` to trigger CPQ's Contract creation logic. Confirm `SBQQ__Subscription__c` records exist and are linked to the Contract before activating the Order. Add a validation check: query `SBQQ__Subscription__c WHERE SBQQ__Contract__c = :contractId` and confirm count > 0 before activating.

---

## Gotcha 2: Advanced Approvals Is a Separate Managed Package — Not Bundled With CPQ

**What happens:** Code or configuration referencing `sbaa__ApprovalChain__c`, `sbaa__ApprovalRule__c`, or `sbaa__ApprovalRequest__c` throws `sObject type 'sbaa__ApprovalChain__c' is not supported` in environments where the Advanced Approvals package is not installed. In CPQ-only orgs, these objects do not exist.

**When it occurs:** When an administrator or developer assumes Advanced Approvals is included with the CPQ package (SBQQ) and attempts to create records, run SOQL, or deploy Apex that references `sbaa__` objects. It also occurs during sandbox refreshes where the CPQ package is present but Advanced Approvals was never installed in the refreshed sandbox.

**How to avoid:** Always verify both package installations separately: `SELECT NamespacePrefix FROM PackageLicense WHERE NamespacePrefix IN ('SBQQ', 'sbaa', 'blng')`. If `sbaa` is missing, Advanced Approvals is not installed and its objects are unavailable. Do not deploy Apex with `sbaa__` object references to an org where the package is absent — use dynamic SOQL or feature flags to guard these code paths.

---

## Gotcha 3: Standard Quote/QuoteLineItem APIs Return Empty Results in CPQ Orgs

**What happens:** SOQL queries against `Quote` and `QuoteLineItem`, reports built on the Quote object, and standard Approval Process email merge fields for Quote return zero records or blank values, even though the org has many active quotes.

**When it occurs:** CPQ quotes are stored on `SBQQ__Quote__c` and `SBQQ__QuoteLine__c` — not on the standard Salesforce `Quote` and `QuoteLineItem` objects. Any Apex, Flow, or SOQL that targets the standard objects will find nothing. This also affects standard report types (the "Quotes" report type returns no CPQ quote data), standard approval process entry criteria referencing `Quote` fields, and any Metadata API operations that use the standard `Quote` object.

**How to avoid:** Always use `SBQQ__Quote__c` and `SBQQ__QuoteLine__c` in CPQ orgs. Audit all existing Apex, triggers, reports, and dashboards for references to the standard `Quote` object. The presence of Salesforce CPQ does not remove the standard `Quote` object from the org schema — both objects coexist, which makes the confusion worse. Standard `Quote` records may exist for non-CPQ use cases, but CPQ-managed records live only on the SBQQ objects.

---

## Gotcha 4: Order Activation Must Precede Billing — Creation Alone Is Not Enough

**What happens:** `blng__BillingSchedule__c` records are not created even though Orders exist and the billing run has executed. The billing run log shows no errors but also no processed records.

**When it occurs:** The Order was created but its `Status` was never set to `Activated`. Revenue Cloud Billing generates billing schedules in response to the Order activation event, not Order creation. An Order in "Draft" status is invisible to the billing engine. Additionally, even if the Order is activated, `SBQQ__Contracted__c` on the Order must be `true` — CPQ sets this flag when the Order is created through the correct Contract-based path. If the Order was created outside the CPQ flow, this field defaults to `false` and billing schedules are not generated.

**How to avoid:** Confirm both conditions before expecting billing schedules: `Order.Status = 'Activated'` AND `Order.SBQQ__Contracted__c = true`. Use this diagnostic query: `SELECT Id, Status, SBQQ__Contracted__c FROM Order WHERE AccountId = :accountId ORDER BY CreatedDate DESC`. If either condition is false, billing schedules will not be created regardless of billing rule configuration.

---

## Gotcha 5: sbaa__ApprovalRequest__c Is Invisible to Standard Approval Process Queries

**What happens:** Automation or reports designed to track approval status by querying `ProcessInstance` or `ProcessInstanceWorkitem` return no records for quotes managed by Advanced Approvals. Dashboards showing "quotes pending approval" show zero even though dozens of quotes are waiting for approver action.

**When it occurs:** Advanced Approvals creates `sbaa__ApprovalRequest__c` records, not `ProcessInstance` records. The two systems are completely separate. Standard Salesforce approval-related merge fields (e.g., `{!ApprovalRequest.ApproverName}`), the Approval History related list on standard layouts, and the `ProcessInstance` API all operate on the Salesforce native approval engine — they have no visibility into the `sbaa__` runtime records.

**How to avoid:** Build all approval status reporting against `sbaa__ApprovalRequest__c`. Use fields like `sbaa__Status__c` (Pending / Approved / Rejected / Recalled), `sbaa__Approver__r.Name`, and `sbaa__TargetId__c` (the Quote's Id). Expose a custom related list on the Quote page layout showing `sbaa__ApprovalRequest__c` records for real-time approval chain visibility.

---

## Gotcha 6: Amendment Must Use CPQ's Amend Action — Raw New Orders Duplicate Billing

**What happens:** After a subscription is amended mid-term, duplicate `blng__BillingSchedule__c` records exist — one from the original Subscription and one from the new Order. The billing run generates double invoices for the same period.

**When it occurs:** The administrator or developer creates a new Order directly on the Contract (using the standard Order creation path) rather than using the CPQ "Amend" button on the Contract. The Amend flow automatically sets `SBQQ__SubscriptionEndDate__c` on the original `SBQQ__Subscription__c` to co-terminate it at the amendment date. Bypassing this step leaves the original Subscription active with no end date, causing the original billing schedule to continue alongside the new one.

**How to avoid:** Always use the CPQ Contract's "Amend" action to generate Amendment Quotes (`SBQQ__Type__c = "Amendment"`). Never create Orders or Subscriptions manually on a Contract that already has active Subscriptions. The Amendment flow handles co-termination, proration, and start-date alignment automatically.
