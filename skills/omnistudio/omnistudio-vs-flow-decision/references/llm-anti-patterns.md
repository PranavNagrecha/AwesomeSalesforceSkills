# LLM Anti-Patterns — OmniStudio vs Flow Decision

Mistakes AI assistants make when asked to choose between OmniStudio and Flow. The
dominant cause is that this is a decision about *operating cost*, and a model
asked to compare two technologies produces a comparison of two technologies.

---

## Anti-Pattern 1: Answering without routing

**What the LLM generates:** a direct OmniScript-vs-Screen-Flow comparison, in
response to "should this be an OmniScript or a Screen Flow", with a
recommendation at the end.

**Why it happens:** the question names two options, so the completion compares two
options. Stepping back to ask whether either is the right *class* of solution is
not the shape the prompt invites.

**Correct pattern:** run `standards/decision-trees/automation-selection.md` first
and cite the branch. Several of its outcomes make the question moot — a
before-save record-triggered Flow (Q2) has no OmniStudio equivalent at all, and a
high-volume batch requirement (Q10) resolves to Apex regardless of which UI tool
anyone prefers. Where it lands on Flow, run
`flow-pattern-selector.md` to get the specific Flow type, because that is the
baseline any OmniStudio proposal has to beat.

An answer that begins "which branch of the automation tree did this land on?" is
more useful than one that begins with a feature table.

**Detection hint:** an OmniStudio-vs-Flow recommendation with no reference to
either decision tree, or one that compares "OmniScript" against "Flow" as though
Flow were a single thing.

---

## Anti-Pattern 2: One answer for the whole capability

**What the LLM generates:** "Use OmniStudio for this requirement" or "Use Flow for
this requirement" — a single verdict covering UI, orchestration, and data shaping.

**Why it happens:** the question is phrased as a binary, and a binary question
invites a binary answer. Producing three answers where one was asked for reads as
evasive.

**Correct pattern:** it is three decisions — UI (OmniScript / FlexCard vs Screen
Flow / LWC / Lightning Record Page), orchestration (Integration Procedure vs
autolaunched Flow / Invocable Apex), and data shaping (Data Mapper vs
Get/Update/Create Records / Apex). Mixed answers are normal and usually correct: an
OmniScript UI over Flow side-effects, or a Screen Flow calling an Integration
Procedure for one externally-dictated payload.

The instinct toward one vendor per capability is aesthetic, not architectural.

**Detection hint:** a recommendation with a single tool name and no per-layer
breakdown.

---

## Anti-Pattern 3: Ignoring team capability because it was not in the prompt

**What the LLM generates:** a well-reasoned recommendation for OmniScript, based
entirely on fit, in an org where one contractor built two OmniScripts and has
since left.

**Why it happens:** the requirement was in the prompt and the staffing situation
was not. The model optimizes what it can see, and "who maintains this in eighteen
months" is not derivable from a capability description.

**Correct pattern:** ask. Team capability is frequently the largest term in this
comparison and the one least often written down. Flow skills are common and
transferable; OmniStudio skills are neither. A recommendation that says
"OmniScript fits this shape better and I would not use it here unless you have at
least two people who can maintain it — do you?" is materially more useful than a
confident verdict.

**Detection hint:** a tool recommendation with no question about who will
maintain the result, or one that treats "the org has OmniStudio" as equivalent to
"the org can operate OmniStudio".

---

## Anti-Pattern 4: Managed-package assumptions on a standard-runtime org

**What the LLM generates:** deployment advice built entirely around DataPacks,
Apex snippets using `vlocity_*` namespaces, and an extension model that belongs to
the managed package.

**Why it happens:** OmniStudio spent most of its life as the Vlocity managed
package, so the training distribution is overwhelmingly managed-package material.
Nothing in "we use OmniStudio" indicates which runtime.

**Correct pattern:** establish the runtime as a precondition. On the standard
runtime, components deploy through the Metadata API as `OmniProcess`,
`OmniDataTransform`, and `OmniUiCard` — after the Omnistudio Metadata setting is
enabled — and the Apex and extension surfaces differ too. Migration between
runtimes is a documented three-phase project, now assisted by the Omnistudio
Migration Assistant.

Where the runtime is unknown, give both and say which is which. Guessing produces
advice that fails at the first implementation detail.

**Detection hint:** DataPacks or a `vlocity_*` namespace in a recommendation with
no accompanying question about the runtime.

---

## Anti-Pattern 5: Recommending a rewrite of something that works

**What the LLM generates:** "migrate the existing Screen Flows to OmniScript for
consistency", offered as part of an OmniStudio adoption plan.

**Why it happens:** consistency is a genuine architectural value, adoption plans
have a shape that includes migrating the old thing, and the model has no
visibility into what the rewrite costs or what bugs the existing artifact has
already had fixed.

