# Well-Architected Notes — DataWeave for Apex

## Relevant Pillars

- **Performance** — DataWeave runs inside the Apex governor envelope; heap and CPU planning is part of the design, not an afterthought. The choice to use DataWeave vs hand-rolled Apex is largely a performance/maintainability tradeoff.
- **Reliability** — A registered, declarative `.dwl` script is more robust to schema drift than a hand-rolled DOM/Map walker. The Apex code stays small and the change-surface for new fields is one line.

## Architectural Tradeoffs

- **DataWeave-for-Apex vs MuleSoft Anypoint** — When a MuleSoft license already exists, complex transformations belong off-platform: better tooling, no Apex governor limits, and centralized integration governance. DataWeave-for-Apex earns its place when you need a transformation *inside* a Salesforce transaction (trigger, Queueable, REST class) and pulling MuleSoft into the call path adds unacceptable latency or operational cost.
- **DataWeave-for-Apex vs hand-rolled Apex** — Use DataWeave when field count >15 or the source has nested arrays, attribute-vs-element XML quirks, or "one or many" repeats. Use hand-rolled Apex for trivial reshapes where the script registration and call overhead exceed the maintainability gain.
- **In-line vs registered scripts** — Apex only supports deployed scripts (`DataWeaveResource` metadata, `api_meta.txt` 264 L52106–52120). The tradeoff is "more files for the smallest transform" vs "single source of truth for the spec." On any transformation that will be called from more than one place, the registered script wins by default.

## Anti-Patterns

1. **Treating DataWeave as a license-free MuleSoft replacement** — The transformation language is the same; the runtime, deployment model, and operational guarantees are not. Don't migrate orchestration / connector / SLA-bound integrations from MuleSoft into Apex DataWeave wholesale.
2. **Storing the script as a static resource** — `createScript` loads `.dwl` metadata deployed as `DataWeaveResource` (262: `apexrefguide.txt` L155951); a static resource is not that, and static-resource cache control has no bearing on DataWeave.
3. **Catching `System.DataWeaveScriptException` and discarding the message** — The platform's diagnostic detail is in the message; collapsing to a generic exception with no log line is the difference between a 5-minute fix and a 5-day incident.

## Official Sources Used

- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm — Summer '26 (262) copy: `DataWeave.Script` and `DataWeave.Result` are the namespace's only classes (`salesforce_apex_reference_guide.txt` L155814–155830); `createScript` loads a deployed `.dwl` (L155940–155951); `DataWeaveScriptException` is in the System exception list (L214945). No `ExecuteException` or `ScriptException` exists in the namespace.
- Metadata API Developer Guide (Winter '27, 264) — `DataWeaveResource`: `.dwl` suffix in the `dw` folder, API 58.0+, fields `apiVersion` (required), `isGlobal`, `isProtected` (`api_meta.txt` L52106–52142).
- Apex Developer Guide (Winter '27, 264) — scripts created as metadata, generated `DataWeaveScriptResource` classes, `System.DataWeaveScriptException`, unsupported content types, API 53.0 class floor, 50-script and 100,000-character limits (`salesforce_apex_developer_guide.txt` L26822–26823, L26870–26888, L26979–26986).
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm — DataWeave-for-Apex section, governor-limit interactions.
- Apex Developer Guide (Winter '27, 264) — DataWeave scripts enforce "the same heap and CPU limits on the executing code" (`salesforce_apex_developer_guide.txt` L26823–26824); total heap 10 MB sync / 25 MB async (L19780), a release-level change absent from the API 68.0 versioned list (L45118–45129); nonproduction opt-out `ApexSettings.enableEnforceSummer26ApexHeapLimit`, Winter '27 only (`api_meta.txt` 264 L113855–113862).
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html — when to transform on-platform vs off-platform.
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Performance and Reliability framing.
