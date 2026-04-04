# Change Data Capture Integration — Work Template

Use this template when designing or implementing a CDC external subscription integration.

---

## Scope

**Skill:** `change-data-capture-integration`

**Request summary:** (fill in what the external integration needs to accomplish)

**Subscriber technology:** [ ] Pub/Sub API (gRPC)  [ ] CometD / EMP Connector  [ ] MuleSoft CDC connector  [ ] Other: ___

---

## 1. Entity Selection Inventory

List all objects that need CDC. Confirm against the 5-entity default limit.

| Object API Name | Type (Standard / Custom) | Channel Assignment | Justification |
|---|---|---|---|
| | | Default ChangeEvents / Custom: ___ | |
| | | | |
| | | | |

**Total entity count:** ___  (limit: 5 without add-on)
**Add-on licensed?** [ ] Yes  [ ] No  [ ] To be confirmed

---

## 2. Channel Topology

**Using default ChangeEvents channel?** [ ] Yes  [ ] No

**Custom channels required?** [ ] Yes  [ ] No

If custom channels, document each:

| Channel API Name | Entities | Subscribers | Event Enrichment Fields |
|---|---|---|---|
| `_____chn` | | | |

**Rationale for channel design:** (why default vs custom; isolation requirements)

---

## 3. Subscriber Protocol Decision

| Factor | Decision |
|---|---|
| Need `changedFields` / `nulledFields` delta in subscriber? | [ ] Yes → Pub/Sub API required  [ ] No → CometD acceptable |
| Existing middleware connector (MuleSoft, Boomi)? | [ ] Yes: ___ connector  [ ] No, building custom |
| Protocol selected | [ ] Pub/Sub API  [ ] CometD |
| Subscription channel/topic path | `/data/___` |

---

## 4. Replay ID Strategy

| Decision Point | Choice |
|---|---|
| Initial subscription replay | [ ] -2 (full catch-up)  [ ] -1 (tip only)  [ ] Specific ID: ___ |
| Replay ID storage location | [ ] Database table  [ ] Redis/cache  [ ] Config file  [ ] Other: ___ |
| Storage key / identifier | |
| Persistence timing | [ ] After each event  [ ] After each batch |
| Recovery when stored ID outside 72h window | [ ] Bulk API re-sync then tip  [ ] Accept gap  [ ] Other: ___ |
| Subscriber offline alerting threshold | ___ hours (recommended: < 24h to stay well inside 72h window) |

---

## 5. Gap Event Handling Design

**Gap events detected by:** `changeType.startsWith("GAP_")` check at ___ in code

**Recovery action on gap event:**

- [ ] Fetch current record state via REST API using `recordIds` from event header
- [ ] Mark record as dirty in external system and schedule reconciliation
- [ ] Log gap event with `commitTimestamp` for audit trail
- [ ] Reconcile using `commitTimestamp` to avoid overwriting newer non-gap changes

**Gap event test plan:** (how will gap event handling be validated in sandbox)

---

## 6. Event Delivery Allocation Assessment

| Metric | Value |
|---|---|
| Org Edition | Performance/Unlimited / Enterprise / Developer |
| Default daily delivery allocation | 50,000 / 25,000 / 10,000 events per 24h |
| Estimated daily event volume (per subscriber) | ___ |
| Number of API subscribers (CometD + Pub/Sub API) | ___ |
| Estimated total daily consumption | ___ (volume × subscriber count) |
| At risk of hitting allocation? | [ ] Yes — review  [ ] No |
| Add-on needed? | [ ] Yes  [ ] No |

**Monitoring approach:** [ ] Setup > Event Manager  [ ] REST API `/services/data/vXX.0/limits/`  [ ] Other: ___

---

## 7. Checklist

Copy from SKILL.md and tick as you complete each item:

- [ ] All target entities are enabled and the 5-entity limit (or add-on) is accounted for.
- [ ] Channel topology is confirmed: default channel vs per-entity channel vs custom channel.
- [ ] Subscriber uses Pub/Sub API (preferred) or has a documented reason for CometD.
- [ ] Replay ID is persisted to durable external state after each processed batch.
- [ ] Gap event handling is implemented and tested with a `GAP_CREATE` or `GAP_UPDATE` scenario.
- [ ] Initial replay strategy is documented (`-1` tip or `-2` full catch-up).
- [ ] Event delivery allocation usage is monitored with alerting before the daily cap.
- [ ] Subscriber reconnect behavior under the 72-hour window is tested.
- [ ] If multiple subscribers exist, evaluate custom channels to prevent shared delivery allocation exhaustion.

---

## 8. Notes

(Record deviations from the standard pattern, open questions, decisions pending confirmation)
