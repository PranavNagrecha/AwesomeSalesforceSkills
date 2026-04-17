# LLM Anti-Patterns — Flow Error Monitoring

## Anti-Pattern 1: Logging PII in message bodies

**What the LLM generates:** `message = 'Failed for user ' + user.Email + ' with SSN ' + user.SSN__c`

**Why it happens:** LLMs dump context into error messages.

**Correct pattern:** Log record Ids only. Reference the User via Id; never log PII fields.

---

## Anti-Pattern 2: One generic email alert

**What the LLM generates:** Every fault → Send Email to ops@company.com.

**Why it happens:** Default single-channel alerting.

**Correct pattern:** Route by severity + domain. CRITICAL → page. ERROR → domain-specific email. WARNING → daily digest.

---

## Anti-Pattern 3: Log without correlation Id

**What the LLM generates:** Flat log schema without a correlation Id.

**Why it happens:** LLMs produce minimal schemas.

**Correct pattern:** Every log entry has a correlation Id that groups related failures across the transaction (all entries with same correlation Id = one root cause).

---

## Anti-Pattern 4: Dashboard without filter

**What the LLM generates:** "Show all errors from last 30 days" — 50,000 rows, dashboard times out.

**Why it happens:** LLMs default to comprehensive views.

**Correct pattern:** Filter by severity = CRITICAL or ERROR for headline view; WARNING and INFO on demand.

---

## Anti-Pattern 5: No retention policy

**What the LLM generates:** Log forever.

**Why it happens:** LLMs don't think about storage cost.

**Correct pattern:** Archive to Big Object at 90 days; delete at 2 years. External observability (Splunk) holds the long-tail.

---

## Anti-Pattern 6: Ignoring unhandled faults

**What the LLM generates:** Flow without fault connectors; relies only on default fault email.

**Why it happens:** LLMs treat fault-path wiring as optional when not explicitly required.

**Correct pattern:** Every DML-class element has an explicit fault connector wired to the central log.
