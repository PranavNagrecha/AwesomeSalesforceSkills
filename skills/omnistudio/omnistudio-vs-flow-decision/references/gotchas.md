# Gotchas — OmniStudio vs Flow Decision

Ways this decision goes wrong in practice. Grounded in the Object Reference for
the Salesforce Platform, the Apex Developer Guide, Salesforce Help's Omnistudio
documentation, and the two decision trees this skill runs after (Summer '26,
API 67.0).

Most of these are not capability mistakes. They are decisions made on the wrong
axis — comparing what the tools can do, when what decides it is who maintains the
result and whether it can be promoted.

---

## Gotcha 1: Two Runtimes, and Most of What You "Know" Is About the Older One

**What happens:** a design references an Apex entry point, a deployment
mechanism, or an extension model that does not exist in the org — because it
belongs to the other runtime.

Omnistudio has a **managed package runtime** (the Vlocity lineage, custom data
model, `vlocity_*` namespaces, DataPacks) and a **standard runtime** (Salesforce
standard objects, Metadata API). Migration between them is a documented
three-phase process, now assisted by the Omnistudio Migration Assistant. The
managed package existed for years longer, so it dominates every search result,
every community post, and every model's training data.

**When it occurs:** at the first line of implementation detail in any design that
did not start by asking which runtime.

**How to avoid:** make it a precondition question, before any comparison. It
changes deployment, the Apex entry points, and the extension model — which means
"should we use OmniStudio" has two different answers and they are not close. On
Salesforce Help the managed-package pages carry "(Managed Package)" in the title.

---

## Gotcha 2: The Deployment Mechanism Is a First-Class Cost, Not a Detail

**What happens:** an OmniScript is built, approved, demonstrated — and then
cannot be promoted, because the release pipeline has never carried an Omnistudio
artifact.

On the managed package runtime, components move as DataPacks: a mechanism unlike
anything else in a normal Salesforce pipeline, with its own tooling and its own
failure modes. On the standard runtime they move through the Metadata API as
`OmniProcess` (OmniScript and Integration Procedure), `OmniDataTransform` (Data
Mapper), and `OmniUiCard` (FlexCard) — but only after the **Omnistudio Metadata**
setting is enabled: "To deploy and retrieve Omnistudio standard objects with
Salesforce Metadata API, enable the Omnistudio Metadata setting." Until it is on,
the components are invisible to the API.

**When it occurs:** at the end of the first sprint that built one, which is the
worst possible moment to discover it.

**How to avoid:** treat "can this pipeline promote this artifact **today**" as a
gate on the decision, not as an implementation task. If the answer is no, the
choice is to fix the pipeline first or to pick the tool the pipeline already
carries. Both are legitimate; discovering it at the release gate is not.

---

## Gotcha 3: The Omnistudio Standard Objects Are Internal-Use-Only

**What happens:** a governance dashboard, a bulk-audit script, or a
"rename everything" utility is built against `OmniProcess` or `OmniDataTransform`,
and the org develops errors nobody traces back to it.

The Object Reference says of `OmniProcess`, `OmniDataTransform`, and
`OmniDataTransformItem`:

> "For internal use only. This object and associated records are only for
> internal use. Don't perform any create, edit, or delete operations on this
> object."
>
> "Modifying or deleting this object's records may result in errors with your
> implementation."

**When it occurs:** when an inventory turns into a remediation. Reading them to
count what exists is reasonable; the next step is the one that breaks things.

**How to avoid:** read for analysis, change through the designer or the Metadata
API. This is also a genuine point of comparison with Flow: `Flow` and
`FlowDefinition` metadata carry no equivalent restriction, so governance tooling
over Flows is a supported activity and governance tooling over Omnistudio is
narrower than it looks.

---

## Gotcha 4: OmniStudio Has No Before-Save Equivalent

**What happens:** a field-derivation requirement on an Industry Cloud org gets
built as an Integration Procedure called from an after-save Flow, because the
org's default is OmniStudio.

`automation-selection.md` Q2 routes same-record field work under ten seconds to a
**before-save record-triggered Flow**, and `flow-pattern-selector.md` Q3 confirms
it: the supported element set is Assignment, Decision, Get Records, Loop, and it
writes the field in the save the trigger already pays for rather than issuing a
second one.

**When it occurs:** on orgs with a standing "use OmniStudio" default, which is
most Industry Cloud orgs.

**How to avoid:** run the automation tree first. Several of its branches resolve
to something OmniStudio cannot do at all, and on those branches there is no
comparison to have. The cost of getting this wrong is not aesthetic: it is a
second save on every record, plus an artifact and a deployment mechanism.

---

## Gotcha 5: "It Performs Well" May Be a Setting Somebody Turned On

**What happens:** OmniStudio performance is compared between two orgs and the
numbers disagree, with no difference in the artifacts.

The standard runtime is governed by a set of Setup switches an architect should
know exist before committing: Omnistudio Metadata API Support, Managed Package
Runtime, Managed Package Designer, Deploy Custom Lightning Web Components,
Omnistudio SLDS 2 Theme, Data Mapper Versioning, Omni Global Auto Number, and
**Enhanced Runtime Performance** — the last documented as making "Omnistudio
communicate[] with the Salesforce Platform with in-platform capabilities instead
of through Apex calls".

**When it occurs:** whenever a benchmark, a proof of concept, or a vendor demo is
generalised to the target org without checking its configuration.

