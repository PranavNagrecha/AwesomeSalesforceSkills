---
name: change-management-and-training
description: "Use this skill when planning user adoption, structuring Salesforce training materials, drafting release communications, or running a change impact assessment for a Salesforce rollout or update. Triggers: user adoption plan, training materials, release announcement, change impact, go-live communication, communication plan, training plan by persona, adoption metrics, LoginHistory adoption report, PromptAction, training sandbox, go-live checklist, post-go-live feedback, super user program, pilot group. NOT for org deployment mechanics or sandbox promotion — use admin/change-management-and-deployment. NOT for adoption of an Agentforce or Einstein AI feature — use admin/ai-adoption-change-management. NOT for configuring the in-app prompts themselves — use admin/in-app-guidance-and-walkthroughs."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - User Experience
triggers:
  - "build an adoption and communication plan for a Salesforce go-live"
  - "write the go-live announcement for a Salesforce release"
  - "assess which users are affected by a Salesforce page or process change"
  - "nobody is using the new Salesforce feature we shipped last month"
  - "training deck screenshots do not match what users actually see"
  - "measure Salesforce adoption without just counting logins"
  - "we announced a new field and users say they cannot see it"
  - "which sandbox should we run end-user training in and when"
  - "design role-based training for a Salesforce rollout"
tags:
  - change-management
  - user-adoption
  - training
  - release-communication
  - go-live
inputs:
  - "Description of the Salesforce change or rollout being communicated"
  - "User roles and personas affected by the change"
  - "Go-live date and any phased rollout schedule"
  - "Existing training assets or Trailhead paths (optional)"
outputs:
  - "Change impact assessment by role/persona"
  - "Lintable change-plan artefact (personas, communications, adoption metrics, feedback loop)"
  - "Role-based training plan and material structure"
  - "Release communication template (go-live announcement, What Changed guide)"
  - "Adoption metrics as SOQL queries and report definitions"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Change Management and Training

Use this skill when a Salesforce rollout, major feature release, or org-wide configuration change requires structured user adoption planning, role-based training, and stakeholder communications. This skill produces change impact assessments, training plans, and release communication artifacts — it does not implement the technical change itself.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which user roles are affected and in what way (new screens, changed workflows, removed steps)?
- What is the go-live date and whether the rollout is all-at-once or phased by region/role?
- Are there existing Trailhead trails, in-app guidance walkthroughs, or training videos already available?
- What adoption metric does leadership care about (login rate, record creation volume, pipeline data quality)?

---

## Questions to Ask Before Configuring

