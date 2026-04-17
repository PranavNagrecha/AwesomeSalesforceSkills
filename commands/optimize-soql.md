# /optimize-soql — Find and fix SOQL anti-patterns

Wraps [`agents/soql-optimizer/AGENT.md`](../agents/soql-optimizer/AGENT.md). Scans a scope for queries-in-loops, non-selective WHEREs, missing security clauses, and SELECT-star patterns. Returns ranked fixes.

---

## Step 1 — Collect inputs

Ask:

```
1. What scope should be analyzed?
   File or folder path. Example: force-app/main/default/classes/AccountService.cls
   or: force-app/main/default/classes/

2. Expected record count for any objects queried? (optional — escalates severity for LDV)

3. Target-org alias? (optional — enables live-org context)
```

---

## Step 2 — Load the agent

Read `agents/soql-optimizer/AGENT.md` fully + every skill and template listed in its **Mandatory Reads**.

---

## Step 3 — Execute

Follow the 5-step plan:
1. Extract every SOQL query in scope
2. Classify (query-in-loop, select-star, non-selective, no-security, etc.)
3. Propose before/after fixes for P0 and P1 findings
4. Recommend centralization if > 3 queries on the same sObject
5. (Optional) org-side validation

---

## Step 4 — Deliver

- Summary counts (files, queries, findings by severity)
- Findings table (file, line, severity, code, one-liner)
- Per-finding before/after code block for P0 and P1
- Centralization recommendation
- Citations

---

## Step 5 — Recommend follow-ups

- `/refactor-apex` on any class whose queries should move into a `BaseSelector` subclass.
- `/score-deployment` before shipping selector changes to production.

---

## What this command does NOT do

- Does not modify files.
- Does not create custom indexes in the org.
- Does not attempt to rewrite `Database.query(<variable>)` dynamic SOQL.
