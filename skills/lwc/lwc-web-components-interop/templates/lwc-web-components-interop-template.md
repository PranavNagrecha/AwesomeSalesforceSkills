# LWC Web Components Interop — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `lwc-web-components-interop`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answers to the Before Starting questions from SKILL.md:

- Candidate library, and evidence it is a true standard custom element:
- Module format shipped (ESM / UMD / IIFE) — `loadScript` cannot load ESM:
- Org security architecture: Lightning Web Security enabled, or Locker:
- Target surfaces (Lightning app, Experience Cloud, mobile, embedded):

## Approach

Wrapper design: who owns the load, the tag registration, the property contract, and the event renaming:

## Checklist

From the review checklist in SKILL.md, plus the failure modes in `references/gotchas.md`:

- [ ] LWS confirmed enabled — Locker does not support custom elements at all
- [ ] Tag carries `lwc:external` in the template
- [ ] Registration guarded with `customElements.get()` before `define()`
- [ ] Reactive data reaches the element as a property; update path tested, not just first render
- [ ] Non-lowercase events attached with `addEventListener`, re-dispatched lowercase
- [ ] Experience Builder excluded from targets while LWS is enabled
- [ ] Fallback UI when the library fails to load

## Notes

Deviations from the standard pattern, and the reason for each:

