---
name: lwc-typescript-migration
description: "Plan, execute, and verify a Lightning Web Components JavaScript-to-TypeScript migration with an explicit Salesforce toolchain strategy, bundle-by-bundle sequencing, Lightning base-component types, generated-output ownership, tests, and rollback. Trigger keywords: migrate LWC to TypeScript, LWC .ts, defaultLwcLanguage, lightning-types, TypeScript LWC build. General TypeScript tutorials and non-Salesforce web applications are outside this package. NOT for performance refactoring unrelated to the language migration — use lwc/lwc-performance."
category: lwc
salesforce-version: "Spring '26+"
well-architected-pillars:
  - Reliability
  - Performance
  - User Experience
  - Operational Excellence
triggers:
  - "migrate our Lightning Web Components from JavaScript to TypeScript"
  - "configure defaultLwcLanguage typescript for a Salesforce DX project"
  - "add Salesforce Lightning base-component types to an LWC project"
  - "decide whether to deploy raw TypeScript or compiled JavaScript for LWC"
  - "audit a mixed JavaScript and TypeScript LWC migration"
tags:
  - lwc
  - typescript
  - migration
  - lightning-types
  - tooling
  - static-analysis
inputs:
  - "Salesforce DX project root, package directories, and current LWC bundles"
  - "Installed Salesforce CLI and VS Code extension versions or generated project template"
  - "Declared deployment strategy: native TypeScript/type stripping or local compile-to-JavaScript"
  - "Current Jest, ESLint/Code Analyzer, build, deployment, and source-control behavior"
outputs:
  - "Bundle inventory and migration sequence with explicit generated-file ownership"
  - "Project configuration and representative migrated TypeScript bundle"
  - "Type-check, unit-test, static-analysis, deployment validation, and rollback evidence"
  - "Migration audit identifying mixed-source collisions, deprecated flags, weak typing, and missing build gates"
dependencies:
  - lwc/lwc-testing
  - lwc/lwc-jest-testing-with-accessibility
  - devops/salesforce-code-analyzer
runtime_orphan: true
runtime_orphan_reason: "No dedicated runtime agent owns JS-to-TypeScript LWC migration as its primary deliverable; existing LWC agents remain build/audit/debug focused."
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-09-01
---

# LWC TypeScript Migration

Migrate Lightning Web Components one bundle at a time while preserving behavior and making the deployment contract explicit. Salesforce's TypeScript tooling changed materially during the Spring '26 rollout: earlier guidance compiled TypeScript locally and deployed JavaScript, while current Salesforce Extensions guidance describes first-class TypeScript projects and server-side type stripping. Pin the installed CLI/extensions/project template and validate the selected path rather than mixing both models.

---

## Start With a Toolchain Decision

Record one strategy for the project or package directory.

| Strategy | Use when | Source of truth | Deployment artifact | Required proof |
|---|---|---|---|---|
| Native TypeScript / type stripping | The installed Salesforce project tooling creates TypeScript projects, `defaultLwcLanguage: "typescript"` is supported, and the target validation environment accepts `.ts` bundles | `.ts` source; generated local output is disposable | Raw LWC bundle containing `.ts` | Type check, project deploy preview/validate, scratch or approved non-production deployment |
| Local compile to JavaScript | The project or target toolchain follows the Spring '26 compile-before-deploy path, or CI deliberately owns transpilation | `.ts` source plus deterministic build config | Generated `.js` bundle | Clean build from a fresh checkout, diff/manifest of generated output, deploy validation |
| JavaScript remains canonical | Tooling, package, test, or delivery constraints are not ready | `.js` source | `.js` | Document why migration is deferred and what unlocks it |

Do not infer strategy from file extensions alone. Check the installed CLI command help, Salesforce Extensions version, generated project template, target API/release support, and an actual deployment validation. Record contradictions between current official pages rather than hiding them.

---

## Project Preconditions

Before renaming a component:

