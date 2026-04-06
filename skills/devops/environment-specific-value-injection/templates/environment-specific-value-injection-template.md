# Environment-Specific Value Injection — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `environment-specific-value-injection`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Values to inject (list each):**
  - Value name:
  - Secret or non-sensitive?: (secret = password/token/key | non-sensitive = URL/flag/threshold)
  - Which environments differ?:
  - Current storage location (if any):

- **Deployment model in use:**
  - [ ] `sf project deploy start` (sfdx source deploy — string replacement applies)
  - [ ] Change set
  - [ ] 2GP unlocked/managed package (`sf package version create`)
  - [ ] OmniStudio DataPack
  - [ ] Other: _______________

- **CI/CD platform:** (GitHub Actions / Bitbucket Pipelines / GitLab CI / Azure DevOps / other)

- **API version in sfdx-project.json:** (check whether >= 57.0 for External Credential model)

## Mechanism Selection

For each value, select the mechanism using the Decision Guidance table in SKILL.md:

| Value | Classification | Mechanism | Rationale |
|---|---|---|---|
| (value name) | secret / non-sensitive | Named Cred stub + post-deploy / CMT record / sfdx replacement | (why) |

## Approach

Which patterns from SKILL.md are being applied and why:

- [ ] Pattern 1: Named Credential + sfdx string replacement for endpoint URL
- [ ] Pattern 2: Custom Metadata records for non-secret per-env config
- [ ] Pattern 3: External Credential + Named Credential for OAuth

## Implementation Checklist

- [ ] Named Credential XML stubs created with `${PLACEHOLDER}` tokens (no real URLs)
- [ ] `sfdx-project.json` `replacements` block has an entry for each placeholder
- [ ] CI platform has per-environment secret variables configured for each placeholder
- [ ] Custom Metadata records created in source control for non-secret config
- [ ] Post-deploy script scaffolded for credential population (if secrets involved)
- [ ] Post-deploy validation step added to CI job (smoke test callout)
- [ ] Pre-commit check or `.forceignore` added to prevent retrieved Named Credential XML commits
- [ ] Checker script run: `python3 scripts/check_environment_specific_value_injection.py --manifest-dir force-app`

## Post-Deploy Validation

Steps to confirm injection worked correctly after deploying to a new environment:

1. Confirm Named Credential appears in Setup > Named Credentials with correct endpoint URL
2. Run post-deploy credential population script (or verify manual Setup entry)
3. Execute smoke test script that calls each Named Credential endpoint and asserts non-4xx response
4. Confirm Custom Metadata records have expected values via Developer Console SOQL: `SELECT DeveloperName, FieldName__c FROM MyType__mdt`

## Notes

Record any deviations from the standard pattern and why:

- Deviation:
- Reason:
- Risk accepted:
