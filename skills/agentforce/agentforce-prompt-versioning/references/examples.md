# Examples — Agentforce Prompt Versioning

**Scope note.** This skill is the **repository lifecycle**: where templates live,
what a change record contains, how models are pinned and re-evaluated, and how
org-vs-repo drift is detected. The runtime flip — how the live version changes,
what rollback costs in wall-clock time, and how to run two variants at once —
is `agentforce/prompt-template-versioning`. They meet at
`activeVersionIdentifier`.

---

## Example 1 — The repository layout, and the file shape that determines it

### The metadata facts that drive the layout

`GenAiPromptTemplate` lives in the `genAiPromptTemplates` directory with suffix
`.genAiPromptTemplate`, minimum API version 60.0
([GenAiPromptTemplate](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplate.htm)).
Crucially, **all versions of a template live in one file** — `templateVersions`
is an array on the template, not a separate file per version.

```text
force-app/main/default/
└── genAiPromptTemplates/
    ├── Sales_Email.genAiPromptTemplate-meta.xml          <- v1..v4 all in here
    ├── Refund_Status_Summary.genAiPromptTemplate-meta.xml
    └── Case_Wrap_Up.genAiPromptTemplate-meta.xml
```

### WRONG — the file-per-version layout

```text
genAiPromptTemplates/
  Sales_Email_v1.genAiPromptTemplate-meta.xml
  Sales_Email_v2.genAiPromptTemplate-meta.xml
  Sales_Email_v3.genAiPromptTemplate-meta.xml
```

Three separate *templates*, not three versions of one. Every consumer must be
repointed to promote, the platform's own activation model is bypassed, and a
`git log` on any one file shows the history of a version rather than the history
of the prompt.

### RIGHT — one file, and what that means for review

Because every version is in one file, `git log --follow` on that file **is** the
prompt's complete history. That is a genuine advantage and it has one cost worth
planning for: diffs are large and noisy, since adding a version appends a whole
`<templateVersions>` block.

Two conventions make review tractable:

```gitattributes
# .gitattributes — keep the XML readable in review
*.genAiPromptTemplate-meta.xml diff
```

```bash
# Review the ENVELOPE separately from the prose. The envelope is where
# breaking changes hide; the prose is where the intent is.
git diff HEAD~1 -- force-app/main/default/genAiPromptTemplates/ \
  | grep -E '^[+-].*(<versionNumber>|<status>|<primaryModel>|<required>|<apiName>|responseFormat|outputSchema|templateDataProviders|activeVersionIdentifier)'
```

The second command is the one to put in the PR template. A reviewer reading a
400-line diff will read the prose and skim the structure; this inverts that.

### Ownership

Prompt templates are product artefacts as much as technical ones — the wording
is usually owned by someone who does not read XML. Record it explicitly:

```text
# CODEOWNERS
force-app/main/default/genAiPromptTemplates/Sales_Email.*    @sales-ops @platform-team
force-app/main/default/genAiPromptTemplates/Case_Wrap_Up.*   @service-ops @platform-team
```

Two owners per template — the business owner of the wording and the engineer who
owns the envelope — is the arrangement that survives, because the failure modes
are split the same way.

---

## Example 2 — A change record that is worth writing

### WRONG — a changelog nobody can act on

```markdown
## 2026-08-10 — Sales Email v4
- Improved the prompt.
- Fixed tone.
```

Unactionable. It does not say what changed structurally, what was measured, or
what to do if it goes wrong — which are the three things a reader six months
later needs.

### RIGHT — the four sections that make it useful

```markdown
## 2026-08-10 — Sales_Email v4  (versionIdentifier: e5f6g7h8)

### Contract impact: NONE
- inputs:              unchanged (opportunityId, tone required as before)
- responseFormat:      unchanged (MarkDown)
- outputSchema:        n/a
- templateDataProviders: unchanged
- primaryModel:        unchanged
- => activation is a one-field flip; no consumer deployment required

### What changed
- Removed the "As an AI assistant" preamble.
- Added an explicit instruction to reference the most recent Opportunity stage
  change by name.
- Shortened the closing paragraph guidance from 3 sentences to 1.

### Why
Sales ops reported reps deleting the opening line in 60% of drafts (sampled
n=80, 2026-07). The preamble was pure overhead.

### Measured before promotion
- Golden suite: 48/48 pass (unchanged from v3).
- Draft length: median 214 -> 168 words.
- Canary (10%, 5 working days, n=41 reps): send-without-edit rate
  38% -> 51%. No adverse latency change.

### Rollback
Revert activeVersionIdentifier to a1b2c3d4 (v3) and deploy.
Measured rollback time in the 2026-08-04 rehearsal: 6 minutes.
v3 retained until 2026-10-01.
```

### Why "Contract impact" is the first section

It is the only section a release manager must read, and it answers the question
that determines the deployment shape: is this a one-field flip, or a coordinated
release with consumers? Putting it first makes the common case (no impact) a
two-second read and the dangerous case impossible to miss.

Note what the "Measured" section contains: numbers with sample sizes. A change
record that says "improved tone" records a belief; one that says
"send-without-edit 38% → 51%, n=41" records a finding that a later reader can
disagree with.

---

## Example 3 — Model pinning: what the field is, and how to decide

### The field

Each `GenAiPromptTemplateVersion` carries `primaryModel`. That is the documented
field name — **not** `modelVersion`, which is a plausible invention that appears
in a lot of generated advice.

Do not write a model identifier you have not verified against what the org
actually offers. A wrong-but-plausible value deploys and then behaves
unexpectedly, which is a worse failure than omitting the field.

### The decision, per template, not per org

