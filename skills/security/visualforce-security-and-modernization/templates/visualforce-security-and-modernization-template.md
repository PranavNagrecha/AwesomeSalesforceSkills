# Visualforce Security And Modernization — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `visualforce-security-and-modernization`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the `## Questions to Ask Before Configuring` table in SKILL.md: audience, pinned `apiVersion` per controller, page-action DML, `cspHeader` and external hosts, formula fields, dynamic components, view state size.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

Disposition (`rewrite-lwc` / `harden-in-place` / `leave-alone`) from the Core Concept 3 table, and which Common Pattern applies.

## Checklist

From Recommended Workflow step 3:

- [ ] CSRF switches on (`SessionSettings.enableCSRFOnPost` / `enableCSRFOnGet`; no `csrfProtection="false"` on the page)
- [ ] Every getter returning an sObject queries `WITH USER_MODE` (or the class pins `apiVersion` 67.0+)
- [ ] Controller declares `with sharing` explicitly
- [ ] No DML in `<apex:page action>` methods
- [ ] sObject fields rendered with `<apex:outputField>`, not `<apex:outputText>`
- [ ] `check_visualforce_security_and_modernization.py --manifest-dir <dir>` run after each round

> UNVERIFIED (2026-10-20): the `csrfProtection` page attribute in the checklist appears in no corpus guide; the documented switches are `SessionSettings.enableCSRFOnGet` / `enableCSRFOnPost` (api_meta 264 L129739-129745).

## Notes

Record any deviation from the standard pattern, why it was accepted, and who signed off.
