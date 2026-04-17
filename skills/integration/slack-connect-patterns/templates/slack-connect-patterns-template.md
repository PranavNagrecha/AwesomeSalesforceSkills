# Slack Connect Channel Governance Template

Use this template to document and govern a Slack Connect channel relationship between two organizations. Complete all sections before the channel is externally shared. File in your organization's governance register.

---

## 1. Channel Identity

| Field | Value |
|---|---|
| Channel name | `ext-[partnerco]-[purpose]` (replace with actual name) |
| Channel purpose | |
| Date created | YYYY-MM-DD |
| Slack workspace (inviting org) | |
| Slack workspace (receiving org) | |
| Invite link generated date | YYYY-MM-DD |
| Invite link expiry date | YYYY-MM-DD (14 days after generated) |
| Connection accepted date | YYYY-MM-DD |
| Review cadence | Quarterly |

---

## 2. Plan Tier Check

Both organizations must be on a paid Slack plan to use Slack Connect.

| Organization | Slack Plan | Plan Confirmed By | Confirmation Date |
|---|---|---|---|
| Inviting org | [ ] Free  [ ] Pro  [ ] Business+  [ ] Enterprise Grid  [ ] Enterprise+ | | |
| Receiving org | [ ] Free  [ ] Pro  [ ] Business+  [ ] Enterprise Grid  [ ] Enterprise+ | | |

**Eligibility result:**
- [ ] Both organizations are on paid plans — Slack Connect eligible.
- [ ] One or both organizations are on a Free plan — Slack Connect NOT eligible. See alternatives below.

**If not eligible — alternatives:**
- Ask the partner to upgrade to a paid Slack plan.
- Add the partner as a Single-Channel Guest (consumes your seat count, different model).
- Use an alternative collaboration tool (email, Microsoft Teams Shared Channel, etc.).

---

## 3. DLP Approach Decision

Each organization is responsible for configuring DLP controls covering its own members' messages. DLP rules are workspace-scoped and do not apply to the partner organization's messages.

### Inviting Organization DLP

| Item | Detail |
|---|---|
| Plan tier | |
| Native Slack DLP available? | [ ] Yes (Enterprise Grid / Enterprise+)  [ ] No (Pro / Business+) |
| DLP tool selected | Native Slack DLP / Nightfall AI / Symantec DLP / Microsoft Purview / Other: _______ |
| DLP configured by | |
| DLP configuration date | YYYY-MM-DD |
| DLP rule set documented at | (link to internal policy doc) |

### Receiving Organization DLP

| Item | Detail |
|---|---|
| Plan tier | |
| Native Slack DLP available? | [ ] Yes (Enterprise Grid / Enterprise+)  [ ] No (Pro / Business+) |
| DLP tool selected | Native Slack DLP / Nightfall AI / Symantec DLP / Microsoft Purview / Other: _______ |
| DLP confirmed by (partner contact) | |
| DLP confirmation date | YYYY-MM-DD |

**DLP coverage acknowledgment:**
- [ ] Both organizations have independently confirmed DLP is configured and active before the channel is externally shared.
- [ ] Both organizations acknowledge that each org's DLP applies only to its own members' messages.
- [ ] For regulated environments: contractual clause requiring partner notification of DLP changes is in place.

---

## 4. Connection Setup Checklist

Complete each step in order before the first external message is sent.

- [ ] Confirmed both organizations are on paid Slack plans.
- [ ] Created a NEW, empty channel (not converted from an existing channel).
- [ ] Confirmed channel contains no prior internal message history.
- [ ] Channel name follows `ext-[partnerco]-[purpose]` convention.
- [ ] Channel description notes it is externally shared and identifies the partner organization.
- [ ] DLP configured on inviting org side and confirmed active.
- [ ] DLP configuration confirmed with receiving org.
- [ ] Governance register entry created (this document).
- [ ] Legal/compliance acknowledgment of split-ownership retention model obtained.
- [ ] Invite link generated and sent directly to receiving org's Slack admin email.
- [ ] Invite acceptance confirmed by receiving org's Slack admin.
- [ ] Initial channel members added (limited to appropriate personnel).
- [ ] Quarterly review calendar entry created.

