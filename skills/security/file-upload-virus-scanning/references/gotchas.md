# File Upload Virus Scanning — Gotchas

## 1. ContentDocument Sharing Doesn't Auto-Gate On Custom Fields

Sharing honors Content Delivery / Library settings. A `ScanStatus__c = Pending` value does not by itself block sharing — you must wire the gate in LWC, Apex, or sharing rules.

## 2. Email-to-Case Attachments Arrive Without UI

Inbound emails create ContentVersions without a UI upload. The trigger fires but the user who sent the email gets no scan-pending message.

## 3. Preview Generation Is Async And Fast

Salesforce can generate a file preview before your post-save scan completes. Users can see bytes you have not yet verified.

## 4. Files Are Insert-Only

You cannot "clean" a ContentVersion blob. Quarantine means retaining the record with restricted sharing and redacting downstream.

## 5. Scanner Timeouts Need An Explicit Policy

If the scanner is unreachable, your policy must decide: fail-open (allow) or fail-closed (block). Defaults vary by service.
