# Change Data Capture Admin — Work Template

Use this template when configuring or auditing Change Data Capture settings.

## Scope

**Skill:** `change-data-capture-admin`

**Salesforce edition:** [ ] Performance  [ ] Unlimited  [ ] Enterprise  [ ] Developer

**Daily event limit:** [ ] 50,000  [ ] 25,000  [ ] 10,000

**Data Cloud active in org?** [ ] Yes  [ ] No

## Pre-Configuration Check

- [ ] Checked for Data Cloud CRM Data Streams (if Data Cloud active)
- [ ] Identified which objects are Data Cloud-managed CDC (do not modify via Metadata API)

## CDC Entity Selection

| Object | Standard/Custom | CDC Enabled? | Channel URL |
|---|---|---|---|
| Account | Standard | [ ] | /data/AccountChangeEvent |
| Contact | Standard | [ ] | /data/ContactChangeEvent |
| | | [ ] | |
| | Custom | [ ] | |

## Channel Configuration

**Using per-object channels only?** [ ] Yes → No further channel configuration needed

**Using multi-entity channel?** [ ] Yes

| Setting | Value |
|---|---|
| Channel Name | |
| Channel Type | data |
| Objects Included | |
| Enriched Fields | |

- [ ] Enriched fields are persistent (not formula fields)
- [ ] Custom channel created via Tooling API or metadata

## Usage Monitoring

**PlatformEventUsageMetric query configured?** [ ] Yes  [ ] No

Estimated daily event volume for enabled objects: ___

Alert threshold (70% of limit):
- Enterprise: 17,500 events/day
- Performance/Unlimited: 35,000 events/day

- [ ] Monitoring alert configured
- [ ] Alert notification recipient: ___

## Post-Configuration Verification

- [ ] Selected objects appear in Setup > Integrations > Change Data Capture
- [ ] Integration team confirmed connection to correct channel URL
- [ ] Test events received by subscriber after updating a test record
- [ ] Data Cloud CRM Data Streams still functioning (if applicable)

## Notes

(Record any Data Cloud interactions and decisions made.)
