# LLM Anti-Patterns — Security Incident Response

Common mistakes AI assistants make when advising on Salesforce security incident response. Each pattern describes the mistake, why it is wrong, and what the correct guidance is.

---

## Anti-Pattern 1: Treating Password Reset as Complete Containment

**The mistake:** Advising the user to "reset the compromised user's password to cut off attacker access" as the primary or only containment action.

**Why it is wrong:** Password reset only prevents new logins using the old password. It has no effect on:
- Active browser sessions (`AuthSession` records remain valid even after password reset)
- OAuth refresh tokens issued to Connected Apps (these are long-lived tokens independent of the user's password)
- Sessions that were established using OAuth flows (which do not use the user's password at all)

An attacker who established a session via OAuth or who has an open browser session retains full access after a password reset.

**Correct guidance:** Password reset is one step in a multi-step containment sequence. The complete sequence is: (1) freeze the user account to block new logins, (2) delete all active `AuthSession` records via REST API or Setup > Session Management, (3) revoke OAuth tokens via Setup > Connected Apps > OAuth Usage, (4) then reset the password. All four steps are required.

---

## Anti-Pattern 2: Claiming 30-Day Event Log Retention Without Confirming Shield or Event Monitoring Add-On

**The mistake:** Telling users they can "query EventLogFile for the past 30 days to investigate what the attacker accessed" without first confirming the org has the Event Monitoring add-on or Shield.

**Why it is wrong:** In Salesforce orgs without the Event Monitoring add-on, most EventLogFile event types have **1-day retention only** — the log file for a given day is available for approximately 24 hours after midnight UTC. Only 5 event types are available on the free tier. For an incident discovered 48 hours after the attack, the EventLogFile records will have already been permanently deleted with no recovery option.

**Correct guidance:** Always begin by confirming the org's Event Monitoring tier:
```soql
SELECT EventType, LogDate, LogFileLength FROM EventLogFile
WHERE LogDate >= LAST_N_DAYS:7 ORDER BY LogDate DESC
```
If only a few event types appear with only today's or yesterday's logs, the org is on free tier. Inform the user immediately that EventLogFile forensics may be limited or unavailable, and pivot to LoginHistory (free, 6-month retention) and SetupAuditTrail (free, 180-day retention) as the primary evidence sources.

---

## Anti-Pattern 3: Treating LoginHistory as Equivalent to Event Monitoring for Forensics

**The mistake:** Using LoginHistory records as a proxy for full forensic evidence — concluding that "login from an unusual IP" is the complete picture of attacker activity, or that if no suspicious logins appear in LoginHistory, there was no attacker access.

**Why it is wrong:** LoginHistory records only login events — it shows that a user authenticated, from which IP, and with which method. It does not show:
- What SOQL queries were executed (ApiTotalUsage EventLogFile)
- What reports were run or exported (Report, ReportExport EventLogFile)
- What data was exported (DataExport EventLogFile)
- What Metadata API operations were performed (MetadataApiOperation EventLogFile)
- What UI pages were navigated (URI, LightningPageView EventLogFile)

An attacker who authenticated legitimately with stolen credentials will appear in LoginHistory as a normal login. The attacker's data access activities only appear in EventLogFile event types that require the Event Monitoring add-on.

**Correct guidance:** LoginHistory is a starting point for establishing the attack timeline (when did the attacker log in, from where, how). It is not a substitute for EventLogFile analysis. Blast radius assessment requires EventLogFile. Explicitly state which evidence sources were available and what the coverage gaps are.

---

## Anti-Pattern 4: Starting Containment Before Preserving Evidence

**The mistake:** Advising the user to immediately freeze the user account, delete sessions, and revoke tokens as the first response action — before downloading forensic evidence.

**Why it is wrong:** In free-tier orgs with 1-day EventLogFile retention, containment actions can themselves trigger the destruction of forensic evidence. More broadly, deleting AuthSession records and revoking OAuth tokens removes indicators of compromise that are part of the forensic record. The blast radius cannot be assessed after the evidence is gone.

In orgs where the incident window is close to the EventLogFile retention boundary (e.g., a free-tier org where the incident was 18 hours ago), beginning containment first and then attempting forensics may result in the logs expiring during the containment sequence.

**Correct guidance:** The canonical IR sequence for Salesforce is: **Preserve → Contain → Eradicate → Recover → Verify**. Evidence preservation is always the first phase. Download all EventLogFile CSVs for the attack window, export LoginHistory, export SetupAuditTrail, and snapshot AuthSession records before taking any containment action.

---

## Anti-Pattern 5: Assuming Org-Wide "Read-Only Mode" or "Freeze" Is a Self-Service Option

**The mistake:** Recommending that the user "put the org in read-only mode" or "freeze the org" to halt attacker activity while the investigation proceeds.

**Why it is wrong:** Salesforce does not provide a self-service "read-only mode" or org-wide freeze capability for production orgs. Salesforce Sandbox orgs can be refreshed, but production orgs cannot be put into read-only mode by the org admin. There is no Setup option, Apex API, or Admin UI that enables a complete org freeze.

The closest available options are: (1) freeze individual user accounts (Setup > Users > Freeze — blocks that user's new logins, but not sessions or tokens), (2) activate System Maintenance mode on specific Community/Experience Cloud sites (not the core org), or (3) contact Salesforce Support for emergency org-level interventions in extreme cases (e.g., ransomware or mass data destruction).

**Correct guidance:** Containment must be executed user-by-user and access-path-by-access-path. Freeze all identified compromised users, revoke their sessions and tokens, disable or restrict any Connected Apps used in the attack, and activate Transaction Security Policies to block ongoing attack vectors. There is no single "freeze org" lever available to admins.

---

## Anti-Pattern 6: Ignoring Connected App OAuth Token Revocation

**The mistake:** Completing the IR workflow without checking for and revoking OAuth tokens issued to Connected Apps used by the attacker.

**Why it is wrong:** OAuth refresh tokens are long-lived (default: no expiry unless configured) and completely independent of the user's password and session. An attacker who obtained a refresh token via a compromised Connected App retains the ability to request new access tokens and continue accessing the org even after the user's password is reset, the user is frozen, and all browser sessions are deleted.

**Correct guidance:** After deleting AuthSession records, always query `AuthToken` for the compromised user(s) and DELETE any tokens associated with suspicious Connected Apps. Review Setup > Connected Apps > OAuth Usage to identify all Connected Apps that have issued tokens to the affected users. Consider temporarily disabling the Connected App if the specific app used in the attack cannot be immediately identified.

---

## Anti-Pattern 7: Advising Manual LoginAnomaly Queries as a Replacement for Shield

**The mistake:** Suggesting the user "query the LoginAnomaly object" to detect suspicious logins when the org does not have Salesforce Shield.

**Why it is wrong:** `LoginAnomaly` is a Real-Time Event Monitoring (RTEM) object that is only available with Salesforce Shield. Without Shield, the object either does not exist or returns no records. Attempting to query it in a non-Shield org returns an error or empty results, not a graceful indication that the feature is unavailable.

**Correct guidance:** Confirm Shield availability before referencing LoginAnomaly. Without Shield, anomalous login detection requires manual analysis of LoginHistory — specifically looking for unusual source IPs, unusual countries, logins outside normal business hours, new browser/platform fingerprints, and impossible travel (two successful logins from different countries within a timeframe that precludes physical travel). This manual analysis is more time-consuming but is the only forensic option in non-Shield orgs.
