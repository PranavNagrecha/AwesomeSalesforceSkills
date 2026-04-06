# Copado Essentials — Work Template

Use this template when setting up, troubleshooting, or reviewing a Copado Essentials pipeline. Fill in every section before beginning work.

---

## Scope

**Skill:** `copado-essentials`

**Request summary:** (describe what is needed — e.g., "configure a new three-stage pipeline," "diagnose a blocked promotion," "choose between deployment modes")

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md before proceeding.

**Copado Essentials version:**
(check: Setup > Installed Packages > Copado Essentials > version number)

**Deployment mode in use:**
- [ ] Work Items (in-app approvals and conflict resolution)
- [ ] Deployments with Pull Requests (Git-native PR-based promotion)
- [ ] Not yet configured

**Pipeline stages (fill in order, first to last):**

| Stage # | Environment | Salesforce Org | Git Branch | Credential Status |
|---------|-------------|----------------|------------|-------------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

**Git hosting provider:** (GitHub / GitLab / Bitbucket / Azure DevOps)

**User story reference field format example:** (e.g., `US-2024-042` — confirm no spaces or special characters)

**Known inter-story metadata dependencies requiring merge order override:**
(list user stories where promotion sequence matters, or write "None identified")

---

## Approach

Which pattern from SKILL.md applies to this request?

- [ ] Setting Up a Three-Stage Pipeline (new installation)
- [ ] Resolving Merge Conflicts in Work Items Mode (blocked promotion)
- [ ] Merge Order Override (dependency-sequenced promotion)
- [ ] Deployment Mode Selection (Work Items vs. Pull Requests decision)
- [ ] Other: (describe)

**Reason this pattern applies:**

---

## Environment Branch Pre-Check

Before configuring or troubleshooting the pipeline, confirm all environment branches exist in the remote Git repository:

- [ ] `develop` branch exists in remote
- [ ] `staging` branch exists in remote (or equivalent UAT branch name)
- [ ] `main` / `master` branch exists in remote

If any branch is missing, create it before proceeding:

```bash
git checkout -b <branch-name> && git push origin <branch-name>
```

---

## User Story Audit (for promotion issues)

Complete this section when diagnosing a user story that is not promoting correctly.

**User Story Reference:** ____________________

**User Story Reference field populated?** Yes / No

**User Story Task records present?**
- Task count: ______
- Component types listed: ______________________

**Current promotion status:** ____________________

**Conflict indicator present?** Yes / No
- If yes, conflicting component(s): ______________________
- Competing user story reference: ______________________

**Merge order integer set?** Yes / No / Not applicable
- If yes, value: ______

---

## Deployment Mode Decision

Complete this section when helping a team choose between Work Items and Pull Requests mode.

| Factor | Team's Situation | Implication |
|--------|-----------------|-------------|
| Admin Git access | (Yes / No / Some admins) | Work Items if admins need pipeline access without Git |
| Branch protection rules required | (Yes / No) | Pull Requests if Git-native enforcement is required |
| Approval audit trail location | (Salesforce / Git platform) | Drives mode choice |
| PR review workflow already established | (Yes / No) | Pull Requests if team already reviews code in Git |

**Recommended mode:** ____________________

**Rationale:**

---

## Checklist

Work through these before marking the task complete:

- [ ] Copado Essentials managed package is installed and Git repository connection is authenticated
- [ ] All pipeline stages have a unique org credential and a unique Git branch assignment
- [ ] All environment branches (`develop`, `staging`, `main`) exist in the remote Git repository
- [ ] Deployment mode (Work Items or Pull Requests) is confirmed and documented
- [ ] A test user story has been created with a populated reference field, branched, and promoted through at least one stage
- [ ] User Story Task records are confirmed to list the correct metadata components
- [ ] Merge order overrides are set for any inter-story metadata dependencies
- [ ] Conflict resolution procedure is documented for the deployment mode in use

---

## Notes

Record deviations from the standard pattern, emergency bypasses performed, and rationale. Include dates and user story references.

| Date | User Story | Action Taken | Reason | Pipeline State Reconciled? |
|------|------------|--------------|--------|---------------------------|
| | | | | |
