# Lead Management and Conversion — Work Template

Fill this in as you work. Leave a row blank only when you have decided it does not apply, and say so —
a blank cell and "deliberately not mapped" are different answers, and the second one stops the next
admin re-investigating in six months.

## Scope

**Skill:** `lead-management-and-conversion`

| | |
|---|---|
| Request summary | |
| Target org / sandbox | |
| Web-to-Lead in scope? | Yes / No |
| Bulk or automated conversion in scope? | Yes / No |
| Date | |

## Answers to the Questions to Ask

| Question | Answer | Consequence for this build |
|---|---|---|
| Which custom Lead fields must survive, and which are deliberately Lead-only? | | |
| How often do reps convert into an existing Account or Contact? | | |
| Record types on Lead / Account / Contact / Opportunity? Does conversion change owner? | | |
| Do any leads sit in a queue when converted? | | |
| Anything converting in bulk (backfill, Flow on a load, mass-convert button)? | | |
| Which validation rules or required fields must hold at conversion? | | |
| Active Block duplicate rule on Lead? | | |

## Field mapping inventory

One row per custom Lead field. This table becomes the `objectMapping` blocks in
`settings/LeadConvert.settings-meta.xml`.

| Lead field (API name) | Type | Account target | Contact target | Opportunity target | Not mapped — why |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

Type must match on both sides. Picklist-to-picklist needs identical API values, or the value is
dropped silently.

## Configuration decisions

| Setting | Value chosen | Reason |
|---|---|---|
| `shouldLeadConvertRequireValidation` (read from org, not assumed) | | |
| `doesPreserveLeadStatus` | | |
| `allowOwnerChange` | | |
| `opportunityCreationOptions` | | |
| Converted `LeadStatus` value(s) | | |
| Lead process(es) and the record types using them | | |

## Record-type matrix

Only if record types are in play. The new owner's default record type shapes the created records; the
converting user's constrains the Lead Source values in the dialog.

| Profile | Converts leads? | Receives ownership? | Default Lead RT | Default Account RT | Default Contact RT | Default Opportunity RT |
|---|---|---|---|---|---|---|
| | | | | | | |

## Checklist

Copy the Review Checklist from `SKILL.md` and tick as you go. These are the ones most often skipped:

- [ ] Retrieved `Settings:LeadConvert`, `Settings:LeadConfig`, `StandardValueSet:LeadStatus` **before** editing
- [ ] `python3 ../scripts/check_lead_management_and_conversion.py --manifest-dir <dir>` reports no issues
- [ ] Queue-owned lead converted successfully in sandbox
- [ ] Merge-into-existing-Account conversion tested; refresh gap accepted or handled
- [ ] Verification query 3 from `references/metadata-examples.md` §8 returns no rows with a populated source and a null target
- [ ] No target field depends on a custom-field default value to be populated

## Verification evidence

Paste the result of the verification queries, not a summary of them.

```text
```

## Notes and deviations

Record anything done differently from the skill's patterns, and why. Also record every field left
unmapped on purpose — that list is the deliverable that stops the same investigation happening again.
