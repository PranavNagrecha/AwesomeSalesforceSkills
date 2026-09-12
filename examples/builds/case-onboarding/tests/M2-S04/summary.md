# M2-S04 test summary — Case queues and public groups

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| `skills/admin/queues-and-public-groups/scripts/check_queues.py --manifest-dir artefacts/M2-S04` | checker | PASS (exit 0; check-outputs ok) | n/a |
| xml | always-on | PASS (7/7 files parse) | n/a |
| manifest | always-on | PASS (consistent) | n/a |
| manual: all six components present, queueSobject=Case | manual | deferred to milestone gate (file evidence: matches) | n/a |
| manual W02 (1/3): per-queue email posture | manual | deferred to milestone gate (file evidence: **mismatch** — see below) | n/a |
| manual W02 (2/3): no named users; roster confirmed by manager | manual | deferred to milestone gate (file-checkable half matches; roster half needs a human) | n/a |
| manual W02 (3/3) / S4: runbook records threshold, monitor, remedy | manual | deferred to milestone gate (file evidence: matches) | n/a |

`passed: true` — every runnable test (checker, xml, manifest) passed. Manual tests never count toward `passed`/`failed`; see Process Observations for what was found while checking them against disk.

## Checker output (full capture in `check_queues_stdout.txt`)

```
Warnings found (2):
  WARN: [Queue: Tier 1 General] No <email> configured — the queue address will not receive notifications when records are assigned to this queue.
  WARN: [Queue: Tier 2 Engineering] No <email> configured — the queue address will not receive notifications when records are assigned to this queue.
```
Exit 0.

## check-outputs (full capture in `check_outputs_stdout.txt`)

```json
{"ok": true, "step": "M2-S04", "missing": [], "empty": [], "malformed": []}
```

## Observation: the declared checker test's description predicts one WARN; two were printed

`acceptance_tests[0].description` says the fixture run "printed 'Warnings found (1): WARN: [Queue: Tier 1 General] No <email> configured'." The actual run against these exact six files prints **Warnings found (2)** — Tier 1 General and Tier 2 Engineering both lack `<email>`. This is a plan-text vs. artefact mismatch, not a test failure: the checker's pass condition (exit 0) still holds, and check-outputs is ok. The step's own `runs[]` entry for 2026-09-12T00-52-00Z already records "2 documented no-email WARNs (Tier 1 by Q88, Tier 2 ungrounded address)" — so only `acceptance_tests[0].description` in plan.json is stale.

## Observation: manual test W02 (1/3) does not match the artefact it is checking

The criterion asserts Tier_2_Engineering "carries the Tier 2 shared mailbox." The file `artefacts/M2-S04/queues/Tier_2_Engineering.queue-meta.xml` has no `<email>` element at all — there is no mailbox address on it to carry. This is the same fact the checker's second WARN reports. Recorded as evidence for the human at the gate, not ticked.
