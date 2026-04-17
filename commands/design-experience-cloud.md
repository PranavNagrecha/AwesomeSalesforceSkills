# /design-experience-cloud — Design or audit an Experience Cloud site admin setup

Wraps [`agents/experience-cloud-admin-designer/AGENT.md`](../agents/experience-cloud-admin-designer/AGENT.md). Produces template choice, audience model, member license + PSG composition, sharing set decisions, guest-user posture, CMS/branding plan, login flow, and moderation rules.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Mode? design | audit

2. Target org alias (required — agent probes Networks, Profiles, PS/PSGs, Sharing Sets)?

3. Scenario? customer-portal | partner-community | help-center | b2b-storefront | guest-microsite | other

4. Member license type(s)? (Customer Community, Customer Community Plus, Partner Community, External Identity, guest)

5. Authentication? (SSO | login+password | self-register | passwordless | SMS OTP | guest-only)

6. Sensitivity of exposed data? (public | authenticated-only | pii | phi | pci)
```

If scenario is vague or license type is unstated, STOP.

---

## Step 2 — Load the agent

Read `agents/experience-cloud-admin-designer/AGENT.md` + mandatory reads (admin/experience-cloud-setup, admin/sharing-sets, security/guest-user-hardening, integration/sso-patterns).

---

## Step 3 — Execute the plan

- Choose template per scenario.
- Design audience model (branches, overrides).
- Compose profile + PSGs per audience.
- Decide sharing-set vs criteria-based-sharing-set vs share group.
- Harden guest user access (min-permissions posture).
- Plan CMS + branding workflow.
- Design login flow + self-registration + SSO.
- Author moderation rules.

---

## Step 4 — Deliver the output

- Summary + confidence
- Template + audience model
- PS/PSG design per audience
- Sharing decisions
- Guest posture (explicit "denies access to X")
- CMS + branding plan
- Login flow
- Moderation rules
- Audit findings (audit mode)
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/scan-security` on Apex/LWC exposed to the site
- `/audit-sharing` before go-live
- `/architect-perms` if PSG composition needs redesign

---

## What this command does NOT do

- Does not deploy site metadata.
- Does not build LWCs for the site — use `/build-lwc`.
- Does not write page-builder pages — emits the policy surface.
