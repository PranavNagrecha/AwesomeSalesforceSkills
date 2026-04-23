# /debug-lwc — Diagnose a live LWC failure

Wraps [`agents/lwc-debugger/AGENT.md`](../agents/lwc-debugger/AGENT.md). Takes a bundle + a symptom, returns a ranked hypothesis list, read-only diagnostic probes, and a proposed fix.

---

## Step 1 — Collect inputs

Ask:

```
1. Path to the LWC bundle directory?
   Example: force-app/main/default/lwc/accountDetail

2. Symptom — what's happening, in as much concrete detail as you can give (≥ 10 words)?
   Example: "Record page tile renders blank — no console error — but handleRecord logs the expected payload."

3. Optional — paste any error text, stack trace, or Lightning Inspector event.

4. Optional — where does it reproduce?
   record-page / flow-screen / quick-action / experience-cloud / app-page / home-page / utility-bar / local-jest

5. Optional — which files did you change most recently?

6. Optional — may the agent suggest temporary console.log / debugger; probes? (y/N)
```

---

## Step 2 — Load the agent

Read `agents/lwc-debugger/AGENT.md` fully + the cited LWC skills and `templates/lwc/`.

---

## Step 3 — Execute

Follow the 5-step plan:
1. Parse the bundle and classify the symptom (Data / Render / Event / Exposure / Style / Datatable / Quick action / Performance / Runtime error).
2. Emit a ranked hypothesis list keyed to the axis — each hypothesis cites a specific skill.
3. Produce diagnostic probes — grep / console / skill-local checker / network / (optional) transient instrumentation.
4. Propose a fix for the top-ranked hypothesis as a before/after block.
5. Cross-axis follow-ups — bundle-local sibling smells the investigation surfaced.

---

## Step 4 — Deliver

- Symptom classification
- Ranked hypotheses with skill citations
- Diagnostic probes (read-only unless `allow_transient_edits=true`)
- Proposed fix (before/after)
- Related likely-broken patterns
- Confidence (HIGH / MEDIUM / LOW) + Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/audit-lwc` — once the immediate bug is fixed, run a full static pass on the bundle.
- `/build-lwc` — if the fix implies a ground-up rewrite.
- `/gen-tests` / `/scan-security` — if the backing Apex is the real offender.

---

## What this command does NOT do

- Does not modify bundle files — proposes diffs only.
- Does not run the bundle, deploy, or run Jest. Probes are user-executed.
- Does not scope across multiple bundles — one bundle + one symptom per invocation.
- Does not replace `/audit-lwc` for a full static audit.
