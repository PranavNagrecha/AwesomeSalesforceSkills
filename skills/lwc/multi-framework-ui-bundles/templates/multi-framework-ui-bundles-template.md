# Multi-Framework UI Bundles — Work Template

Use this template when building or reviewing a React app packaged as a UIBundle
(Salesforce Multi-Framework, Open Beta).

## Scope

**Skill:** `multi-framework-ui-bundles`

**Request summary:** (fill in what the user asked for)

## Beta Go/No-Go (complete FIRST)

- Target org type: scratch org / sandbox / ~~production~~ (beta apps cannot deploy to production)
- Org default language is English: yes / no (non-English-default orgs are excluded in beta)
- Setup: Salesforce app domain enabled under **React Development with Salesforce Multi-Framework**: yes / no
- Requires React on a *Lightning page* (micro-frontend)? → closed pilot (Spring 2026) only; flag it
- Verdict: GO / NO-GO (if NO-GO, route to LWC — `lwc/*` skills)

## Context Gathered

- App concept + surface: App Launcher (`CustomApplication`) | external site (`Experience`)
- Data needs: GraphQL reads / Apex via SDK `fetch()` / UI-API context
- Agent conversation needed? → embed ACC (Beta, LWCI on Lightning Out 2.0)
- API version floor: 66.0+ (67.0+ for `CustomApplication` target)

## Bundle plan

```
force-app/main/default/uiBundles/<app>/
  <app>.uibundle-meta.xml   -> masterLabel + version + isActive (required),
                               description, target: CustomApplication | Experience
  ...built assets only      -> <= 2,500 files; no node_modules/, no .env
```

Scaffold: `sf template generate ui-bundle` (Multi-Framework SDK + Vite + Vitest +
shadcn/ui + Tailwind CSS preconfigured; local dev on http://localhost:5173).

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Beta go/no-go recorded above; no production promise made
- [ ] Setup enablement confirmed in the target org
- [ ] Meta XML has masterLabel / version / isActive; no deprecated `AppLauncher` target
- [ ] Manifest at API 66.0+ (67.0+ for CustomApplication)
- [ ] Bundle ships built output only; file count under the 2,500 cap
- [ ] All data access via `createDataSDK()` — no tokens/OAuth in app code
- [ ] ACC embed (if any) flagged as Beta; Lightning-page embedding flagged as closed pilot

## Validation

Run the skill checker against your metadata tree:

```bash
python3 scripts/check_multi_framework_ui_bundles.py --manifest-dir force-app/main/default
```

## Notes

(Record any deviations from the standard pattern and why.)
