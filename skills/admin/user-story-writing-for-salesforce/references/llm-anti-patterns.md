# LLM Anti-Patterns — User Story Writing For Salesforce

Common mistakes AI assistants make when generating Salesforce user stories. These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Inventing Personas Not In The Org

**What the LLM generates:**

```
As a Customer Success Architect with the CSA Premium Tier permission set...
```

…when the org has no such role and no such permission set.

**Why it happens:** LLMs trained on generic SaaS/CRM corpora invent plausible-sounding job titles and Salesforce constructs. The generation is statistically reasonable, but factually wrong for the org being implemented in.

**Correct pattern:**

```
As a [persona drawn from the persona list provided in the BA brief or extracted from the requirements doc],
I want...
```

If no persona list exists, ask for one before drafting. Do not invent.

**Detection hint:** The persona names a profile or permission set that doesn't appear elsewhere in the requirements document or org metadata. Run the story through the BA's persona inventory before committing.

---

## Anti-Pattern 2: Writing Implementation Steps As Acceptance Criteria

**What the LLM generates:**

```
Acceptance Criteria:
- Create a Record-Triggered Flow on the Lead object
- Add a Decision element checking Score >= 80
- Add an Update Records element setting OwnerId
- Activate the flow
```

**Why it happens:** LLMs default to "show me how to build it" because that's what most coding training data looks like. User stories aren't build instructions — they're observations of behavior.

**Correct pattern:**

```
Acceptance Criteria:
- Given a Lead with Score >= 80, When it is created, Then OwnerId is set to the Inside Sales queue.
```

The AC describes the *observable outcome*, not the *flow steps*. The build agent picks the implementation per `standards/decision-trees/automation-selection.md`.

**Detection hint:** AC text contains words like "Flow", "Apex", "Trigger", "Decision element", "Update Records". These are build verbs, not observation verbs. Reject and reshape.

---

## Anti-Pattern 3: "The System Shall…" Waterfall Voice

**What the LLM generates:**

```
The system shall validate that the discount is less than 25% before allowing save.
The system shall route quotes over $100,000 to the regional manager for approval.
```

**Why it happens:** LLMs trained on classical Software Requirements Specification (SRS) documents revert to "the system shall" voice when asked for "requirements." Salesforce user stories are not SRS shall-statements.

**Correct pattern:**

```
As a Sales Rep with the Sales User profile,
I want a save attempt with discount > 25% to fail with an inline validation error,
So that I cannot accidentally exceed company discount policy and lose margin.
```

The actor is the persona, not "the system." The behavior is what the persona observes.

**Detection hint:** The phrase "the system shall" or "the system must" anywhere in the story body. Auto-reject.

---

## Anti-Pattern 4: Omitting Handoff Metadata

**What the LLM generates:** A clean markdown story stem and well-formed AC, but no JSON block — or a JSON block with `recommended_agents: []`.

**Why it happens:** The LLM treats the story as the deliverable and considers the handoff "extra ceremony." But the handoff JSON is what lets the next agent pick up the work without re-asking the user.

**Correct pattern:** Every story emits the handoff JSON with `recommended_agents[]` populated and non-empty. If the chain is genuinely unknown, default to `["object-designer"]` and explain in `notes`.

```json
{
  "story_id": "US-...",
  "complexity": "M",
  "recommended_agents": ["flow-builder", "permission-set-architect"],
  "recommended_skills": ["flow/record-triggered-flows"],
  "dependencies": [],
  "notes": "..."
}
```

**Detection hint:** No fenced ```json block in the output, or `recommended_agents` is missing/empty. Lint with `scripts/check_invest.py`.

---

## Anti-Pattern 5: Writing Stories Nobody Can Demo

**What the LLM generates:**

```
As a Data Architect with the System Administrator profile,
I want the underlying data model to be normalized to third normal form,
So that future queries are efficient.
```

**Why it happens:** The LLM picks a "developer-flavored" persona and writes a technical hygiene story dressed as a user story. Nobody can demo "third normal form" at a sprint review.

**Correct pattern:** A story is demoable. The persona, action, and outcome must be observable in a sandbox. If the work is genuine refactoring with no demoable outcome, file it as a *technical debt task*, not a user story.

```
As a Sales Rep with the Sales User profile,
I want the Account-to-Contact relationship to surface all related contacts on the Account record page,
So that I can see every stakeholder when prepping for a meeting.
```

This is demoable. The earlier version isn't.

**Detection hint:** AC contains internal/architectural language ("normalized", "indexed", "decoupled") with no observable user-visible behavior. Reshape or reroute to a tech-debt backlog.

---

## Anti-Pattern 6: Generating Stories Without Checking For Existing/Duplicate Work

**What the LLM generates:** A clean new story for "auto-assign hot leads" — when the backlog already has US-LEAD-031 doing exactly the same thing.

**Why it happens:** The LLM doesn't search the existing backlog before drafting. It optimizes for "produce a story" rather than "produce a story that's net new."

**Correct pattern:** Before drafting, run a search against the existing backlog (or the SfSkills repo's `search_knowledge.py` for skill-level dedup, or the BA's Jira/ADO query for backlog-level dedup). Only draft net-new stories or *extensions* of existing ones (with a cross-reference in `dependencies[]`).

**Detection hint:** Story title closely paraphrases an existing backlog title. Search before drafting; the BA's backlog tool query is cheap.

---

## Anti-Pattern 7: Sizing By Hours Instead Of The Heuristic

**What the LLM generates:**

```
Complexity: 13 story points (≈ 5 days of dev work)
```

…when the canonical sizing in this repo is S / M / L / XL.

**Why it happens:** LLMs default to Fibonacci story points or hour estimates from generic agile training data, ignoring the project's local convention.

**Correct pattern:** Apply the S/M/L/XL heuristic from SKILL.md based on object count, automation count, and persona count. Output exactly one of those four values. The downstream agents are tuned to consume those four buckets, not arbitrary point scales.

**Detection hint:** `complexity` field is anything other than `"S"`, `"M"`, `"L"`, or `"XL"`. The lint script enforces this.
