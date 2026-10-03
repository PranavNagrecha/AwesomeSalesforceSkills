# Apex Governor Limits: Quoted Reference

Every value below is copied from the Apex Developer Guide, Summer '26 (release 262), "Execution Governors and Limits," downloaded from https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf and converted with `pdftotext -layout`. "L" numbers are line numbers in that text file so a reviewer can re-check each value. The guide says these limits throw a runtime exception that can't be handled.

## Per-Transaction Apex Limits

The guide: "These limits count for each Apex transaction. For Batch Apex, these limits are reset for each execution of a batch of records in the execute method" (L19530 to L19531). "Although scheduled Apex is an asynchronous feature, synchronous limits apply to scheduled Apex jobs" (L19536). "For Bulk API and Bulk API 2.0 transactions, the effective limit is the higher of the synchronous and asynchronous limits" (L19537).

| Limit | Synchronous | Asynchronous | Line |
|---|---|---|---|
| Total number of SOQL queries issued | 100 | 200 | L19544 |
| Total number of records retrieved by SOQL queries | 50,000 | 50,000 | L19546 |
| Total number of records retrieved by Database.getQueryLocator | 10,000 | 10,000 | L19548 |
| Total number of SOSL queries issued | 20 | 20 | L19550 |
| Total number of records retrieved by a single SOSL query | 2,000 | 2,000 | L19552 |
| Total number of DML statements issued | 150 | 150 | L19554 |
| Total number of records processed as a result of DML statements, Approval.process, or database.emptyRecycleBin | 10,000 | 10,000 | L19556 |
| Total stack depth for any Apex invocation that recursively fires triggers due to insert, update, or delete statements | 16 | 16 | L19559 |
| Total number of callouts (HTTP requests or web services calls) in a transaction | 100 | 100 | L19563 |
| Maximum cumulative timeout for all callouts in a transaction | 120 seconds | 120 seconds | L19565 |
| Maximum number of methods with the future annotation allowed per Apex invocation | 50 | 0 in batch and future contexts; 50 in queueable context | L19568 |
| Maximum number of Apex jobs added to the queue with System.enqueueJob | 50 | 1 | L19573 |
| Total number of sendEmail methods allowed | 10 | 10 | L19575 |
| Total heap size | 6 MB | 12 MB | L19577 |
| Maximum CPU time on the Salesforce servers | 10,000 milliseconds | 60,000 milliseconds | L19579 |
| Maximum execution time for each Apex transaction | 10 minutes | 10 minutes | L19581 |
| Maximum number of push notification method calls allowed per Apex transaction | 10 | 10 | L19583 |
| Maximum number of EventBus.publish calls for platform events configured to publish immediately | 150 | 150 | L19598 |
| Maximum number of rows across all Apex cursors per transaction | 50 million | 50 million | L19601 |
| Maximum number of Cursor.fetch calls per transaction | 100 | 100 | L19603 |
| Maximum number of rows across all Apex pagination cursors per transaction | 100,000 | 100,000 | L19605 |
| Maximum number of Apex pagination cursor instances per transaction | 50 | 50 | L19607 |

Footnotes that change how the counts work:

- Parent-child relationship subqueries count as extra queries, limited to three times the top-level query number; custom metadata records can have unlimited SOQL queries; `Database.countQuery`, `Database.getQueryLocator`, and `Database.query` (and their WithBinds forms) count as SOQL statements (L19613 to L19621).
- `Approval.process`, `Database.convertLead`, `Database.emptyRecycleBin`, `Database.rollback`, `Database.setSavePoint`, all DML verbs, `EventBus.publish` for publish-after-commit events, and `System.runAs` count as DML statements (L19623 to L19636).
- Email services heap size is 50 MB (L19650).
- CPU time includes processes called from the code, such as package code and workflows; time spent in the database for DML, SOQL, and SOSL and waiting time for callouts isn't counted (L19652 to L19657).
- Limits apply individually to each test method (L19660).

## Certified Managed Package Cumulative Limits

Certified managed packages get their own per-namespace limits; the cumulative cross-namespace limit is 11 times the per-namespace limit (L19676 to L19682).

| Limit | Cumulative cross-namespace | Line |
|---|---|---|
| Total number of SOQL queries issued | 1,100 | L19693 |
| Total number of records retrieved by Database.getQueryLocator | 110,000 | L19695 |
| Total number of SOSL queries issued | 220 | L19707 |
| Total number of DML statements issued | 1,650 | L19709 |
| Total number of callouts | 1,100 | L19711 |
| Total number of sendEmail methods allowed | 110 | L19713 |

Heap size, CPU time, transaction execution time, and the number of unique namespaces count for the whole transaction regardless of packages (L19717 to L19721).

## Salesforce Platform Apex Limits (org-wide)

| Limit | Value | Line |
|---|---|---|
| Asynchronous Apex method executions (batch, future, Queueable, scheduled) per 24 hours | 250,000 or applicable user licenses multiplied by 200, whichever is greater | L19732 to L19736 |
| Maximum number of Apex cursors per day | 10,000 | L19753 |
| Maximum cumulative new cursor rows and pagination cursor rows per 24-hour period | 100 million | L19763 |
| Maximum number of Apex pagination cursor instances per 24-hour period | 200,000 | L19765 |
| Concurrent long-running (over 5 seconds) synchronous transactions | 1 per 100 licenses; minimum 10, maximum 50 | L19767 to L19774 |
| Maximum number of Apex classes scheduled concurrently | 100 (5 in Developer Edition) | L19776 |
| Batch Apex jobs in the flex queue in Holding status | 100 | L19779 |
| Batch Apex jobs queued or active concurrently | 5 | L19781 |
| Batch Apex job start method concurrent executions | 1 | L19783 |
| Batch jobs that can be submitted in a running test | 5 | L19785 |

## Static and Size-Specific Limits

| Limit | Value | Line |
|---|---|---|
| Default timeout of callouts | 10 seconds | L19843 |
| Maximum size of callout request or response | 6 MB synchronous, 12 MB asynchronous (counts toward heap) | L19845, L19860 |
| Maximum SOQL query run time before Salesforce cancels the transaction | 120 seconds | L19848 |
| Apex trigger batch size | 200 (2,000 for platform events and Change Data Capture events) | L19852, L19862 |
| For loop list batch size | 200 | L19854 |
| Maximum records returned for a Batch Apex query in Database.QueryLocator | 50 million | L19856 |
| Maximum characters for a class or trigger | 1 million | L19869, L19871 |
| Maximum amount of code used by all Apex in an org | 6 MB (10 MB for scratch orgs; excludes managed packages and @IsTest classes) | L19873, L19885 to L19896 |
| Method size limit | 65,535 bytecode instructions in compiled form | L19875 |
| MAX_DML_ROWS in a single synchronous Apex test execution context | 450,000 | L19916 |

UNVERIFIED (2026-10-03): the release in which Apex cursors became generally available; the 262 guide documents them without a version note.
