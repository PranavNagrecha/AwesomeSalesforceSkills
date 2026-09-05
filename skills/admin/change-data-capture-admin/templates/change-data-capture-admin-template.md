# Change Data Capture Admin — Work Template

Use this template when configuring or auditing Change Data Capture settings.

## Scope

**Skill:** `change-data-capture-admin`

**Salesforce edition:** [ ] Performance  [ ] Unlimited  [ ] Enterprise  [ ] Developer

**Daily event delivery allocation, read from this org's CDC Allocations page:** ___
(Do not fill this from memory — the App Limits cheat sheet names the "Change Data Capture Allocations" set without printing its values.)

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
| Channel full name (`<Name>__chn`) | |
| Channel Type | data |
| Objects Included (`selectedEntity` per member) | |
| Enriched Fields (`enrichedFields`, API 51.0+) | |
| Filter Expression (`filterExpression`, API 56.0+) | |

- [ ] Enriched fields are persistent (not formula fields)
- [ ] Custom channel created via Tooling API or metadata
- [ ] Member full names have every doubled underscore collapsed (`Sales_chn_AccountChangeEvent`)
- [ ] Channel file and member files are in the same deployment package

## Deployable Source

| File | Present? |
|---|---|
| `platformEventChannels/<Name>__chn.platformEventChannel-meta.xml` (custom channels only) | [ ] |
| `platformEventChannelMembers/<Channel>_<Entity>ChangeEvent.platformEventChannelMember-meta.xml` (one per entity) | [ ] |
| `manifest/package.xml` listing both types | [ ] |
| `destructiveChanges.xml` prepared for the off switch | [ ] |

- [ ] `python3 scripts/check_change_data_capture_admin.py --manifest-dir <source dir>` run with no ERROR or WARN

## Usage Monitoring

**PlatformEventUsageMetric query configured?** [ ] Yes  [ ] No
(`Name IN ('CHANGE_EVENTS_PUBLISHED','CHANGE_EVENTS_DELIVERED')`, `Value` as the count, `StartDate`/`EndDate` in UTC — see `references/metadata-examples.md`.)

**Enhanced Usage Metrics enabled in this org (API 58.0+)?** [ ] Yes → per-object figures available  [ ] No → org-wide totals only

Estimated daily event volume for enabled objects: ___

Alert threshold (70% of the allocation recorded above): ___ events/day

- [ ] Monitoring alert configured
- [ ] Alert notification recipient: ___

## Post-Configuration Verification

- [ ] Selected objects appear in Setup > Integrations > Change Data Capture
- [ ] Integration team confirmed connection to correct channel URL
- [ ] Test events received by subscriber after updating a test record
- [ ] `EventBusSubscriber` shows `Status = 'Running'` for each in-org trigger/Flow on the topic
- [ ] External (Pub/Sub, CometD) subscribers confirmed by their owners — `EventBusSubscriber` does not list them
- [ ] Subscriber behaviour on `GAP_` change types agreed in writing
- [ ] Data Cloud CRM Data Streams still functioning (if applicable)

## Notes

(Record any Data Cloud interactions and decisions made.)
