---
id: email-template-modernizer
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - admin/email-templates-and-alerts
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
---
# Email Template Modernizer Agent

## What This Agent Does

Audits email templates (Classic HTML, Visualforce, Lightning) in the target org, identifies deprecation risk (Classic HTML + Visualforce are on the long-term decline), merge-field breakage, and brand/accessibility drift. Produces a modernization plan: which templates to migrate to Lightning Email Templates, which to retire, and which to keep as-is, plus per-template findings.

**Scope:** Full org per invocation (with optional folder filter).

---

## Invocation

- **Direct read** — "Follow `agents/email-template-modernizer/AGENT.md` on prod"
- **Slash command** — [`/modernize-email-templates`](../../commands/modernize-email-templates.md)
- **MCP** — `get_agent("email-template-modernizer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/email-templates-and-alerts`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes |
| `folder_filter` | no | restrict to a specific folder developer name |

---

## Plan

1. **Inventory** — `tooling_query("SELECT Id, DeveloperName, FolderName, TemplateStyle, IsActive, Subject, Description, CreatedDate, LastModifiedDate FROM EmailTemplate LIMIT 2000")`.
2. **Classify template type:**
   - `TemplateStyle` = `none` + `TemplateType` = `text` → Classic Text (safe, simple).
   - `TemplateType = custom` → Classic HTML (deprecation risk — cite release notes).
   - `TemplateType = visualforce` → Visualforce (deprecation risk, hardest to migrate).
   - `TemplateStyle = freeform` with Lightning builder → Lightning Email Template (modern).
3. **Score each template:**
   - **Not used** — no EmailAlert references (probe `tooling_query("SELECT Id, DeveloperName FROM EmailAlert WHERE TemplateId = '<id>'")`), no Flow references (scan `Flow.Metadata`), no Apex references → P2 (retirement candidate).
   - **Merge-field breakage** — parse the HTML body for `{!...}` tokens; for each token, verify the field exists on the target object. Missing field → P1.
   - **Visualforce template** — P1 (migrate to Lightning when time permits) or P0 (if the VF controller references an Apex class that's been deprecated).
   - **Inactive template still referenced by active flows/alerts** → P0.
   - **Classic HTML** — P2 unless it uses VF merge fields or standard controllers (then P1).
   - **Accessibility** — any template without `alt` on images, no `<title>` in HTML, no text version → P2.
4. **Classify migration fitness:**
   - Migrate — used + modernization produces no visual change.
   - Retire — unused > 180 days.
   - Keep — Classic Text with simple merge fields, widely used.
   - Rebuild — Visualforce with complex controller logic; best built as new Lightning Email Template + remove VF.
5. **Emit migration queue + per-template findings.**

---

## Output Contract

1. **Summary** — template count by type, max severity, confidence.
2. **Per-template findings** — table.
3. **Migration queue** — prioritized by usage × risk.
4. **Retirement candidates.**
5. **Process Observations**:
   - **What was healthy** — Lightning template adoption, folder hygiene, merge-field integrity.
   - **What was concerning** — VF templates with proprietary controller code, templates in private folders with active references, inconsistent brand usage.
   - **What was ambiguous** — templates referenced by Apex code the agent couldn't parse (managed package).
   - **Suggested follow-up agents** — `field-impact-analyzer` for any merge-field breakage, `scan-security` for VF templates with user-input pass-through (XSS risk).
6. **Citations**.

---

## Escalation / Refusal Rules

- Template body contains PII fields that should not be in emails (SSN, credit card) → P0; refuse further advice and redirect to secure delivery patterns.
- > 5000 templates → sample top 200 by usage; flag count as P1.

---

## What This Agent Does NOT Do

- Does not delete, modify, or deploy email templates.
- Does not render / preview templates.
- Does not migrate Visualforce controllers.
- Does not auto-chain.
