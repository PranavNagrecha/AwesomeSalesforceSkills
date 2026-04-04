# Network Security and Trusted IPs — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `network-security-and-trusted-ips`

**Request summary:** (fill in what the user asked for)

**Mode:** (circle one)
- Mode 1 — Configure from scratch
- Mode 2 — Audit existing config
- Mode 3 — Troubleshoot login-blocked or CSP violation

---

## Context Gathered

Answer these before taking any action:

- **My Domain deployed?** Yes / No — (Setup > My Domain — required for CSP Trusted Sites and Lightning)
- **Org type:** Production / Sandbox / Scratch Org
- **Is this a sandbox that was recently refreshed?** Yes / No — (if yes, IP ranges may be stale)
- **IPs to allow (for Mode 1):**
  - Office egress: `___.___.___.___ to ___.___.___.___.___`
  - VPN exit: `___.___.___.___ to ___.___.___.___.___`
  - Other: ___
- **Profile(s) requiring Login IP Ranges:**
  - Profile name: ___ — Ranges: ___
  - Profile name: ___ — Ranges: ___
- **External domains needing CSP Trusted Sites:**
  - Domain: ___ — Directives: script-src / connect-src / font-src / style-src / frame-src / img-src
  - Domain: ___ — Directives: ___
- **External app origins needing CORS:**
  - Origin: `https://___`
  - Origin: `https://___`
- **For Mode 3 (troubleshooting):**
  - Affected user(s): ___
  - Affected user's profile: ___
  - User's current IP (from whatismyip.com or LoginHistory): ___
  - CSP violation error text from browser console: ___

---

## Trusted IP Ranges (Org-Wide) — Current State

Setup > Security > Network Access

| Start IP | End IP | Description | Date Added | Still Valid? |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

---

## Login IP Ranges — Per Profile

| Profile | Start IP | End IP | Description | Date Added | Still Valid? |
|---|---|---|---|---|---|
| System Administrator | | | | | |
| | | | | | |
| | | | | | |

---

## CSP Trusted Sites — Current State

Setup > CSP Trusted Sites

| Site Name | Site URL | Directives | Date Added | Justification |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

## CORS Allowlist — Current State

Setup > CORS

| Origin URL Pattern | Date Added | Owner / Application | Still Active? |
|---|---|---|---|
| | | | |
| | | | |

---

## Approach

(Which mode from SKILL.md applies? Why?)

---

## Checklist

- [ ] Confirmed Trusted IP Ranges vs. Login IP Ranges distinction — used the correct control for the use case
- [ ] Login IP Ranges on privileged profiles tested from a known-good IP before saving
- [ ] CSP Trusted Sites entries use minimum required directives (not all directives)
- [ ] CORS entries use exact origin URLs; wildcards documented and justified
- [ ] My Domain is deployed
- [ ] Sandbox IP config documented separately — will be lost on full refresh
- [ ] LoginHistory queried for `Status = 'No Salesforce.com Access'` to confirm no unintended denials
- [ ] TLS 1.2+ confirmed for external systems referenced in CORS or CSP entries
- [ ] All changes logged in the tables above with description and date

---

## LoginHistory Troubleshooting Query

```soql
SELECT UserId, LoginTime, SourceIp, Status, LoginType
FROM LoginHistory
WHERE Status = 'No Salesforce.com Access'
  AND LoginTime >= LAST_N_DAYS:30
ORDER BY LoginTime DESC
LIMIT 500
```

---

## Notes

(Record any deviations from the standard pattern, decisions made, and the reason.)
