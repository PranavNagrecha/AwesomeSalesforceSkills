# OmniStudio vs Flow — Per-Layer Decision Template

One per capability. Sections 0 and 1 come first: the routing may make the rest
unnecessary, and the preconditions change the answer more than the requirement
does.

---

## 0. Routing — do this before comparing anything

- `standards/decision-trees/automation-selection.md`, branch that resolved it:
  > e.g. "Q1 → user filling a form → Q7 → Q8 → No → LWC calling imperative Apex"
- If it landed on **before-save record-triggered Flow** (Q2) or on **Apex for
  volume** (Q10): stop. OmniStudio has no equivalent on those branches. Record
  the outcome and close this document.
- If it landed on Flow, `standards/decision-trees/flow-pattern-selector.md`
  branch:
  > e.g. "Q1 → user interaction → Q7 → pausing mid-flow → Orchestration OR
  > screen flow + pause element"
- **Baseline to beat** (the tool the trees produced):

## 1. Preconditions — answer from the org, not from the requirement

| Question | Answer |
|---|---|
| Does the org have OmniStudio, enabled and in use? | |
| Which runtime? (managed package / standard) | |
| Is a runtime migration in flight? | |
| How many people can independently build and maintain an OmniScript? | |
| How many can maintain a Screen Flow? | |
| Has this release pipeline ever promoted an Omnistudio artifact? | |
| Are the capability's neighbours already built in one of the two tools? | |

- If a migration is in flight: new capability should go outside its scope unless
  it genuinely cannot. Note the decision here:
- If the maintainer count for OmniStudio is 1 or 0: say so explicitly in the
  recommendation. A one-person capability is a staffing risk, not a platform.

## 2. Capability

- Name:
- User surface (internal console / Experience Cloud / mobile / several):
- Number of steps, and depth of conditional branching:
- Save-and-resume required across sessions?
- Externally dictated payload shape? (Who dictates it?)
- Expected cadence of change, and who requests changes:
- Latency and volume expectations:

---

## 3. Layer Decisions

Decide each layer separately. Mixed answers are normal and usually correct.

### UI Layer

| Option | Fit (H/M/L) | Rationale |
|---|---|---|
| OmniScript | | |
| Screen Flow | | |
| FlexCard | | |
| Lightning Record Page | | |
| Custom LWC | | |

**Chosen:**

If FlexCard is chosen, answer both:
- Is this consumed anywhere other than the Lightning record page?
- Which FlexCard-specific behaviour is required (actions from the central
  designer, IP-powered save chain, state shared across cards)?
- Two noes means Lightning Record Page. Record which it was.

### Orchestration Layer

| Option | Fit (H/M/L) | Rationale |
|---|---|---|
| Integration Procedure | | |
| Autolaunched Flow | | |
| Invocable Apex | | |

**Chosen:**

- Where do record-triggered side effects live? (They belong in Flow — see
  `flow-pattern-selector.md` Q4–Q5 — even when the journey is OmniStudio.)

### Data Layer

| Option | Fit (H/M/L) | Rationale |
|---|---|---|
| Data Mapper (Extract / Turbo Extract / Transform / Load) | | |
| Flow record elements (Get / Create / Update / Delete) | | |
| Apex SOQL / DML | | |

**Chosen:**

- Is the shape crossing the boundary dictated by an external system? (If not, a
  Data Mapper is an extra artifact for no gain.)

---

## 4. Boundary Contracts

One per mixed-tool seam. This is where the design will break, and it usually has
two owners.

| From | To | Owner (from side) | Owner (to side) |
|---|---|---|---|
| | | | |

For each seam:

- **Input shape** (name, type, required, allowed values):
- **Output shape** (name, type, meaning):
- **Failure contract** — does the callee throw, or return a structured status the
  caller can render? A fault path cannot meaningfully explain an unhandled error
  from the other tool to an end user.
- **Change protocol** — which changes are additive and safe, which require notice
  and a regression test on both sides in the same release:

---

## 5. Operational Cost

- Deployment mechanism for each chosen tool:
- Setup switches that are **prerequisites** in the target org, and their current
  state (Omnistudio Metadata API Support, Managed Package Runtime, Managed
  Package Designer, Deploy Custom Lightning Web Components, Data Mapper
  Versioning, Enhanced Runtime Performance, …):
- Can this pipeline promote every chosen artifact **today**? If no, what is the
  gap and who is closing it?
- Who maintains this in 18 months:
- Governance and inventory tooling available for each tool (note that
  `OmniProcess`, `OmniDataTransform`, and `OmniDataTransformItem` are documented
  "For internal use only" — read, never write):

---

## 6. Revisit Conditions

The most useful thing this document produces. A decision with revisit conditions
is reversible; a verdict is not.

- This decision should be revisited if:
  - [ ] OmniStudio maintainer count reaches 2 or more
  - [ ] The pipeline gains the ability to promote Omnistudio artifacts
  - [ ] The runtime migration completes
  - [ ] The capability's step count or surface count materially grows
  - [ ] Other:
- Owner of the revisit:
- Earliest sensible revisit date:

---

## 7. Sign-Off

- [ ] `automation-selection.md` was run first and the branch is cited
- [ ] `flow-pattern-selector.md` was run where the answer was Flow
- [ ] Preconditions answered from the org, not inferred
- [ ] Each layer decided separately, with explicit rationale
- [ ] Record-triggered side effects are in Flow
- [ ] FlexCard vs Lightning Record Page decided on its own two questions
- [ ] Every mixed-tool seam has a written contract including a failure contract
- [ ] Deployment mechanism verified as working in this pipeline today
- [ ] Maintainer availability stated honestly, including single-person risk
- [ ] Revisit conditions recorded, with an owner
