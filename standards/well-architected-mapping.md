# Well-Architected Framework Pillar Reference

This is the reference mapping for applying Salesforce Well-Architected Framework (WAF) pillars to skill findings. Use this when tagging findings in code reviews and org assessments.

Source: [Salesforce Well-Architected Framework](https://architect.salesforce.com/well-architected/overview)

---

## The Six Pillars

### 1. Security

**What it covers:** Protecting data from unauthorised access, ensuring FLS/CRUD/sharing rules are correctly applied, preventing injection attacks, managing credentials safely.

**In practice — tag a finding as Security when:**
- SOQL is missing `WITH SECURITY_ENFORCED` or `WITH USER_MODE`
- DML is performed without FLS checks (`stripInaccessible` or field-level `isUpdateable()` check)
- Dynamic SOQL uses string concatenation instead of bind variables
- Credentials, IDs, or sensitive values are hardcoded
- A class is declared `without sharing` without documented justification
- Sensitive data appears in logs or is returned to the UI without masking

**WAF questions for Security:**
- Who can read/write this data?
- What happens if an attacker crafts a malicious input?
- What happens if a user without field access calls this code?

---

### 2. Reliability

**What it covers:** The system behaves correctly under normal and abnormal conditions. Error handling, transaction integrity, recovery from failures.

**In practice — tag a finding as Reliability when:**
- try/catch blocks swallow exceptions without logging or rethrowing
- DML inside a try/catch has no `Database.rollback()` strategy
- Callouts have no error handling for non-200 responses
- Flows have no fault connectors on callout elements
- Batch jobs have no scope-level error isolation (failure of one record kills the batch)
- Code assumes data exists without null checks

**WAF questions for Reliability:**
- What happens when this fails?
- Is the failure silent or observable?
- Can a user or admin recover from the failure state?

---

### 3. Performance

**What it covers:** Response time, efficient resource usage, avoiding patterns that cause user-visible slowness.

**In practice — tag a finding as Performance when:**
- SOQL inside a for loop (query-in-a-loop)
- Synchronous operations that should be async (heavy computation in a before-save trigger)
- Missing SOQL query filters on large objects (full-table scans)
- SOQL queries selecting `SELECT *` (all fields) when only a few are needed
- LWC making multiple server calls when one would do
- Apex CPU time approaching limits in non-batch context

**WAF questions for Performance:**
- How does this behave with 10,000 records instead of 10?
- Is the user waiting for something that could be background-processed?
- Are we fetching more data than we need?

---

### 4. Scalability

**What it covers:** Behaviour under increasing data volumes, user concurrency, and transaction scale. Governor limits, bulkification, architecture that grows with the org.

**In practice — tag a finding as Scalability when:**
- Not bulkified (written to process one record, not 200)
- Approaching governor limits in current implementation — will hit them as data grows
- Single-threaded patterns where parallel processing would help
- LDV (Large Data Volume) patterns missing on objects that will grow large
- Record locks and concurrency issues (e.g. row locking in update-heavy triggers)
- SOQL queries missing selective indexes on filter fields

**WAF questions for Scalability:**
- At what data volume does this break?
- What happens if 100 users trigger this simultaneously?
- What happens when this object has 10 million records?

---

### 5. User Experience

**What it covers:** The quality of the experience for end users: clarity of error messages, accessibility, page load time, Flow screen design.

**In practice — tag a finding as User Experience when:**
- Error messages expose internal system details (`Apex error: NullPointerException at line 42`)
- LWC has no loading state for async operations
- Flow screen doesn't handle validation gracefully
- Accessibility: interactive elements missing labels, colour-only information
- Screen Flow has no "previous" button where backtracking makes sense
- UI blocks the user with a spinner for a background operation

**WAF questions for User Experience:**
- What does the user see when this fails?
- Can a non-technical user understand the error message and recover?
- Is there a loading indicator for operations that take > 1 second?

---

### 6. Operational Excellence

**What it covers:** Maintainability, deployability, observability, and the ability of a team to work confidently with the system over time.

**In practice — tag a finding as Operational Excellence when:**
- No test class, or test class has no assertions
- Hardcoded IDs that will break on sandbox refresh or deployment
- No `salesforce-context.md` or equivalent org documentation
- No scratch org definition (no repeatable environment)
- `System.debug` as the only logging (not queryable, not structured)
- Code with no comments where the intent isn't obvious
- Flows with undescriptive variable names (`variable1`, `tempCollection`)
- Missing or outdated `package.json` / `sfdx-project.json`

**WAF questions for Operational Excellence:**
- Can a new developer understand and modify this safely?
- Will this deploy cleanly to a fresh org?
- When this fails in production at 2am, is there enough context to diagnose it quickly?

---

## Pillar Tagging Rules

**One primary pillar per finding.** If a finding touches multiple pillars, assign it to the one that best describes the *consequence* of not fixing it.

| Finding | Primary Pillar | Why |
|---------|---------------|-----|
| SOQL without `WITH SECURITY_ENFORCED` | Security | Consequence is data exposure |
| SOQL inside a for loop | Scalability | Consequence is governor limit failure at scale |
| try/catch with no error handling | Reliability | Consequence is silent failure |
| Missing loading spinner | User Experience | Consequence is user confusion |
| Hardcoded RecordType ID | Operational Excellence | Consequence is deployment failure |

**Escalation rule:** If the finding is in the Security pillar, it is always at least High severity — there is no such thing as a Low-severity security finding that isn't worth fixing.

---

## Scoring Model

Used by the org-assessor agent:

| Severity | Score Deduction | Per Pillar |
|----------|----------------|-----------|
| Critical | -20 | From 100 base |
| High | -10 | |
| Medium | -5 | |
| Low | -1 | |
| Floor | 0 | Cannot go below 0 |

A Critical finding in Security caps the Security pillar score at 40/100 regardless of other findings. This reflects that a single FLS bypass in an otherwise clean codebase is still a serious security posture problem.
