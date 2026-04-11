# Health Cloud APIs — Work Template

Use this template when building or debugging Health Cloud API integrations.

## Scope

**Skill:** `health-cloud-apis`

**Request summary:** (fill in what the user asked for)

## API Layer Selection

| Operation | Standard SObject API | FHIR Healthcare API |
|-----------|---------------------|---------------------|
| SOQL queries on clinical objects | Yes | No |
| FHIR-conformant reads for external FHIR clients | No | Yes |
| Bulk data loads | Yes (Bulk API) | No (30-entry limit) |
| FHIR $everything operations | No | Yes |
| Internal analytics queries | Yes | No |

**Selected API layer for this integration:** _______________

## Authentication Checklist

- [ ] Connected App OAuth scopes include `api`
- [ ] Connected App OAuth scopes include `healthcare` (if FHIR Healthcare API is used)
- [ ] HealthCloudICM permission set assigned to integration user
- [ ] FHIR R4 Support Settings enabled in Setup (if FHIR Healthcare API is used)

## FHIR Bundle Configuration (if applicable)

- Maximum entries per bundle: 30
- Maximum read/search operations per bundle: 10
- Bundle chunking implemented: [ ] Yes [ ] No
- HTTP 424 dependency error handling implemented: [ ] Yes [ ] No

## Error Handling Pattern

For FHIR bundles:
1. Scan all bundle entries for HTTP 424 status
2. Trace each 424 to its referenced bundle entry
3. Find root non-424 failure
4. Fix root cause
5. Retry full bundle

## Notes

(API version used, specific FHIR resources in scope, bundle transaction type, error handling decisions)