1. Identify all package directories and every LWC bundle with `.js`, `.ts`, templates, styles, metadata, tests, mocks, and shared modules.
2. Capture a passing baseline: Jest, accessibility checks, ESLint/Code Analyzer, deployment validation, and representative behavior.
3. Inspect `sfdx-project.json`, `package.json`, lockfile, `tsconfig.json`, `.forceignore`, `.gitignore`, `.vscode/settings.json`, and CI workflows.
4. Confirm whether generated JavaScript is committed, ignored, or created only in CI. One owner must be explicit.
5. Verify the installed Salesforce project template rather than copying a stale `tsconfig.json` from a blog.
6. Create a migration branch and rollback point. Do not combine language migration with state-management, API, styling, or behavior redesign.

---

## Configuration Contract

### Salesforce DX project

For current first-class tooling, `sfdx-project.json` can declare the default language used by component generation:

```json
{
  "packageDirectories": [
    { "path": "force-app", "default": true }
  ],
  "defaultLwcLanguage": "typescript",
  "sourceApiVersion": "67.0"
}
```

Treat the shown API version as an example, not a universal minimum. Preserve the project's supported version and validate feature behavior against the target org and installed tools.

For a new project, prefer the installed template when the CLI exposes the option:

```bash
sf project generate --name sample-typescript-project --lwc-language typescript
```

Run `sf project generate --help` first in automation because option availability is tied to the installed CLI/plugin version.

### TypeScript and Lightning types

Current official Spring '26 guidance identifies TypeScript and `@salesforce/lightning-types` as development dependencies for Lightning base-component typing:

```bash
npm install --save-dev typescript @salesforce/lightning-types
```

Use the generated Salesforce `tsconfig.json` as the base. Current Salesforce Extensions guidance uses Salesforce-specific configuration, including `erasableSyntaxOnly`, standard decorators, ES module output, and a generated `.sfdx` base config. Do not hand-copy those settings across tool versions without regenerating or verifying them.

### Generated output policy

Choose exactly one:

| Policy | Source control | CI responsibility | Guardrail |
|---|---|---|---|
| Raw TypeScript deployment | Commit `.ts`; ignore disposable `dist` or generated JS | Type-check and deploy/validate `.ts` | Fail if same-stem `.js` shadows `.ts` |
| Compile before deployment | Commit `.ts`; generated `.js` either reproducibly committed or generated in CI | Clean compile before every deploy | Fail if generated JS differs from clean build |
| Transitional mixed project | Bundle-level canonical source is declared | Run both JS and TS validation | Fail when one bundle contains competing same-stem `.js` and `.ts` |

Never allow developers to edit generated JavaScript by hand.

---

## Recommended Workflow

For each bundle:

1. Record current public API (`@api` properties/methods), events, wire adapters, Apex calls, navigation, message channels, DOM queries, and tests.
2. Rename only the implementation file from `.js` to `.ts`; retain the bundle's `.js-meta.xml` metadata filename.
3. Add types at boundaries first: public properties, method parameters/returns, custom-event detail, wire/Apex data, and DOM/base-component targets.
4. Keep runtime behavior unchanged. Do not add optional chaining, refactor state, change event payloads, or rewrite error handling unless a separate change owns it.
5. Replace broad `any` with interfaces, discriminated unions, `unknown` plus narrowing, or generated/declared data shapes.
6. Type-check, run unit/accessibility tests, run Code Analyzer/ESLint, and validate deployment before moving to the next bundle.
7. Compare public API, emitted events, rendered states, and error paths to the baseline.

---

## Salesforce Boundary Types

TypeScript proves compile-time shape; Salesforce data and DOM values still require correct boundary handling.

### Lightning base components

Use `@salesforce/lightning-types` for supported base-component element types instead of maintaining local approximations.

