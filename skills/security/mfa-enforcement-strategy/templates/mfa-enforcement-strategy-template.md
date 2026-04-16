# MFA Enforcement Strategy — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `mfa-enforcement-strategy`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Setting / configuration:** SSO vendors, remaining Salesforce-password populations, Experience Cloud or external auth in scope
- **Known constraints:** Regions with device restrictions, regulated industries, blackout dates, IdP change freezes
- **Failure modes to watch for:** Integration outages, admin lockout, IdP saturation during registration waves, exemption sprawl

## Approach

Which pattern from SKILL.md applies (phased rollout, SSO-first, verification standardization), and why?

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] SSO and direct-login posture documented; no silent bypass for the populations in scope
- [ ] Verification methods standardized; help desk trained on recovery
- [ ] Integration and automation accounts reviewed; exemptions documented with owners and expiry
- [ ] Executive and legal/compliance stakeholders aligned on timelines and residual risk
- [ ] Post-cutover monitoring for login failures and IdP saturation

## Notes

Record any deviations from the standard pattern, org-specific constraints, or decisions made during implementation.
