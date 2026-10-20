# Flow Screen Input Validation Patterns — Work Template

Use this template when designing or auditing the validation of a screen flow's inputs.

## Scope

**Skill:** `flow-screen-input-validation-patterns`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md.

- Component type per input (InputField, LargeTextArea, PasswordField, picklist-style, custom component):
- Required inputs and the valid-value contract per input:
- Cross-field and cross-screen dependencies:
- Flow API version and reactivity expectation:
- Object-level validation rules on the fields the flow writes:
- Multilingual org?:
- Accessibility reviewer:

## Approach

Which pattern from SKILL.md applies (per-input rule, cross-field rule on the second field, reactive validation, screen-level Decision), and why.

## Checklist

- [ ] Every required input has `isRequired` (not on DisplayText or a boolean input)
- [ ] Every formatted InputField, LargeTextArea or PasswordField has a `validationRule` returning BOOLEAN with an `errorMessage`
- [ ] Cross-field rules sit on the second (dependent) field
- [ ] No Decision after a screen validates that screen's own inputs
- [ ] Custom components validate themselves; no `validationRule` is placed under them
- [ ] Object-level validation rules checked for consistency with the screen rules
- [ ] `check_flow_screen_input_validation_patterns.py --manifest-dir` run with no ERROR

## Notes

Record any deviation from the standard pattern and why.
