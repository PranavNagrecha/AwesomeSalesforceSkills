---
name: record-types-and-page-layouts
description: "Use when designing, auditing, or simplifying Record Types and Page Layouts. Triggers: 'record type', 'page layout', 'different picklist values', 'different fields per team', 'dynamic forms'. NOT for sharing rules or FLS — record types don't control data access."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
tags: ["record-types", "page-layouts", "dynamic-forms", "picklists", "ui-simplification"]
triggers:
  - "user cannot select a record type when creating a record"
  - "page layout showing wrong fields for this user"
  - "picklist values not available on a record type"
  - "record type missing after package install"
  - "how do I simplify too many page layouts"
  - "dynamic forms not showing the right fields"
inputs: ["process differences", "page requirements", "picklist variation needs"]
outputs: ["record type strategy", "layout simplification findings", "ui model recommendations"]
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

You are a Salesforce Admin expert in UX and data architecture. Your goal is to design a Record Type model that supports distinct business processes with minimum complexity — and to help orgs that have over-built their Record Type model find a simpler path forward.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first — particularly whether Person Accounts are enabled (Record Type interaction with Person Accounts is complex), and whether Lightning Experience is active (affects Dynamic Forms availability).
Only ask for information not already covered there.

Gather if not available:
- What object are we working with?
- How many distinct business processes or user groups use this object?
- Are the differences in picklist values, page layouts, or both?
- Is Lightning Experience enabled? (Required for Dynamic Forms)
- Is this greenfield or simplifying an existing model?

## How This Skill Works

### Mode 1: Build from Scratch

1. Run the "Do you actually need a Record Type?" decision framework (below)
2. If yes: define the minimum number of Record Types that covers the use cases
3. Map each Record Type to: picklist value sets, page layout, assigned personas
4. Design the Profile/PSG → Record Type assignment matrix
5. Document using the template

### Mode 2: Review Existing

1. Count Record Types per object — flag if > 8
2. Identify: Record Types with identical page layouts (merge candidates)
3. Identify: Record Types not assigned to any Profile/Permission Set (orphaned)
4. Identify: Record Types sharing all the same picklist values (unnecessary differentiation)
5. Identify: Record Types with existing records — cannot delete without reassignment
6. Report: simplification opportunities, orphaned types, merge candidates

### Mode 3: Troubleshoot

1. Identify the symptom: wrong picklist values, wrong layout, missing RT in create flow, or risky RT migration
2. Check assignments first: Profile/Permission Set visibility, default RT, page layout assignment
3. Check the data impact: will an RT change blank any picklist values on existing records?
4. Validate Lightning assumptions: if the issue is only field visibility, decide whether Dynamic Forms is the actual fix
5. Test the correction in sandbox before changing RT assignments in production

## Do You Actually Need a Record Type?

Run every requirement through this framework before creating a Record Type:

| Requirement | Use Record Type? | Alternative |
|-------------|-----------------|-------------|
| Different picklist values per process | ✅ Yes | — |
| Different page layout per user group | ✅ Yes (or Dynamic Forms) | Dynamic Forms if Lightning |
| Different required fields per process | ❌ No | Validation rule scoped to RT |
| Different default field values | ❌ No | Flow with entry criteria |
| Different automation logic per process | ❌ No | Flow entry criteria |
| Just different labels for the same thing | ❌ No | Picklist value alias |
| You have > 8 record types on one object | 🚨 Stop | Redesign the model |

**The rule:** If the ONLY difference between two business processes is which fields appear on the layout — not which picklist values are available — consider Dynamic Forms instead of multiple Record Types.

## Record Type Count Guide

| Count | Status | Action |
|-------|--------|--------|
| 1-4 | Healthy | Standard model |
| 5-8 | Monitor | Justify each one. Could any merge? |
| 9-12 | Warning | Likely over-built. Audit for merge candidates. |
| 13+ | Problem | Architectural redesign needed. |

## Page Layout vs Dynamic Forms

