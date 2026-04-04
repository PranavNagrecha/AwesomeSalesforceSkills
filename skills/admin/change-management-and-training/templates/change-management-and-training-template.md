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

## Notes

(Record deviations from the standard plan and their justification)
