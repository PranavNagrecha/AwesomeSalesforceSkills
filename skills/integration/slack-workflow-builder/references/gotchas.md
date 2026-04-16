# Gotchas — Slack Workflow Builder

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: “Run a Flow” is not a generic Flow picker

**What happens:** The Slack step appears to list Salesforce flows, but **only autolaunched** flows are valid targets. Picking a familiar **screen** or **record-triggered** flow produces failures or unsupported behavior.

**When it occurs:** During first connector setup or after copying naming from an existing Salesforce automation.

**How to avoid:** Maintain a naming convention for Slack-invoked flows (for example, prefix `AL_Slack_`) and code-review any new **Run a Flow** mapping against Flow metadata (`processType`, `status`).

---

## Gotcha 2: Deployment breaks published Slack workflows

**What happens:** A deployment **renames, deactivates, or deletes** the target flow. Published Slack workflows still reference the old API name until someone edits and republishes them in Slack.

**When it occurs:** CI/CD promotes Flow metadata without a paired checklist for Slack Workflow Builder consumers.

**How to avoid:** Treat Slack workflow definitions as **dependent artifacts**: when Flow API names change, update Slack steps in the same change window and verify **workflow activity logs** in Slack after release.

---

## Gotcha 3: Data visibility is channel-level, not per-Salesforce-user

**What happens:** Outputs from **Run a Flow** are rendered into Slack messages or threads. Anyone who can read the channel sees those values, even if they would fail a field-level security check in Salesforce.

**When it occurs:** Workflows post to **public** channels or **Slack Connect** conversations with external partners.

**How to avoid:** Minimize sensitive fields in Flow outputs, use **private channels** or **DM** workflows where appropriate, and align with the record-preview governance mindset described in slack-salesforce-integration-setup.