**How to avoid:** list the relevant switches as prerequisites in the design, with
their state in the target org. A performance claim measured in an org with
different switches is not evidence about yours.

---

## Gotcha 6: A One-Person Capability Is a Staffing Risk Wearing an Architecture Costume

**What happens:** an org "has OmniStudio" and builds accordingly. The one person
who can maintain an OmniScript changes teams. Every subsequent change to that
capability becomes a project with a lead time.

**When it occurs:** twelve to eighteen months after the consultant who built it
rolled off, which is long enough for it to be nobody's decision.

**How to avoid:** make team capability an explicit input to the decision, written
down in the same document as the tool choice, in the same tone. "OmniScript is
the better fit for this shape and we are not using it, because one person can
maintain it and that person is not on this team" is a defensible architectural
statement. Leaving it unsaid means the risk is carried without ever being
accepted.

Flow skills are common and transferable; OmniStudio skills are neither. Over a
five-year horizon this is frequently the largest term in the comparison and the
one least often written into it.

---

## Gotcha 7: FlexCard vs Lightning Record Page Is a Different Decision

**What happens:** a team decides "OmniScript over Screen Flow" for a journey and
applies that outcome to the record page, replacing a Lightning Record Page with a
FlexCard.

The two layers have different cost profiles. A record page is edited far more
often, by far more people, than a guided journey is. Trading a surface every
admin can change in App Builder for one that needs an OmniStudio skillset is a
much worse trade at that layer than at the journey layer.

**When it occurs:** whenever a tool choice is made once per capability rather than
once per layer.

**How to avoid:** decide the UI-composition layer on its own two questions — is
this consumed anywhere other than the record page, and does it need a
FlexCard-specific behaviour (actions from the central designer, an IP-powered save
chain, state shared across cards)? Two noes means Lightning Record Page,
regardless of what the journey layer decided.

---

## Gotcha 8: Building New OmniStudio During a Runtime Migration

**What happens:** an org mid-migration from managed package to standard runtime
builds a new OmniScript on the managed package runtime, because that is what is
live and the team is fluent in it. The artifact is immediately in scope for the
migration it just enlarged.

**When it occurs:** mid-project, when the migration has been running long enough
that "we'll handle it in the migration" sounds reasonable.

**How to avoid:** during a migration, new capability goes into something outside
its scope — Flow, Apex, LWC — unless it genuinely cannot. Where OmniStudio is
unavoidable, build on the target runtime even if the capability lands later. The
second-order cost is worse than the first: an artifact built on managed-package
idioms teaches the team the patterns they are supposed to be leaving.

---

## Gotcha 9: A Managed OmniScript Is Not a Free Head Start

**What happens:** an industry solution ships OmniScripts as part of a managed
package. The team plans to "just tweak them" and discovers the override surface
is narrower than a greenfield build would have been.

Components delivered in a managed package are constrained by that package's
design — which parts are overridable, and how, is the package's decision, not
yours. A packaged starting point that needs changes outside the sanctioned
extension points is not a head start; it is a constraint discovered late.

**When it occurs:** at the first requirement the packaged flow did not anticipate,
which is usually the first requirement that is specific to the customer.

**How to avoid:** before planning around a packaged component, establish exactly
what is overridable and what is not, and design the customer-specific parts to sit
outside it. Where the required change is inside the package's sealed surface, the
options are the vendor's extension mechanism or a parallel implementation — and
knowing which, early, is worth a day.

<!-- UNVERIFIED: the precise override and extension surface for managed-package
     OmniScripts varies by package and by release, and no fetchable Salesforce
     source was found that states it generally. Treat the paragraph above as a
     process instruction — establish it for the specific package — rather than as
     a claim about a fixed platform behaviour. -->

---

## Gotcha 10: The Mixed-Tool Boundary Is the Part Nobody Documents

**What happens:** a Screen Flow calls an Integration Procedure. Six months later
the IP's output shape changes by one field. The Flow's fault path shows a service
agent an error string from an artifact they have never heard of.

Mixed designs are correct and common — an OmniScript UI over Flow side-effects, a
Screen Flow calling an IP for one hard payload. What makes them fragile is that
the seam usually has two owners and no written contract.

**When it occurs:** at the first change to either side after the original team has
dispersed.

**How to avoid:** write the boundary as a contract: input shape with types and
required flags, output shape, the owner of each side, the change protocol (which
changes are additive and safe, which require notice and a regression test on both
sides), and — most importantly — the **failure contract**. Does the callee throw,
or return a status the caller can render? A Flow fault path cannot meaningfully
explain an unhandled error from the other tool, so the callee returning a
structured failure is usually the only workable answer.

---

## Gotcha 11: Comparing Capability When Operations Decide It

**What happens:** a thorough, well-argued capability comparison concludes that
OmniScript is the better fit. It is correct and it is not the decision.

Capability comparisons are easy to write and are almost always won by OmniStudio
on the branches where it is a candidate at all — that is what "OmniStudio is a
candidate here" means. The terms that actually decide it are the ones that do not
appear in a feature table: who can maintain this in eighteen months, whether the
pipeline can promote it today, whether a runtime migration is in flight, and
whether the neighbouring capabilities are already built in one tool.

**When it occurs:** in every decision document that opens with a feature matrix.

**How to avoid:** price the operational tax in the same document, with the same
seriousness. A decision record that says "OmniScript fits better; we are using
Screen Flow, because of X, Y and Z; revisit when X and Y are fixed" is more useful
than either verdict on its own, and it is reversible — which a bare verdict is
not.
