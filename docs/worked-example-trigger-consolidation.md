# Worked example — three triggers on Account, one fires twice

A complete pass through the library on a real Salesforce problem, with the
commands as they were typed and the output as it came back. Run on
2026-07-31 against `main`.

**The problem.** An Account object carries three Apex triggers. One of them
updates Account records from an after-update context, which re-enters the
trigger, so downstream logic runs twice. A previous developer added a static
Boolean guard, which stopped the double-run and quietly started skipping
records in bulk loads.

**The demo tree.** To keep the output reproducible without a customer
codebase, the walkthrough uses a three-file synthetic tree that reproduces the
shape exactly: a self-DML after-update trigger, its static Boolean guard
class, and a second unguarded trigger on the same object.

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
- skills/flow/flow-record-save-order-interaction/templates/save-order-map.md [0.472]
  ## Observed Recursion - Chain description: - Guard / fix:
- skills/apex/recursive-trigger-prevention/references/well-architected.md [0.455]
  # Well-Architected Notes — Recursive Trigger Prevention
- skills/apex/trigger-framework/SKILL.md [0.417]
  ## Output Artifacts | When you ask for... | You get... | |---------------------|------------| | New trigger scaffold | Trigger body, handler shape, activation guard, and recursion strategy | | Trigger review | Findings …
- skills/apex/recursive-trigger-prevention/SKILL.md [0.398]
  ## Output Artifacts | Artifact | Description | |---|---| | Recursion review | Findings on recursion source, guard precision, and skipped-processing risk | | Guard recommendation | Choice of set-based, delta-based, or fr…
- skills/apex/recursive-trigger-prevention/SKILL.md [0.366]
  Use this skill when trigger behavior is correct once and wrong on the second pass. The objective is to prevent accidental recursion without suppressing legitimate processing. In Salesforce, recursion often comes from se…
- skills/flow/recursion-and-re-entry-prevention/references/examples.md [0.347]
  # Examples — Flow Recursion and Re-Entry Prevention
- skills/apex/recursive-trigger-prevention/SKILL.md [0.346]
  ### Delta-Based Guard Clause **When to use:** Recursion should happen only if a meaningful field transition occurs. **How it works:** Compare `Trigger.oldMap` to `Trigger.new` and exit unless the relevant state actually…

Related official sources:
- apex_developer_guide: Apex Developer Guide
- salesforce_well_architected_overview: Salesforce Well-Architected Overview
```

15.34 s. One skill above the confidence threshold, and seven of the ten
returned chunks are inside it. This is the library working well; see
[Where this fell short](#where-this-fell-short) for the query that does not
behave this way.

The skill number moved during the day this page was written: the same command
printed `6.901` in the morning and `2.505` after a ranking change landed,
because the displayed figure became `rank_score` (best single chunk, 1.255,
plus the name/description bonus). The chunk scores did not move. Read the
skill id; treat the number as dated.

## Step 2 — Read the skill

`skills/apex/recursive-trigger-prevention/SKILL.md` names three guard
strategies (set-based, delta-based, framework-level) and says which one fits
which recursion source. Its
`references/llm-anti-patterns.md` opens with exactly the mistake in the demo
tree — "Using a single static Boolean guard that blocks ALL re-entry" — and
gives the reason it is wrong rather than just labelling it:

> this blocks ALL re-entry for the entire transaction, not just re-entry for
> the same records. If an after-update trigger updates other Account records
> that legitimately need processing, those records are silently skipped.

The correct pattern in that file is a `Set<Id>` of already-processed record
ids, filtered per record rather than per transaction.

Grounding: a trigger that performs DML on its own object re-enters the save
order from step 1, and Salesforce documents that re-entry and its recursion
limits in
[Triggers and Order of Execution](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm)
(Apex Developer Guide). That is the URL behind the `apex_developer_guide`
entry the search returned, resolved through
`standards/official-salesforce-sources.md`.

## Step 3 — Confirm the tier before writing code

Three triggers on one object is a structural problem, not only a recursion
problem, so route it through
`standards/decision-trees/automation-selection.md` before choosing a fix.
Q3 of that tree is the branch that resolves this case:

```
Q3. Does the logic require any of:
      - loops over 2,000+ records in-transaction
      - HTTP callouts
      - complex exception handling with rollback
      - recursive DML on the same object
      - unit tests with 90%+ coverage requirements
      - custom exception types exposed to calling code
    ├── Yes  → Apex (trigger + handler + service layer)
    └── No   → Q4
