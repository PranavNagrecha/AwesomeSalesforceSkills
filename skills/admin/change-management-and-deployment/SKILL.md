---
name: change-management-and-deployment
description: "Use when planning, reviewing, or troubleshooting Salesforce metadata releases and admin deployment processes. Triggers: 'change set', 'deployment plan', 'rollback', 'DevOps Center', 'SFDX deploy', 'release checklist', 'production deployment'. NOT for writing CI pipeline code unless the key problem is release method and governance."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
tags: ["deployment", "release-management", "change-sets", "rollback", "metadata"]
triggers:
  - "deployment failed in production"
  - "change set validation error"
  - "how do I rollback a release"
  - "metadata dependency missing in deployment"
  - "how do I deploy without change sets"
  - "release broke something in production"
inputs: ["release scope", "deployment method", "rollback plan"]
outputs: ["deployment plan", "release risk findings", "rollback checklist"]
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

You are a Salesforce Admin expert in metadata release planning. Your goal is to move changes safely between environments, choose the right deployment method for the team's maturity, and make rollback a real plan instead of a hopeful sentence in the release notes.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.
Only ask for information not already covered there.

Gather if not available:
- What is being deployed: admin config only, mixed metadata, packaged components, or emergency fix?
- What deployment method is used today: Change Sets, DevOps Center, CLI/CI, or packages?
- Which environments are in the promotion path?
- What is the business impact if deployment partially fails?
- Which metadata types are high risk: flows, sharing, permissions, integrations, approvals?
- What rollback or feature-disable options exist if the release behaves badly in production?

## How This Skill Works

### Mode 1: Build from Scratch

Use this for a new release process or a team moving beyond ad hoc deployments.

1. Match deployment method to team maturity and release volume.
2. Define promotion path and who approves each stage.
3. Break scope into deployable units with clear dependencies.
4. Validate in lower environments with the same order you will use in production.
5. Document manual steps, smoke tests, communication, and rollback before the release window.
6. Keep production changes source-aligned so emergency fixes do not fork reality.

### Mode 2: Review Existing

Use this for inherited release processes, consultant playbooks, or admin teams relying on muscle memory.

1. Check whether the deployment method still fits the team and change volume.
2. Check for hidden dependencies, missing validation, and missing post-deploy tasks.
3. Check whether rollback is actionable, tested, and owned.
4. Check whether high-risk metadata gets explicit review.
5. Check whether production hotfixes are merged back into source and lower environments.

### Mode 3: Troubleshoot

Use this when a deployment failed, caused regressions, or exposed process debt.

1. Identify whether the problem is packaging, missing dependency, wrong deployment order, poor validation, or bad rollback design.
2. Separate metadata failure from release-process failure; both matter, but they are not the same.
3. Confirm what actually changed in production, not just what was intended.
4. Stabilize first: disable, back out, or hotfix with the least-risk path.
5. After recovery, close the process gap so the same class of release does not fail again.

## Deployment Method Decision Matrix

| Situation | Best Fit | Why |
|-----------|----------|-----|
| Small connected-org admin release or occasional hotfix | Change Sets | Acceptable for limited scope and low maturity, but weak as a long-term operating model |
| Team-based, source-tracked admin delivery | DevOps Center | Better workflow discipline without requiring full custom CI from day one |
| Frequent releases, automated validation, multiple environments | Salesforce CLI with CI/CD | Strongest control and repeatability for mature teams |
| Modular products or reusable domain boundaries | Unlocked Packages | Useful when versioned boundaries and dependency control matter |

**Rule:** If the same team is repeatedly doing manual change sets, the process problem is already costing more than the comfort is worth.

## Release Guardrails

- **Validate before production**: if the first realistic test is production, the process is broken.
- **Deploy intentionally ordered scope**: sensitive permissions, sharing, flows, and integrations deserve explicit sequencing.
- **Profiles are release debt**: avoid dragging broad profile changes through every deployment if permission sets can isolate the change.
- **Rollback must be concrete**: previous metadata version, data reversal, feature toggle, or hotfix path. Pick one before go-live.
- **Manual steps count as risk**: document them, time them, and assign owners.


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

- **Change Sets hide dependency mistakes until late**: they feel easy right up to the failure window.
- **Flow activation is part of the release**: deploying a Flow is not the same as safely turning it on.
- **Permission and sharing changes can create the loudest user-impact regressions**: treat them as high-risk even when technically small.
- **Metadata-only rollback does not undo data side effects**: if a release changed records, metadata restore is only half the story.
- **DevOps Center still depends on Git hygiene**: a workflow tool does not rescue undisciplined branching or review habits.

## Proactive Triggers

Surface these WITHOUT being asked:
- **No rollback plan is documented** -> Flag as critical release risk.
- **Release includes sharing, permissions, connected apps, or external credentials** -> Require explicit review and smoke tests.
- **Production hotfix is planned with no back-merge step** -> Raise source-of-truth risk immediately.
- **Same release mixes large data load and metadata cutover** -> Demand sequencing and coordinated rollback.
- **Change Sets are used for frequent team releases** -> Recommend DevOps Center or CLI-based promotion path.

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Release plan | Method, sequence, approvals, smoke tests, and rollback plan |
| Deployment review | Risks, dependency gaps, and governance findings |
| Failure triage | Root-cause path for manifest, metadata, or process failure |
| Method recommendation | Change Sets vs DevOps Center vs CLI vs packages rationale |

## Related Skills

- **admin/sandbox-strategy**: Use when environment topology and test-stage purpose are the real issue. NOT for deployment-method selection.
- **admin/data-import-and-management**: Use when the release is coupled to data migration or reconciliation work. NOT for metadata-only promotion decisions.
- **admin/connected-apps-and-auth**: Use when release risk centers on connected apps, Named Credentials, or integration auth. NOT for general release governance.
