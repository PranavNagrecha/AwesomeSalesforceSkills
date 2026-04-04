# Custom Permissions — Work Template

Use this template when working on a custom permissions task. Fill in each section before starting implementation.

---

## Scope

**Skill:** `custom-permissions`

**Request summary:** (describe what the user asked for — what feature needs to be gated, or what access check needs to be added)

---

## Context Gathered

Answer these before writing any metadata or code:

- **Custom permission API name:** (must start with a letter; alphanumeric + underscore only)
- **Custom permission label:** (human-readable; appears in permission set editor)
- **Platform contexts that will check the permission:**
  - [ ] Apex (`FeatureManagement.checkPermission`)
  - [ ] Validation rule (`NOT($Permission.X)` in AND condition)
  - [ ] Formula field (`$Permission.X`)
  - [ ] Flow (formula resource of type Boolean)
  - [ ] Visualforce (`{!$Permission.X}`)
  - [ ] Connected App (OAuth gate)
- **Permission sets that will carry this permission:** (list all)
- **Users or personas who should receive the permission:** (list or describe)
- **Is this a new permission or modifying an existing one?**

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Feature Gate for Beta or Graduated Rollout
- [ ] Admin-Only Bypass in Validation Rules
- [ ] Conditional UI Visibility Gate in LWC
- [ ] Other: _______________

Why this pattern:

---

## Metadata Checklist

- [ ] Custom permission created in Setup (or `customPermissions/*.customPermission-meta.xml` authored)
- [ ] Permission set XML updated with `<customPermissions>` node
- [ ] All permission sets that need this permission have been updated
- [ ] Metadata committed to source control

## Apex / Formula Checklist

- [ ] `FeatureManagement.checkPermission('API_Name')` used in all Apex guards
- [ ] `$Permission.API_Name` used in all formula/validation rule references
- [ ] Apex unit tests have permission set assignment in `@TestSetup`
- [ ] Both positive (has permission) and negative (no permission) test cases exist
- [ ] `System.runAs(testUser)` wraps the code-under-test in permission-gated test methods

## Flow Checklist

- [ ] Formula resource of type Boolean created with value `$Permission.API_Name`
- [ ] Decision element conditions reference the formula resource variable, not the raw `$Permission` syntax

---

## Deployment Checklist

- [ ] Custom permission metadata included in deployment package
- [ ] All dependent permission sets included in deployment package
- [ ] Apex classes with updated guards included
- [ ] Validation rule updates included
- [ ] `check_custom_permissions.py` run on the post-deploy metadata to confirm assignments

---

## Notes

Record any deviations from the standard pattern and why:

---

## Reference Syntax

| Context | Syntax |
|---|---|
| Apex | `FeatureManagement.checkPermission('My_Custom_Permission')` |
| Validation rule bypass | `AND(NOT($Permission.My_Custom_Permission), /* rule conditions */)` |
| Formula field | `$Permission.My_Custom_Permission` |
| Flow formula resource | `$Permission.My_Custom_Permission` (used as resource value, type Boolean) |
| Visualforce | `{!$Permission.My_Custom_Permission}` |
| Permission set XML | `<customPermissions><enabled>true</enabled><name>My_Custom_Permission</name></customPermissions>` |
