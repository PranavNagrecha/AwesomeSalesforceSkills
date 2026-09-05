# Change Management and Training — Work Template

Use this template when planning and executing a Salesforce rollout change management process.

---

## Scope

**Skill:** `change-management-and-training`

**Project / Change:** (describe the Salesforce change being rolled out)

**Go-Live Date:** (target date)

**Rollout Type:** [ ] All-at-once  [ ] Phased by region  [ ] Phased by role

---

## Change Impact Assessment

Complete this table for every user role affected by the change.

| Change | Affected Role | Current Behavior | New Behavior | Training Required? | Communication Priority |
|--------|--------------|-----------------|--------------|-------------------|----------------------|
| | | | | Yes / No | High / Medium / Low |
| | | | | Yes / No | High / Medium / Low |
| | | | | Yes / No | High / Medium / Low |

---

## Adoption Success Metrics

Define measurable targets before go-live. Agree with stakeholders.

| Metric | Target | Measurement Method | Baseline (pre-go-live) |
|--------|--------|-------------------|----------------------|
| Login rate (% of affected users logging in daily) | ___% by week 4 | Adoption Dashboard / LoginHistory report | |
| Feature engagement (e.g., cases created via Salesforce vs. email) | | | |
| Data quality (required field completion rate) | ___% | Custom report on target fields | |

---

## Training Plan

### Role: [Role Name]

**Training Format:** [ ] Live session  [ ] Self-paced  [ ] In-App Guidance  [ ] Trailhead trail

**Training Environment:** [ ] Sandbox  [ ] Training org  [ ] Production demo

**Delivery Date:** (at least 1 week before go-live)

**Training Outline:**
1. Why this is changing (2 min — business reason only)
2. What is different — before/after walkthrough (10 min)
3. Hands-on exercise: [describe scenario] (20 min)
4. Q&A and where to get help (10 min)

**Training Materials:**
- [ ] What Changed Guide (role-specific, bullet-point format)
- [ ] Trailhead trail: [trail name and URL]
- [ ] In-App Guidance walkthrough: [page and prompt name]

---

## Release Communication Plan

### Communication 1: Pre-Go-Live Announcement (5 business days before)

**Audience:** [list roles]

**Channel:** [ ] Email  [ ] Chatter  [ ] Both

**Subject:** Salesforce Update on [DATE]: [One-line description of change]

**Template:**
> Hi [Role] team,
>
> On [DATE], we are updating Salesforce to [brief description of change — 1 sentence].
>
> **What is changing for you:**
> - [bullet: specific change 1]
> - [bullet: specific change 2]
>
> **What you need to do before go-live:**
> - [action item, if any]
>
> **Training resources:**
> - [link to What Changed Guide]
> - [Trailhead trail link]
>
> **Questions?** Contact [name] in [Chatter group link] or reply to this email.
>
> [Your name]

---

### Communication 2: Go-Live Day Announcement

**Audience:** All affected users

**Channel:** Chatter (company-wide or group)

**Template:**
> [Change name] is live today! 🎉
>
> [1-sentence description of what changed and why it matters to the business.]
>
> If you have questions, [name] is available in [Chatter group] today.
> Training resources: [link]

---

### Communication 3: Post-Go-Live Check-In (2 weeks after go-live)

**Audience:** All affected users

**Channel:** Email or Chatter

**Template:**
> Hi team,
>
> It has been two weeks since [change name] went live. Thank you for making the transition!
>
> **How's it going?** Share feedback in [Chatter group] or fill out this 2-question survey: [link]
>
> **Top questions we have heard:**
> - [FAQ 1 and answer]
> - [FAQ 2 and answer]
>
> Training resources remain available at: [link]

---

## Checklist

- [ ] Change impact assessment completed for all affected roles
- [ ] Adoption metrics defined and baseline captured
- [ ] Training delivered at least 1 week before go-live
- [ ] In-App Guidance configured and tested in sandbox
- [ ] Pre-go-live announcement sent 5 business days before
- [ ] Go-live announcement sent on go-live day
- [ ] Adoption dashboard/report scheduled for weekly review
- [ ] Post-go-live check-in scheduled for 2 weeks after go-live
- [ ] Feedback loop in place (Chatter group or survey)

---

## The Lintable Plan Artefact

The prose sections above are for humans. This block is the machine-checkable record of the
same plan. Save it as `change-plan.yaml` beside this document and lint it with:

```bash
python3 scripts/check_change_management_and_training.py --file change-plan.yaml --repo-root .
```

A filled-in version of exactly this shape is in `references/worked-examples.md` section 3.

```yaml
change_plan:
  id: CM-                         # unique id for this change
  title: ""
  deploy_date: ""                 # YYYY-MM-DD; every 'when' below is relative to this
  release_window_check: ""        # instance upgrade date checked? see admin/salesforce-release-preparation
  owner: ""
  status: planned                 # planned | in-progress | complete | blocked | cancelled

personas:
  # One row per group who TOUCHES THE OBJECT, not per group who attends meetings.
  # Include the unaffected (they need a "nothing changes" message) and the
  # API-only users (they need a mapping request). training_format: none is a
  # legal, recorded answer.
  - id: P-
    label: ""
    headcount: 0
    screen_change: ""
    process_change: ""
    permission_change: ""
    training_format: hands-on-lab # hands-on-lab | live-demo | self-paced-video |
                                  # in-app-guidance | trailhead-trail | quick-reference | none
    training_env: ""              # which org, and when it is refreshed relative to the deploy
    owner: ""
    status: planned
    reads: []                     # repo paths the plan depends on; the checker resolves them

communications:
  # Every row: audience, channel, D-relative timing, owner. Managers before their teams.
  # A message naming a new field must land AFTER the permission set is assigned.
  - id: MSG-01
    audience: P-                  # a persona id, or 'all'
    channel: email                # email | chatter | chatter-group | slack | in-app-guidance |
                                  # town-hall | manager-cascade | intranet | survey
    when: D-10                    # D-10 | D0 | D+14 — never a calendar date
    owner: ""
    subject: ""
    status: planned

adoption_metrics:
  # If it cannot be written as a query or a report definition, it will not be measured.
  # Presence: LoginHistory. Guidance engagement: PromptAction. Behaviour: record counts.
  # List-view usage has no query — do not promise it.
  - id: AM-01
    label: ""
    source: ""                    # LoginHistory | PromptAction | <sObject>
    query: ""
    target: ""                    # capture the baseline BEFORE the deploy
    owner: ""
    status: planned

feedback_loop:
  - id: FB-01
    channel: chatter-group
    audience: P-
    when: D0
    owner: ""
    status: planned
```

---

## Notes

(Record deviations from the standard plan and their justification)
