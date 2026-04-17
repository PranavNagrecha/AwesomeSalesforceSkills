# /build-agentforce-action — Scaffold a complete Agentforce action

Wraps [`agents/agentforce-builder/AGENT.md`](../agents/agentforce-builder/AGENT.md). Produces Apex `@InvocableMethod` + topic YAML + agent definition + test class + starter eval.

---

## Step 1 — Collect inputs (ask all five upfront)

Ask:

```
1. Action name (user-facing label)?
   Example: "Summarize Account Cases"

2. Primary sObject the action grounds on?
   Example: Account

3. Actor invoking the action?
   Example: Service Agent / Sales Rep / Customer

4. Intent (what should the action do)?
   One or two sentences. What data does it retrieve / what does it change?

5. Trust constraints?
   Pick any that apply: no-pii-in-prompt, mask-email, no-external-callout,
   require-user-confirmation, audit-every-invocation, rate-limit-per-actor.
   Add free-form constraints as needed.
```

If any of the five is missing, STOP and ask.

---

## Step 2 — Load the agent

Read `agents/agentforce-builder/AGENT.md` fully + the Agentforce skills + `evals/framework.md` + the templates under `templates/agentforce/`.

---

## Step 3 — Execute

Follow the 6-step plan:
1. Classify the action (read-only / write / composite / callout)
2. Generate the Apex action class (subclass `AgentActionSkeleton`, CRUD/FLS via `SecurityUtils`, logging via `ApplicationLogger`)
3. Generate the topic YAML (classifier prompt, scope boundary, grounding sources, confirmation flag)
4. Generate the agent definition JSON
5. Generate the test class (including bulk + runAs + wrong-actor tests)
6. Generate the starter golden eval

---

## Step 4 — Deliver

- Action summary
- Generated files, each as a fenced block labelled with its target path:
  - Apex action class + meta
  - Test class + meta
  - Topic YAML
  - Agent meta XML
  - Golden eval markdown
- Trust checklist (each constraint → where it's enforced)
- Citations

---

## Step 5 — Recommend follow-ups

- `/gen-tests` if additional coverage beyond the scaffold is needed
- `/scan-security` on the action Apex before promoting to production
- Deploy the eval file under `evals/golden/` and run `evals/scripts/run_evals.py`

---

## What this command does NOT do

- Does not deploy.
- Does not run the eval.
- Does not modify existing agents / topics — creates new ones.
- Does not allow callouts when `no-external-callout` is in the trust constraints.
