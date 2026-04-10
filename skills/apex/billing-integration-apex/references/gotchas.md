# Gotchas — Billing Integration Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: TransactionAPI Callout + Uncommitted DML Causes Immediate Exception

**What happens:** Any call to a `blng.TransactionAPI` method (`generateToken`, `authorize`, `capture`, `charge`, `void`, `refund`) that occurs in the same Apex transaction as uncommitted DML throws `System.CalloutException: You have uncommitted work pending. Please commit or rollback before calling out`. The entire transaction rolls back. No partial work is persisted.

**When it occurs:** In trigger handlers that perform DML (insert/update/delete) on any sObject before invoking `TransactionAPI`; in Visualforce controller actions that set fields and then call `TransactionAPI` in the same method; in `@AuraEnabled` methods that do both; in Batch Apex `execute()` when the scope processing includes DML before a gateway call.

**How to avoid:** Move all `blng.TransactionAPI` calls into a dedicated Queueable class implementing `Database.AllowsCallouts`. Enqueue the job from the synchronous context, let the synchronous transaction commit, and perform gateway calls in the async job. Use `@future(callout=true)` only when Queueable chaining is not needed and testability requirements are minimal.

---

## Gotcha 2: Connect REST API Rejects Requests with More Than 200 Billing Schedule IDs

**What happens:** Submitting a `POST /services/data/v63.0/commerce/invoices` request with a `billingScheduleIds` array containing more than 200 entries returns an HTTP 400 error. The entire call fails; no invoices are generated for any of the IDs in the oversized batch. There is no partial-success behavior — it is all-or-nothing per request.

**When it occurs:** Any time code collects billing schedule IDs (e.g., from a SOQL query returning a large active subscription base) and passes them directly to the API without chunking. A common scenario is an integration that fires on contract renewal and passes all the account's schedules in a single call.

**How to avoid:** Always chunk `billingScheduleIds` into sublists of no more than 200 before calling the API. Implement chunking at the service layer so callers cannot accidentally violate the limit. The `List.subList(fromIndex, toIndex)` method makes chunking straightforward in Apex. For very large volumes, use a Queueable chain where each job handles one chunk and enqueues the next.

---

## Gotcha 3: Omitting the blng__ Namespace Prefix Causes Silent or Compile-Time Failures

**What happens:** References to Billing managed package sObjects or fields without the `blng__` namespace prefix either cause compile-time errors (when the object is a custom managed package object) or, in dynamic SOQL/DML, cause runtime errors that are harder to diagnose. For example, querying `Invoice__c` instead of `blng__Invoice__c` fails with `SObject type 'Invoice__c' is not supported`.

**When it occurs:** When developers familiar with non-namespaced orgs write Billing code for the first time; when code is copied from documentation examples that use short names; when dynamic Apex string-builds field API names without the prefix.

**How to avoid:** Use the full `blng__` prefix on every managed package sObject API name and every field API name in SOQL, DML, and string references. Note the distinction: Apex class names use `blng.ClassName` (dot notation, no double underscore), while sObject and field API names use `blng__ObjectName__c` (double underscore). Document this convention in code comments and enforce it in code review.

---

## Gotcha 4: Connect REST API Endpoint Requires API Version 63.0 or Later

**What happens:** Calling `POST /services/data/v55.0/commerce/invoices` (or any version below 63.0) returns an HTTP 404 "The requested resource does not exist" error. The endpoint was introduced in API v63.0 (Spring '25). Earlier versions of the Connect REST API do not expose it.

**When it occurs:** When endpoint URLs are copied from documentation examples and the version is not updated; when org-wide API version defaults are below 63.0; when Named Credentials or Remote Site Settings use a base URL that hardcodes an older version.

**How to avoid:** Hardcode `v63.0` (or a constant for the minimum required version) in the endpoint string. Add a version assertion in the class header as a comment. When using Named Credentials, ensure the base URL does not include an API version suffix — compose the version in the Apex code where it is visible.

---

## Gotcha 5: Billing Package Upgrades Can Break Custom Gateway Adapter Compilation

**What happens:** Upgrading the Salesforce Billing managed package to a new version can modify the `blng.PaymentGateway` interface (adding new required methods or changing method signatures). When this happens, any Apex class implementing the interface fails to compile after the upgrade because it no longer satisfies the updated interface contract. This causes a deployment or package upgrade failure in production.

**When it occurs:** During scheduled or forced managed package upgrades in sandbox or production, when the `blng.PaymentGateway` interface has changed between the installed version and the new version.

**How to avoid:** Before upgrading the Billing package in any environment, deploy the upgrade to a full-copy sandbox first and run all Apex tests. Review the Billing package release notes for interface changes. If the interface has changed, update all adapter classes to match the new signature before upgrading production. Pin the Billing package version in CI/CD pipeline validation steps so that accidental upgrades are caught before deployment.
