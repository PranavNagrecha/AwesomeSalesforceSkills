# /request-skill — Report a Missing Skill

Use this when you know a skill is missing but don't want to build it yourself.
Takes 4 questions, checks existing coverage, and adds the request to the release plan (`RELEASES.yaml`) with `scripts/release_plan.py add`. `/add-to-backlog` does the same for any ask.

---

## Step 1 — Ask the 4 questions

Ask the user exactly these questions. Ask all 4 upfront, not one at a time:

```
1. What Salesforce task does this skill cover?
   (Describe it as a task someone performs, not a feature name)
   Example: "Configure case assignment rules in Service Cloud"
   Not: "Case assignment rules"

2. Who is this skill for?
   Admin / BA / Developer / Data / Architect

3. Which Salesforce cloud does this apply to?
   Core Platform / Sales Cloud / Service Cloud / Experience Cloud /
   Marketing Cloud / Revenue Cloud / Field Service / Health Cloud /
   Financial Services Cloud / Nonprofit Cloud / Commerce Cloud /
   Agentforce / OmniStudio / CRM Analytics / Integration / DevOps

4. What's the main problem it solves or mistake it prevents?
   (One sentence)
```

---

## Step 2 — Check for existing coverage

```bash
cd /path/to/SfSkills
python3 scripts/search_knowledge.py "<task from question 1>"
python3 scripts/search_knowledge.py "<task from question 1>" --domain <domain>
```

**If `has_coverage: true`:**
Show the user the existing skill. Ask: "Does this cover what you need, or is your use case different enough to warrant a new skill?"
- If covered → stop. Point them to the existing skill.
- If different → continue with a clear disambiguation note.

**If `has_coverage: false`:**
Continue.

---

## Step 3 — Determine domain and skill name

Map role → domain:
```
Admin / BA role → admin
Architect role → architect
Developer role → most specific: apex / lwc / flow / integration / devops
Data role → data
OmniStudio topics → omnistudio
Agentforce topics → agentforce
Security topics → security
```

Generate a kebab-case skill name from the task:
- "Configure case assignment rules" → `case-assignment-rules`
- "Set up territory management for Sales Cloud" → `sales-cloud-territory-management`
- "Apex callout error handling patterns" → `callout-error-handling`

Rules:
- All lowercase, hyphens only
- No cloud prefix unless the skill is cloud-specific and ambiguous without it
- Keep it short — 2-4 words is ideal

---

## Step 4 — Write the description

Compose a one-sentence description:

```
"Use when [trigger scenario — what the practitioner is doing when they need this].
Triggers: [2-3 keyword phrases]. NOT for [explicit exclusion]."
```

Example:
```
"Use when configuring automatic routing of new cases to queues or users.
Triggers: 'set up case routing', 'auto-assign cases', 'case queue assignment'.
NOT for opportunity routing or lead assignment rules."
```

The "NOT for..." is mandatory. Without it, the skill will be rejected by the Validator.

---

## Step 5 — Add it to the release plan

Confirm the flags with `python3 scripts/release_plan.py add --help`, then:

```bash
python3 scripts/release_plan.py add --size S --title "<domain>/<skill-name>" \
  "<description from Step 4> (requested by user)"
```

The script slots the ask into a release by size. Run `python3 -m pytest tests/test_releases.py -q` afterwards; if it fails, report that and do not commit.

---

## Step 6 — Confirm with the user

Report back the item id and release that `release_plan.py add` printed:
```
✓ Skill request added to the release plan: <domain>/<skill-name>
  Item: <id>   Release: <version>
```

`/start-building` works the plan; `python3 scripts/release_plan.py status` shows where it stands.

---

## What This Command Does NOT Do

- It does not build the skill. Building goes through Content Researcher → Role Agent → Validator.
- It does not guarantee a build timeline — the release plan sets the order.
- It does not accept requests for skills that already exist — check first, always.