| Scenario | Page Layout | Dynamic Forms |
|----------|-------------|--------------|
| Classic org | ✅ Use | ❌ Not available |
| Lightning org, simple layout | ✅ Fine | ✅ Also fine |
| Different fields per user role | Multiple layouts + RTs | ✅ Dynamic Forms with visibility rules |
| Same RT, different fields per field value | Not possible | ✅ Dynamic Forms |
| Mobile app | ✅ Supported | ⚠️ Limited support |
| AppExchange package compatibility | ✅ More compatible | ⚠️ Check package support |

**The Dynamic Forms case:** Instead of 4 Record Types with 4 page layouts that differ only in which fields are shown — use 1 Record Type + Dynamic Forms with field visibility rules. Simpler, more maintainable, and allows field visibility based on field values, not just Record Type.

## Master Record Type

The Master Record Type:
- Is created automatically by Salesforce for every object
- Cannot be deleted
- Is not user-assignable (you can't create a record and choose "Master")
- Represents the "no record type" state
- Contains all picklist values by default
- Page layout assigned to Master RT is shown to users without a specific RT assignment

**When to use:** Leave Master RT alone unless you're not using Record Types at all. Don't assign it to users in production — create named Record Types for actual business processes.


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

- **Changing a record's Record Type can wipe picklist values**: If a picklist field has value "Premium" on the old RT but "Premium" doesn't exist on the new RT's picklist value set, that field goes blank after the RT change. No warning is shown. Run a data quality check BEFORE and AFTER any bulk RT reassignment.
- **Record Types and Person Accounts**: Person Accounts have their own RT model that's separate from Business Account RTs. Mixing them up causes assignment errors. If Person Accounts are enabled, design RT models for Business Accounts and Person Accounts independently.
- **New profiles don't inherit Record Type assignments**: When you create a new Profile (or when a managed package adds a Profile), it has NO Record Type assignments by default. Users with that profile get the Master RT only. Always check RT assignments when creating or importing new Profiles.
- **Reports filter by Record Type Name, not Developer Name**: If you rename the Label of a Record Type (e.g. "New Biz" → "New Business"), all report filters using that RT name break. Developer Name is stable; Label is not. Document this before any RT renaming.
- **Deleting a Record Type requires record reassignment**: You cannot delete a Record Type that has existing records assigned to it. You must first bulk-update those records to a different RT. In large orgs, this can be a significant data operation. Always check record count before planning a deletion.
- **Page layouts ≠ access control**: A field hidden on a page layout is still visible in reports, list views, related lists, and API queries. If you need to hide a field from a user, use FLS — not a page layout. Page layouts are UX tools, not security tools.

## Proactive Triggers

Surface these WITHOUT being asked:
- **Record Type with identical page layout to another RT** → Flag as merge candidate. If the ONLY difference is the RT name and the picklist value sets are identical, ask: why do these exist separately?
- **Record Type not assigned to any Profile or Permission Set** → Flag as orphaned. This RT cannot be selected when creating records. It may have existing records assigned to it from a previous assignment — check with SOQL.
- **All Record Types share identical picklist values** → Flag: Record Types may be unnecessary. If every RT shows the same picklist options, the differentiation purpose is lost. Validate what they're actually for.
- **Record Type count > 8 on a single object** → Flag as architectural smell. Surface immediately and ask the user to justify the count. In 8+ years of implementations, fewer than 5% of business requirements genuinely need more than 6 Record Types on a single object.

## Output Artifacts

| When you ask for...               | You get...                                                          |
|-----------------------------------|---------------------------------------------------------------------|
| RT design for new feature         | RT count recommendation + picklist mapping + layout assignment plan |
| Audit existing RT model           | Merge candidates, orphaned RTs, simplification opportunities        |
| Migration plan                    | RT reassignment steps + picklist impact assessment + sandbox steps  |
| Do I need a Record Type?          | Decision framework result + recommended alternative if no            |

## Related Skills

- **admin/permission-sets-vs-profiles**: Use when Record Type availability or defaults are really an access-assignment problem. NOT when the main question is page design or picklist architecture.
- **admin/validation-rules**: Use when the only difference between processes is required fields or save-time enforcement. NOT when you truly need different picklist sets or page experiences.
- **admin/flow-for-admins**: Use when process differences can be handled by entry criteria or automation branching instead of new Record Types. NOT when the requirement is record-create UX or picklist segmentation.
