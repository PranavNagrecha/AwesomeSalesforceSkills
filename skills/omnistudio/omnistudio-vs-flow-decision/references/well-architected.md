# Well-Architected Notes — OmniStudio vs Flow Decision

## Relevant Pillars

- **Operational Excellence** — Primary pillar, and the one that decides this. On
  the branches where OmniStudio is a candidate at all, it usually wins a
  capability comparison; what it loses on is operating cost, and every term of
  that cost is invisible in a feature table. Deployment mechanism (DataPacks, or
  the Metadata API after a Setup switch is enabled). Setup prerequisites nobody
  discovers until the release gate. Introspection limits — `OmniProcess`,
  `OmniDataTransform`, and `OmniDataTransformItem` are documented "For internal
  use only", so governance tooling over them is narrower than over Flow. And the
  term that dominates on a five-year horizon: who can maintain it after the
  people who built it move on.

- **Adaptable** — The choice determines who can change the thing later. Flow's
  audience is every admin in the org; OmniStudio's is a specialised subset. That
  gap compounds at the layers that change most often — a record page is edited
  far more frequently, by far more people, than a fourteen-step guided journey —
  which is why the UI-composition decision deserves a different answer from the
  journey decision even inside the same capability. A decision that optimises
  build-time fit and ignores change-time audience is optimising the smaller
  number.

- **Reliability** — Mixed designs are correct and common, and their failure mode
  is concentrated at the seam. An OmniScript calling a Flow, or a Flow calling an
  Integration Procedure, crosses an ownership boundary as well as a technical one,
  and the failure contract across it is the part most often left undefined. A
  Flow fault path cannot meaningfully explain an unhandled error raised in the
  other tool to an end user, so a callee that returns a structured status rather
  than throwing is usually the only workable answer — and that is a design
  decision, not an implementation detail.

- **Performance** — Both tools sit inside the same platform governor limits, so
  the tool choice rarely moves performance on its own. Two things do. First, the
  branch: OmniStudio has no before-save equivalent, and before-save
  record-triggered Flow writes the field in the save the trigger already pays for
  rather than issuing a second one — so building that requirement in OmniStudio
  costs a save on every record forever. Second, configuration: Enhanced Runtime
  Performance is documented as making "Omnistudio communicate[] with the
  Salesforce Platform with in-platform capabilities instead of through Apex
  calls", which means a performance measurement taken in one org may not transfer
  to another with different switches.

## Architectural Trade-offs

**Capability fit versus maintainability.** OmniScript is genuinely better at long
branching journeys with save-and-resume and cross-step validation; Screen Flow
becomes hard to reason about well before step fourteen. Against that, Flow skills
are common and transferable and OmniStudio skills are neither. An org with one
person who can maintain an OmniScript has a single point of failure described as a
platform capability. The defensible position is to state both halves — "OmniScript
fits this shape better and we are using Screen Flow, because of X and Y, revisit
when they are resolved" — which is reversible in a way that a bare verdict is not.

**Per-layer choice versus one tool per capability.** Deciding UI, orchestration,
and data shaping separately produces better answers and a more complex system: an
OmniScript over Flow side-effects has two deployment mechanisms, two debugging
surfaces, and a documented seam. Picking one tool for the whole capability is
simpler to operate and forces at least one layer into the wrong tool. Mixed is
usually right; the cost is that the boundary becomes a first-class artifact you
have to maintain.

**Data Mapper versus Flow record operations.** For simple reads and writes, a Data
Mapper is an extra artifact, an extra deployment concern, and an extra thing to
learn, for no benefit — Flow's Get and Update Records are simpler in every
dimension. Where an external system dictates a nested JSON contract, the position
inverts: the Transform type performs "intermediate data transformations without
reading from or writing to Salesforce", which makes the payload contract a named,
versionable artifact, and expressing the same reshape in Flow formulas is
genuinely worse. The threshold is whether the shape is dictated from outside.

**FlexCard versus Lightning Record Page.** FlexCard buys real reuse across
surfaces and behaviours a record page cannot express — actions from a central
designer, IP-powered save chains, state shared across cards. It costs the ability
of any admin to change the panel in App Builder, and it moves the artifact onto
the Omnistudio deployment path. At the layer that changes most often, that is an
expensive trade for a single-surface panel.

**Standard runtime versus managed package runtime.** The standard runtime removes
a managed-package dependency, puts Omnistudio components on the Metadata API
alongside everything else, and gives faster documented Apex entry points.
Migration is a documented three-phase project, now assisted by the Omnistudio
Migration Assistant, and it is not something to start because one capability needs
a decision. What *is* actionable inside this decision: if a migration is in
flight, new capability should go into something outside its scope, because
anything built on the source runtime enlarges the migration you are trying to
finish.

**Rewriting versus leaving alone.** Consistency across an org's automation is a
real value and rewrites are how you get it. They also consume the budget new
capability needed and reintroduce defects that were fixed years ago, in exchange
for a consistency nobody outside the architecture team experiences. Migrate on the
next substantial change to a capability, not on a platform decision.

## Anti-Patterns

1. **Deciding before routing.** `automation-selection.md` has branches — before-save
   record-triggered work, high-volume batch — where OmniStudio is not a candidate
   at all. Running the tree first turns some of these conversations into
   non-conversations.

2. **One verdict for the whole capability.** UI, orchestration, and data shaping
   are three decisions, and mixed answers are normal.

3. **Treating "the org has OmniStudio" as "the org can operate OmniStudio".**
   The second is a staffing fact and it decides more outcomes than the first.

4. **Managed-package assumptions on a standard-runtime org**, or the reverse.
   Deployment, Apex entry points, and the extension model all differ.

