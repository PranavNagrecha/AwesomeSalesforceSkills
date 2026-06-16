# Agentforce Custom Lightning Types — Work Template

Use this template when overriding an agent action's input/output UI with a LightningTypeBundle.

## Scope

**Skill:** `agentforce-custom-lightning-types`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Action and parameter being customized: (e.g. "Search Flights" action, output)
- Backing Apex class + exposed fields: (e.g. `c__Flight` — airline, price, ...)
- Input or output? → editor.json vs renderer.json
- Target channel(s): lightningDesktopGenAi / lightningMobileGenAi / enhancedWebChat / experienceBuilder
- Packaging context: org (`c/`) or managed package (`isv/`)

## Approach

- Override scope: `"$"` (whole-type) | property-name | `"collection"`
- Pattern from SKILL.md applied and why:

## Bundle plan

```
lightningTypes/<type>/
  schema.json                 -> lightning:type @apexClassType/c__<Class>
  <channel>/
    editor.json | renderer.json -> componentOverrides "$": { definition: c/<lwc> }
lwc/<lwc>/                    -> target lightning__AgentforceInput | ...Output
```

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Action input/output is an Apex class (not a primitive)
- [ ] Apex fields `@AuraEnabled`; class `global`, top-level, `@JsonAccess`
- [ ] schema.json binds via `@apexClassType`, no re-declared fields
- [ ] LWC target matches editor/renderer; `@api value` exposed
- [ ] Channel folder present for every target surface; no renderer.json under experienceBuilder
- [ ] package.xml at API 64.0+; bundle has masterLabel

## Validation

Run the skill checker against your metadata tree:

```bash
python3 scripts/check_agentforce_custom_lightning_types.py --manifest-dir force-app/main/default
```

## Notes

(Record any deviations from the standard pattern and why.)
