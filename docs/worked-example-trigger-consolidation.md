# Worked example — three triggers on Account, one fires twice

A complete pass through the library on a real Salesforce problem, with the
commands as they were typed and the output as it came back. Every command on
this page was re-run on **2026-08-15** against the working tree and the output
below is what came back that day. Scores and timings move; re-run rather than
quoting.

**The problem.** An Account object carries three Apex triggers. One of them
updates Account records from an after-update context, which re-enters the
trigger, so downstream logic runs twice. A previous developer added a static
Boolean guard, which stopped the double-run and quietly started skipping records
in bulk loads.

**The demo tree.** To keep the output reproducible without a customer codebase,
the walkthrough uses a three-file synthetic tree that reproduces the shape
exactly: a self-DML after-update trigger, its static Boolean guard class, and a
second unguarded trigger on the same object.

```apex
// force-app/main/default/triggers/AccountTrigger.trigger
trigger AccountTrigger on Account (after update) {
    if (!AccountRecursionGuard.hasRun) {
        AccountRecursionGuard.hasRun = true;
        for (Account a : Trigger.new) {
            a.Description = 'touched';
        }
        update Trigger.new;
    }
}

// force-app/main/default/classes/AccountRecursionGuard.cls
public class AccountRecursionGuard {
    public static Boolean hasRun = false;
}

// force-app/main/default/triggers/AccountRollupTrigger.trigger
trigger AccountRollupTrigger on Account (after update) {
    update [SELECT Id FROM Contact WHERE AccountId IN :Trigger.newMap.keySet()];
}
```

> The demo tree is illustrative, not deployable. `a.Description = 'touched'`
> inside an *after*-update loop throws `System.FinalException: Record is
> read-only` before it ever reaches the `update` — see
> `skills/apex/apex-trigger-context-variables/references/gotchas.md`, Gotcha 5.
> That is deliberate: it is the shape the Step 4 checker has to recognise
> statically, and it is what a static Boolean guard is usually sitting on top
> of. Do not lift this code.

---

## Step 1 — Find the skill

```
$ python3 scripts/search_knowledge.py "trigger recursion"
Query: trigger recursion

Top skills:
- apex/recursive-trigger-prevention (2.505)

Top chunks:
- skills/apex/recursive-trigger-prevention/SKILL.md [1.255]
  ## Trigger Scenarios - how do I prevent recursive Apex triggers - static boolean recursion guard problem - trigger updates same object again - after update trigger firing repeatedly - Set<Id> recursion guard pattern - t…
- skills/apex/recursive-trigger-prevention/templates/recursive-trigger-prevention-template.md [0.755]
  # Recursion Guard Worksheet
- skills/apex/recursive-trigger-prevention/references/examples.md [0.588]
  # Examples — Recursive Trigger Prevention
- skills/flow/flow-record-save-order-interaction/templates/save-order-map.md [0.470]
  ## Observed Recursion - Chain description: - Guard / fix:
- skills/apex/recursive-trigger-prevention/references/well-architected.md [0.455]
  # Well-Architected Notes — Recursive Trigger Prevention
- skills/apex/trigger-framework/SKILL.md [0.417]
  ## Output Artifacts | When you ask for... | You get... |…
- skills/apex/recursive-trigger-prevention/SKILL.md [0.398]
  ## Output Artifacts | Artifact | Description |…
- skills/apex/recursive-trigger-prevention/SKILL.md [0.366]
  Use this skill when trigger behavior is correct once and wrong on the second pass…
- skills/apex/recursive-trigger-prevention/SKILL.md [0.355]
  ### Delta-Based Guard Clause **When to use:** Recursion should happen only if a meaningful field transition occurs…
- skills/flow/recursion-and-re-entry-prevention/references/examples.md [0.338]
  # Examples — Flow Recursion and Re-Entry Prevention

Related official sources:
- apex_developer_guide: Apex Developer Guide
- salesforce_well_architected_overview: Salesforce Well-Architected Overview
```

