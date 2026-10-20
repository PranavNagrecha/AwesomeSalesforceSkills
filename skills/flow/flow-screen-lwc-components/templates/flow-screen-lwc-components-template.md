# Flow Screen LWC Components — Work Template

Use this template when building a custom LWC for a Screen Flow step.

## Scope

**Skill:** `flow-screen-lwc-components`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answers to the Before Starting questions in SKILL.md:

- Stock-component gap (what the palette or a reactive formula cannot do):
- Consuming flow API version (59.0+ built-in reactivity; 57.0/58.0 need `enableFlowReactiveScreens`):
- I/O contract (property, input/output/both, declared type):
- Validation rule and the cached data it reads:
- Programmatic navigation needed (scanner/kiosk) or user-clicked Next:
- Mobile in scope (UNVERIFIED for FlowScreen; device test needed):

## Approach

Which Common Pattern applies (output via `FlowAttributeChangeEvent`, programmatic Next, reactive pair) and why.

## Checklist

- [ ] `lightning__FlowScreen` target and `<isExposed>true</isExposed>` are in meta.xml.
- [ ] Every admin-facing `@api` property has a `<property>` with a documented `type`.
- [ ] Every `outputOnly` property has a `FlowAttributeChangeEvent` dispatch naming it exactly.
- [ ] `validate()` is a plain synchronous method returning `{ isValid, errorMessage? }`.
- [ ] Navigation events fire only from event handlers, only when listed in `availableActions`.
- [ ] `python3 scripts/check_flow_screen_lwc_components.py --manifest-dir <bundle dir>` exits 0.

## Notes

Deviations from the standard pattern and why:
