# LLM Anti-Patterns

Use these patterns to challenge a proposed migration. The goal is behavior-preserving, toolchain-proven conversion—not merely a repository full of `.ts` files.

## 1. One-shot repository rename

**Mistake:** Convert every LWC bundle before establishing a passing project strategy.

**Why it happens:** Bulk mechanical edits look efficient and produce a dramatic diff.

**Correct form:** Inventory the project, prove one low-coupling pilot bundle through type check, Jest, static analysis, build/deploy, and runtime validation, then migrate in bounded waves with rollback points.

## 2. Stale configuration paste

**Mistake:** Copy `tsconfig.json`, package scripts, ignore rules, or metadata assumptions from another Salesforce tooling generation.

**Why it happens:** TypeScript setup appears generic and online examples age quickly.

**Correct form:** Capture installed CLI, Salesforce Extensions, Node, package manager, API version, and generated-project behavior. Derive the minimum configuration from the target toolchain and document the chosen deployment strategy.

## 3. Dual deployment model

**Mistake:** Commit generated JavaScript while also claiming raw TypeScript is the deployable source, or let different developers use different paths.

**Why it happens:** Native TypeScript rollout and compile-to-JavaScript workflows coexist in official material and existing projects.

**Correct form:** Choose exactly one authoritative source/deploy strategy for this project. Record whether `.ts` or generated `.js` is deployed, who owns generated output, and how CI proves a clean checkout is deterministic.

## 4. Behavior-refactor camouflage

**Mistake:** Change events, public APIs, wire usage, state, DOM behavior, or Apex contracts during the language migration.

**Why it happens:** Types expose design problems and invite opportunistic cleanup.

**Correct form:** Preserve behavior and public contracts in the migration diff. Capture discovered refactors separately with independent acceptance criteria and review.

## 5. `any` migration

**Mistake:** Rename `.js` to `.ts` and annotate every boundary as `any`.

**Why it happens:** It clears compiler errors quickly while retaining old assumptions.

**Correct form:** Type public properties, event targets, custom events, wire/Apex boundaries, state, and helper return values deliberately. Use `unknown` at untrusted boundaries and narrow it before use.

## 6. Assertion laundering

**Mistake:** Use blanket casts such as `as unknown as T`, non-null assertions, or oversized interfaces to silence mismatches.

**Why it happens:** The compiler becomes an obstacle rather than evidence.

**Correct form:** Prove the runtime shape, narrow with guards, model optional/null states, and make casts local with a documented reason. A cast never validates server data.

## 7. Runtime-guarantee claim

**Mistake:** Present TypeScript interfaces as runtime payload validation or security enforcement.

**Why it happens:** Static types improve confidence and can be mistaken for execution-time checks.

**Correct form:** State the compile-time boundary. Validate untrusted Apex, wire, message, URL, storage, and third-party data at runtime where correctness or security depends on shape.

## 8. Metadata rename

**Mistake:** Rename or duplicate `.js-meta.xml` because the implementation file becomes `.ts`.

**Why it happens:** The extension appears coupled to the implementation language.

**Correct form:** Preserve the LWC bundle's metadata filename and public component identity. Validate with the actual toolchain and target environment before changing source conventions.

## 9. Extension-only proof

**Mistake:** Treat editor IntelliSense or a clean Problems panel as migration success.

**Why it happens:** The extension performs helpful background checks that are not necessarily reproduced in CI.

**Correct form:** Run deterministic command-line type checking, Jest, Code Analyzer/ESLint, the declared build/deploy path, and target validation. Record versions and commands.

## 10. Jest-only proof

**Mistake:** Accept passing tests without proving whether Jest executed TypeScript, stale generated JavaScript, or a mocked path that bypasses the changed code.

**Why it happens:** Green tests provide a familiar completion signal.

**Correct form:** Inspect transforms/resolution, clean generated output, introduce a controlled proof during the pilot, and verify coverage/source maps point to the intended canonical source.

## 11. Target-org assumption

**Mistake:** Claim raw TypeScript deployment or a generated configuration is supported because a current template or extension supports it locally.

**Why it happens:** Tooling support is conflated with the project's target release and deployment pipeline.

**Correct form:** Validate against the actual installed toolchain and a scratch or approved non-production target. When official guidance reflects different rollout stages, make the branch explicit and cap confidence until deployment is proven.

## 12. Generated-code editing

**Mistake:** Modify compiled JavaScript directly and lose the change on the next build.

**Why it happens:** Generated output is visible, deployable in some strategies, and may be the first file opened during debugging.

**Correct form:** Mark generated directories, enforce clean generation, add CI drift checks, and direct all edits to canonical TypeScript. Choose whether generated files are committed or CI-only and apply that policy consistently.
