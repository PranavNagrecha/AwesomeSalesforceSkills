# Changelog

All notable changes to this skills library are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/):
- **Major** — breaking changes to skill structure or agent interfaces
- **Minor** — new skills, new agents, new templates
- **Patch** — fixes, content updates, gotcha additions

---

## [Unreleased]

### Planned
- `skills/apex/soql-security` — SOQL injection prevention + FLS enforcement
- `skills/apex/governor-limits` — Governor limit patterns and async offloading
- `skills/flow/fault-handling` — Fault connectors, error handling, bulkification
- `skills/security/fls-crud` — FLS, CRUD, WITH SECURITY_ENFORCED, stripInaccessible
- `agents/code-reviewer` — Full implementation with Python checker scripts

---

## [0.3.0] — 2026-03-13

### Added (from Cursor rules analysis)
- `skills/apex/trigger-framework/` — Single-trigger pattern, handler architecture, recursion guard, Custom Metadata activation bypass; full SKILL.md, references, templates
- `skills/lwc/lifecycle-hooks/` — Lifecycle hooks, wire service, memory leak prevention, LWS constraints; full SKILL.md, references, templates
- `skills/omnistudio/integration-procedures/` — IP build pattern, propertySetConfig, HTTP action config, null guards, failure handling; full SKILL.md, references, templates

### Updated
- `standards/code-review-checklist.md` — Added: dangerous system permissions table, recursion guard + activation bypass (Trigger), sharing test with System.runAs() (Tests), NavigationMixin + ShowToastEvent + cross-component DOM + Static Resources (LWC), Get Records selectivity + duplicate automation check + screen flow navigation (Flow), OmniStudio section
- `skills/admin/permission-sets-vs-profiles/SKILL.md` — Added dangerous system permissions table (ViewAllData, ModifyAllData, ManageUsers, AuthorApex, CustomizeApplication, ManageAuthProviders) and Government Cloud / CMS ARC-AMPE compliance section

---

## [0.2.0] — 2026-03-13

### Added
- `skills/admin/permission-sets-vs-profiles/` — Full skill: SKILL.md, examples, gotchas, well-architected, template
- `skills/admin/validation-rules/` — Full skill: SKILL.md, examples, gotchas, well-architected, template
- `skills/admin/flow-for-admins/` — Full skill: SKILL.md, examples, gotchas, well-architected, template
- `skills/admin/record-types-and-page-layouts/` — Full skill: SKILL.md, examples, gotchas, well-architected, template
- `skills/admin/reports-and-dashboards/` — Full skill: SKILL.md, examples, gotchas, well-architected, template

---

## [0.1.0] — 2026-03-13

### Added
- Repository foundation and directory structure
- `CLAUDE.md` — Full repo instructions for Claude Code
- `README.md` — Public-facing overview
- `SKILL-AUTHORING-STANDARD.md` — Authoritative skill authoring guide
- `CONTRIBUTING.md` — Contribution process and review criteria
- `CHANGELOG.md` — This file
- `agents/code-reviewer/` — Agent definition and SKILL.md
- `agents/org-assessor/` — Agent definition and SKILL.md
- `agents/skill-builder/` — Agent definition and SKILL.md
- `agents/release-planner/` — Agent definition and SKILL.md
- `commands/review.md` — `/review` slash command
- `commands/new-skill.md` — `/new-skill` slash command
- `commands/assess-org.md` — `/assess-org` slash command
- `commands/release-notes.md` — `/release-notes` slash command
- `standards/naming-conventions.md` — Salesforce naming standards
- `standards/code-review-checklist.md` — Master review checklist
- `standards/well-architected-mapping.md` — WAF pillar reference
- Skeleton `skills/` directories for all 9 domains
- Skeleton `templates/` directories for apex, lwc, flow, agentforce
- `docs/adr/` and `docs/guides/` directories

### Notes
- Seed release. Foundation only — no skills populated yet.
- All agent SKILL.md files operational; Python checker scripts pending.
