# LWC TypeScript Migration Examples

## Existing project using native TypeScript tooling

1. Capture installed CLI and Salesforce Extensions versions.
2. Generate a temporary TypeScript Salesforce project with the same installed CLI.
3. Compare its `sfdx-project.json`, `tsconfig.json`, package dependencies, ignore files, and scripts to the target project.
4. Apply the minimum project changes.
5. Migrate one low-coupling bundle.
6. Validate raw `.ts` deployment to a scratch org or approved non-production org.
7. Do not commit disposable `dist` output if the native strategy owns deployment.

## Existing project compiling to JavaScript

Keep `.ts` canonical, run a deterministic clean compile before deploy, and verify generated `.js` cannot be edited independently. The migration packet must show whether generated JS is committed or CI-only and prove a fresh checkout recreates it.

## Safe boundary migration

Convert untyped event handling first:

```ts
import type { LightningInput } from '@salesforce/lightning-types';

handleChange(event: Event): void {
  const input = event.target as LightningInput;
  this.searchTerm = input.value;
}
```

Then type server data separately. Do not cast the entire Apex response merely to clear compiler errors.

## Behavior change deferred

A migration reveals that a custom event uses `composed: true` unnecessarily. Record it as a separate refactor. Preserve the existing flag in the TypeScript-only change so consumers are not broken by an unreviewed API change.
