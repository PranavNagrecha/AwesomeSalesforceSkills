# /add-skill — one command, topic in, landed skill out

You give it a topic. It works out everything else.

```
/add-skill Data Cloud calculated insights refresh failures
```

That is the whole interface. No domain to pick, no slug to invent, no checklist
to track, no "did I remember the fixture" at the end.

## Why this exists

`/new-skill` prints a six-step checklist and then the checklist lives in your
head: which TODOs are left, whether `llm-anti-patterns.md` reached five entries,
whether a query fixture exists, whether an agent should cite it, whether the
registry is stale, whether it actually retrieves. `validate_repo.py` will tell
you eventually — in about twelve minutes, as a list of problems rather than a
next action.

This command does that bookkeeping, and it does the part that is easy to skip:
**it checks whether the skill should exist at all.**

## What it does

```
Screen   -> run the real search, 2-3 phrasings, record verbatim output
Decide   -> BUILD | DEEPEN | STOP, on that evidence
Research -> official-docs fact sheet; unverifiable claims are dropped, not softened
Author   -> scaffold via new_skill.py --strict, fill from the fact sheet only
Review   -> adversarial fact-check; revert anything the sheet does not support
Land     -> fixture, agent wiring, sync, retrieval check, validate, doctor
```

**It will usually tell you not to build.** This library has 1,027 packages and is
saturated at topic level: three independent screens in August 2026 found that of
94 research-claimed gaps only 12 were real, of 31 hand-picked topics 1, and of 88
verified platform changes 0. A "gap" here is almost never a missing package — it
is a missing *fact* inside a package that already owns the topic. So `DEEPEN` is
the common outcome and it is the right one. `STOP` means the facts are already
there.

If you disagree with the screen, pass `force: true`. It still runs the screen and
still reports the evidence, so the override is recorded rather than invisible.

## Usage

```
Workflow { scriptPath: ".claude/workflows/add-skill.js",
           args: { topic: "Data Cloud calculated insights refresh failures" } }
```

Optional args:

| arg | effect |
|---|---|
| `domain` | suggest a domain; the Decide phase may still overrule it |
| `slug` | suggest a slug; `new_skill.py --strict` still refuses near-duplicates |
| `force` | build even when the screen says the topic is owned |

## The bit that matters most

The Author phase must end the `description:` with a real boundary clause:

```
NOT for <the adjacent question> — use <domain>/<slug-that-exists>
```

That is not styling. On a fresh install there is **no search index** —
`vector_index/` is gitignored and never ships. Claude picks a skill by reading
one-line glosses in `.claude/skills/salesforce-<domain>/references/skill-index.md`,
generated from these descriptions and trimmed to 220 characters. The roster's own
header tells its reader that a `NOT for X - use Y` clause is the most useful thing
on the line. The Review phase confirms the target exists on disk, because a
redirect to a package that does not exist sends the reader nowhere.

## Checking a skill afterwards, or any time

```bash
python3 scripts/skill_doctor.py apex/trigger-framework   # one skill
python3 scripts/skill_doctor.py --all                    # unfinished, worst first
python3 scripts/skill_doctor.py --all --new              # only placeholder packages
```

It evaluates every gate the repo enforces against the real files and prints the
single next action:

```
admin/consumer-goods-cloud-setup   [######....] 64%
   warn  routing          the `NOT for …` clause names no package that exists
  BLOCK  no-placeholders  3 file(s) still hold TODO/placeholder text

NEXT: fill the placeholders in skills/admin/consumer-goods-cloud-setup/references/examples.md
```

`--json` gives the same thing machine-readable.

## What it will not do

- Write a fact it could not confirm on a page it rendered. `help.salesforce.com`
  is a client-side SPA that blocks crawlers and returns a loading shell, so a
  claim sourced only from there is dropped rather than softened.
- Manufacture an agent citation to clear the orphan warning. If no agent
  genuinely needs the skill, it records `runtime_orphan: true` with a reason.
- Re-point a failing query fixture at whatever currently wins. If the skill does
  not retrieve, the description and triggers get fixed instead.

## Related

- `commands/new-skill.md` — the manual path, still there if you want to drive it
- `commands/onboard-source.md` — for onboarding an external repo or attachment,
  which adds a licence wall on top of this flow
- `scripts/skill_doctor.py` — the state check used by the Land phase
- `AGENT_RULES.md`, `standards/validation-gates.md` — the gates behind it
