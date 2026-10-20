# LWC Jest Testing With Accessibility — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `lwc-jest-testing-with-accessibility`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answers to the Questions to Ask Before Configuring table in SKILL.md:

- A11y surface of the template (roles, aria-*, tabindex, focus targets, key handlers):
- Async hops between each action and the asserted attribute:
- `jest-axe` in or out, and who owns browser-side contrast checks:

## Approach

Follow the Recommended Workflow in SKILL.md: setup, accessible-name baseline,
ARIA-state tests, focus and keyboard tests, axe decision, checker run.

## Checklist

- [ ] `package.json` has `@salesforce/sfdx-lwc-jest` and `"test:unit": "sfdx-lwc-jest"`.
- [ ] `jest.config.js` spreads `jestConfig` from `@salesforce/sfdx-lwc-jest/config`.
- [ ] Every query goes through `element.shadowRoot`.
- [ ] Every `aria-*` state the template toggles has a test.
- [ ] Focus tests assert `shadowRoot.activeElement`, not `document.activeElement`.
- [ ] `check_lwc_jest_testing_with_accessibility.py --strict` exits 0.

## Notes

Record any deviation from the Recommended Workflow and why.