**Correct pattern:** an artifact that works is not a migration candidate because
the org bought a platform. A rewrite consumes the budget new capability needed and
reintroduces defects that were fixed years ago, in exchange for consistency that
nobody outside the architecture team experiences. Migrate on the next substantial
change to that capability, not on a platform decision.

**Detection hint:** "for consistency" as the stated reason for a migration, with
no other trigger.

---

## Anti-Pattern 6: Building new OmniStudio into an active migration

**What the LLM generates:** a design that adds an OmniScript on the managed
package runtime, in an org whose stated context includes a standard-runtime
migration in flight.

**Why it happens:** the managed package runtime is what is live, and building for
what is live is normally correct. The interaction with the migration's scope is a
second-order consequence.

**Correct pattern:** anything built on the runtime being migrated away from is
immediately in scope for that migration, so every hour spent building it will be
spent again migrating it. During a migration, new capability goes into something
outside its scope — Flow, Apex, LWC — unless it genuinely cannot; where OmniStudio
is unavoidable, build on the target runtime even if the capability lands later.

**Detection hint:** a new OmniStudio artifact proposed on the source runtime of a
migration the prompt already mentioned.

---

## Anti-Pattern 7: FlexCard as the default record-page composition tool

**What the LLM generates:** a FlexCard for a summary panel on a record page,
because the org uses OmniStudio.

**Why it happens:** the tool choice was made once for the capability and applied
to every layer, which is the same error as Anti-Pattern 2 in a specific and very
common location.

**Correct pattern:** the UI-composition layer has its own cost profile. A record
page is edited far more often, by far more people, than a guided journey is, so
trading a surface every admin can change in App Builder for one needing an
OmniStudio skillset is a worse trade here than elsewhere. Two questions decide it:
is this consumed anywhere other than the record page, and does it need a
FlexCard-specific behaviour? Two noes means Lightning Record Page.

**Detection hint:** a FlexCard recommended for a single-surface panel with no
FlexCard-specific requirement named.

---

## Anti-Pattern 8: Mixed design with no boundary contract

**What the LLM generates:** a correct mixed recommendation — Screen Flow UI,
Integration Procedure for the payload — and then moves straight to implementation
detail on each side.

**Why it happens:** the decision was the question, the seam is an implementation
concern, and "write down the interface" is not a satisfying conclusion to an
architecture answer.

**Correct pattern:** in a mixed design the seam is where it will break, and it has
two owners. The boundary needs a written contract: input shape with types and
required flags, output shape, the owner of each side, the change protocol, and
the failure contract. That last one is load-bearing — a Flow fault path cannot
meaningfully explain an unhandled error from the other tool to an end user, so the
callee returning a structured status rather than throwing is usually the only
workable answer.

**Detection hint:** a mixed-tool recommendation with no interface definition, or
one whose error handling is described as "add a fault path".

---

## Anti-Pattern 9: Writing to the Omnistudio standard objects

**What the LLM generates:** a governance or inventory utility that queries — and
then updates — `OmniProcess` or `OmniDataTransform`, for example to bulk-rename
components or apply a change across many artifacts.

**Why it happens:** the objects are queryable, the change is mechanical, and
scripting a mechanical change across many artifacts is exactly the kind of
leverage a model is good at proposing. The prohibition is a documentation
sentence, not an API restriction.

**Correct pattern:** the Object Reference says of `OmniProcess`,
`OmniDataTransform`, and `OmniDataTransformItem`: "For internal use only. This
object and associated records are only for internal use. Don't perform any create,
edit, or delete operations on this object." Reading them for an inventory is fine;
writing is not. This is also a real point of comparison — Flow metadata carries no
equivalent restriction, so governance tooling over Flows is broader than
governance tooling over Omnistudio.

**Detection hint:** any DML against an `Omni*` standard object in a proposal.

---

## Anti-Pattern 10: A feature matrix presented as a decision

**What the LLM generates:** a thorough capability comparison table — branching
depth, JSON handling, reuse, licensing — with a recommendation derived from the
row count.

**Why it happens:** it is the canonical shape of a technology comparison, it is
genuinely informative, and it is what "compare these two" asks for.

**Correct pattern:** on the branches where OmniStudio is a candidate at all, it
tends to win a capability comparison — that is roughly what "candidate" means. The
terms that decide the outcome do not appear in a feature table: who maintains it
in eighteen months, whether the pipeline can promote it today, whether a runtime
migration is in flight, and whether neighbouring capabilities are already built in
one tool.

The most useful output is not a verdict but a reversible decision: "OmniScript
fits this shape better; we are using Screen Flow because of X and Y; revisit when
X and Y are resolved."

**Detection hint:** a recommendation whose stated reasoning is entirely
capability-based, with no operational term and no revisit condition.
