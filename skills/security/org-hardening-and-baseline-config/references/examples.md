# Examples: Org Hardening And Baseline Config

## Example 1: New Org Baseline Before App Growth

**Context:** A new business unit is launching on a fresh Salesforce org.

**Problem:** Teams want to defer security settings until after the first release.

**Solution:** Deploy the baseline `Security.settings-meta.xml` from [metadata-examples.md](metadata-examples.md) in the first sprint, then run Health Check against the Salesforce Baseline Standard and record the settings that Fix Risks can't change.

```bash
sf project retrieve start --metadata "Settings:Security" ProfileSessionSetting ProfilePasswordPolicy --target-org newbu-uat
python3 skills/security/org-hardening-and-baseline-config/scripts/check_org_hardening_and_baseline_config.py --manifest-dir force-app
sf project deploy start --metadata "Settings:Security" --target-org newbu-uat --wait 30
```

**Why it works:** The org grows from a known, versioned baseline instead of accumulating exceptions first. Profile-level overrides are visible from day one.

---

## Example 2: Exception Register for Trusted Sites

**Context:** The org has accumulated many CSP Trusted Sites and CORS allowlist entries.

**Problem:** Nobody can explain which ones are still needed, and the CSP header is growing toward the 12 KB size where customers report problems.

**Solution:** Build an exception register, put the short form in each entry's `description`, and remove what has no owner.

| Entry | Type | Directives / pattern | Owner | Purpose | Review date | Action |
|---|---|---|---|---|---|---|
| `Maps_Vendor_Tiles` | CspTrustedSite | ImgSrc only, context LEX | Field Ops | Route Planner LWC tiles | 2027-01-15 | Keep |
| `Old_Chat_Widget` | CspTrustedSite | all directives, context All | none | retired vendor | n/a | Remove |
| `Partner_Portal` | CorsWhitelistOrigin | `https://portal.partner.example.com` | Partner IT | portal calls REST API | 2027-03-01 | Keep |
| `Wildcard_Example` | CorsWhitelistOrigin | `https://*.example.com` | none | unknown | n/a | Narrow or remove |

**Why it works:** Convenience exceptions become governed risk decisions instead of hidden configuration drift.

---

## Example 3: Restricting Admin Logins to the Office

**Context:** Security asks that System Administrator logins come only from the corporate network.

**Problem:** The first proposal adds the office range to Network Access (trusted IP ranges), which only skips device activation.

**Solution:** Add Login IP Ranges to the admin profile, enable `enforceIpRangesEveryRequest` in Session Settings, and keep a documented break-glass account on a separate profile.

**Why it works:** Profile Login IP Ranges deny login from other addresses, and the every-request setting extends that to existing sessions and client apps.

---

## Anti-Pattern: Health Check Score as the Only Signal

**What practitioners do:** They point to the score and assume hardening is complete.

**What goes wrong:** Profile-level overrides, trust exceptions, and pending release updates stay untreated.

**Correct approach:** Use Health Check as one input to the quarterly review, alongside the checker output and the exception register.
