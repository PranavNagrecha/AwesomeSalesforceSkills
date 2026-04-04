# Dynamic Forms and Dynamic Actions — Work Template

Use this template when designing or reviewing a Dynamic Forms or Dynamic Actions configuration.

## Scope

**Object:** (API name of the target object, e.g., `Opportunity`, `My_Custom_Object__c`)

**Record Page Name:** (name of the Lightning record page in Lightning App Builder)

**Request summary:** (what behavior change is needed — e.g., hide Field X unless Status = Active)

---

## Pre-Flight Checks

Before making changes, confirm:

- [ ] Object is supported for Dynamic Forms (custom objects always supported; verify standard objects at the official help article)
- [ ] Org is Enterprise Edition or higher
- [ ] Sandbox is available for testing before production activation
- [ ] Current page layout assignment matrix is documented (which profiles/record types are assigned to which pages)

---

## Context Gathered

| Question | Answer |
|---|---|
| Is the object custom or standard? | |
| What edition is the org? | |
| Is there an existing page layout driving field display? | |
| How many record types does the object have? | |
| Are there mobile users who need offline access? | |
| Are any of the fields sensitive (require FLS restriction)? | |

---

## Field Visibility Matrix

List each field that needs conditional visibility. Leave "Visibility Condition" blank for fields that are always visible.

| Field API Name | Field Label | Visible When | Filter Type | Notes |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

### Filter Type Reference

| Filter Type | Use When |
|---|---|
| Field Value | Show/hide based on a field on the current record |
| Record Type | Show/hide based on record type |
| Profile | Show/hide based on viewing user's profile |
| Permission | Show/hide based on a custom permission |
| Device | Show/hide based on desktop / phone / tablet |

---

## Action Visibility Matrix

List each action that needs conditional visibility. Only applicable if enabling Dynamic Actions.

| Action Label | Action API Name | Visible When | Filter Type | Notes |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

## Migration Plan (if converting from page layout)

1. Open the Lightning record page in Lightning App Builder.
2. Select the "Fields" section component.
3. Click "Upgrade Now" to run the Dynamic Forms migration wizard.
4. Verify all expected fields appear on the canvas after conversion.
5. Apply visibility filters per the Field Visibility Matrix above.
6. If enabling Dynamic Actions:
   - Enable Dynamic Actions in Page Properties.
   - Remove migrated actions from the page layout action section.
   - Add each action as a Dynamic Actions component with the visibility rules from the Action Visibility Matrix.
7. Save the page.
8. Activate the page for the correct app/profile/record type combination.

---

## Testing Checklist

- [ ] Tested as a user in each relevant profile — fields appear as expected
- [ ] Tested with records in each record type — visibility rules trigger correctly
- [ ] Tested with records where field values cross the visibility threshold (e.g., Status changes from Draft to Active — field appears)
- [ ] Confirmed hidden fields remain hidden when conditions are not met
- [ ] Confirmed sensitive fields are also restricted by FLS (tested via API if required)
- [ ] Tested on mobile (if applicable) — documented any limitations
- [ ] Dynamic Actions verified — buttons appear and disappear per conditions

---

## Notes and Deviations

(Record any edge cases, limitations, or workarounds applied during implementation.)