**0.53 s.** One skill above the confidence gate, and seven of the ten returned
chunks are inside it. This is the library working well; see
[Where this fell short](#where-this-fell-short) for the query that does not
behave this way.

Treat the displayed skill number as dated, and do not compare it across
revisions of this page. It is `rank_score` — the best single chunk score (1.255)
plus a name/description centrality bonus — and the CLI deliberately prints that
field rather than the raw aggregate (`scripts/search_knowledge.py:468-470`,
"Print rank_score, the value the list is ordered by"). A ranking change in July
2026 changed which field is displayed without moving any chunk score, so the
headline number jumped while the retrieval did not. Read the skill id; re-run
for the number.

## Step 2 — Read the skill

`skills/apex/recursive-trigger-prevention/SKILL.md` names three guard strategies
— `Set<Id>`-based, delta-based, and framework-level — and says which fits which
recursion source. Its `references/llm-anti-patterns.md` opens with exactly the
mistake in the demo tree, "Using a single static Boolean guard that blocks ALL
re-entry", and gives the reason rather than just the label:

> But this blocks ALL re-entry for the entire transaction, not just re-entry for
> the same records. If an after-update trigger updates other Account records
> that legitimately need processing, those records are silently skipped.

The correct pattern in that file is a `Set<Id>` of already-processed record ids,
filtered per record rather than per transaction.

**Grounding.** A trigger that performs DML on its own object re-enters the save
order from step 1, and Salesforce documents that re-entry and its recursion
limits in
[Triggers and Order of Execution](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm)
(Apex Developer Guide). Note what that URL is and is not: it is the citation
carried by `skills/apex/order-of-execution-deep-dive/SKILL.md:229`. It is *not*
what the search result's `apex_developer_guide` line resolves to — that id is
defined in `knowledge/sources.yaml:75` and points at the guide's root page,
`apex_dev_guide.htm`. The "Related official sources" footer names the guide, not
the page; you still have to find the page.

## Step 3 — Confirm the tier before writing code

Three triggers on one object is a structural problem, not only a recursion
problem, so route it through
`standards/decision-trees/automation-selection.md` before choosing a fix. Q3 of
that tree is the branch that resolves this case:

```
Q3. Does the logic require any of:
      - a loop whose per-record work would breach the per-transaction
        governor limits Flow shares with Apex (10 s CPU, 100 SOQL,
        150 DML statements, 10,000 DML rows, 50,000 rows queried)
      - callouts that need retry/backoff, chaining, or binary payloads
      - complex exception handling with rollback (savepoints)
      - recursive DML on the same object
      - a deployable unit under an enforced coverage gate with
        assertion-style tests (Apex needs 75% org-wide to deploy; Flow
        has no coverage gate at all)
      - custom exception types exposed to calling code
    ├── Yes  → Apex (trigger + handler + service layer)
    └── No   → Q4
```

"Recursive DML on the same object" is a yes, so the answer is Apex with a
handler and service layer — not a rewrite into Flow. Worth checking, because the
same tree's stated strategic default is that "new automation should be built in
Flow, escalating to Apex only when Flow cannot meet the requirement". Q3 is
where "cannot meet the requirement" gets defined, and this case lands inside it.

## Step 4 — Measure the existing code

The skill ships its own checker. Point it at the tree:

```
$ python3 skills/apex/recursive-trigger-prevention/scripts/check_recursive_trigger_prevention.py --manifest-dir ./demo
WARN: 5 finding(s) detected
{
  "score": 90,
  "findings": [
    {
      "severity": "HIGH",
      "location": ".../classes/AccountRecursionGuard.cls",
      "message": "static Boolean recursion guard found; verify it does not suppress valid multi-record processing"
    },
    {
      "severity": "REVIEW",
      "location": ".../triggers/AccountRollupTrigger.trigger",
      "message": "trigger contains DML without obvious set-based guard or delta-check logic"
    },
    {
      "severity": "REVIEW",
      "location": ".../triggers/AccountRollupTrigger.trigger",
      "message": "after-update logic with DML found without obvious old/new delta comparison"
    },
    {
      "severity": "REVIEW",
      "location": ".../triggers/AccountTrigger.trigger",
      "message": "trigger contains DML without obvious set-based guard or delta-check logic"
    },
    {
      "severity": "REVIEW",
      "location": ".../triggers/AccountTrigger.trigger",
      "message": "after-update logic with DML found without obvious old/new delta comparison"
    }
  ],
  "summary": "Scanned 3 Apex file(s); 5 recursion-prevention finding(s) detected."
}
```

Exit code 1. It found the static Boolean (HIGH) and flagged both triggers for
missing delta comparison. The `location` values are absolute paths in the real
output and are abbreviated here; nothing else is edited. Reproduced byte-for-byte
on 2026-08-15.

## Step 5 — Apply the canonical template

Do not hand-roll a framework. `templates/apex/TriggerHandler.cls` is the
canonical base class and already solves both problems in the demo tree. From
`run()`, lines 38–52:

```apex
if (!TriggerControl.isActive(sObjectName, handlerName)) {
    return;
}

if (skipOnceHandlers.remove(handlerName)) {
    return;
}

Integer depth = depthByHandler.get(handlerName);
if (depth == null) { depth = 0; }
if (depth >= MAX_DEPTH) {
    throw new TriggerHandlerException(
        'Recursion depth exceeded for ' + handlerName + ' on ' + sObjectName
    );
}
```

Three things a static Boolean does not give you:

1. a **per-handler depth counter** with a bound (`MAX_DEPTH = 10`,
   `TriggerHandler.cls:28`) that throws rather than silently skipping — and the
   counter is decremented in a `finally` block, so a thrown handler does not
   leave the depth pinned for the rest of the transaction;
2. a single-shot **`skipOnce(handlerName)`** for the deliberate self-DML case,
   which consumes itself on read (`skipOnceHandlers.remove(...)` returns `true`
   and clears in one step);
3. a declarative **activation switch**, `templates/apex/TriggerControl.cls`,
   which reads `Trigger_Setting__mdt` records keyed by object plus handler class
   and honours a `TriggerControl_BypassAll` Custom Permission for data loads and
   break-glass. That permission is *not* shipped with the templates, and
   `TriggerControl` fails closed when it is absent — no bypass, triggers keep
   running.

The three triggers collapse to one:

```apex
trigger AccountTrigger on Account (before insert, before update, after insert, after update) {
    new AccountTriggerHandler().run();
}
```

## Step 6 — Route it through the agent

Consolidation is more than a copy-paste: the deactivation order matters or the
org breaks mid-migration. `commands/consolidate-triggers.md` is the slash
command; it wraps `agents/trigger-consolidator/AGENT.md`, whose declared job is:

> Finds every Apex trigger on a given sObject across the user's `force-app`
> tree, checks the target org (if connected) for additional triggers, and
> produces a consolidation plan that lifts them all into a single
> `<Object>TriggerHandler extends TriggerHandler` class using the canonical
> framework from `templates/apex/TriggerHandler.cls` +
> `templates/apex/TriggerControl.cls`. The output is a migration patch plus a
> deactivation order so nothing is live-broken mid-migration.

Its six steps are: discover triggers and adjacent automation, classify, draft
the consolidation, scaffold the `Trigger_Setting__mdt` metadata, produce the
ordered deactivation plan, and — Step 6, "Gate C" — verify the emitted code
before returning it. Gate C is the one worth knowing about: it requires that
every field the handler touches appeared in the Step 1 discovery output rather
than in the model's picture of the object, that every non-platform
`Type.method(...)` is quoted from `TriggerHandler.cls` or `TriggerControl.cls`,
and that without a `target_org_alias` the agent states no compile check ran and
caps its confidence at MEDIUM.

Its frontmatter declares `requires_org: false`, so it runs against a local
`force-app` tree with no org connected, and its `dependencies` block declares
**35 skills** — including `apex/recursive-trigger-prevention` and
`apex/order-of-execution-deep-dive` — plus four templates and the decision tree
used in Step 3.

```bash
python3 -c "
import yaml,pathlib
d=yaml.safe_load(pathlib.Path('agents/trigger-consolidator/AGENT.md').read_text().split('---')[1])
print(len(d['dependencies']['skills']), 'skills;', d['dependencies']['decision_trees'])"
# -> 35 skills; ['automation-selection.md']
```

Invoke it as `/consolidate-triggers` once `python3 scripts/bootstrap.py` has
installed the 67 commands into `.claude/commands/` — and restart the CLI
afterwards, because Claude Code loads slash commands at session start. See
[getting-started.md §A2](getting-started.md). In any tool that cannot load slash
commands, read the AGENT.md directly.

## The full chain

Every artifact this task touched, all present on disk:

| Layer | Path |
|---|---|
| Skill | `skills/apex/recursive-trigger-prevention/SKILL.md` |
| Skill checker | `skills/apex/recursive-trigger-prevention/scripts/check_recursive_trigger_prevention.py` |
| Decision tree | `standards/decision-trees/automation-selection.md` |
| Template | `templates/apex/TriggerHandler.cls` |
| Template | `templates/apex/TriggerControl.cls` |
| Agent | `agents/trigger-consolidator/AGENT.md` |
| Command | `commands/consolidate-triggers.md` |
| Official source | [Apex Developer Guide — Triggers and Order of Execution](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm) |

---

## Where this fell short

Three real problems and one honest caveat about the measurements themselves.
None are fatal; all were observed while writing this page.

### 1. The natural-language phrasing of the problem does not find the skill

The query in this document's title is the query a user would actually type. It
routes somewhere else:

```
$ python3 scripts/search_knowledge.py "three triggers on Account one fires twice"
Query: three triggers on Account one fires twice

Top skills:
- apex/order-of-execution-deep-dive (1.230)

Top chunks:
- skills/apex/order-of-execution-deep-dive/references/gotchas.md [1.230]
- skills/apex/lead-conversion-customization/SKILL.md [0.716]
- skills/apex/fsc-apex-extensions/references/examples.md [0.556]
- skills/apex/order-of-execution-deep-dive/references/well-architected.md [0.480]
… 6 more chunks, snippets elided
```

`apex/recursive-trigger-prevention` does not appear at all — not in the single
gated skill and not in any of the ten returned chunks. The winner,
`order-of-execution-deep-dive`, is defensible but still not the skill that
answers the question. Retyping the jargon — `"trigger recursion"` — lands
`apex/recursive-trigger-prevention` at 2.505, comfortably above the gate.

That gap between symptom phrasing and vocabulary phrasing is the library's most
significant current weakness, and it is measured rather than guessed:
`python3 evals/measurement/run_heldout.py` scores 40.3% Hit@1 on hand-written
practitioner phrasings against 98.4% on the generated fixtures, on the same
binary and the same index. See `evals/measurement/README-heldout.md`.

It is also moving. An earlier revision of this page recorded this exact query
returning a *different* top skill twice on 2026-07-31, before and after a
ranking change landed that afternoon — `apex/order-of-execution-deep-dive` and
then `apex/lead-conversion-customization`. Those readings cannot be reproduced
against today's index and are not repeated here as figures; the point that
survives is that the winner for this query has changed at least twice. Treat the
result above as a dated reading of `main`, not a permanent property.

### 2. CLI query latency is fixed — the old figure on this page was ten to fifty times too high

An earlier revision of this page said "every CLI query costs 13 to 29 seconds".
That was true when written and is false now. Commit `d8c95d5de`
("perf(retrieval): 3,190 MB -> 76 MB per query, byte-identical results") removed
an unconditional load of the chunk-level embeddings file, and the on-disk
footprint shrank with it.

Measured 2026-08-15, three consecutive runs each:

| Query | Wall clock |
|---|---|
| `"trigger recursion"` | 0.54 s, 0.53 s, 0.53 s |
| `"three triggers on Account one fires twice"` | 0.68 s |
| `"why is my LWC slow"` | 0.58 s |
| `"permission sets" --domain admin` | 0.57 s |

Peak resident set for one query is 372 MB
(`/usr/bin/time -l python3 scripts/search_knowledge.py "trigger recursion"` →
`389709824 maximum resident set size`). The chunk-level
`vector_index/embeddings.jsonl` that dominated the old numbers — loaded
unconditionally on every invocation, per that commit's own measurements — is not
present on this machine at all. What `vector_index/` holds today is
`chunks.jsonl` (127.4 MB), `lexical.sqlite` (168.7 MB) and
`skill_embeddings.jsonl` (5.0 MB). Interactive iteration on phrasing — exactly
what problem 1 forces you into — is now cheap.

### 3. The CLI and the MCP server are separate implementations of one gate

They have drifted before. In the morning of 2026-07-31 the CLI denied coverage
on `"why is my LWC slow"` while the MCP server found it — for the wrong reason,
since the MCP module then set `has_coverage = bool(results)` and applied no
threshold at all. Both halves were fixed the same day.

They agree today. Both read the same gate predicate
(`max_score >= min_skill_max_score or score >= min_skill_score`, thresholds 1.0
and 1.5 in `config/retrieval-config.yaml`) and both blend
`vector_index/skill_embeddings.jsonl` when present, so `rank_score` matches to
the digit:

| Query | CLI `rank_score` | MCP `rank_score` |
|---|---|---|
| `trigger recursion` | 2.505 | 2.505 |
| `why is my LWC slow` | 2.508 | 2.508 |
| `three triggers on Account one fires twice` | 1.230 | 1.230 |

One trap when comparing them by hand: the MCP result carries **two** numbers per
skill, `score` and `rank_score`, and only `rank_score` is what the CLI prints.
For `trigger recursion` the MCP `score` is 6.909 while `rank_score` is 2.505 —
compare the wrong field and you will conclude they have diverged when they have
not.

The MCP server denies coverage too — `search_skill("xylophone")` returns
`has_coverage: false` with zero skills, verified today.

What has not changed is the structure: two implementations of one gate, in two
files. They are policed rather than trusted —
`evals/measurement/check_cli_mcp_parity.py --heldout` runs both surfaces over all
154 held-out queries and fails on any disagreement about which skills clear the
gate:

```
$ python3 evals/measurement/check_cli_mcp_parity.py --heldout
CLI/MCP retrieval parity: 154/154 queries agree
OK: both surfaces return the same gated skill list for every query.
```

A PyPI install still diverges by construction, having no vector files to blend.
See [architecture.md](architecture.md).

### 4. The roster changed under this document while it was being written

The agent counts quoted on the earlier revision were read at different moments:
the count lint reported 47 active run-time agents early in that session and 48
later, because an agent directory was added in between. Both readings were
correct when taken. `python3 scripts/check_doc_counts.py` is the arbiter and
prints, today:

```
Doc counts consistent: 1027 skills, 48 active runtime + 14 build + 14 deprecated = 76 agents, 38 MCP tools.
```

The MCP `health` tool derives the same figures from the same source, so a
mismatch means one number is stale, not that the two classify differently.
Re-run the lint rather than trusting any agent count written into prose, this
page included.

---

None of this changes the answer to the original problem. It changes how long it
takes to find it, and which surface you should be asking.
