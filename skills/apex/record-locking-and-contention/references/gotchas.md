# Gotchas — Record Locking and Contention

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Child DML Silently Locks the Parent Row

**What happens:** Inserting, updating, or deleting a child record acquires an exclusive lock on the parent record in addition to the child row. This is not visible in code and is not documented in the DML statement itself.

**When it occurs:** Any master-detail or lookup relationship where the parent has rollup summary fields, sharing rules, or where the platform recalculates parent-level aggregates. Most commonly seen with Account-Contact, Account-Opportunity, and custom master-detail hierarchies.

**How to avoid:** Recognize that concurrent child operations against the same parent will contend. Sort child records by parent ID before DML. For extreme skew, request Granular Locking from Salesforce Support.

---

## Gotcha 2: FOR UPDATE Is Prohibited in Batch Apex Start Queries

**What happens:** Using FOR UPDATE in the SOQL query returned by `Database.getQueryLocator()` throws a runtime error. FOR UPDATE is only allowed in inline SOQL within `execute()` methods or synchronous Apex.

**When it occurs:** Developers try to "pre-lock" records in the batch start method to prevent contention during execute.

**How to avoid:** Use ORDER BY in the start query to group records by parent key. Handle locking within the execute method if needed, or sort the scope list before DML.

---

## Gotcha 3: Aggregate SOQL Blocks on Locked Rows

**What happens:** A SOQL query with aggregate functions (COUNT, SUM, GROUP BY) that touches rows locked by another transaction will wait for the lock to release, potentially timing out with UNABLE_TO_LOCK_ROW.

**When it occurs:** Reporting queries or summary calculations that run concurrently with DML-heavy batch jobs or data loads.

**How to avoid:** Schedule aggregate queries during low-activity windows. Alternatively, use async summarization so the aggregate runs after the DML transaction completes.

---

## Gotcha 4: Platform Events and Change Data Capture Replay Can Amplify Contention

**What happens:** Platform event subscribers and CDC triggers process events in parallel by default. If multiple events reference the same parent records, the subscriber transactions contend on those parent rows.

**When it occurs:** High-volume event publishing where events share a common parent record, such as many OrderItem events all referencing the same Order.

**How to avoid:** Use event partition keys to route related events to the same subscriber instance. Implement retry logic in the subscriber. Consider serial processing for skewed event streams.

---

## Gotcha 5: The Lock Timeout Is Always 10 Seconds and Is Not Configurable

**What happens:** When a transaction waits for a row lock held by another transaction, the platform waits exactly 10 seconds before throwing UNABLE_TO_LOCK_ROW. There is no API, setting, or support request that changes this timeout.

**When it occurs:** Any concurrent access to the same row, whether from Apex, Bulk API, Data Loader, or the UI.

**How to avoid:** Design for short lock-hold times. Move expensive logic before or after the DML window. Use FOR UPDATE only when necessary, and keep post-query logic minimal.
