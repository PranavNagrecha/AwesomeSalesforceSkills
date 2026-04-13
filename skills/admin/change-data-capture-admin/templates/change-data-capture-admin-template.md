# Change Data Capture Admin — Work Template

Use this template when working on tasks in this area. Fill in every section before proceeding.

---

## Scope

**Skill:** `change-data-capture-admin`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer every question in the SKILL.md "Before Starting" section before proceeding.

- **Org Edition:** [ ] Performance/Unlimited (50K events/24h) | [ ] Enterprise (25K events/24h) | [ ] Developer (10K events/24h)
- **CDC add-on licensed:** [ ] Yes | [ ] No (5-entity hard limit applies)
- **Data Cloud active with CRM Data Streams:** [ ] Yes — do not modify `DataCloudEntities` channel | [ ] No
- **Existing entity selections (Tooling API audit):**

  ```soql
  SELECT QualifiedApiName, PlatformEventChannel.MasterLabel
  FROM PlatformEventChannelMember
  ORDER BY PlatformEventChannel.MasterLabel, QualifiedApiName
  ```

  _Paste results here:_

- **Enrichment required:** [ ] Yes | [ ] No
  - If yes, confirm target channel is a custom channel (name ends in `__chn`): [ ] Confirmed
  - Enriched fields list: _(list field API names — no formula fields)_
- **Known constraints / failure modes:**

---

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Standard entity selection via Setup UI (default channel, ≤5 entities, no enrichment)
- [ ] Custom channel via Metadata API (enrichment required, or subscriber isolation needed)
- [ ] Delivery allocation monitoring / remediation

**Rationale:**

---

## Channel Configuration Plan

| Channel Name | Channel Type | Entities | Enriched Fields | Managed By |
|---|---|---|---|---|
| `ChangeEvents` (default) | Standard | _(list)_ | None | Setup UI |
| `DataCloudEntities` | Data Cloud-managed | _(do not modify)_ | N/A | Data Cloud |
| `_____________________` | Custom (`__chn`) | _(list)_ | _(list)_ | Metadata API |

---

## Metadata Files to Deploy

List each file to be created or modified:

- [ ] `platformEventChannels/<ChannelName>.platformEventChannel`
- [ ] `platformEventChannelMembers/<ChannelName>-<Entity>.platformEventChannelMember`
- [ ] _(additional files as needed)_

---

## Delivery Allocation Monitoring Plan

- **Daily limit for this org:** _______ events/24h
- **Alert threshold (80%):** _______ events/24h
- **Monitoring mechanism:** [ ] Scheduled Flow | [ ] Apex job | [ ] External monitoring tool
- **PlatformEventUsageMetric query:**

  ```soql
  SELECT Name, Value, StartDate, EndDate
  FROM PlatformEventUsageMetric
  WHERE Name = 'CDC Event Notifications Delivered'
  ORDER BY StartDate DESC
  LIMIT 7
  ```

---

## Checklist

Run through the SKILL.md Review Checklist before marking this work complete.

- [ ] Org Edition and daily delivery allocation limit confirmed
- [ ] CDC add-on licensing status verified against entity count
- [ ] All `PlatformEventChannelMember` records audited via Tooling API (not only Setup UI)
- [ ] `DataCloudEntities` channel not modified
- [ ] Enrichment configured only on custom multi-entity channel members
- [ ] No formula fields listed as enriched fields
- [ ] `PlatformEventUsageMetric` monitoring in place with alert threshold
- [ ] Custom channel metadata committed to version control
- [ ] Checker script run: `python3 scripts/check_change_data_capture_admin.py --manifest-dir <path>`

---

## Handoff Notes

- **Subscriber setup:** Route the subscriber team to `integration/change-data-capture-integration` for Pub/Sub API / CometD configuration, replay ID management, and gap event handling.
- **Deviations from standard pattern:** _(document any deviations and the reason)_
- **Open items / follow-up actions:**
