# Lead Conversion Customization — Work Template

Use this template when working on tasks that require Apex to control, extend, or react to lead conversion.

## Scope

**Skill:** `lead-conversion-customization`

**Request summary:** (describe what the user asked for — e.g., "convert leads from a Flow and map custom fields")

## Context Gathered

Answer these before writing any code:

- **Converted LeadStatus API name:** (query `LeadStatus WHERE IsConverted = true` — do not guess)
- **Custom fields to transfer:** (list each field, its source object Lead, and its target Contact/Account/Opportunity)
- **Opportunity creation:** suppress (`setDoNotCreateOpportunity(true)`) or allow?
- **Merge into existing Account/Contact:** yes/no — if yes, what is the source of the target Id?
- **Trigger framework in use:** (check for existing Lead trigger — do not create a second one)
- **Volume expectations:** (how many leads per invocation? Chunking at 100 is required above that)
- **Conversion paths in scope:** UI only / Apex only / all paths (determines whether trigger-based or service-layer field transfer is needed)

## Approach

Which pattern from SKILL.md applies?

- [ ] Controlled Apex conversion service (programmatic path only)
- [ ] After-update trigger detecting `IsConverted` flip (all conversion paths)
- [ ] Both (service calls `convertLead()`, trigger handles UI/API-initiated conversions)

## Implementation Plan

1. Query the converted LeadStatus API name dynamically.
2. Build `Database.LeadConvert` list with required setters (see SKILL.md Decision Guidance).
3. Chunk to 100 per `convertLead()` call.
4. Handle `LeadConvertResult` — log errors, collect converted record Ids.
5. Post-conversion DML: map unmapped custom fields to Contact/Account/Opportunity.
6. Write test class: use a real `convertLead()` call in tests; do not instantiate `LeadConvertResult`.

## Checklist

- [ ] Converted status API name queried dynamically — no hardcoded string literal
- [ ] `convertLead()` calls chunked at 100
- [ ] Custom field transfer via post-conversion DML (not assumed to be automatic)
- [ ] No second Lead trigger created — logic added to existing handler if one exists
- [ ] Test class uses `isSuccess()` from real `LeadConvertResult` instances
- [ ] Post-conversion DML uses `with sharing` and respects FLS
- [ ] Error handling covers partial failure (`allOrNone = false`) if applicable
- [ ] `ConvertedContactId` read only in `after update` context, not `before update`

## Notes

(Record any deviations from the standard pattern, e.g., why `allOrNone = false` was chosen, or why Opportunity creation was suppressed)
