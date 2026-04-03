# OmniStudio Security — Gotchas

## 1. OmniStudio Outputs Are Still Data Exposure Surfaces

Because they are configured declaratively, teams sometimes under-review what they return.

Avoid it:
- Review response contracts like any other application API.
- Return only what the caller needs.

## 2. Apex Behind OmniStudio Keeps Its Own Security Risk

The OmniStudio layer does not compensate for weak `@AuraEnabled` or invocable Apex.

Avoid it:
- Check sharing and CRUD/FLS enforcement explicitly.
- Treat custom Apex as a first-class security boundary.

## 3. Guest-User Scope Should Be Smaller Than Internal Scope

Reusing internal assets externally is the fastest way to overexpose data.

Avoid it:
- Build narrow guest or portal variants.
- Remove unnecessary fields and actions from the external path.

## 4. External Callouts Need Contract Review Too

Authentication is only one part of the security story.

Avoid it:
- Review which Salesforce data leaves the org.
- Keep HTTP responses and failure messages business-safe.
