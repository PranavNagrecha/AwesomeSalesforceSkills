# Source Hierarchy

Every agent and skill author in this repo uses this file to decide what to trust, in what order, and what to do when sources disagree.

This file extends `official-salesforce-sources.md`, which maps specific official URLs by domain.
That file answers "which URL do I use?" — this file answers "which source wins when they conflict?"

---

## The Trust Ladder

```
TIER 1 ── Official Salesforce
TIER 2 ── Official Community (Salesforce-endorsed)
TIER 3 ── Expert Community (trusted, not official)
TIER 4 ── Community Signal (useful context, lower confidence)
```

A lower tier NEVER overrides a higher tier on factual platform behavior.
A lower tier CAN fill gaps where higher tiers are silent.
Every claim in a skill must be tagged with the tier that grounds it.

---

## Tier 1 — Official Salesforce

**Trust level:** `official`
**Authority:** Platform behavior, limits, API contracts, metadata semantics, security model, deprecations.

These are Salesforce's own published documentation. When Tier 1 says X, X is true for the stated release.
If Tier 1 is wrong (platform bug, doc error), the skill notes the discrepancy explicitly — it does not silently adopt community workarounds as the primary claim.

| Source | Domain | Use For |
|--------|--------|---------|
| help.salesforce.com | admin, flow, security | Product behavior, admin configuration, UI features |
| developer.salesforce.com | apex, lwc, integration, data, devops | APIs, Apex, LWC, metadata, Bulk API |
| architect.salesforce.com | all | Patterns, WAF, anti-patterns, integration guidance |
| Salesforce Release Notes | all | What changed, when, and what is deprecated |
| Salesforce Trust & Compliance | security | Data residency, certifications, Shield |

**Release Notes rule:** Release notes are the most current Tier 1 source.
When release notes contradict an older Tier 1 doc, release notes win.
Always note the release version when citing a limit or behavior that changes across releases.

---

## Tier 2 — Official Community

**Trust level:** `official-community`
**Authority:** Recommended patterns, learning-level guidance, Salesforce-reviewed content.

Salesforce endorses these sources. They are not the same as product documentation — they may simplify behavior for learning purposes or reflect best practices rather than strict platform contracts.

| Source | URL | Use For |
|--------|-----|---------|
| Trailhead modules and trails | trailhead.salesforce.com | Learning-oriented guidance, feature overviews |
| Salesforce Architects blog | architect.salesforce.com/content | Real-world pattern application, architecture decisions |
| Salesforce Ben | salesforceben.com | Admin-focused how-tos, feature walkthroughs |
| Salesforce Developers blog | developer.salesforce.com/blogs | Dev patterns, new feature guidance from Salesforce engineers |
| Salesforce YouTube (official) | youtube.com/@SalesforceDevs | Demo walkthroughs, release feature explanations |

**Tier 2 rules:**
- Use to fill gaps where Tier 1 is silent or too sparse for a practitioner audience.
- Do not use Tier 2 to override a Tier 1 behavioral claim.
- Trailhead simplifies. Always verify limits and behavior against Tier 1 before citing Trailhead as the source for a specific number or constraint.
- Salesforce Ben is strong on admin tasks and new features. Cross-check against help.salesforce.com for exact UI flows.

---

## Tier 3 — Expert Community

**Trust level:** `expert-community`
**Authority:** Real-world patterns, non-obvious gotchas, performance nuance, community-validated techniques.

These sources are not endorsed by Salesforce but are authored by recognized Salesforce experts (MVPs, certified architects, experienced practitioners). They are valuable for filling content that Tier 1 and 2 don't cover — particularly gotchas, performance patterns, and real-world implementation nuance.

| Source | URL | Strengths |
|--------|-----|-----------|
| Andy in the Cloud | andyinthecloud.com | Apex, LWC, deep platform internals |
| Apex Hours | apexhours.com | Dev tutorials, governor limits, async patterns |
| Salesforce Stack Exchange | salesforce.stackexchange.com | Specific problem/solution pairs — accepted answers only |
| SF MVP blogs (identified by name) | varies | High signal when author's MVP status is current |
| Unofficial SF | unofficialsf.com | LWC community components, screen flow extensions |

**Tier 3 rules:**
- A Tier 3 claim must be corroborated by at least one of:
  - One other independent Tier 3 source, OR
  - Absence of conflicting Tier 1/2 content AND plausible platform reasoning
- Stack Exchange: only accepted answers count as Tier 3. Non-accepted answers are Tier 4.
- MVP status must be current. An MVP from 2018 who has not kept their certification active is Tier 4.
- When using Tier 3, tag it explicitly in the skill: `[T3: source-name]` so future agents know the confidence level.
- Tier 3 content belongs in `gotchas.md` and `examples.md` — not as the primary behavior claim in `SKILL.md`.

---

## Tier 4 — Community Signal

**Trust level:** `community`
**Authority:** Context, anecdotal patterns, questions worth investigating.

Tier 4 is never the sole basis for a skill claim. Use it to find areas worth investigating, then verify with Tier 1-3 before including in a skill.

| Source | Use |
|--------|-----|
| Trailblazer Community threads | Identify common pain points worth covering in gotchas |
| Non-MVP dev blogs | Context for what practitioners struggle with — verify before using |
| YouTube tutorials (non-official) | Feature walkthroughs — always verify against Tier 1 |
| Reddit (r/salesforce) | Symptom identification only — never cite as a source |
| LinkedIn posts | Trend signals only — never cite as a source |