```

"Recursive DML on the same object" is a yes, so the answer is Apex with a
handler and service layer — not a rewrite into Flow. Worth checking, because
the same tree's stated default for new automation is Flow first.

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
output and are abbreviated here; nothing else is edited.

## Step 5 — Apply the canonical template

Do not hand-roll a framework. `templates/apex/TriggerHandler.cls` is the
canonical base class and already solves both problems in the demo tree:

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

Three things a static Boolean does not give you: a per-handler depth counter
with a bound (`MAX_DEPTH = 10`) that throws rather than silently skipping, a
single-shot `skipOnce()` for the deliberate self-DML case, and a declarative
activation switch. That switch is `templates/apex/TriggerControl.cls`, which
reads `Trigger_Setting__mdt` records keyed by object plus handler class and
honours a `TriggerControl_BypassAll` Custom Permission for data loads and
break-glass.

The three triggers collapse to one:

```apex
trigger AccountTrigger on Account (before insert, before update, after insert, after update) {
    new AccountTriggerHandler().run();
}
```

## Step 6 — Route it through the agent

Consolidation is more than a copy-paste: the deactivation order matters or the
org breaks mid-migration. `commands/consolidate-triggers.md` is the slash
command; it wraps `agents/trigger-consolidator/AGENT.md`, whose declared job
is:

> Finds every Apex trigger on a given sObject across the user's `force-app`
> tree, checks the target org (if connected) for additional triggers, and
> produces a consolidation plan that lifts them all into a single
> `<Object>TriggerHandler extends TriggerHandler` class using the canonical
> framework from `templates/apex/TriggerHandler.cls` +
> `templates/apex/TriggerControl.cls`. The output is a migration patch plus a
> deactivation order so nothing is live-broken mid-migration.

Its five steps are discover, classify, draft, scaffold the
`Trigger_Setting__mdt` record, and produce the ordered deactivation plan. Its
frontmatter declares `requires_org: false`, so it runs against a local
`force-app` tree with no org connected, and cites 35 skills as dependencies —
including `apex/recursive-trigger-prevention` and
`apex/order-of-execution-deep-dive`, and the decision tree used in Step 3.

Invoke it as `/consolidate-triggers` once
`python3 scripts/install_local_commands.py` has run (see
[getting-started.md](getting-started.md)), or read the AGENT.md directly in any
tool that cannot load slash commands.

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

Three real problems and one honest caveat about the measurements themselves,
none of them fatal, all of them observed while writing this page.

**1. The natural-language phrasing of the problem does not find the skill.**
The query in this document's title is the query a user would actually type.
It routes somewhere else:

```
$ python3 scripts/search_knowledge.py "three triggers on Account one fires twice"
Query: three triggers on Account one fires twice

Top skills:
- apex/lead-conversion-customization (1.300)
- apex/order-of-execution-deep-dive (0.564)

Top chunks:
- skills/apex/lead-conversion-customization/SKILL.md [1.216]
- skills/apex/fsc-apex-extensions/references/examples.md [0.723]
- skills/apex/order-of-execution-deep-dive/references/well-architected.md [0.564]
- skills/apex/order-of-execution-deep-dive/references/gotchas.md [0.481]
```

`apex/recursive-trigger-prevention` does not appear at all. The winner is a
lead-conversion skill, on a question that has nothing to do with lead
conversion — it wins because it contains a section about a single call firing
triggers on multiple objects, and the query says "triggers" and "fires".
`order-of-execution-deep-dive` in second place is defensible but is still not
the skill that answers the question. Retyping the jargon —
`"trigger recursion"` — lands `apex/recursive-trigger-prevention` at 2.505,
comfortably above the gate.

That gap between symptom phrasing and vocabulary phrasing is the library's
most significant current weakness. It is under active work: this query was
measured twice on 2026-07-31, before and after a ranking change landed the
same afternoon, and the top skill moved from
`apex/order-of-execution-deep-dive (1.642)` to the output above. Treat both as
dated measurements of `main`, not as a permanent property.

**2. Every CLI query costs 13 to 29 seconds.** Measured across 2026-07-31:
`"trigger recursion"` 13.14 s, 15.34 s and 17.37 s on three separate runs,
`"why is my LWC slow"` 17.73 s and 18.77 s,
`"permission sets" --domain admin` 19.32 s and 29.25 s. Earlier the same day
on a cold page cache the same commands took 52 s to 90 s, and a re-run while
another process was rebuilding the index took 83.08 s. Nothing about the
search is slow; process startup reads a 535 MB
`vector_index/embeddings.jsonl` and a 126 MB `vector_index/chunks.jsonl` every
single time. Interactive iteration on phrasing — exactly what problem 1 forces
you into — is painful at that cost, and the spread is wide enough that you
cannot tell a slow machine from a stuck one.

**3. The CLI and the MCP server are separate implementations, and they have
drifted before.** Same query, same checkout, both surfaces, on 2026-07-31:

```
Morning, before a retrieval change landed that day:
  CLI  scripts/search_knowledge.py "why is my LWC slow"
       -> Coverage: NONE, best chunk skills/lwc/lwc-performance/SKILL.md [1.257], 17.73 s
  MCP  skills.search_skill("why is my LWC slow")
       -> has_coverage true, lwc/lwc-performance rank 1 (1.100), 0.08 s

Afternoon, after it landed:
  CLI  -> lwc/lwc-performance (2.507), coverage granted, 18.77 s
  MCP  -> lwc/lwc-performance (2.507), coverage granted, 0.18 s
```

The morning pair is the interesting one: the CLI denied coverage on a question
the library answers, and the MCP server found it — for the wrong reason, since
at that point the MCP module set `has_coverage = bool(results)` and applied no
threshold at all. Both halves were fixed the same day. The two now share the
gate predicate (`max_score >= min_skill_max_score or score >= min_skill_score`
from `config/retrieval-config.yaml`) and both embed the query when
`vector_index/skill_embeddings.jsonl` is present, which is why the afternoon
scores are identical. The MCP server denies coverage too — verified,
`search_skill("xylophone")` returns `has_coverage: false` with zero skills.

What has *not* changed is the structure: two implementations of one gate, in
two files, with nothing in CI comparing them. The MCP module's own docstring
names `evals/measurement/check_cli_mcp_parity.py` as the regression test, and
that file does not exist on this checkout. A PyPI install also diverges by
construction, having no vector files to blend. See
[architecture.md](architecture.md).

**4. The roster changed under this document while it was being written.** The
agent counts quoted here were read at different moments: the count lint
reported 47 active runtime agents early in the session and 48 later, because
an agent directory was added in between. Both readings were correct when
taken. `python3 scripts/check_doc_counts.py` and the MCP `health` tool agree
with each other — checked together afterwards, both report 48 runtime, 14
build, 14 deprecated, 76 total — so a mismatch means one of the two numbers is
stale, not that they classify differently. Re-run the lint rather than
trusting any agent count written into prose, this page included.

None of this changes the answer to the original problem. It changes how long
it takes to find it, and which surface you should be asking.
