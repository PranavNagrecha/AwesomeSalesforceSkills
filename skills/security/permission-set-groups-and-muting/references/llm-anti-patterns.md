# LLM Anti-Patterns: Permission Set Groups and Muting

Common mistakes AI coding assistants make when generating or advising on Salesforce Permission Set Groups (PSGs) and muting permission sets.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Muting to Grant Permissions

**What the LLM generates:** "Create a muting permission set to add the missing permission to the group."

**Why it happens:** LLMs infer from the name "muting permission set" that it is a permission set that can be attached to a group for any purpose. Training data does not consistently clarify that muting is strictly subtractive.

**Correct pattern:**

```
A muting permission set can only SUBTRACT permissions from the effective group
evaluation. It cannot grant new permissions. If a permission is missing from
the PSG, add a new permission set to the group that includes the needed access.

Muting is for narrowing: when the combined permission sets in a group grant
slightly too much, muting removes the excess. It is never a source of new access.
```

**Detection hint:** If the advice creates a muting permission set to add or grant access, the mechanism is being used backwards.

---

## Anti-Pattern 2: Leaving Profiles Overloaded When Introducing PSGs

**What the LLM generates:** "Create Permission Set Groups for your user personas and assign them to users" without addressing the existing profile-based access.

**Why it happens:** LLMs generate the PSG creation steps as an additive recommendation. They do not mention that profiles should be minimized as part of the PSG adoption, because training data rarely covers the migration path.

**Correct pattern:**

```
PSGs are ineffective if profiles still carry most feature-specific access. The
migration path is:
1. Audit what permissions currently live on profiles.
2. Move feature-specific access into focused permission sets.
3. Compose permission sets into PSGs.
4. Reduce profiles to thin bases: login hours, login IP ranges, page layout
   assignments, and the default record type. Record type access itself can
   be granted by permission sets and PSGs (Security Guide), so it does not
   have to stay on the profile.

Layering PSGs on top of feature-heavy profiles creates duplicate access paths
that are harder to audit, not easier.
```

**Detection hint:** If the advice introduces PSGs without mentioning profile minimization, the access model will have redundant and conflicting permission sources.

---

## Anti-Pattern 3: Creating PSGs That Are Random Collections Instead of Meaningful Bundles

**What the LLM generates:** "Group all the permission sets the sales team uses into one PSG."

**Why it happens:** LLMs optimize for reducing assignment count. They group everything together without validating that the bundle represents a coherent job function or feature set.

**Correct pattern:**

```
A PSG should represent a meaningful access bundle, either a job function
(e.g., "Service Console Agent") or a feature set (e.g., "CPQ Quote Management").
Dumping all of a team's permission sets into one group creates a bundle that:
- Cannot be reused across other personas
- Is hard to audit because it has no clear purpose
- Becomes a governance problem as permissions are added over time

Name PSGs to reflect their purpose. If you cannot describe what the PSG
represents in one sentence, it is too broad.
```

**Detection hint:** If the PSG groups unrelated permission sets with no clear functional theme, it is a collection, not a bundle.

---

## Anti-Pattern 4: Using Muting as a Substitute for Proper Permission Set Design

**What the LLM generates:** "The PSG grants too many permissions, create muting permission sets to suppress each one."

**Why it happens:** LLMs reach for muting as a fix for permission design problems. Training data shows muting as a powerful tool without emphasizing that excessive muting signals a design flaw.

**Correct pattern:**

```
If a PSG requires extensive muting to be safe, the underlying permission sets
are not well-designed. Muting should be the exception, not the rule.

Before creating a muting permission set:
1. Ask whether the base permission set should be split into smaller, more
   focused permission sets.
2. Ask whether a different PSG composition would avoid the need for muting.
3. Only use muting when two personas share 90%+ of a bundle and muting the
   remaining 10% is cleaner than maintaining two separate bundles.
```

**Detection hint:** If the advice creates multiple muting permission sets for a single PSG, the base permission sets need redesign rather than suppression.

---

## Anti-Pattern 5: Not Testing Composed Access with Real User Personas

**What the LLM generates:** PSG design recommendations based on permission metadata alone, without mentioning testing with actual user scenarios.

**Why it happens:** LLMs operate on metadata and documentation. They do not model the runtime behavior of composed permissions, which can interact in unexpected ways.

**Correct pattern:**

```
Composed access can behave differently than designers expect. Before rolling
out PSGs:
1. Assign the PSG to a test user on the target profile.
2. Log in as the test user and walk through critical business workflows.
3. Verify that the effective access matches the design: check object CRUD,
   field visibility, tab access, and record type availability.
4. Test with muting applied to confirm subtracted permissions are actually
   removed from the effective set.

PSG design on paper and PSG behavior in practice diverge more often than
expected.
```

**Detection hint:** If the advice designs PSGs purely from metadata review without testing with a real user login, composed permission behavior may differ from expectations.

---

## Anti-Pattern 6: Ignoring the Migration Rollback Plan

**What the LLM generates:** "Move all users from profiles to PSGs" as a one-step migration without a rollback strategy.

**Why it happens:** LLMs generate the target-state recommendation. They do not consistently recommend a phased migration with rollback options.

**Correct pattern:**

```
Profile-to-PSG migration is an access-architecture project, not a metadata
conversion. A safe migration includes:
1. Pilot: Assign PSGs to a small test group while keeping their profile access
   unchanged. Verify effective access.
2. Parallel run: Users have both profile and PSG access. Confirm PSG covers
   all needed permissions.
3. Profile reduction: Remove feature permissions from profiles one batch at a
   time. Keep rollback scripts ready.
4. Cutover: Profiles are minimized. PSGs are the primary access mechanism.

At every phase, the rollback plan is: restore the profile permissions.
Never remove profile access before confirming the PSG replacement works.
```

**Detection hint:** If the advice migrates from profiles to PSGs in a single step without a phased approach or rollback plan, the risk of access disruption is high.

---

## Anti-Pattern 7: Writing Muting XML as If `false` Removed the Permission

**What the LLM generates:** A muting permission set with `<allowDelete>false</allowDelete>` or `<editable>false</editable>` "to block delete" or "to make the field read-only."

**Why it happens:** In every other permission file, `false` means "no access," so the LLM reuses that reading.

**Correct pattern:**

```
In a MutingPermissionSet, a setting that is ENABLED is turned OFF for the
group. To remove Delete on Case for the group:
  <objectPermissions>
      <allowDelete>true</allowDelete>   <!-- true = mute delete -->
      <object>Case</object>
  </objectPermissions>
To make a field read-only for the group, mute edit only:
  <fieldPermissions>
      <editable>true</editable>          <!-- true = mute edit -->
      <field>Case.Priority</field>
      <readable>false</readable>         <!-- false = keep read -->
  </fieldPermissions>
```

**Detection hint:** A muting permission set whose entries are mostly `false`.

---

## Anti-Pattern 8: Deploying a Trimmed Permission Set File

**What the LLM generates:** A permission set XML containing only the one new object permission, presented as "deploy this to add access."

**Why it happens:** LLMs assume metadata deploys merge, which is true for some types but not for permission sets.

**Correct pattern:**

```
Since API 40.0, a deployed permission set file is the complete definition;
missing grants are removed. Retrieve the full permission set, add the new
grant, review the diff, then deploy it together with the PSG and muting set
that reference it.
```

**Detection hint:** A permission set snippet with one or two entries and no instruction to retrieve the existing file first.