---

## Contradiction Resolution Rules

### Rule 1: Release Notes vs Older Tier 1 Doc
**Release Notes win.**
Update the skill to reflect the current release. Note the old behavior if practitioners may have org-specific settings that preserve it.

```
Example:
  Tier 1 doc (2022): "Process Builder is recommended for..."
  Release Notes (Winter '24): "Process Builder is being retired..."
  → Release Notes win. Skill directs to Flow. Old guidance is removed, not cited.
```

### Rule 2: Tier 1 vs Tier 2
**Tier 1 wins on behavior and limits.**
Tier 2 may be cited for context, phrasing, or learning-friendly explanation — but the factual claim uses Tier 1.

```
Example:
  Tier 1 (Apex Dev Guide): "Heap limit is 6MB synchronous, 12MB async."
  Tier 2 (Trailhead): "Be careful with heap size."
  → Skill cites Tier 1 for the specific number. Trailhead is not cited for this claim.
```

### Rule 3: Tier 1 vs Tier 3
**Tier 1 wins.**
The Tier 3 claim is not discarded — if it describes a real-world nuance not in Tier 1, surface it in `gotchas.md` with explicit attribution and a note that it is community-observed, not officially documented.

```
Example:
  Tier 1: "WITH SECURITY_ENFORCED throws an exception if a field is inaccessible."
  Tier 3 (Andy in the Cloud): "WITH USER_MODE is preferred in most cases because it silently strips."
  → SKILL.md cites Tier 1 for the behavior. gotchas.md surfaces the Tier 3 nuance with tag [T3: Andy in the Cloud].
```

### Rule 4: Tier 2 vs Tier 3
**Tier 2 wins unless Tier 3 has a specific version/release citation.**
A Tier 3 source that says "as of Spring '25 this changed" and references a release note beats general Tier 2 guidance.

### Rule 5: Tier 3 vs Tier 3 (two expert sources disagree)
**Document both explicitly.**
Do not pick a winner. Present both positions in `gotchas.md` with the attribution for each. Let the practitioner choose based on their context.

```
Format for Tier 3 disagreement:
  ## Gotcha: [Topic] — Community Disagreement
  **Position A [T3: Source1]:** ...
  **Position B [T3: Source2]:** ...
  **When A applies:** ...
  **When B applies:** ...
  **Official guidance:** [Tier 1 URL if exists, or "No official guidance found."]
```

### Rule 6: Any Source vs Platform Reality (skill is stale)
**Platform reality wins.**
When Currency Monitor flags a skill as potentially stale after a Salesforce release, the skill must be reviewed and updated. A skill that was accurate in Spring '24 may be wrong in Winter '25. Do not leave stale claims in place because the original source was Tier 1 — the release notes are also Tier 1 and they are newer.

---

## Confidence Tagging

Every factual claim in a skill body should carry an inline confidence tag when the claim is not universally known or when the tier matters for the reader.

| Tag | Meaning |
|-----|---------|
| `[T1]` | Sourced from Tier 1 official documentation |
| `[T2]` | Sourced from Tier 2 official community |
| `[T3: source-name]` | Sourced from named Tier 3 expert — verify before critical use |
| `[T4]` | Community signal only — must be verified before relying on |
| `[CONTRADICTED: see gotchas]` | Multiple sources disagree — contradiction documented in gotchas.md |
| `[STALE-RISK: release]` | This claim may be affected by a specific release — verify |

**Where tags are required:**
- Any specific limit (number, threshold, count) → must have `[T1]` and URL
- Any "recommended pattern" claim → must have `[T1]` or `[T2]` minimum
- Any gotcha sourced from community → must have `[T3: name]`
- Any claim flagged by Currency Monitor → must have `[STALE-RISK: release]` until reviewed

**Where tags are optional:**
- Generally known facts ("Apex runs in a transaction") — no tag needed
- Claims immediately followed by an official source link — link is sufficient

---

## Source Selection Workflow for Agents

When a Research Agent or Skill Builder is grounding a claim:

```
1. Search Tier 1 first.
   → Found and clear? Use it. Tag [T1].
   → Found but ambiguous? Note the ambiguity. Use it anyway. Check release notes.
   → Not found? Continue to Tier 2.

2. Search Tier 2.
   → Found? Use it. Tag [T2]. Note it is not a platform contract.
   → Not found? Continue to Tier 3.

3. Search Tier 3 (named sources only — see table above).
   → Found in one source? Use it. Tag [T3: source-name]. Flag for corroboration.
   → Found in two sources that agree? Use it. Tag both. Higher confidence.
   → Found in two sources that disagree? Document both. Tag [CONTRADICTED: see gotchas].
   → Not found in Tier 1-3? Do not include the claim. Mark it [NEEDS SOURCE] for human review.

4. Never use Tier 4 as the basis for a skill claim.
   Tier 4 signals what to research — it does not ground content.
```

---

## Updating This File

This file is maintained by humans. Do not auto-generate it.
When a new trusted source is identified (new MVP blog, Salesforce product blog, official doc section):
- Add it to the appropriate tier table above.
- Add an entry to `knowledge/sources.yaml` with the correct `trust` level.
- Note the date it was added and why it was assigned its tier.

New sources added by agents must be reviewed by a human before being treated as Tier 2 or above.
