---
name: change-management-and-training
description: "Use this skill when planning user adoption, structuring Salesforce training materials, drafting release communications, or running a change impact assessment for a Salesforce rollout or update. Triggers: user adoption plan, training materials, release announcement, change impact, go-live communication. NOT for org deployment mechanics or sandbox promotion (use change-management-and-deployment)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - User Experience
triggers:
  - "how do I plan user adoption for our Salesforce rollout"
  - "what should be in a Salesforce training plan for end users"
  - "how do I write a release communication for a Salesforce go-live"
  - "how do I assess the impact of a Salesforce change on users"
  - "our users are not adopting Salesforce, how do I fix that"
  - "how do I structure training materials for different roles in Salesforce"
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
  - "User adoption plan with milestones and success metrics"
  - "Role-based training plan and material structure"
  - "Release communication template (go-live announcement, What Changed guide)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
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
- **In-App Guidance (Walkthroughs)** — step-by-step prompts shown inside the Salesforce UI, configurable without code. Navigate to Setup > In-App Guidance. Target specific pages and user profiles. Use for new features and process changes.
- **Path** — visual stage guidance on records (Opportunity, Lead, Case). Shows key fields and coaching text per stage. Configured per object and record type in Setup > Path Settings.
- **Chatter** — announcements, group updates, polls to surface process changes inside the platform users already use.
- **Adoption Dashboards** — the Salesforce Adoption Dashboards package (available on AppExchange, free from Salesforce Labs) provides prebuilt reports on login frequency, record creation, and feature usage by profile.

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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

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

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **In-App Guidance is profile-gated but not permission-set-gated in older orgs** — In older orgs and certain setups, In-App Guidance filtering may be limited to profile only. If your org uses permission sets as the primary access control model and profiles are generic, prompts may show to users who are not affected by the change. Always test prompt visibility in a sandbox with test users assigned the correct profile before go-live.

2. **Path coaching text is record-type-scoped** — Salesforce Path supports different coaching text per record type (e.g., Enterprise vs. SMB Opportunity stages). If you add a new stage to one record type and copy coaching text from another, the change applies only to the specific record type and picklist combination you configure. BAs frequently configure the "default" record type and assume it propagates — it does not.

3. **Adoption Dashboard login metrics count OAuth API logins** — The Adoption Dashboards package uses the LoginHistory object to measure daily active users. API integrations and connected apps that authenticate using OAuth also appear as logins. This can inflate "active users" metrics. Filter by LoginType = 'Application' (standard browser logins) when measuring human adoption, not total logins.

---

## Output Artifacts

| Artifact | Description |
|----------|-------------|
| Change Impact Assessment Matrix | Table mapping each change to affected roles, before/after behavior, training severity, and communication priority |
| Adoption Plan | Document covering success metrics, training delivery plan, adoption levers, and milestone dates |
| Role-Based What Changed Guide | Per-role bullet list of what is different; written in business language, not technical terms |
| Go-Live Announcement Template | Email/Chatter post template announcing the change, training resources, and support contact |
| Post-Go-Live Check-In Template | 2-week follow-up communication template requesting feedback and surfacing help resources |

---

## Related Skills

- requirements-gathering-for-sf — Use to capture the business requirements that drive the change impact assessment
- uat-and-acceptance-criteria — UAT completion is the gate before go-live communications are sent
- change-management-and-deployment — Handles the technical deployment mechanics; this skill handles the human side
