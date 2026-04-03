# Gotchas: Permission Sets vs Profiles

---

## FLS Grants Are Additive — Permission Sets Can Give MORE Access Than the Profile

**What happens:** An admin sets a field to Read-Only on the user's profile, thinking that locks it down. The user has a Permission Set that grants Edit on the same field. The user gets Edit. The profile restriction is overridden.

**When it bites you:** Security audits. "We restricted that field on the profile" — yes, but the Permission Set won. You need to check the combined effective access, not just the profile.

**How to avoid it:**
- Use the "View Summary" / "Effective Access" check on a specific user to see their actual combined access
- When restricting access, remove the grant from ALL Permission Sets, not just the profile
- Don't rely on Profile FLS to cap access when Permission Sets are in play

**The rule:** Permission Sets only add. They cannot restrict below what the Profile grants. But a Profile can set Read, and a Perm Set can elevate to Edit. Read: if you need a hard ceiling on access, do not use a Profile to set it — use sharing rules and record visibility, not field-level security via profile alone.

---

## Login Hours and IP Restrictions Live on the Profile — Forever

**What happens:** An org moves users to a "Minimum Access" profile and Permission Set Groups. Six months later, the security team asks: "Why can users log in from any IP at any time? We had IP restrictions before." The IP restrictions were on the old profile. The new profile doesn't have them configured.

**When it bites you:** During profile migration. Old profiles often have login hour restrictions (e.g. "business hours only") and IP allowlists. These do not exist in Permission Sets — they cannot be migrated to PSGs.

**How to avoid it:**
- Before decommissioning a profile, explicitly check and document:
  - Login Hours: `Setup → Profiles → [Profile] → Login Hours`
  - Login IP Ranges: `Setup → Profiles → [Profile] → Login IP Ranges`
- Transfer these settings to the replacement base profile before migrating users

---

## Cloned Profiles Are Not Clean Slates

**What happens:** An admin clones "Standard User" to create a profile for a new team. Three years later, someone finds the profile has 47 custom object permissions, FLS grants on 200+ fields, and access to a deprecated AppExchange package. None of it was intentional — it all came from the original clone.

**When it bites you:** Every time. Cloned profiles inherit everything, including explicit denies, package grants, and legacy settings. People assume clones start "clean" because they haven't added anything — they haven't added anything, but they inherited everything.

**How to avoid it:**
- Audit any profile before using it as a migration base: use the Profile Comparison tool in Setup
- Better: start from the Minimum Access platform profile, not a cloned Standard User
- Document what was intentionally granted vs inherited

---

## The "Minimum Access" Base Profile Pattern

**Why it exists:** All users need a profile. The profile handles system-level settings (login hours, password policy, session settings). The goal is to put nothing else in the profile — no object access, no field access. All of that goes in Permission Sets.

**The pattern:**
1. Create a profile cloned from "Minimum Access — Salesforce" (a standard platform profile with almost nothing granted)
2. Set login hours, password policy, and session settings appropriate for your user population
3. Grant zero object access, zero FLS, zero custom permissions
4. Assign this profile to all internal users
5. All actual access comes from Permission Set Groups

**Gotcha:** Users with the Minimum Access profile cannot log in if they have no Permission Sets. Assign the base PSG before switching profiles. Don't leave users stranded.

---

## Permission Set Group Propagation Delay

**What happens:** An admin adds a Permission Set to a PSG and immediately gets a Slack message: "I still can't see the field." The admin checks, the assignment looks correct. The user isn't lying — the propagation just hasn't completed.

**When it bites you:** Any time you make PSG changes and immediately ask the user to verify.

**How to avoid it:**
- Allow up to 10 minutes for PSG changes to propagate
- If urgency requires faster access, assign the Permission Set directly to the user (not via PSG) as a temporary measure
- Add this to your change management runbook: "PSG changes take up to 10 minutes"
