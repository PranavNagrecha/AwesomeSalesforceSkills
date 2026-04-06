# Email-to-Case Configuration — Work Template

Use this template when setting up or troubleshooting Email-to-Case for an org.

## Scope

**Skill:** `email-to-case-configuration`

**Request summary:** (fill in what the user asked for — e.g., "set up Email-to-Case for support@acme.com" or "customer replies are creating new cases instead of threading")

---

## Context Gathered

Answer these before proceeding:

- **Email-to-Case mode required:** On-Demand / Standard (circle one)
  - If Standard: reason (data residency / firewall policy / other): ___________________
- **Inbound support addresses to configure:**
  1. ___________________
  2. ___________________
  3. ___________________
- **Case defaults per address:**

  | Address | Case Origin | Status | Priority | Default Owner / Queue |
  |---|---|---|---|---|
  |  |  |  |  |  |
  |  |  |  |  |  |

- **Auto-response emails required?** Yes / No
  - If Yes: confirmed active case assignment rule exists? Yes / No
  - Auto-response From address (must NOT be a routing address): ___________________

- **Known constraints:**
  - High attachment volume? (On-Demand 10 MB per-attachment limit risk): ___________________
  - Email security gateway in use? (threading token stripping risk): ___________________

---

## Approach

Which pattern from SKILL.md applies?

- [ ] On-Demand Email-to-Case with verified threading (single address)
- [ ] Multiple routing addresses for channel-based classification
- [ ] Standard Email-to-Case with local agent (justify above)
- [ ] Troubleshooting existing configuration (describe symptom below)

**Symptom / scenario (if troubleshooting):** ___________________

---

## Configuration Steps

Track each step as you complete it:

- [ ] Email-to-Case enabled in Setup; mode selected and documented
- [ ] On-Demand Service option enabled (if applicable)
- [ ] Routing address(es) created with correct case defaults
- [ ] Salesforce-generated address(es) copied and recorded
- [ ] Mail server forwarding rule(s) configured and active
- [ ] Routing address(es) verified (Send Verification Email → click link → status = Verified)
- [ ] Active case assignment rule confirmed; entries match Email-to-Case cases
- [ ] Auto-response rule configured with non-routing From address (if applicable)
- [ ] Threading tested end-to-end through production mail gateway
- [ ] Checker script run; issues resolved

---

## Checklist (from SKILL.md)

- [ ] Email-to-Case feature enabled; mode documented and justified
- [ ] Each routing address has external email, Salesforce target address, and verified status
- [ ] Mail server forwarding active and tested: inbound email creates a case
- [ ] Threading tested end-to-end: reply adds Email Message to original case (not new case)
- [ ] Active assignment rule with entries matching Email-to-Case cases; catch-all to queue
- [ ] Auto-response rule (if used): valid template, From address is not the routing address
- [ ] Attachment limits communicated: 25 MB total, 10 MB per attachment (On-Demand)
- [ ] Checker script output reviewed

---

## Notes

Record any deviations from the standard pattern and the reason:

- ___________________
- ___________________

## Routing Address Record (fill in after configuration)

| Field | Value |
|---|---|
| Routing Name | |
| External Email Address | |
| Salesforce-Generated Address | |
| Verification Status | Verified / Unverified |
| Case Origin | |
| Case Status | |
| Case Priority | |
| Default Owner / Queue | |
| Auto-Response Rule Active | Yes / No |