5. **Discovering the deployment mechanism at the release gate.** "Can this
   pipeline promote this artifact today" is a gate on the decision, not a task
   after it.

6. **Building new OmniStudio on the runtime you are migrating away from.** Every
   hour spent is an hour that will be spent again, and the artifact teaches the
   team the idioms they are supposed to be leaving.

7. **FlexCard as the default record-page composition tool.** The layer that
   changes most often is the worst place to narrow the audience who can change it.

8. **Mixed designs with no boundary contract.** Two owners, one interface, no
   written failure contract is the standard shape of a production incident.

9. **Writing to `OmniProcess` or `OmniDataTransform`.** "For internal use only…
   Don't perform any create, edit, or delete operations on this object."

10. **A feature matrix presented as a decision.** The terms that decide it —
    maintainer availability, pipeline readiness, migration state, neighbouring
    implementations — are the ones a feature matrix has no column for.

## Official Sources Used

- Salesforce Help — Omnistudio Settings (the standard-runtime Setup switches: Omnistudio Metadata API Support, Managed Package Runtime, Managed Package Designer, Deploy Custom Lightning Web Components, Omnistudio SLDS 2 Theme, Data Mapper Versioning, Omni Global Auto Number, and Enhanced Runtime Performance — "Omnistudio communicates with the Salesforce Platform with in-platform capabilities instead of through Apex calls") — https://help.salesforce.com/s/articleView?id=xcloud.os_omnistudio_settings.htm&language=en_US&type=5
- Salesforce Help — Enable Omnistudio Metadata API Support (Omnistudio Metadata covers `OmniProcess` (OmniScript and Integration Procedure), `OmniDataTransform` (Data Mapper), and `OmniUiCard` (FlexCard); "To deploy and retrieve Omnistudio standard objects with Salesforce Metadata API, enable the Omnistudio Metadata setting") — https://help.salesforce.com/s/articleView?id=sf.os_enable_omnistudio_metadata_api_support.htm&language=en_US&type=5
- Salesforce Help — Deploying Omnistudio Components Between Orgs or Migrating from Omnistudio for Managed Packages (the managed package → standard runtime migration as a three-phase process; DataPacks as the managed-package deployment mechanism) — https://help.salesforce.com/s/articleView?id=xcloud.os_deploy_or_migrate.htm&language=en_US&type=5
- Salesforce Help — Disable the Managed Package Runtime and Deploy Custom Lightning Web Components — https://help.salesforce.com/s/articleView?id=sf.os_enable_standard_omnistudio_runtime.htm&language=en_US&type=5
- Salesforce Developers Blog — Automate Your Move to the Omnistudio Standard Runtime with the New Migration Assistant — https://developer.salesforce.com/blogs/2025/12/automate-your-move-to-the-omnistudio-standard-runtime-with-the-new-migration-assistant
- Object Reference for the Salesforce Platform — `OmniProcess` ("For internal use only. This object and associated records are only for internal use. Don't perform any create, edit, or delete operations on this object. Modifying or deleting this object's records may result in errors with your implementation.") — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_omniprocess.htm
- Object Reference for the Salesforce Platform — `OmniDataTransform` (same internal-use-only statement) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_omnidatatransform.htm
- Industries Common Resources Developer Guide — Data Mapper (the four types, including "Transform—Perform intermediate data transformations without reading from or writing to Salesforce") — https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/omnistudio_data_mapper_apis.htm
- Salesforce Help — Before-Save Record-Triggered Flows (supported elements Assignment, Decision, Get Records, Loop; updates limited to the triggering record — the branch OmniStudio has no equivalent for) — https://help.salesforce.com/s/articleView?id=platform.flow_concepts_trigger_record.htm&language=en_US&type=5
- Apex Developer Guide — Execution Governors and Limits (the per-transaction limits both tools share) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Help — Workflow Rules & Process Builder End of Support, 31 December 2025 (via `standards/decision-trees/automation-selection.md`) — https://help.salesforce.com/s/articleView?id=001096524&language=en_US&type=1
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

### Repo decision trees this skill defers to

- `standards/decision-trees/automation-selection.md` — the canonical Flow vs Apex
  vs Agentforce vs Approvals vs Platform Events routing. Run first, always. Its
  Q2 (before-save), Q6 (Flow + Invocable Apex), and Q10 (batch volume) resolve
  several branches before OmniStudio becomes a question.
- `standards/decision-trees/flow-pattern-selector.md` — which Flow type, once the
  first tree says Flow. Its Q7 (pause / resume) and its transaction-boundary
  table are the specific comparison an OmniScript proposal has to beat.

### Claims deliberately not made

**No licensing or entitlement claim.** An earlier version of this skill asserted
that Industry Cloud licensing "can include OmniStudio" and advised confirming
before designing. The advice is sound; the underlying entitlement rules were not
verified against any fetchable Salesforce source and vary by product and contract.
This skill therefore treats "does the org have OmniStudio, and is it enabled" as a
question to answer from the org and the contract, and makes no claim about which
licences include it.

**No claim about the override surface of managed-package OmniScripts.** How much
of a packaged OmniScript can be overridden is a decision of the package that ships
it and varies by package and release. The guidance in
[`gotchas.md`](gotchas.md), Gotcha 9, is a process instruction — establish it for
the specific package — not a statement about a fixed platform behaviour.

**No performance comparison between OmniStudio and Flow.** Both run inside the
same platform limits, orgs differ in their Omnistudio Setup switches (Enhanced
Runtime Performance in particular), and no fetchable Salesforce source compares
them. Where this skill discusses performance, it is about the *branch* — the
avoided second save of a before-save Flow — not about relative execution speed.
