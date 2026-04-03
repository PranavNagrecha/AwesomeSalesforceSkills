# Gotchas: Flow for Admins

---

## Fault Connectors Are Not Optional on DML and Callout Elements

**What happens:** A Record-Triggered Flow creates a child record. The parent record is deleted between the trigger firing and the DML executing (race condition in a concurrent environment). The Flow fails with an unhandled exception. The triggering record's save is rolled back. The user gets a generic error. No one gets notified. The admin finds out three days later when a user says "I've been getting a weird error."

**When it bites you:** Every time a Flow performs DML or makes a callout without a fault connector. Common in: high-concurrency environments, records that users frequently delete, integrations that update records simultaneously.

**How to avoid it:**
- Every Get Records, Create Records, Update Records, Delete Records, and callout element gets a fault connector. No exceptions.
- The fault path minimum: Send an email to the org admin with `{!$Flow.FaultMessage}` and the record ID
- Better: Create a record in an Error_Log__c custom object so errors are queryable
- Best for Screen Flows: Show the user a human-readable error screen so they know what happened

---

## Record-Triggered Flows Run Once Per Record in the Batch — Not Once Per Bulk Operation

**What happens:** An admin writes a Record-Triggered Flow that includes a Get Records element to query related Cases. The flow works fine in testing (one record at a time). In production, a data migration updates 200 Accounts simultaneously. The flow runs 200 times, executing 200 Get Records queries. The SOQL limit is 100 per transaction. The 101st Account fails.

**When it bites you:** Any bulk operation on an object with a Record-Triggered Flow that includes Get Records — data migrations, mass updates via reports, API batch operations.

**How to avoid it:**
- Don't use Get Records inside a Loop element in a Record-Triggered Flow
- Use Flow formulas to reference the triggering record's fields directly — no additional SOQL needed
- For truly complex cross-object logic in bulk contexts, consider Apex (which can batch queries efficiently) rather than Flow

---

## Before-Save Flows Cannot Make DML Calls

**What happens:** An admin builds a Before-Save Record-Triggered Flow. Partway through, they add a "Create Records" element to create a related Task. The flow activates. First time it runs, it throws: `CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY`. The error is confusing. The admin spends an hour investigating.

**When it bites you:** Every time someone adds a DML element to a Before-Save flow without realising the restriction.

**How to avoid it:**
- Before-Save flows: field updates on the triggering record ONLY (using "Update Triggering Record" element)
- Any DML on other records → change to After-Save
- The distinction to remember: Before-Save = "change this record before it's written." After-Save = "do things after the record exists."

---

## Screen Flows Don't Support Bulk — and That's Okay

**What happens:** An admin tries to use a Screen Flow to process multiple records. The Screen Flow processes one user session at a time — it's not designed for bulk operations. The admin tries to call it from a trigger or a batch process and gets unexpected behaviour.

**When it bites you:** When someone tries to use a Screen Flow as automation logic rather than user interface.

**How to avoid it:**
- Screen Flows are for user-guided processes — one user, one session, one interaction
- For bulk processing: use Record-Triggered Flows, Scheduled Flows, or Batch Apex
- A Screen Flow invoked from a list view Quick Action runs once per selected record — it is NOT truly bulk; the user clicks through multiple times

---

## Flow Interviews Consume Governor Limits in the Calling Transaction

**What happens:** An Apex trigger calls a Flow via `Flow.Interview`. The Apex trigger processes 200 records. The Flow has 2 Get Records elements each. That's 400 Flow SOQL calls, plus the Apex trigger's own queries. Total exceeds 100 SOQL limit. Transaction fails. Data is rolled back.

**When it bites you:** Apex-invoked Flows in triggers, especially in bulk contexts.

**How to avoid it:**
- When calling Flows from Apex, design the Flow to be SOQL-minimal
- Pass data INTO the Flow as input variables (Apex queries once, passes results) rather than having the Flow query
- Or: Avoid calling Flows from Apex triggers altogether for complex logic — keep the logic in Apex where you control the query pattern
