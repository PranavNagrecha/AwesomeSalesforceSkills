# /scan-security — Security audit for Apex, callouts, and sharing

Wraps [`agents/security-scanner/AGENT.md`](../agents/security-scanner/AGENT.md). Walks a `force-app/` tree and flags CRUD/FLS, sharing, callout-without-Named-Credential, and hardcoded-secret issues.

---

## Step 1 — Collect inputs

Ask:

```
1. What scope should be scanned?
   Example: force-app/main/default/

2. Target-org alias? (optional)

3. Severity threshold? (default P2 — show all; use P1 to hide low-severity)
```

---

## Step 2 — Load the agent

Read `agents/security-scanner/AGENT.md` in full + every reference under **Mandatory Reads Before Starting**, especially `standards/decision-trees/sharing-selection.md`.

---

## Step 3 — Execute

Follow the 6-step plan:
1. Class-level checks (sharing keyword, unescaped SOQL, callouts, hardcoded secrets)
2. DML-level checks (CRUD/FLS)
3. SOQL-level checks (WITH SECURITY_ENFORCED / USER_MODE)
4. Config-level checks (Remote Sites, debug logs with secrets)
5. Decision-tree routing for sharing findings
6. (Optional) `validate_against_org` lookup for existing `SecurityUtils` equivalents

---

## Step 4 — Deliver

- Summary counts by severity and confidence
- Findings table
- Per-finding before/after for P0 and P1
- Hardcoded-secret summary with `[REDACTED]` placeholder — never print secret values
- Citations

---

## Step 5 — Recommend follow-ups

- `/refactor-apex` for classes that need `SecurityUtils` integrated
- `/score-deployment` before shipping security fixes to production
- `/request-skill` if a finding type has no canonical skill yet

---

## What this command does NOT do

- Does not modify any file.
- Does not print secret values in the output — always `[REDACTED]`.
- Does not replace professional penetration testing.