```ts
import { LightningElement } from 'lwc';
import type { LightningInput } from '@salesforce/lightning-types';

export default class ContactEditor extends LightningElement {
  handleChange(event: Event): void {
    const input = event.target as LightningInput;
    const value: string = input.value;
    // Preserve the component's existing behavior here.
    void value;
  }
}
```

A cast asserts a relationship; it does not validate runtime data. Cast only at a boundary you control and keep the target narrow.

### Custom events

```ts
type SaveDetail = {
  recordId: string;
  source: 'manual' | 'automation';
};

const event = new CustomEvent<SaveDetail>('save', {
  detail: { recordId: this.recordId, source: 'manual' },
  bubbles: true,
  composed: false
});
this.dispatchEvent(event);
```

Preserve existing event names, detail shape, bubbling, and composition during migration. Changing them is an API change.

### Apex and wire data

A TypeScript interface does not force Apex or UI API data to match it. Define only fields actually selected/returned, handle nullable values, and add runtime narrowing when the source is not guaranteed.

```ts
type AccountSummary = {
  Id: string;
  Name: string;
  AnnualRevenue?: number | null;
};

function isAccountSummary(value: unknown): value is AccountSummary {
  if (typeof value !== 'object' || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return typeof candidate.Id === 'string' && typeof candidate.Name === 'string';
}
```

Do not use `as AccountSummary` to conceal an unverified server payload.

---

## Testing and Static Analysis

A migration is complete only when all existing behavior remains covered.

| Gate | What to prove |
|---|---|
| Type check | No TypeScript errors under the committed/generated Salesforce config |
| Jest | Existing tests pass; tests and mocks resolve the TypeScript source strategy |
| Accessibility | Existing axe/accessibility assertions remain active |
| ESLint / Code Analyzer | TypeScript rules run for `.ts`; LWC rules still cover applicable sources |
| Clean build | Fresh checkout plus lockfile produces the same deployable artifact |
| Deploy validation | Selected strategy is accepted by a disposable or approved non-production target |
| Behavioral smoke | Public properties/methods, events, wire/Apex states, and errors match baseline |

Salesforce Code Analyzer v5's ESLint engine supports TypeScript analysis. ApexGuru is unrelated; it scans Apex `.cls` and `.trigger` files only.

---

## Migration Review Checklist

- [ ] Toolchain versions and selected deployment strategy are recorded
- [ ] Official guidance contradiction is resolved for this project by a real validation
- [ ] Generated output has one owner and cannot be hand-edited
- [ ] No bundle has competing same-stem `.js` and `.ts` sources
- [ ] `.js-meta.xml`, public API, event contracts, and runtime behavior are preserved
- [ ] Base-component types come from `@salesforce/lightning-types` where supported
- [ ] Apex, wire, event, and DOM boundaries are typed without blanket assertions
- [ ] `any`, `@ts-ignore`, unsafe double casts, and non-null assertions are reviewed
- [ ] Type check, Jest, accessibility, Code Analyzer/ESLint, clean build, and deploy validation pass
- [ ] Rollback restores the last JavaScript baseline without generated-file ambiguity

---

## Audit Command

Run the bundled project checker:

```bash
python3 skills/lwc/lwc-typescript-migration/scripts/check_lwc_typescript_migration.py --project path/to/sfdx-project
```

Use `--strict` to treat unsafe typing warnings as failures. The checker does not deploy; it inspects configuration, bundle collisions, deprecated preview flags, dependencies, scripts, and high-confidence source anti-patterns.

---

## Related Skills

- `lwc/lwc-testing` — preserve unit-test behavior and mocks across migration.
- `lwc/lwc-jest-testing-with-accessibility` — keep accessibility checks in the migrated suite.
- `lwc/lwc-component-architecture` — refactor component boundaries only after language migration is stable.
- `devops/salesforce-code-analyzer` — configure current TypeScript/LWC static analysis.
- `lwc/lwc-typescript-migration` does not decide project release authority or deploy to production.

See the references for migration examples, contradictory toolchain guidance, and common TypeScript-specific failures.
