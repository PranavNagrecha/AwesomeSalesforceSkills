# System map

## Product category

SfSkills V2 is a **Salesforce engineering intelligence and assurance layer**. It sits between an agentic host and Salesforce engineering evidence. It does not replace the host model, Salesforce APIs, a source-control system, or a DevOps platform.

```text
Practitioner
    |
    v
Host experience: Cursor first, then Claude/Copilot/Vibes
    |
    v
Typed product command and preflight
    |
    +---------------- Control plane ----------------+
    | run | authority | target | host capability    |
    | state | policy | schemas | status             |
    +-----------------------------------------------+
    |
    +------- Context plane --------+     +------ Evidence plane ------+
    | product core                 |     | fixture                    |
    | selected SfSkills packages   |     | external Salesforce project|
    | conditional references       |     | Salesforce org/job/test    |
    | checkpoints and summaries    |     | analyzer/vendor exports     |
    +------------------------------+     +----------------------------+
              |                                      |
              +------------------+-------------------+
                                 v
                        Focused agent stages
             route -> ground -> diagnose -> challenge
                                 |
                                 v
                       Claim/evidence graph
                                 |
                                 v
                Validated result + replayable run bundle
```

## The eight planes

### Experience plane

Owns product entrypoints, argument validation UX, progress, result rendering, report paths, replay, and user-visible limitations. Hosts can express this differently, but the product command and result semantics remain stable.

### Agent plane

Owns narrow probabilistic reasoning roles. Core roles select context, inspect an optional project, normalize the grounding task, review evidence, review policy, grade QA, and resume a run. Product roles synthesize one user job. Agents never own permission enforcement or deterministic parsing.

### Context plane

Owns what the model sees at each stage. It discovers compact metadata first, selects a small core plus conditional pack, calculates cost, reserves output space, records omissions, creates checkpoints, and prevents complete transcripts from becoming handoffs.

### Knowledge plane

Owns the existing SfSkills packages, references, examples, templates, source records, freshness status, retrieval indexes, and legacy compatibility. Knowledge explains Salesforce behavior; it does not prove the state of a specific org or project.

### Evidence plane

Owns normalized observations from a supplied fixture, explicit external project, selected org, deployment/test result, static analyzer, snapshot, or vendor export. Every item carries identity, time, source, digest, classification, bounds, and a stable ID.

### Control plane

Owns run lifecycle, authority, target identity, tool policy, host capability negotiation, schemas, permission profiles, continuation, and terminal status. The model cannot enlarge authority with natural-language instructions.

### Quality plane

Owns schema validation, deterministic claim lint, independent evidence review, security adversaries, context-rot tests, versioned scenarios, baseline comparison, actual host proof, persistent read-only drift checks, and scratch-org known truth.

### Adapter plane

Owns thin host-specific packaging: Cursor plugins, native skills, commands, subagents, hooks and MCP configuration; Claude and Copilot equivalents; Vibes integration; portable Agent Plugins where licensing and capability permit. Adapters cannot redefine product truth.

## Canonical ownership

```text
Existing skills/ packages      -> Salesforce knowledge
Product JSON definitions       -> product portfolio contract
Agent JSON + narrative         -> execution role contract
Command JSON                   -> user/API entry contract
Evidence-tool JSON             -> normalized observation contract
Schemas                        -> machine validity
Policies                       -> authority and enforcement intent
Scenarios                      -> known-truth quality contract
Numbered specification         -> normative behavior
Generated host artifacts       -> derived distributions
```

A generated catalog or plugin is never a second source of truth. If generated output is edited manually, the build check must fail.

## Product boundary

The product may read, classify, compare, diagnose, explain, review, plan, and render. It may write only local redacted run/report artifacts. It may not mutate Salesforce.

Disposable scratch-org setup is a separate QA system with separate credentials, allowlists, markers, scripts, and teardown. The model never receives that authority as a product tool.
