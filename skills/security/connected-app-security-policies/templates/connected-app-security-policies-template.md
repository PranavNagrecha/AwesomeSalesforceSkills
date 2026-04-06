# Connected App Security Policies — Work Template

Use this template when working on a Connected App security hardening task.

## Scope

**Skill:** `connected-app-security-policies`

**Request summary:** (fill in what the user asked for)

**Connected App name:** ___________________________________________

**OAuth flow type in use:** [ ] Web Server (Auth Code)  [ ] JWT Bearer  [ ] User-Agent  [ ] Device  [ ] Client Credentials

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md.

- **Current IP relaxation value:** [ ] enforceIpRanges  [ ] relaxIpRangesWithSecondFactor  [ ] relaxIpRanges  [ ] unknown
- **Integration source IPs (if applicable):** ___________________________________________
- **PKCE enabled?** [ ] Yes  [ ] No
- **Require Secret for Web Server Flow?** [ ] Yes  [ ] No
- **High Assurance state:** [ ] High Assurance  [ ] Switch to High Assurance  [ ] Blocked  [ ] Not configured
- **ECA model (API v65+)?** [ ] Yes  [ ] No  [ ] Unknown
- **JWT Bearer in use?** [ ] Yes  [ ] No — if yes, NTP sync verified: [ ] Yes  [ ] No

## Approach

Which pattern from SKILL.md applies? (check one)

- [ ] Hardening a server-to-server integration (enforce IP + no PKCE + Blocked high assurance)
- [ ] PKCE for a public client SPA or mobile app (PKCE + disable Require Secret)
- [ ] Migration to high assurance enforcement (Switch -> Blocked after migration window)
- [ ] Client secret rotation (ECA zero-grace-period coordinated swap)
- [ ] JWT Bearer invalid_grant troubleshooting (clock drift + TTL check)
- [ ] Other: ___________________________________________

## Policy Configuration

| Policy | Current Value | Target Value | Rationale |
|---|---|---|---|
| IP Relaxation | | | |
| PKCE | | | |
| Require Secret for Web Server Flow | | | |
| High Assurance Required | | | |
| OAuth Scopes | | | |

## Credential Rotation Plan (if applicable)

- [ ] All consumers identified and documented
- [ ] New secret staged and tested in sandbox
- [ ] Deployment window confirmed with stakeholders
- [ ] Rollback plan documented (old secret is immediately invalid — rollback = rotate again)
- [ ] Post-rotation verification test ready

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] IP Relaxation value is documented and justified for the flow type
- [ ] PKCE enabled and Require Secret disabled (if public client), or vice versa for confidential client
- [ ] High Assurance session policy set to Blocked for API-only apps, or documented exception recorded
- [ ] Client secret rotation procedure documented with zero-grace-period warning
- [ ] JWT Bearer signing host NTP sync verified if flow is in use
- [ ] OAuth scopes restricted to minimum required

## Notes

Record any deviations from the standard pattern and the reason for the deviation.
