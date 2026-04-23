# Flow Batch Alternatives — Gotchas

## 1. Scheduled Flow Does Not Retry A Failed Interview

One failure fails that record, not the schedule. You must build retry
explicitly (error-path flow, custom log, next-run resume).

## 2. Per-Record Flow ≠ Bulk Flow

Record-Triggered Flow sounds bulk but runs per record unless you use the
"Run Asynchronously" path or collection actions carefully.

## 3. Platform Event Limits Still Apply

Fan-out via Platform Events has daily allocation and per-transaction publish
caps. Plan for the total daily event volume.

## 4. Invocable Apex Called In A Loop Is A Trap

Calling an Invocable Action inside a Flow loop over a collection re-invokes
Apex per record, not once with the bulk. Pass the whole collection.

## 5. Scheduled Flow Does Not Promise Ordering

Interviews can run in any order. Do not depend on record-A-before-record-B.

## 6. Mixed DML Rules Still Apply

Flow that touches User or Group plus standard objects in one transaction can
hit Mixed DML restrictions — chunking does not fix this on its own.
