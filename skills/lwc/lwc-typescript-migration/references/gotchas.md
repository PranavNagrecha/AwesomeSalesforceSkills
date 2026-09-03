# LWC TypeScript Migration Gotchas

## Official guidance reflects more than one rollout stage

Spring '26 developer guidance described local compilation and JavaScript deployment. Current Salesforce Extensions development documentation describes first-class TypeScript project generation and server-side type stripping. Pin versions and prove the path in the target environment; do not splice configuration from both models.

## `.js-meta.xml` does not become `.ts-meta.xml`

The component metadata filename remains the LWC bundle's `.js-meta.xml` file even when the implementation is TypeScript.

## TypeScript does not validate Salesforce data at runtime

A type assertion changes the compiler's belief, not the payload. Apex, wire, message-channel, storage, and event inputs can still be null or malformed.

## Same-stem JS and TS can create ambiguous ownership

A bundle containing hand-authored `component.ts` and `component.js` with the same role is a migration defect unless the JS is deterministic generated output and tooling guarantees which file deploys.

## Decorator settings are toolchain-sensitive

Current Salesforce-generated configuration uses standard decorators and Salesforce-specific type-stripping options. Copying a generic TypeScript config with legacy decorator settings can produce misleading editor/build behavior.

## Jest passing is not enough

A transform can execute generated JavaScript while TypeScript source is stale or untested. Confirm which file the test runner resolves and run the type checker separately.

## Base-component types and similarly named Lightning Types are different concepts

`@salesforce/lightning-types` supplies TypeScript definitions for Lightning base components. Do not confuse that package with Agentforce/JSON-schema "Lightning Types" product documentation.

## Migration can silently alter public APIs

Narrowing an `@api` property's accepted type, changing custom-event detail, or adding default values can break parent components even when local tests pass.
