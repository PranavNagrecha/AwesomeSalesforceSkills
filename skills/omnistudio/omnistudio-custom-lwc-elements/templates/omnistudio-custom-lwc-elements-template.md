# OmniStudio Custom LWC Elements — Work Template

Use this template when working on tasks in this area. Fill in each section before writing any code.

---

## Scope

**Skill:** `omnistudio/omnistudio-custom-lwc-elements`

**Request summary:** (describe the custom element the user needs — what UX requirement cannot be met by the standard OmniScript element)

**OmniScript host:** (OmniScript type and subtype that will contain the custom element)

---

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding.

- **OmniStudio runtime:** [ ] Native OmniStudio (`enableOaForCore = true`) — use `omnistudio/pubsub` | [ ] Managed package (vlocity_cmt / vlocity_ins / vlocity_ps) — use `vlocity_cmt/pubsub`
- **Custom element type needed:** [ ] Custom LWC Element (scalar/field-level output) | [ ] Custom Merge Map Element (structured nested object output)
- **Custom validation required:** [ ] Yes — must subscribe to `omniscriptvalidate` | [ ] No — only `omniupdatebyfield` output needed
- **Apex data needed inside the element:** [ ] Yes — will use imperative Apex in `connectedCallback` | [ ] No

---

## Field Contract

Define the input/output field names before writing any code. These names are case-sensitive and must match exactly in both the LWC and the OmniScript designer configuration.

| Direction | OmniScript Data Key | LWC Property / Event Key | Notes |
|---|---|---|---|
| Input (OmniScript → LWC) | | `omniJsonData.<key>` | Restore in `connectedCallback` |
| Output (LWC → OmniScript) | | Key in `omniupdatebyfield` payload | Must match OmniScript designer output mapping |

---

## Pattern Selection

Which pattern from SKILL.md applies? (Choose one)

- [ ] **Custom LWC Element with `omniupdatebyfield`** — for scalar or flat field-level output
- [ ] **Custom LWC Element with custom validation** — for elements that block step navigation
- [ ] **Custom Merge Map Element with `omnimerge`** — for structured nested object output

Reason: (explain why the standard OmniScript element cannot satisfy the requirement)

---

## Implementation Checklist

Track implementation progress:

- [ ] LWC component created with correct namespace
- [ ] `@api omniJsonData` declared (not `@track`)
- [ ] `@api omniOutputMap` declared
- [ ] `connectedCallback` implemented — restores state from `omniJsonData`
- [ ] `disconnectedCallback` implemented — unregisters all pubsub listeners
- [ ] No `@wire` adapters used; server data loaded imperatively in `connectedCallback`
- [ ] Pubsub import uses correct namespace for this org's runtime
- [ ] `pubsub.fireEvent(this.omniOutputMap, ...)` used (not `dispatchEvent`)
- [ ] `omniupdatebyfield` event keys match field contract exactly (case-sensitive)
- [ ] If validation: `omniscriptvalidate` registered and unregistered symmetrically
- [ ] If merge map: `omnimerge` event used (not `omniupdatebyfield`)
- [ ] LWC deployed to org without errors
- [ ] OmniScript designer step configured with component API name, input mapping, output mapping
- [ ] OmniScript activated
- [ ] Forward navigation tested — values captured in data model
- [ ] Backward navigation tested — values restored when returning to step
- [ ] Checker script run: `python3 skills/omnistudio/omnistudio-custom-lwc-elements/scripts/check_omnistudio_custom_lwc_elements.py --manifest-dir force-app/main/default`

---

## OmniScript Designer Configuration

Record the configuration entered in the OmniScript designer for the custom element step:

- **Element type:** (Custom LWC Element | Custom Merge Map Element)
- **Component API name:** (e.g., `c/myCustomElement` or `myns/myCustomElement`)
- **Input mappings:** (list each mapping: OmniScript data key → LWC property)
- **Output mappings:** (list each mapping: LWC event key → OmniScript data destination)

---

## Testing Notes

- Tested forward navigation: [ ] Yes | [ ] No
- Tested backward navigation (state restoration): [ ] Yes | [ ] No
- Tested validation rejection (if applicable): [ ] Yes | [ ] No | [ ] N/A
- Checker script result: [ ] No issues | [ ] Issues found (list below)

Issues found by checker:

(list any issues and resolution)

---

## Deviations from Standard Pattern

(Record any deviations from the patterns in SKILL.md and the reason for each)
