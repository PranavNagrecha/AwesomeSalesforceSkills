# Examples — Security Incident Response

## Example 1: Compromised Service Account via Leaked API Credentials

**Scenario:** Production org, Event Monitoring add-on licensed (no Shield).

**Context:** A developer accidentally committed Salesforce Connected App OAuth client credentials to a public GitHub repository. The credentials were live for approximately 72 hours before the developer noticed. The Connected App was configured for server-to-server integration with the `client_credentials` OAuth flow and had a profile granting View All Data on Account and Contact objects.

**Problem:** By the time the team was alerted, 72 hours had passed. The immediate instinct was to revoke the Connected App's credentials and consider the incident closed. However, the full blast radius — which records were accessed, whether any data was exported or exfiltrated, and whether any configuration changes were made — was completely unknown. The team also did not know whether the attacker had escalated access or installed persistence mechanisms.

**Solution:**

1. **Evidence preservation first.** The team queried `EventLogFile` for the 30-day window and downloaded all `ApiTotalUsage`, `ReportExport`, and `DataExport` event CSVs for the attack window. Because the org had the Event Monitoring add-on, 30-day retention was available — the logs had not expired despite the 72-hour delay.

2. **Blast radius assessment.** Parsing the `ApiTotalUsage` EventLogFile CSVs revealed that the service account had executed 4,200 SOQL queries against Account and Contact objects over the 3-day window, with a pronounced spike during business hours in a timezone inconsistent with the org's known integration patterns. No `DataExport` events were present, but the volume of API calls indicated systematic data access consistent with bulk extraction via paginated SOQL.

3. **Containment.** The Connected App was disabled (Setup > Connected Apps > Edit > IP Relaxation > Enforce IP Restrictions and disable). All active `AuthSession` records for the associated integration user were deleted via REST: `DELETE /services/data/v60.0/sobjects/AuthSession/{Id}`. OAuth tokens were revoked via Setup > Connected Apps > OAuth Usage. A Transaction Security Policy was activated with a Notification action on `ApiTotalUsage` events exceeding 500 queries per hour for any single user.

4. **Eradication.** The client secret was rotated. The Connected App's profile was tightened from View All Data to a custom permission set scoped to only the specific objects required for the integration. IP allowlisting was enabled on the Connected App.

5. **Recovery.** A post-incident review confirmed no Apex, Flow, or permission set changes had been made during the window (SetupAuditTrail showed no entries for the integration user). The incident was scoped to data access only.

**Why this worked:** Starting with evidence preservation before containment was critical. Revoking the Connected App first would have cleared the OAuth token records without preserving the ApiTotalUsage logs needed to establish blast radius. The 30-day retention from the Event Monitoring add-on made evidence recovery possible despite the 72-hour detection delay.

---

## Example 2: Credential Stuffing Attack with Session Hijack

**Scenario:** Enterprise org, Salesforce Shield licensed.

**Context:** An org admin received an automated LoginAnomaly alert from a Transaction Security Policy configured with Notification action and Score > 0.7 threshold. The alert identified a sales user logging in from an IP in Eastern Europe — the user had no travel history or remote work arrangement, and the org's users were exclusively US-based. The alert fired at 2:17 AM local time.

**Problem:** The admin needed to determine whether the login was successful, what the attacker accessed during any active session, whether the user's credentials were still valid, and whether the attacker had made any configuration changes or installed persistence.

**Solution:**

1. **Assess the LoginAnomaly event.** The admin queried `LoginGeoEventStream` and `LoginAnomalyEventStore` to retrieve the full event details: Score = 0.92, SourceIp matched a known TOR exit node, Country = "RO", the login was successful, and the login type was `Application` (UI session), not API.

2. **Preserve evidence.** LoginHistory was exported for the user covering the prior 30 days to establish the user's normal login pattern (all US, all business hours, consistent browser fingerprint). EventLogFile for `Report`, `URI`, and `LightningPageView` event types was downloaded for the attack window to identify what pages and reports were accessed.

3. **Containment.** The active `AuthSession` record for the Eastern Europe session was immediately deleted via REST API (identified by matching `SourceIp` and `LoginTime`). The user's password was reset via Setup > Users > Reset Password. All remaining AuthSession records for the user were deleted. The user was contacted via phone to confirm account compromise and verify the password reset was legitimate.

4. **Blast radius.** EventLogFile `URI` events showed the attacker navigated to Opportunity list views and ran two standard reports (identified by ReportId) within a 22-minute window before the session was terminated. No `DataExport` events. No `ReportExport` events. SetupAuditTrail showed no config changes.

5. **Eradication.** MFA was enforced for the user's profile (which had previously used a security token rather than Salesforce Authenticator). An IP allowlist was added to the user's profile for the user's known IP ranges. The Transaction Security Policy threshold for LoginAnomaly was reviewed and retained.

6. **Post-incident.** The two reports accessed were identified and reviewed for sensitivity. Both were standard pipeline reports with no PII beyond name and deal value. The incident was classified as a minor access breach with no data exfiltration evidence.

**Why this worked:** The pre-configured LoginAnomaly Transaction Security Policy with Notification action meant the admin was alerted within minutes of the suspicious login. Without the policy, the login would have succeeded silently and the attacker would have had an unrestricted session. Shield's 30-day EventLogFile retention and Real-Time Event Monitoring combined to provide both immediate alerting and complete forensic reconstruction.
