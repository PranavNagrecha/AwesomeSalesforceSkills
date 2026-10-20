# Guest User Security Audit — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `guest-user-security-audit`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answers to the Questions to Ask Before Configuring table in SKILL.md:

- Sites in scope and the guest profile behind each:
- Classes reachable from guest, with their `apiVersion`:
- Guest user sharing rules and their criteria:

## Approach

Walk the Recommended Workflow in SKILL.md in order: sites, profiles,
sharing rules, Apex, Run-As-Guest, endpoint probes, prioritised report.

## Checklist

- [ ] Every site's guest profile audited, not just one.
- [ ] API Enabled and Access Activities unchecked on each guest profile.
- [ ] Every guest user sharing rule has a written business justification.
- [ ] No guest-reachable class is `without sharing`; bare classes read against their `apiVersion`.
- [ ] No `WITH SECURITY_ENFORCED` left in guest-reachable classes.
- [ ] Records owned by a guest user reassigned to an internal user.
- [ ] `check_guest_user_security_audit.py` run on the source tree.

## Notes

Record any deviation from the Recommended Workflow and why.