---

## 5. Retention Register

Document the retention policies for both organizations and acknowledge the split-ownership model.

| Item | Inviting Org | Receiving Org |
|---|---|---|
| Retention policy duration | | |
| Retention policy set by | | |
| Applicable regulatory minimum (if any) | | |
| Policy effective date | | |

**Data sovereignty acknowledgment (required):**

By completing this section, the undersigned acknowledges:

1. Each organization independently retains its own members' messages in this Slack Connect channel under its own retention policy.
2. Message deletion by one organization — whether manual, by admin action, or by automated retention policy — does NOT propagate to the partner organization. The partner retains its copy under its own policy.
3. This split-ownership model is by Slack platform design and cannot be overridden by configuration.
4. Short retention policies cannot be relied upon as bilateral data minimization controls in Slack Connect channels.

| Role | Name | Date |
|---|---|---|
| Compliance / Legal sign-off (inviting org) | | YYYY-MM-DD |
| IT / Security sign-off (inviting org) | | YYYY-MM-DD |

---

## 6. eDiscovery and Legal Hold Procedure

Document the procedure for producing a complete channel record for legal or regulatory purposes.

**Responsible parties:**

| Organization | eDiscovery Contact | Slack Admin Contact |
|---|---|---|
| Inviting org | | |
| Receiving org | | |

**Export procedure:**

1. **Inviting org export:** Inviting org's Slack admin produces a Compliance Export (Enterprise Grid) or manual export for the channel from their workspace. Export format: JSON (preferred for timestamp merging) or CSV.
2. **Receiving org export:** Receiving org's Slack admin produces a parallel export from their workspace covering the same date range.
3. **Merge:** Exports are merged by timestamp field (`ts` in JSON exports — Unix epoch with microsecond precision) to produce a unified chronological record.
4. **Delivery:** Merged record is delivered to legal/outside counsel with a cover note explaining the dual-export requirement.

**Outside counsel briefing note (include with every production):**
> This channel is a Slack Connect channel shared between two independent Slack workspaces. A single-organization export covers only that organization's members' messages. This production represents [Inviting Org]'s portion of the channel record. A complete conversation record requires a parallel export from [Receiving Org], produced independently, merged by message timestamp.

**Legal hold coordination:**
- [ ] In the event of a litigation hold, both organizations are notified simultaneously.
- [ ] Receiving org has acknowledged its obligation to preserve its copy of channel messages.
- [ ] Receiving org's legal hold contact: ________________________

---

## 7. Quarterly Review Log

| Review Date | Reviewer | Inviting Org Plan Tier Confirmed | Receiving Org Plan Tier Confirmed | DLP Status | Notes |
|---|---|---|---|---|---|
| YYYY-MM-DD | | | | | |
| YYYY-MM-DD | | | | | |
| YYYY-MM-DD | | | | | |

**Review checklist (complete each quarter):**
- [ ] Confirmed inviting org remains on paid Slack plan.
- [ ] Confirmed receiving org remains on paid Slack plan (request written confirmation from partner).
- [ ] Confirmed DLP is active on both sides — follow up with partner to confirm their DLP status.
- [ ] Confirmed retention policies on both sides still match contractual commitments.
- [ ] Reviewed current external organization count in channel (limit: 250).
- [ ] Updated governance register with review date and outcome.

---

## 8. Scope Limitations

This template covers Slack Connect channel governance only.

**This template does NOT cover:**
- Salesforce-to-Salesforce data integration (use Salesforce-to-Salesforce feature, Outbound Messages, or MuleSoft)
- Salesforce for Slack app setup (internal Salesforce record previews in Slack)
- Microsoft Teams Shared Channel governance
- Single-workspace internal Slack channel governance
