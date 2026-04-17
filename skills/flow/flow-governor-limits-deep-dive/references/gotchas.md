# Gotchas — Flow Governor Limits Deep Dive

## Gotcha 1: Limits are shared; your flow doesn't own 100 SOQL

Every SOQL from every concurrent automation counts. Forecast against the shared pool, not the nominal 100 limit.

---

## Gotcha 2: Subflow limits count against parent

Invoking a subflow doesn't create a new transaction; its SOQL + DML add to the parent's budget.

---

## Gotcha 3: Get Records fetches ALL fields by default

Every field counts against heap. Specify fields explicitly to reduce heap + CPU.

---

## Gotcha 4: Scheduled Path limit is fresh but parallel

Multiple Scheduled Paths can fire concurrently on a single trigger event (if batch > 200). Concurrent writes to the same record can race.

---

## Gotcha 5: Async limits are per-execution, not per-job

A Queueable firing 100 times still gets 200 SOQL per firing — not 200 total. Same for scheduled flows per scheduled execution.

---

## Gotcha 6: CPU time limit catches nothing useful in error reports

CPU timeouts surface as "script error"; the specific element that busted the budget isn't obvious. Use debug logs + a pre-deployment benchmark.

---

## Gotcha 7: Loops with zero iterations still consume CPU

Even an empty collection-valued Loop costs CPU for setup. Avoid conditional loops when the input is often empty; branch on Decision instead.

---

## Gotcha 8: Element cost isn't advertised

Salesforce doesn't publish "Decision costs X ms" tables. Benchmark per-element cost in your org; numbers change between releases.

---

## Gotcha 9: Platform-Event subscriber batches can surprise

High-Volume PE subscribers receive up to 10,000 events per batch. Each run has fresh limits but a big loop inside the subscriber flow can still breach CPU.