Ask these before writing a single message or booking a room. Each one traces to a failure documented in `references/gotchas.md`, and each answer becomes a field in the plan artefact in `references/worked-examples.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which permission set carries the new access, who assigns it, and on what day relative to the announcement?" | `PermissionSetAssignment` records are data created per user, not part of the metadata deploy — a message that names a field before assignment produces a ticket wave (gotcha 7) | The assignment step placed on the comms timeline with an owner, and the count query that verifies it |
| "Which page will each persona actually see — which app, record type, profile and form factor?" | A Lightning page assignment is keyed on all four, so the admin's screenshot may be a different page from the reps' (gotcha 8) | The screenshot matrix, and an explicit "nothing changes for you" message for personas whose record type keeps the old page |
| "Which org will training run in, and when is it refreshed relative to the deploy?" | A sandbox refreshed before the deploy teaches the configuration users are about to lose, and the refresh interval makes the mistake expensive to undo (gotcha 5) | A sequenced refresh date on the persona's training environment row |
| "Does the go-live window cross this instance's seasonal upgrade date?" | The UI, click paths and prompt anchor points can move mid-rollout (gotcha 9) | A recorded upgrade-date check and, if needed, a rollout split either side of the weekend |
| "What behaviour — not what login — tells us this landed?" | `LoginHistory` measures presence; only record counts and `PromptAction` measure behaviour, and list-view usage is not queryable at all (gotcha 3) | Adoption metrics written as SOQL or report definitions, with the pre-go-live baseline captured |
| "Who is affected who never opens a Lightning page?" | Integration and API-only users are broken by the same field change and reached by none of the channels (gotcha 10) | An integration-user persona row, a mapping request instead of an announcement, and an id-based exclusion from the metrics |
| "Who owns each message, and who signs it?" | An unowned row is an unsent message; a message signed by IT about a sales process change is ignored | A named owner per row, which the checker enforces |

What a proper change plan adds over just sending an announcement: the people who are told, the people who are trained, the people who get access, and the people who are measured are provably the same set — and where they differ, the difference is recorded rather than discovered at go-live.

---

## Core Concepts

### Change Impact Assessment

A change impact assessment maps each Salesforce change to the user roles it affects, the current versus future state workflow, and the severity of disruption. Salesforce projects fail adoption when the impact is assessed too late — typically after development is complete and training is an afterthought.

Run the assessment during requirements gathering, not after UAT. The output is a matrix:

| Change | Affected Roles | Current Behavior | New Behavior | Training Required | Communication Priority |
|--------|---------------|-----------------|--------------|-------------------|----------------------|
| New Opportunity stage | Sales Rep, Sales Manager | 6 stages | 8 stages | Yes — field meanings | High |
| Page layout update | Service Agent | Fields scattered | Grouped by task | Yes — guided walkthrough | Medium |
| New validation rule | All users on Account | None | Required fields | No — error message explains | Low |

### User Adoption Planning

Salesforce defines adoption across three dimensions: breadth (are people logging in?), depth (are they using the features?), and quality (is the data clean and complete?). Each requires different interventions.

**Six Levers of Change (Salesforce official framework):** Salesforce training explicitly teaches that communications and technical training alone are insufficient for sustained adoption. Six levers must be addressed simultaneously: Leadership (executives visibly use and champion the system), Ecosystem (peer pressure and social norms reinforce usage), Values (the change connects to what users personally care about), Enablement (users have the skills and tools to change their behavior), Rewards (incentives align with the new behavior, not the old), and Structure (the new way is easier than the old way by design). Assess which levers are missing when adoption is lagging.

Adoption levers available natively in Salesforce:

| Lever | Description |
|---|---|
| In-App Guidance (Walkthroughs) | Step-by-step prompts shown inside the Salesforce UI, configurable without code. Navigate to Setup > In-App Guidance. Target specific pages and user profiles. Use for new features and process changes. |
| Path | Visual stage guidance on records (Opportunity, Lead, Case). Shows key fields and coaching text per stage. Configured per object and record type in Setup > Path Settings. |
| Chatter | Announcements, group updates, polls to surface process changes inside the platform users already use. |
| Adoption Dashboards | The Salesforce Adoption Dashboards package (available on AppExchange, free from Salesforce Labs) provides prebuilt reports on login frequency, record creation, and feature usage by profile. |

### Role-Based Training Structure

Training fails when it is delivered as a generic platform tour. Effective Salesforce training is structured by role and anchored to the tasks that role performs daily.

Recommended structure per role:
1. **Why it changed** — 2-3 sentences on the business reason (not the technical reason)
2. **What is different** — before/after comparison of the specific screens or steps they use
3. **Hands-on exercise** — sandbox or training org walkthrough of their specific scenario
4. **Where to get help** — in-app guidance, Chatter group, help contact

Salesforce Trailhead provides free, official, role-specific learning trails. Use Trailhead Academy trails for common roles rather than building content from scratch for standard platform features.

### Release Communication Templates

Release communication for Salesforce projects follows a different cadence than typical IT releases because many users are non-technical. Announcements must be in business language, role-specific, and tied to a concrete go-live date.

Standard release communication pack:
1. **Executive Summary** (1 paragraph) — what changes, why, and when
2. **Role-Specific What Changed Guide** — per affected role, bullet-point list of what is different
3. **Go-Live Announcement** — email/Chatter post sent day-of, links to training, names the support contact
4. **Post-Go-Live Check-In** — 2-week follow-up asking for feedback, surfacing top issues

---

## Common Patterns

### Pattern: Phased Rollout with Pilot Group

**When to use:** The org has more than 50 affected users or the change significantly alters an existing workflow. Piloting with 5–10 volunteer power users before full rollout reduces go-live risk and generates real testimonials for the broader communication.

**How it works:**
1. Identify 5–10 pilot users (mix of skeptics and enthusiasts, covering each affected role)
2. Run pilot group through training 2 weeks before go-live
3. Gather feedback on training clarity, gotchas, and missing guidance
4. Update training materials and in-app guidance based on pilot feedback
5. Send go-live announcement to full audience referencing pilot feedback: "Our early users loved X"

**Why not skip the pilot:** A full rollout with broken training materials creates a support spike, erodes trust, and is much harder to recover from than a delayed launch.

### Pattern: Adoption Metrics Dashboard

**When to use:** Any rollout where leadership wants to track adoption progress post-go-live.

**How it works:**
1. Install Salesforce Adoption Dashboards from AppExchange (Salesforce Labs, free)
2. Configure report filters by profile to segment by role
3. Define adoption targets per role (e.g., 90% of Sales Reps logging in daily within 4 weeks of go-live)
4. Schedule weekly adoption review meeting for the first 4 weeks post go-live
5. Use Chatter groups or manager escalation for roles below target

**Why not use ad hoc reports:** The Adoption Dashboards package provides prebuilt metrics that Salesforce has validated. Building from scratch takes time and often misses important signals like feature engagement vs. login frequency.

### Pattern: In-App Guidance for Process Changes

**When to use:** A page layout, required field, or workflow step is being added or changed. Users need just-in-time guidance without attending a training session.

**How it works:**
1. Navigate to Setup > In-App Guidance
2. Click "Add" and choose the target Lightning page and prompt type (floating, docked, or walkthrough)
3. Set profile/permission set filters to show the prompt only to affected users
4. Write prompt copy in plain language referencing the business task, not the field name
5. Deactivate the prompt 60 days after go-live (when users are habituated)

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|-----------|---------------------|--------|
| < 20 users affected, minor UI change | In-App Guidance prompt only | Overhead of formal training exceeds impact |
| 20–100 users, new workflow | Role-specific What Changed Guide + 30-min live session | Enough scale for structured training, small enough for live delivery |
| > 100 users or critical process | Full change pack: impact assessment, pilot, role training, adoption dashboard | Large audience and high complexity justify full change management |
| Executive stakeholders need visibility | Adoption metrics dashboard scheduled report | Leadership needs numbers, not anecdote |
| Users reverting to old tools (spreadsheets, email) | Escalation via manager + targeted in-app guidance | Resistance requires reinforcement, not re-training |
| Trailhead trail exists for the feature | Assign trail via myTrailhead or direct link in communications | Do not rebuild what Salesforce already provides for free |

---


## Recommended Workflow

1. **Build the ship list, then the persona list.** Name every metadata piece that deploys and the skill that owns it (`references/worked-examples.md` §1), then derive personas from *who touches the object*, not from who attends meetings — that is what catches the unaffected record type and the integration user.
2. **Assess impact in three columns per persona:** what changes on screen, what changes in process, what permission changes ship. A persona with no entry in any column is a persona who needs a "nothing changes for you" message, not silence (`references/worked-examples.md` §2).
3. **Fill the plan artefact.** Copy the YAML from `references/worked-examples.md` §3 to `<project>/change-plan.yaml` and fill it in: every message gets an audience, channel, `D±n` timing and owner; every persona gets a training format (`none` is a legal, recorded answer) and a training environment.
4. **Sequence the training environment against the deploy.** Deploy to the training sandbox → validate → run labs → deploy to production → refresh the training org. Confirm the seasonal upgrade date with `admin/salesforce-release-preparation` and the refresh window with `devops/sandbox-refresh-and-templates` before committing dates.
5. **Write every adoption metric as a query.** `LoginHistory` for presence, `PromptAction` for guidance engagement, record counts for behaviour (`references/worked-examples.md` §6). Capture the baseline before the deploy. If a metric has no query — list-view usage, for instance — drop it at planning time and say why.
6. **Lint the plan.** `python3 scripts/check_change_management_and_training.py --file <project>/change-plan.yaml --repo-root .` — it fails on a missing owner, a calendar date where a `D±n` offset belongs, an audience that matches no persona, a duplicate id, an adoption metric with no query, or a `reads:` path that does not resolve.
7. **Walk `references/gotchas.md` against the finished plan** before the first message goes out. Most of the ten failures are cheap to fix a week early and expensive to fix on go-live morning.

---

## Review Checklist

Run through these before marking the change management deliverable complete:

- [ ] Change impact assessment completed covering all affected roles
- [ ] Adoption success metrics defined and agreed with stakeholders before go-live
- [ ] Training materials are role-specific (no generic platform tour)
- [ ] In-app guidance configured for any new page layouts or required fields
- [ ] Go-live communication sent at least 5 business days before go-live date
- [ ] Adoption dashboard or report scheduled for weekly review post-go-live
- [ ] Feedback mechanism in place (Chatter group, survey, or named support contact)
- [ ] Post-go-live check-in scheduled for 2 weeks after go-live
- [ ] `change-plan.yaml` passes `scripts/check_change_management_and_training.py`
- [ ] Permission set assignments verified by count *before* any message naming a new field is sent
- [ ] Every persona whose screen does NOT change has been told so explicitly
- [ ] Integration and API-only users have a row, an owner, and an exclusion from the adoption metrics
- [ ] Training-environment refresh is sequenced after deploy validation, and the date is recorded
- [ ] Instance upgrade date checked against the rollout window

---

## Salesforce-Specific Gotchas

1. **Profile targeting on a prompt is the wrong lever** — target the audience with `userAccess` = `SpecificPermissions` or a `uiFormulaRule` custom-permission criterion, so one permission-set assignment opens the field and the guidance together.
2. **A Path is bound to one record type** — the Metadata API allows only one path per record type per object; a new record type starts with no coaching text and inherits none.
3. **Login counts are not adoption** — `LoginHistory` includes OAuth and integration logins, and in an SSO org the human browser login is a SAML value, so the copied `LoginType = 'Application'` filter hides the very users you are measuring.
4. **The permission set deploys; the assignment does not** — `PermissionSetAssignment` records are created per user, so any message naming a new field must land after the assignment runs.
5. **The page you screenshotted may not be the page they see** — the assignment is keyed on app, record type, profile and form factor.
6. **The training sandbox must carry the change** — a refresh timed before the deploy teaches the configuration users are about to lose.

All ten, with the source for each, are in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|----------|-------------|
| Change Impact Assessment Matrix | Table mapping each change to affected roles, before/after behavior, training severity, and communication priority |
| Adoption Plan | Document covering success metrics, training delivery plan, adoption levers, and milestone dates |
| Role-Based What Changed Guide | Per-role bullet list of what is different; written in business language, not technical terms |
| Go-Live Announcement Template | Email/Chatter post template announcing the change, training resources, and support contact |
| Post-Go-Live Check-In Template | 2-week follow-up communication template requesting feedback and surfacing help resources |
| `change-plan.yaml` | The lintable artefact holding personas, communications, adoption metrics and the feedback loop |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | You need the filled-in artefact: impact table, plan YAML, training plan, in-app guidance decisions, adoption queries, feedback loop |
| `references/examples.md` | You want two contrasting rollout narratives (200-agent Service Cloud go-live; a required-field change) and the go-live-day-training anti-pattern |
| `references/gotchas.md` | Before the first message goes out, and whenever a plan looks finished — ten platform behaviours that break rollouts |
| `references/llm-anti-patterns.md` | Reviewing AI-generated change-management output, or self-checking your own |
| `references/well-architected.md` | Justifying the approach to an architect or sponsor; also holds the source list |
| `templates/change-management-and-training-template.md` | Starting a plan from scratch — the blank form of the worked example |
| `scripts/check_change_management_and_training.py` | Linting a finished `change-plan.yaml` |

---

## Related Skills

- admin/requirements-gathering-for-sf — captures the business requirements that drive the change impact assessment
- admin/uat-and-acceptance-criteria — UAT completion is the gate before go-live communications are sent
- admin/change-management-and-deployment — the technical deployment mechanics; this skill owns the human side of the same release
- admin/in-app-guidance-and-walkthroughs — builds the `Prompt` metadata this skill decides the audience and copy for
- admin/salesforce-release-preparation — seasonal upgrade dates, Release Updates triage, Sandbox Preview opt-in
- admin/ai-adoption-change-management — the same practice for an Agentforce or Einstein rollout
- admin/stakeholder-raci-for-sf-projects — who decides and who is consulted; this skill assumes those roles exist
- admin/record-types-and-page-layouts — why a persona's screen may not change at all
- devops/sandbox-refresh-and-templates — refresh intervals and templates for the training org
- devops/release-management — the release train the go-live date sits inside
- devops/release-notes-automation — generates the technical change list this skill translates for users
