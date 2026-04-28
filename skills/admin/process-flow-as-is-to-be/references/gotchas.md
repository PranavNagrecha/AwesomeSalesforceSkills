# Gotchas — Process Flow As-Is To-Be

Non-obvious problems that show up in real Salesforce process-mapping engagements.

## Gotcha 1: As-Is map drifts during build

**What happens:** The As-Is is captured at week 1, the build starts at week 3, and by week 5 the team is implementing a To-Be that no longer matches what was on the whiteboard. The As-Is artifact never gets updated, so when QA finds a regression nobody can prove what the original behavior was.

**When it occurs:** Long-running projects (3+ sprints), projects with shifting stakeholders, projects where the process owner is not deeply involved in build standups.

**How to avoid:** Commit the As-Is and To-Be JSON to source control alongside the build artifacts. Treat the process map as living documentation — every PR that changes a Flow or Apex class touched by the process should also bump the corresponding `to_be_steps[].step_id` in the JSON. If the JSON does not change but the build does, that is the drift signal.

---

## Gotcha 2: Missing exception paths

**What happens:** The map shows only happy paths. Build proceeds. At UAT the testers exercise an unhappy path (timeout, validation rejection, auth failure) and the system either silently swallows the error or throws an unhandled exception that breaks the screen.

**When it occurs:** Every time. This is the single most common failure mode in process mapping.

**How to avoid:** Every decision diamond must have ≥2 outgoing branches with conditions labelled. Every integration handshake must have a timeout / fallback path. Every approval step must have a rejection path. The `check_process_map.py` checker enforces this on the JSON.

---

## Gotcha 3: "Automate everything" anti-pattern (manual residue is a feature)

**What happens:** Stakeholders hear "we are automating the process" and assume every step gets a Flow. The map ends up with 30 `[FLOW]` and `[APEX]` steps and zero `[MANUAL]` steps. Build estimates triple. At go-live, the steps that needed human judgement are now broken automations that produce wrong outcomes faster than the manual process did.

**When it occurs:** Greenfield projects with ambitious sponsors. Common in the "we are transforming" framing.

**How to avoid:** Treat the manual residue list as a first-class output. Every step that involves judgement, regulatory sign-off, low volume, or high change-cost should be flagged `[MANUAL]` with an explicit "why manual" reason. The map is more credible when it admits what humans still own. Push back on stakeholders with the four canonical reasons; usually they accept once they hear the reasoning.

---

## Gotcha 4: Swim lanes per system instead of per actor

**What happens:** The map has lanes labelled "Salesforce", "ERP", "Marketing System". Each lane covers many actors and many automation tools. The build team cannot tell who is responsible for each step.

**When it occurs:** When the practitioner mistakes the data flow for the process flow. Architecture diagrams have system lanes; process diagrams have actor lanes.

**How to avoid:** A swim lane represents an actor — a human role or an automated system performing actions. The Salesforce platform itself is one actor (covering Flow, Apex, validation, sharing, approvals). Each named integration is its own actor. Each customer-facing actor (customer, partner, prospect) is its own actor. If a "system" lane has multiple humans inside it, split the lane.

---

## Gotcha 5: Decision points with implicit branches

**What happens:** A decision diamond is drawn with one outgoing arrow labelled "Yes" and the "No" branch is implied to "do nothing" or "go back". The build team interprets this differently from the process owner, and the resulting Flow either loops infinitely or silently drops the unhappy path.

**When it occurs:** When the mapper has a happy-path bias and treats the unhappy branch as "obvious".

**How to avoid:** Every decision diamond gets ≥2 explicit outgoing branches, each labelled with the condition that triggered it ("No → escalate to manager" not just "→ escalate"). The "No" / sad-path branch must terminate explicitly: route to a manual step, raise an error, retry with a delay, or abandon the process. "Implicit" is not allowed.

---

## Gotcha 6: Forgetting the customer-facing lane in B2C contexts

**What happens:** The process map shows internal steps only. The customer's actions (filling out a form, signing a document, replying to an email, clicking a portal link) are missing. The build team designs an internal-only automation that has no place to wait for the customer's input, and the process stalls at run-time.

**When it occurs:** B2C and self-service B2B projects. B2B teams used to enterprise sales sometimes also forget this lane when the customer touches the process via a Community / Experience Cloud portal.

**How to avoid:** Add a Customer or external-counterparty lane explicitly. Every step where the customer must do something gets a node in this lane (no automation tier — the customer is not Salesforce). The transitions into and out of this lane are usually `[INTEGRATION]` callouts (DocuSign envelope sent, portal link emailed) or `[FLOW]` steps that wait on the customer's response.

---

## Gotcha 7: Conflating swim lanes with phases

**What happens:** The map is structured horizontally with phase columns ("Discovery", "Negotiation", "Close") instead of actor lanes. Steps in each phase are shown without an actor, so responsibility is invisible.

**When it occurs:** When the team has a sales-stage bias and applies the same structure to a non-stage process.

**How to avoid:** Phases are for sales-stage maps (`sales-process-mapping`), not generic process maps. For a generic process, lanes go vertically by actor; the horizontal axis is time / sequence. If the process really is stage-based, switch skills.

---

## Gotcha 8: Every approval shown as a Flow

**What happens:** Approval steps get tagged `[FLOW]` because the team has a Flow bias. The build implements a Flow with a decision element that routes to an "Update Approver" path. There is no audit trail of who approved, no approver history, no recall mechanism.

**When it occurs:** Teams with strong Flow expertise and weak Approval Process expertise.

**How to avoid:** Tag approval steps as `[APPROVAL]`, not `[FLOW]`. Approval Process gives free audit trail, approver history, recall, parallel and sequential approver chains, and email/in-app notifications. A Flow that mimics this loses the audit features. The trade-off: Approval Process is less flexible for branching logic. Mix the two — `[APPROVAL]` for the sign-off step, `[FLOW]` for the post-approval actions.
