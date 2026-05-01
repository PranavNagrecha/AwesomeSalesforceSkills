# Examples — Zero-Trust Salesforce Patterns

## Example 1 — "Block report exfiltration without breaking the day-to-day"

**Context:** A regulated org wants to detect and block large report
exports that appear to be exfiltration. Sales reps run normal-sized
reports throughout the day; the threat is a single user exporting a
20k-row report containing PII at 11pm.

**Problem:** The simplest approach — disabling Export — breaks
legitimate work. An after-the-fact Event Monitoring review finds the
incident a day later, after the data has left.

**Solution (composition):**

```text
1. RTEM event: ReportEvent (subscribe via TSP).
2. Transaction Security Policy:
     IF EventType = ReportEvent
        AND RowsProcessed > 5000
        AND TimeOfDay BETWEEN 22:00 AND 06:00 (user local time)
     THEN Action = Require MFA + Notify Security
     ELSE log only.
3. PSG-level High Assurance: required for the "ExportLargeReports" PSG.
4. Login Flow: read Azure AD device-state claim;
     if device is not "compliant", deny session.
5. Quarterly review of TSP firings; tune thresholds.
```

**Why it works:** All four zero-trust legs participate. Verify
explicitly (TSP step-up + High-Assurance), least privilege (the
ExportLargeReports PSG is JIT, not standing), continuous verification
(TSP fires in real time), device awareness (Login Flow checks IdP
claim). The user with normal behavior never sees the controls; the
exfiltration attempt hits step-up MFA at 11pm and the security team
gets paged.

---

## Example 2 — "Step-up before viewing customer SSN, without forcing step-up everywhere"

**Context:** A financial services org stores customer SSNs in a custom
field on Account. Compliance wants step-up MFA before any user views
the field, but does not want every Account interaction to trigger MFA.

**Problem:** Setting High-Assurance Session at the Profile level means
every Account page-load triggers step-up — break-glass moves into the
ordinary work surface and reps disable everything.

**Solution:** Move the SSN field-level read permission into a dedicated
Permission Set, group it into a "ViewSSN" PSG, and configure the PSG's
**Session Settings** to require High Assurance. Default users do not
have the PSG; a JIT-grant Apex Flow assigns the PSG when a rep opens a
case for a customer who has consented to SSN review, and revokes it
after 30 minutes.

```text
PermissionSetGroup ViewSSN
  - Permission Set: Account.SSN__c read = true
  - Session Settings: Session Security Level Required = High Assurance
  - Mute: nothing else
JIT grant: Apex Flow on Case open with reason = SSN-Review,
           assigns PSG, schedules unassign at +30 min.
```

**Why it works:** The high-assurance step-up fires only when the user
exercises the SSN-read right, not on every Account page-load. The PSG
also makes the access logged: Setup Audit Trail shows the PSG
assignment, RTEM can fire on `PermissionSetEvent`, and the JIT pattern
makes the access self-revoking.

---

## Anti-Pattern — "We have MFA, so we have zero trust"

**What practitioners do:** Roll out MFA universally, declare the
zero-trust project complete, and check the auditor's box.

**What goes wrong:** MFA is the **verify-explicitly leg at session
start, once**. It does not provide:

- Continuous verification (no RTEM, no TSP, so a stolen session token works for as long as the session lasts).
- Least privilege (Modify All Data still standing on 200 Profiles).
- Device trust (Login Flow does not consult the IdP for device-state).

The auditor's follow-up question — "show me what blocks an authenticated
user from exporting a 20k-row PII report at 11pm from a personal
device" — has no answer.

**Correct approach:** Treat MFA as one input to the verify-explicitly
leg, then layer the other three. The zero-trust pattern is a composite,
not a single feature. See SKILL.md "The four zero-trust legs in
Salesforce" for the canonical breakdown.