| Signal | Pin | Leave to the platform default |
|---|---|---|
| Output is parsed by downstream code | ✅ | |
| Regulated or customer-facing wording | ✅ | |
| Reproducibility is a stated requirement | ✅ | |
| Internal drafting aid, human always reviews | | ✅ |
| Team has no capacity for quarterly re-evaluation | | ✅ |

The last row is the one teams get wrong. **Pinning is a commitment to
re-evaluate**, not a way to stop thinking about models. A pin that is never
revisited freezes the template on progressively older reasoning, and the cost is
invisible because nothing breaks — output just quietly stops improving while
competitors' does.

### The re-evaluation ritual

```text
QUARTERLY — Prompt model review
For each PINNED template:
  1. Create a new version, identical except primaryModel.
  2. Run the golden suite against both. Record pass rate and any diffs.
  3. Run the adversarial suite against the new one. Non-negotiable gate.
  4. If the new model is >= on goldens and clean on adversarial:
       canary at 10% for one week, then promote.
     Else: record WHY it was rejected, and the date to reconsider.
  5. Update the changelog either way. "We evaluated and declined" is
     as much a record as "we upgraded".
```

Step 5 is what stops the review degenerating into a calendar event nobody
completes. A declined upgrade with a written reason is a completed review.

---

## Example 4 — Detecting org-vs-repo drift, which is otherwise silent

### Context

A prompt is edited directly in Prompt Builder in production to fix a typo before
a customer demo. Nobody retrieves it. Three weeks later a routine deploy
overwrites the fix and the typo returns.

### Problem

The failure is silent in both directions. The UI edit does not fail. The deploy
that reverts it does not fail. The only symptom is behaviour that changed for a
reason nobody can locate.

### Solution — a scheduled retrieve-and-diff

```bash
#!/usr/bin/env bash
# ci/prompt-drift-check.sh — run nightly against production.
set -euo pipefail

sf project retrieve start \
  --metadata GenAiPromptTemplate \
  --target-org prod

if ! git diff --exit-code --stat force-app/main/default/genAiPromptTemplates/; then
    echo "DRIFT DETECTED: production prompt templates differ from the repository."
    echo "Someone edited in Setup, or a deploy did not land. Reconcile before"
    echo "the next release, or the next deploy will silently overwrite it."
    git diff force-app/main/default/genAiPromptTemplates/
    exit 1
fi
echo "No drift."
```

### The policy that has to accompany it

A detector with no decision rule produces a nightly alert that gets muted. State
the authority explicitly and the resolution for each direction:

```text
AUTHORITY: the repository.

Drift found, and the org version is BETTER (a real fix made under pressure):
  -> retrieve, commit with a changelog entry, and note that it bypassed review.
     Do not punish the fix; record it.

Drift found, and the org version is UNINTENDED:
  -> deploy the repo version. Investigate who had edit rights and whether they
     should.

Drift found in BOTH directions across templates:
  -> the deploy pipeline is not running. That is the actual incident.
```

Restricting Prompt Builder edit rights in production is the structural fix.
Detection is the safety net for the cases where the structural fix has an
exception.

---

## Example 5 — Where prompt templates sit in the release train

### The manifest ordering rule

The Metadata API deploys types in the order they appear in `package.xml`.
`GenAiPromptTemplate` must appear **before** `AiAgentScorerDefinition`, because
the template must exist before a scorer that references it can deploy
([Create Custom
Scorers](https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-custom-scorers.html)).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- 1. Templates: a dependency of nearly everything else here. -->
    <types>
        <members>Sales_Email</members>
        <members>Refund_Status_Summary</members>
        <name>GenAiPromptTemplate</name>
    </types>

    <!-- 2. Things that reference templates. -->
    <types>
        <members>Sales_Email_Tone_Scorer</members>
        <name>AiAgentScorerDefinition</name>
    </types>
    <types>
        <members>Resort_Manager</members>
        <name>Bot</name>
    </types>

    <version>67.0</version>
</Package>
```

### Both environments, every release

The failure this prevents: a prompt deployed to sandbox during development and
forgotten in the production release. The agent then behaves differently in the
two orgs, and every comparison made during testing is invalid — including the
comparison used to sign off the release.

```text
RELEASE CHECKLIST ROW
[ ] genAiPromptTemplates/ diff between the release branch and prod is empty
    AFTER deployment (run ci/prompt-drift-check.sh against prod post-deploy)
```

Running the drift check *after* the deploy converts it from a monitoring tool
into a release verification step, which is where it does the most good.

---

## Example 6 — Retirement, and why it is a dated decision

### The mechanics

Each `GenAiPromptTemplateVersion` has a `status` of `Published` or `Draft`, and
only one version can be active at a time. A retained-but-inactive version costs
file size and nothing else.

### The schedule

```text
v4 promoted 2026-08-10
  2026-08-10 -> 2026-09-10   v3 retained, ACTIVE ROLLBACK TARGET
  2026-09-10 -> 2026-10-01   v3 retained, observation window closed
  2026-10-01                 v3 removed from templateVersions; changelog
                             entry records the removal and the reason
  v2 and earlier: already removed 2026-08-10 (two-version retention policy)
```

### Why a date and not an instinct

Deleting the previous version is the cleanup instinct, and it removes the
rollback plan at exactly the moment it is most likely to be needed — the weeks
immediately after a promotion. A two-version retention policy with dated
retirement costs almost nothing and makes rollback availability a property of
the process rather than of whether anyone happened to tidy up.

Record the removal in the changelog. An entry that says "removed v3, superseded
by v4 on 2026-08-10, no incidents in the observation window" is what tells a
future reader that the retention policy was followed rather than forgotten.
