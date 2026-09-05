# Integration Pattern Selection — Decision Record Template

Copy this file to `docs/adr/ADR-INT-<nnnn>.md`, fill every field, then lint the copy:

```bash
python3 scripts/check_integration_pattern_selection.py --decision-record docs/adr/ADR-INT-<nnnn>.md
```

Worked examples of a filled record are in `references/decision-record-examples.md`.
The questions the fields answer live in `standards/decision-trees/integration-pattern-selection.md` —
cite them by number (`integration-pattern-selection.md Q7`), never by paraphrase.

---

## The Record

```yaml
---
record_id:
requirement: >

direction:                # salesforce_to_external | external_to_salesforce | bidirectional_or_decoupled
volume:
  per_day:                # measured peak rows or calls per 24 hours
  per_request:            # rows per API call / per Bulk batch
latency:                  # realtime | near_realtime | batch
idempotency:              # designed_idempotent | idempotency_key_required | not_guaranteed
who_knows_ids:            # salesforce_ids | external_key | neither
ordering:                 # strict | at_least_once | not_required
chosen_pattern:           # see the allowed set below
tree_questions_cited:
  - "integration-pattern-selection.md Q — "
rejected:
  - alternative:
    reason: >

auth:
  named_credential:
  external_credential:
owner:
review_date:              # YYYY-MM-DD
---
```

### Allowed `chosen_pattern` values

`rest_api`, `rest_composite`, `bulk_api_2`, `custom_rest`,
`apex_callout_named_credential`, `continuation`, `queueable_callout`,
`platform_event`, `change_data_capture`, `pub_sub_api`,
`salesforce_connect_odata`, `streaming_api_pushtopic`, `outbound_message`,
`mulesoft_ipaas`.

`streaming_api_pushtopic` and `outbound_message` are legacy — the tree's anti-patterns
section rules both out for new work. If one of them is the answer, the record has to say
why the migration is being deferred.

### Which questions apply to which direction

| `direction` | Work these questions, top to bottom, as a checklist |
|---|---|
| `salesforce_to_external` | Q1 latency and context · Q2 authentication · Q3 payload shape · Q4 rate limiting and retry |
| `external_to_salesforce` | Q5 volume · Q6 latency · Q7 who knows the Ids · Q8 idempotency · Q9 does the data belong in Salesforce tables |
| `bidirectional_or_decoupled` | Q10 who produces the signal · Q11 who subscribes · Q12 ordering · Q13 external producer shape · Q14 replication direction |

They are not a branching graph. Within a direction every question applies, and each one
narrows a different axis.

---

## Supporting Notes (free text, kept below the record)

### Integration inventory

What the org already does with this system. Retrieve `NamedCredential`,
`ExternalCredential`, `ConnectedApp`, `PlatformEventChannel`, `PlatformEventChannelMember`
and `RemoteSiteSetting` — the manifest and commands are in
`references/decision-record-examples.md` § *The Integration Inventory*.

| Existing integration | Mechanism | Owner | Overlaps this requirement? |
|---|---|---|---|
| | | | |

### Limits this pattern will spend

| Limit | Ceiling | Expected usage | Source |
|---|---|---|---|
| | | | |

### Hand-off

| Next skill / agent | Why |
|---|---|
| | |

---

## Review Checklist

- [ ] `direction` chosen before any mechanism was named
- [ ] Every branch of the choice cites a numbered question a reader can look up
- [ ] Each rejected alternative carries a reason, not a strikethrough
- [ ] `volume.per_day` is a measured number, not a sandbox number
- [ ] The per-request ceiling of the chosen mechanism is respected
- [ ] `who_knows_ids` was verified, including that any External Id field is Unique
- [ ] `auth.named_credential` names a real Named Credential; no endpoint is hard-coded
- [ ] `ordering` states what the pattern actually guarantees, not what is wished for
- [ ] Existing integrations to the same system were inventoried before this one was proposed
- [ ] `owner` and `review_date` are filled
- [ ] `check_integration_pattern_selection.py --decision-record` passes
