# LLM Anti-Patterns — Source Tracking and Conflict Resolution

Common mistakes AI coding assistants make when generating or advising on Salesforce source tracking and conflict resolution.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Recommending `--force-overwrite` Instead of `--ignore-conflicts` for sf CLI v2

**What the LLM generates:**

```bash
sf project retrieve start --force-overwrite --target-org mySandbox
```

**Why it happens:** The legacy `sfdx force:source:pull --forceoverwrite` command used `--forceoverwrite` as the flag name. Training data contains many examples of the legacy `sfdx` namespace. LLMs confuse `--force-overwrite` (which does not exist as a flag in `sf project retrieve start`) with the correct `--ignore-conflicts` flag.

**Correct pattern:**

```bash
# sf CLI v2 (Salesforce CLI v2, Spring '25+) — correct flag name
sf project retrieve start --ignore-conflicts --target-org mySandbox

# sf CLI v2 for deploy direction
sf project deploy start --ignore-conflicts --target-org mySandbox
```

**Detection hint:** Any command that uses `--force-overwrite` with `sf project retrieve start` or `sf project deploy start` is wrong. The flag was renamed to `--ignore-conflicts` in the unified `sf` CLI.

---

## Anti-Pattern 2: Telling Users to Edit `maxRevision.json` Directly to Fix Conflicts

**What the LLM generates:**

```
Open .sf/orgs/<orgId>/maxRevision.json and change the RevisionCounter
value for the conflicting component to match the org's current revision.
This will clear the conflict without a full re-retrieve.
```

**Why it happens:** LLMs see that `maxRevision.json` contains revision counters and reason that changing the number will fix the mismatch. This is superficially logical but ignores the multi-field structure of the tracking database and the CLI's internal consistency checks.

**Correct pattern:**

```bash
# Never edit tracking files manually.
# Delete the entire stale tracking directory and rebuild:
rm -rf .sf/orgs/<orgId>/
sf project retrieve start --target-org <alias>
```

**Detection hint:** Any instruction that says "open maxRevision.json and edit" or "change the RevisionCounter" is an anti-pattern.

---

## Anti-Pattern 3: Treating Source Tracking Conflicts as Git Merge Conflicts

**What the LLM generates:**

```
To resolve the conflict, open the file and look for the Git conflict markers
(<<<<<<, =======, >>>>>>>) to see both versions. Edit the file to keep the
changes you want, then run git add and git commit to mark it resolved.
```

**Why it happens:** LLMs are heavily trained on Git conflict resolution patterns. When a user says "source tracking conflict," the LLM pattern-matches to Git merge conflicts and generates the standard Git resolution workflow, which is entirely wrong for SFDX source tracking conflicts.

**Correct pattern:**

```
SFDX source tracking conflicts are not Git conflicts. There are no
conflict markers in the file. The conflict exists in the CLI's tracking
database (.sf/orgs/<orgId>/maxRevision.json), not in the file itself.

Resolution requires choosing a direction (org wins or local wins) and
using --ignore-conflicts on the appropriate command:

# Org wins:
sf project retrieve start --ignore-conflicts --target-org <alias>

# Local wins:
sf project deploy start --ignore-conflicts --target-org <alias>
```

**Detection hint:** Any mention of `<<<<<<<`, `=======`, or `>>>>>>>` conflict markers, or `git add` as a step in resolving a source-tracking conflict, is the wrong approach.

---

## Anti-Pattern 4: Claiming Sandbox Source Tracking Is Enabled by Default

**What the LLM generates:**

```
Developer sandboxes support source tracking automatically. Just run
sf project retrieve start and the CLI will track changes.
```

**Why it happens:** Scratch orgs have source tracking enabled by default, and many LLM training examples conflate scratch orgs and sandboxes. The sandbox source tracking feature (introduced in Summer '22) requires explicit opt-in via an org preference and a sandbox refresh — it is not on by default.

**Correct pattern:**

```
Source tracking in sandboxes is NOT enabled by default.

To enable:
1. In production org: Setup > Sandboxes > Sandbox Settings
2. Enable "Enable Source Tracking in Sandboxes"
3. Create or REFRESH the sandbox after enabling the preference

Important: enabling the preference after a sandbox exists does not
retroactively activate tracking. The sandbox must be refreshed.

Scratch orgs have tracking enabled by default and do not need this step.
```

**Detection hint:** Any claim that "Developer sandboxes automatically support source tracking" or that the user can "just run sf project retrieve start" on a new sandbox without setup is incorrect.

---

## Anti-Pattern 5: Recommending `sf project retrieve start` With No Flags to Resolve a Conflict

**What the LLM generates:**

```bash
# To get the latest org changes and resolve the conflict:
sf project retrieve start --target-org mySandbox
```

**Why it happens:** LLMs see "conflict on retrieve" and recommend re-running the retrieve, assuming repetition will resolve the issue. A plain retrieve without `--ignore-conflicts` will always abort with the same conflict error if both sides have changed. Repeating the same command without the flag does nothing.

**Correct pattern:**

```bash
# A plain retrieve will abort again with the same conflict error.
# You must decide which version wins, then use the appropriate flag:

# If org version should win:
sf project retrieve start --ignore-conflicts --target-org mySandbox

# If local version should win:
sf project deploy start --ignore-conflicts --target-org mySandbox
```

**Detection hint:** If the suggested fix for a conflict error is to re-run the same command that produced the conflict error, the LLM has not understood the resolution mechanism.

---

## Anti-Pattern 6: Advising Users to Commit `.sf/` Tracking Files to Git

**What the LLM generates:**

```bash
# Ensure your tracking state is committed so other developers have the same baseline:
git add .sf/
git commit -m "chore: commit source tracking state"
git push
```

**Why it happens:** LLMs that see `.sf/` directories in project structures sometimes treat them like other project state that should be versioned. Tracking files are machine-local, org-ID-specific, and ephemeral. Committing them causes conflicts between teammates and makes the tracking system unreliable.

**Correct pattern:**

```
NEVER commit .sf/ to Git. Add it to .gitignore:

# .gitignore
.sf/

Each developer maintains their own local tracking state. The tracking
database is rebuilt by running sf project retrieve start when starting
fresh or after a sandbox refresh. Sharing tracking files via Git
causes incorrect conflict detection for all team members.
```

**Detection hint:** Any instruction that runs `git add .sf/` or recommends committing the `.sf/` directory is wrong.
