# LLM Anti-Patterns — Login Forensics

Common mistakes AI coding assistants make when generating or advising on Salesforce login investigation and forensics.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming LoginHistory Retains Data Beyond 6 Months

**What the LLM generates:** "Query LoginHistory for login events from the past 12 months to reconstruct the timeline."

**Why it happens:** LLMs do not consistently enforce the 6-month retention limit. Training data describes LoginHistory without emphasizing the hard purge boundary.

**Correct pattern:**

```
LoginHistory retains records for exactly 6 months. Records older than 6 months
are automatically purged with no recycle bin and no recovery path. There is no
admin override to extend retention.

If the investigation window exceeds 6 months, the data does not exist in
Salesforce unless the org was continuously exporting to a SIEM. For long-term
login audit, automate periodic SOQL exports via REST API into external storage.
```

**Detection hint:** If the advice queries LoginHistory for data older than 6 months, the query will return no results and the data cannot be recovered.

---

## Anti-Pattern 2: Relying on the Setup UI for Cross-User IP Analysis

**What the LLM generates:** "Check Setup > Login History to identify all users who logged in from the suspicious IP."

**Why it happens:** LLMs recommend the simplest UI path. The Setup > Login History page shows recent records but does not support complex filtering, cross-user pivots, or aggregation.

**Correct pattern:**

```
The Setup > Login History UI shows the most recent 20,000 records and does not
support cross-user GROUP BY or IP-based pivot analysis. For incident response:

Use SOQL for cross-user IP pivoting:
  SELECT SourceIp, COUNT(Id) loginCount, COUNT_DISTINCT(UserId) affectedUsers
  FROM LoginHistory
  WHERE LoginTime >= LAST_N_DAYS:7 AND Status != 'Success'
  GROUP BY SourceIp
  ORDER BY loginCount DESC

SOQL is mandatory for incident response at any scale beyond trivial single-user
lookups.
```

**Detection hint:** If the advice relies solely on the Setup UI for multi-user login investigation, it will miss the aggregation and filtering capabilities needed for incident response.

---

## Anti-Pattern 3: Interpreting IdentityVerificationHistory 'Trusted' as MFA Completed

**What the LLM generates:** "The IdentityVerificationHistory shows Trusted status, confirming the user completed MFA."

**Why it happens:** LLMs equate "Trusted" with verified. In reality, "Trusted" means Salesforce skipped the MFA prompt because the device or network was registered as trusted.

**Correct pattern:**

```
IdentityVerificationHistory Status values:
- Success → the user was prompted AND completed verification
- Failure → the user was prompted and failed
- Skipped → the user was not prompted (investigate why)
- Trusted → the user's device or network was trusted, so Salesforce SKIPPED
  the MFA prompt entirely

"Trusted" does NOT mean MFA was performed. It means MFA was NOT required
because of a trust decision. During an investigation, check the Activity field
to understand what was being verified and whether the trust decision was
appropriate.
```

**Detection hint:** If the advice interprets "Trusted" as confirmation of MFA completion, the investigation conclusion is wrong.

---

## Anti-Pattern 4: Not Accounting for Internal IPs on API Logins

**What the LLM generates:** "Use the SourceIp field to determine the geographic origin of all login attempts."

**Why it happens:** LLMs assume SourceIp always reflects the true client IP. For API logins using OAuth client credentials flow or IP relaxation, SourceIp may reflect a Salesforce internal datacenter IP.

**Correct pattern:**

```
When an integration or connected app authenticates using the OAuth client
credentials flow or with IP relaxation enabled, the SourceIp field may contain
a Salesforce internal datacenter IP rather than the true client IP.

This causes:
- IP allowlisting checks to produce false negatives
- Geo-analysis to be unreliable for API-based logins
- Cross-user IP pivot queries to cluster on Salesforce internal IPs

Filter API-based logins (LoginType contains 'Remote Access') separately from
UI logins when performing IP-based analysis.
```

**Detection hint:** If the advice performs geographic IP analysis on all login types without distinguishing API logins from UI logins, the results will include misleading Salesforce internal IPs.

---

## Anti-Pattern 5: Grouping Login Failures with Inconsistent Status Values

**What the LLM generates:** `WHERE Status = 'Failed'` to find all login failures.

**Why it happens:** LLMs assume a single failure status value. The Status field contains inconsistent values depending on LoginType (UI, SAML, API).

**Correct pattern:**

```
The Status field values are NOT normalized across LoginType:
- Direct login failure: "Invalid Password"
- SAML SSO failure: "Failed"
- IP restriction denial: "No Salesforce.com Access"
- Other failures: various values

The only reliable cross-type failure query pattern is:
  WHERE Status != 'Success'

Using Status = 'Failed' alone will miss UI login failures (Invalid Password)
and IP restriction denials (No Salesforce.com Access).
```

**Detection hint:** If the query filters on a single Status value like 'Failed' instead of `!= 'Success'`, it will miss login failures from other LoginTypes.

---

## Anti-Pattern 6: Confusing LoginHistory with Login Forensics Feature

**What the LLM generates:** "Use LoginHistory to see session duration and correlated API calls" or "The Login Forensics feature is available in all orgs."

**Why it happens:** LLMs conflate the free LoginHistory sObject with the paid Login Forensics feature (Event Monitoring add-on). Training data uses both terms loosely.

**Correct pattern:**

```
LoginHistory (free, all orgs): Stores login attempts for 6 months. Fields
include UserId, LoginTime, SourceIp, Status, Browser, Platform. Does NOT
include session duration, pages accessed, or correlated API calls.

Login Forensics (paid, Event Monitoring add-on): Enriched per-session data
including session duration and activity patterns. Accessed via Setup > Login
Forensics, which requires the "View Login Forensics" permission.

Having Event Monitoring access does NOT automatically grant Login Forensics
access — the "View Login Forensics" permission must be explicitly granted.
```

**Detection hint:** If the advice expects session-level detail from LoginHistory or assumes Login Forensics is available without the Event Monitoring add-on, the feature distinction is missing.
