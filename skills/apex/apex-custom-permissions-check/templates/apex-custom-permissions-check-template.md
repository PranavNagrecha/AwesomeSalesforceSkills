# Apex Custom Permissions Check — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `apex-custom-permissions-check`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting and Questions to Ask Before Configuring tables from SKILL.md here.

- Setting / configuration:
- Known constraints:
- Failure modes to watch for:

## Approach

Which pattern from SKILL.md applies (service entry point, LWC render hint, validation-rule gate)? Why?

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] `FeatureManagement.checkPermission` at every gated Apex entry point
- [ ] Granted and denied branches both tested under `System.runAs`

## Notes

Record any deviations from the standard pattern and why.
