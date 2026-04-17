# Examples — Slack Connect Patterns

Real-world implementation scenarios grounded in documented Slack platform behavior.

---

## Example 1: Cross-Org Partner Channel Setup (General Enterprise)

**Scenario:** A mid-size technology company (Organization A, Business+ plan) is starting a joint product development engagement with a consulting partner (Organization B, Enterprise Grid plan). Both organizations use Slack. The project team wants a shared channel for day-to-day communication, file sharing, and milestone coordination.

**Step-by-step setup:**

1. **Plan tier check:** Organization A is on Business+; Organization B is on Enterprise Grid. Both are paid plans. Connection eligibility is confirmed.

2. **DLP gap assessment:** Organization B (Enterprise Grid) can use native Slack DLP via Admin Console > Policies > Data Loss Prevention. Organization A (Business+) does not have access to native Slack DLP — they must configure a third-party DLP integration (Nightfall AI is selected). Nightfall is installed as a bot in Organization A's workspace and subscribed to the Slack Events API before the channel is externally shared.

3. **New channel creation:** Organization A's Slack admin creates a new empty channel named `ext-partnerco-integration-2026`. The admin does not convert any existing internal channel.

4. **Governance register entry created:** Organization A's IT governance team documents: Organization A retention policy (3 years), Organization B retention policy (unknown — must be confirmed), asymmetric deletion acknowledgment, DLP coverage split (Nightfall on A-side, native Slack DLP on B-side), and eDiscovery export procedure.

5. **Invite generation:** Organization A's Slack admin navigates to the channel settings, selects "Share outside [workspace]", and generates a Slack Connect invite link. The link is emailed directly to Organization B's designated Slack admin (not a project manager).

6. **Invite acceptance:** Organization B's Slack admin receives the invite, reviews it in their Slack Admin Console, and accepts the connection. The shared channel becomes visible to members of both workspaces.

7. **Confirmation and kickoff:** Organization A's admin confirms acceptance and notes the date in the governance register. Both organizations' project leads are added to the channel. The channel's description is updated to note "External Slack Connect channel — shared with [PartnerCo]. Do not post confidential IP without legal review."

**Key governance outputs:**
- Governance register entry confirming plan tiers for both organizations
- Nightfall AI DLP active on Organization A's workspace
- Documented asymmetric deletion and eDiscovery acknowledgment signed off by Organization A's legal team
- Channel naming convention following `ext-[partnerco]-[project]` standard

---

## Example 2: Regulated Industry (Financial Services) — Slack Connect with DLP and Retention Compliance

**Scenario:** A registered investment advisor (Organization A, Enterprise Grid) needs to communicate with an independent custodian firm (Organization B, Enterprise Grid) about client account operational issues. Both organizations are subject to FINRA Rule 4511 (books and records, 3-year minimum retention, 6 years for certain records) and SEC Rule 17a-4 (immutability requirements for electronic records). Legal and compliance have approved the use of Slack Connect for operational communications only — no client PII, no investment advice, no trade instructions in the channel.

**Compliance setup:**

1. **Plan tier confirmation:** Both organizations confirm Enterprise Grid status in writing. Both Slack admins share their Slack plan confirmation page screenshots with their respective compliance teams.

2. **Native DLP configuration (both sides):** Organization A's Slack admin navigates to Admin Console > Policies > Data Loss Prevention and creates PCRE rules to detect: Social Security Numbers (`\b\d{3}-\d{2}-\d{4}\b`), account numbers (custom pattern), and common PII indicators. Organization B configures an equivalent rule set independently. Each organization's DLP rules apply only to its own members' messages. Both compliance teams acknowledge in writing that DLP coverage is bilateral but independently operated.

3. **Retention policy configuration:** Organization A sets a retention policy of 7 years (exceeding FINRA minimums) for the shared channel's messages in Organization A's workspace. Organization B is contractually required to apply a matching 7-year retention policy. Both organizations acknowledge that retention applies independently and that deletion by one party does not affect the other's copy. This asymmetry is documented as a feature for compliance purposes (each organization holds its own complete record).

4. **eDiscovery procedure documented:** Both organizations establish an eDiscovery runbook: in the event of a regulatory examination or litigation hold, both organizations independently export the Slack Connect channel using Slack's native Compliance Export (Enterprise Grid feature). Exports are produced in JSON format, merged by `ts` field (Unix timestamp), and delivered as a unified record. Outside counsel is briefed that the merged export is required for a complete conversation record.

5. **EKM consideration:** Organization A uses Slack EKM (Enterprise Key Management) to retain encryption key control over its workspace data. Organization B also has EKM enabled. Each organization's EKM applies only to its own portion of the channel data — neither organization can decrypt the other's messages. This is documented as acceptable because each organization has full custody of its own records.

6. **Channel created and restricted:** A new channel `ext-custodian-ops` is created by Organization A. Channel topic is set to: "Operational communications only. No client PII, no investment advice, no trade instructions. Slack Connect with [Custodian Firm Name]." Membership is limited to operations staff — no advisors or client-facing staff added.

7. **Quarterly compliance review calendar entry:** Compliance officer at Organization A adds a recurring calendar event: quarterly review of partner plan tier, DLP rule currency, and retention policy confirmation. Review dates and outcomes are logged in the compliance register.

**Key compliance outputs:**
- Written confirmation of Enterprise Grid plan status from both organizations
- DLP rule documentation for both organizations with effective dates
- Retention policy register entry with acknowledgment of asymmetric deletion behavior
- eDiscovery runbook covering parallel export and merge procedure
- EKM status documented for both organizations
- Channel membership restriction documented and enforced
