# Feedback Intake

This directory is how external feedback — from other AI assistants, human reviewers, GitHub issues, partner Salesforce MVPs, end-users — gets **heard, logged, and resolved**.

Not every piece of feedback lands as code. Every piece of feedback lands as an entry in `FEEDBACK_LOG.md` with an explicit verdict: **ACCEPT**, **DEFER**, or **REJECT** — each with a dated rationale.

The goal is the same discipline a mature product team uses: feedback is a first-class input, not a to-do list.

---

## Why this exists

The world's best agent collection for Salesforce is not built by one team in isolation. When an outside assistant, a Trailblazer community member, or a PR reviewer audits our agents and says *"here is what I would improve"*, we owe them two things:

1. **Proof we read it** — a log entry with a timestamp and a summary.
2. **Proof we thought about it** — a verdict (accept / defer / reject), with a reason a human can argue with.

Silent dismissal is worse than rejection. Blind implementation is worse than silent dismissal.

---

## The triage verdicts

| Verdict | Meaning | What happens next |
|---|---|---|
| **ACCEPT** | We agree and will ship. | Linked PR / commit hash. Entry stays in the log forever as provenance. |
| **DEFER** | Good idea, not now. | `revisit_date` set; reviewed every quarter. |
| **REJECT** | We disagree or it conflicts with a principle. | Rationale is required. Entry stays in the log so the next reviewer who suggests the same thing can read *why* we said no. |

Every entry has a **decision owner** — the human (or human-plus-AI pair) who made the call — and a **decided_on** date.

---

## How to file feedback

1. Add a new entry at the top of `FEEDBACK_LOG.md` (reverse chronological).
2. Fill in the template (source, summary, each suggestion with a verdict).
3. If you accept something, link the commit or PR.
4. If you defer, set a `revisit_date`.
5. If you reject, say why. Principles > preferences.

External reviewers (including AI assistants in other IDEs) should include the whole feedback verbatim under `raw_excerpt` so we can re-read it without chasing links.

---

## Review cadence

- **Quarterly:** skim every `DEFER` — have conditions changed? Time to promote to ACCEPT or convert to REJECT with a crisper reason?
- **On every major release:** skim every ACCEPT in the last quarter — did it actually ship? Did it deliver the intended outcome?
- **On receiving similar feedback twice:** upgrade the DEFER to ACCEPT or strengthen the REJECT rationale — repeat signal means we under-weighted the first one.

---

## What this is NOT

- Not a roadmap. (See `MASTER_QUEUE.md` + `.planning/` for that.)
- Not a changelog. (See git history for that.)
- Not a way to punt hard decisions indefinitely — the quarterly cadence forces us to re-confront every DEFER.

---

## File layout

```
feedback/
├── README.md              ← this file
├── FEEDBACK_LOG.md        ← the actual log (reverse chronological entries)
└── archive/               ← entries older than 2 years (by decided_on date)
```

Entries never get deleted. If an entry becomes irrelevant, it stays — the lesson is the audit trail.
