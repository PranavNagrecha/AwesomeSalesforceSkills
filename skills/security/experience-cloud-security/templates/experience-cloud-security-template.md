# Experience Cloud Security — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `experience-cloud-security`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Site type:** [ ] Authenticated portal only  [ ] Guest access  [ ] Hybrid
- **Portal user license:** [ ] Customer Community  [ ] Customer Community Plus  [ ] Partner Community
- **Objects needing portal access:** (list objects and required access level — Read/Read-Write)
- **Guest user access required:** [ ] Yes  [ ] No

## Access Model Decision

| Object | Internal OWD | External OWD | Access Mechanism |
|---|---|---|---|
| (e.g., Case) | Private | Private | Sharing Set |
| (e.g., Knowledge) | Public Read Only | Public Read Only | OWD |

**Sharing Sets needed:** [ ] Yes  [ ] No
**Guest sharing rules needed:** [ ] Yes  [ ] No

## Security Header Configuration

- [ ] Clickjack protection: set to "Allow framing from same origin only"
- [ ] CSP: trusted sites explicitly listed
- [ ] Lightning Web Security (LWS): enabled

## Checklist

- [ ] External OWD is Private or more restrictive for all objects without explicit business requirement
- [ ] "Secure Guest User Record Access" is enabled
- [ ] Sharing Sets configured for each object authenticated portal users need access to
- [ ] Guest user profile has minimal object and field permissions
- [ ] Apex classes accessible to guest profile reviewed for `without sharing` usage
- [ ] CSP trusted sites and clickjack protection configured

## Notes

(Record any deviations from the standard pattern and why.)
