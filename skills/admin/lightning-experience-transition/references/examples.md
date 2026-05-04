# Examples — Lightning Experience Transition

## Example 1: Multi-Wave Rollout For A 3,000-User Org With Heavy JS-Button Customization

**Context:** A financial-services org has 3,200 active Classic users across three business units (Banking Ops, Wealth Advisors, Service). The Readiness Check flags 87 JavaScript buttons, 41 Visualforce pages, and 6 installed packages — three of which are not LEX-ready. Leadership wants to be off Classic in two quarters.

**Problem:** Flipping the org-wide LEX setting before triaging assets would break the JavaScript-driven "Process Loan" button used 800+ times a day in Banking Ops. Users would switch back to Classic, and the program would lose credibility before Wave 1 finished.

**Solution:**

Wave plan derived from the Readiness Check:

| Wave | Cohort | Permission Set | In-Scope Triage | Go/No-Go Telemetry |
|---|---|---|---|---|
| 0 | IT + super-users (35) | `LEX_W0_Pilot` | None — pilot validates platform | Switch-back rate < 10%; no Sev-1 in 7 days |
| 1 | Service team (450) | `LEX_W1_Service` | 12 JS buttons → Quick Actions; Service Console rebuild | Switch-back rate < 5%; ticket volume +/-10% baseline |
| 2 | Wealth Advisors (1,100) | `LEX_W2_Wealth` | 38 JS buttons; 18 VF pages → LWCs; 2 package upgrades | Switch-back rate < 5%; advisor productivity (Opps/week) ≥ baseline |
| 3 | Banking Ops (1,650) | `LEX_W3_Banking` | "Process Loan" rebuild as flow + LWC; remaining 37 JS buttons; 1 package replacement | Switch-back rate < 3%; loan-processing throughput ≥ baseline |
| Cutover | All users | `LEX_HideClassic` | Org-wide toggle | LEX adoption > 95% sustained for 14 days |

Each wave's permission set assignment is gated on a deployment that ships the wave's replacements. Asset-level work uses `admin/custom-button-to-action-migration` for buttons and `lwc/visualforce-to-lwc-migration` for VF pages.

**Why it works:** Banking Ops is sequenced last because it has the highest JS-button density. Earlier waves build muscle (and replacement components — the Service Quick Actions inform Banking's design) before the highest-risk rollout. Switch-back rate per wave is the leading indicator and triggers a hold (not a rollback) if it spikes.

---

## Example 2: Resetting The User Switch-Back Preference Before Cutover

**Context:** An org ran a profile-level "remove Classic UI access" flip a year ago, but a subsequent audit found 240 users still landing in Classic at login — they had clicked "Switch to Salesforce Classic" before the flip and the per-user preference (`UserPreferencesLightningExperiencePreferred = false`) survived.

**Problem:** A profile-level rollout does **not** reset the per-user preference. Once a user has set the preference, profile changes do not override it. The "LEX adoption" dashboard reported 100% rollout but 240 users were still working in Classic, with no way to know without sampling `LoginHistory`.

**Solution:**

Build a one-time User-record DML to reset the preference for affected users:

```sql
-- Identify users still on Classic
SELECT Id, Username, ProfileId
FROM User
WHERE IsActive = true
  AND UserPreferencesLightningExperiencePreferred = false
```

Use the **Lightning Experience Hides Classic Switcher** permission set as the durable fix. Assigning it both removes the switcher from the user menu (so the preference cannot be re-set) and forces the user into LEX on next login regardless of preference.

```bash
# After the permission-set deployment, verify on next-day login
sf data query --query "SELECT Id FROM User WHERE UserPreferencesLightningExperiencePreferred = false AND IsActive = true" --target-org prod
```

**Why it works:** The permission set is the platform-supported way to override user preference. Once it's assigned to the cohort, the switch-back trap is closed without requiring DML on the User object (which can hit governance friction in regulated orgs).

---

## Anti-Pattern: Migrating Visualforce Pages "Just In Case"

**What practitioners do:** When the Readiness Check flags 60 Visualforce pages, the team scopes a 6-month workstream to convert all of them to LWC.

**What goes wrong:** 30 of those VF pages have not been viewed in the last 12 months — they are dead assets surfaced because they exist, not because they are used. Six months are spent rebuilding pages that no user will visit. Real-blocker pages (the 8 VF pages on related lists viewed daily) get the same priority as the dead ones and ship later than they should.

**Correct approach:** Cross-reference the Readiness Check inventory with usage data — `EventLogFile` `URI` events for the last 12 months, or audit log VF page hits — before scoping the migration. Triage every VF page into Replace, Rebuild, Retain, or Retire **before** assigning resources. Most legacy orgs will retire 30–50% of flagged Visualforce assets without the user noticing.
