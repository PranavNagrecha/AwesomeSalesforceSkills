# /gen-tests — Generate a bulk-safe Apex test class

Wraps [`agents/test-class-generator/AGENT.md`](../agents/test-class-generator/AGENT.md). Takes a target Apex class, produces a test class targeting ≥ 85% coverage using the canonical factories in `templates/apex/tests/`.

---

## Step 1 — Collect inputs

Ask:

```
1. Path to the Apex class to test?
   Example: force-app/main/default/classes/AccountService.cls

2. Target coverage percentage? (default 85)

3. Include a 200-record bulk test? (default yes)
   Say no only for utility / constant classes with no DML.
```

---

## Step 2 — Load the agent

Read `agents/test-class-generator/AGENT.md` fully, plus every template under its **Mandatory Reads**.

---

## Step 3 — Execute

Follow the 5-step plan:
1. Read the source and extract its public surface
2. Determine scenarios (happy / bulk / runAs / negative / callout)
3. Draft the test class using `TestDataFactory`, `TestUserFactory`, `MockHttpResponseGenerator`, `BulkTestPattern`
4. Estimate coverage and flag gaps
5. Output checklist (no SeeAllData, meaningful assertions, etc.)

---

## Step 4 — Deliver

Output:
- Summary (public methods, scenarios, coverage estimate)
- Full test class as a fenced block at the target path (`<Source>_Test.cls` + `.cls-meta.xml`)
- Coverage gaps with reasons
- Dependencies the user must have deployed (`TestDataFactory`, etc.)
- Citations

---

## Step 5 — Recommend follow-ups

- `/refactor-apex` if the source class is hard to test (suggests shape problems).
- `/scan-security` on the source class if the generator noted CRUD/FLS concerns.

---

## What this command does NOT do

- Does not execute tests.
- Does not modify the source class.
- Does not write `SeeAllData=true`.
