# LLM Anti-Patterns — Permission Set Deployment Ordering

Common mistakes AI coding assistants make when generating or advising on permission set deployment ordering.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting to Deploy a Permission Set Without Retrieving First

**What the LLM generates:** Instructions to create a PermissionSet XML from scratch and deploy it directly to any target org, without mentioning that this will overwrite all existing permissions.

**Why it happens:** LLMs model the "add permissions" task as a straightforward write operation, analogous to writing a config file. They are not aware that the Metadata API performs a full-replace rather than a merge.

**Correct pattern:**

```bash
# WRONG: deploying a PS you constructed locally without retrieving current state first
sf project deploy start --metadata "PermissionSet:My_PS" --target-org production

# CORRECT: retrieve first, then merge, then deploy
sf project retrieve start --metadata "PermissionSet:My_PS" --target-org production
# (edit the retrieved XML to add your new permissions)
sf project deploy start --metadata "PermissionSet:My_PS" --target-org production
```

**Detection hint:** Any LLM response that says "create a PermissionSet file" or "add the permission to the XML" without a preceding retrieve step should be flagged.

---

## Anti-Pattern 2: Combining ConnectedApp and PermissionSet in One Deploy Batch

**What the LLM generates:** A single `sf project deploy start` command or a package.xml that includes both a ConnectedApp and a PermissionSet referencing it.

**Why it happens:** LLMs optimize for "deploy everything at once" as the simplest instruction. They have no awareness of the platform-specific ConnectedApp cross-reference bug.

**Correct pattern:**

```bash
# WRONG: single batch with both
sf project deploy start \
  --metadata "ConnectedApp:My_App,PermissionSet:My_PS" \
  --target-org production

# CORRECT: sequential deploys
sf project deploy start --metadata "ConnectedApp:My_App" --target-org production --wait 30
sf project deploy start --metadata "PermissionSet:My_PS" --target-org production --wait 30
```

**Detection hint:** Any deploy command or package.xml that includes both `ConnectedApp:*` and `PermissionSet:*` (or `PermissionSetGroup:*`) in the same batch.

---

## Anti-Pattern 3: Deploying PSG Before Constituent PSets Exist in Target

**What the LLM generates:** A pipeline definition or deployment script that deploys a PermissionSetGroup without first ensuring its constituent PermissionSets are present in the target org.

**Why it happens:** LLMs assume deployment ordering is handled automatically, similar to how build systems resolve dependencies. The Metadata API does not guarantee this ordering.

**Correct pattern:**

```yaml
# WRONG: single stage deploying PSG and PSets together without explicit ordering
deploy:
  metadata: "PermissionSet:PS_A,PermissionSet:PS_B,PermissionSetGroup:PSG_1"

# CORRECT: two explicit stages
stage_1_deploy_psets:
  metadata: "PermissionSet:PS_A,PermissionSet:PS_B"

stage_2_deploy_psg:
  needs: [stage_1_deploy_psets]
  metadata: "PermissionSetGroup:PSG_1"
```

**Detection hint:** Any pipeline that deploys a `PermissionSetGroup` in the same stage as its constituent `PermissionSet` members without a documented ordering guarantee.

---

## Anti-Pattern 4: Treating Profile Deployment Differently from Permission Set Deployment

**What the LLM generates:** Advice to deploy profiles freely without the retrieve-first requirement, or vice versa.

**Why it happens:** LLMs sometimes conflate profiles and permission sets or treat profiles as less risky to overwrite.

**Correct pattern:**

Profiles have the same full-replace behavior as PermissionSets. Both must be retrieved from the target org before deployment to avoid silent data loss. Profile deployments are additionally risky because profiles contain page layout assignments, record type visibility, and login hours — all of which are silently overwritten by a deploy that does not include those settings.

**Detection hint:** Any instruction that says "deploy a profile" without mentioning that it should be retrieved from the target org first.

---

## Anti-Pattern 5: Assuming `--ignore-conflicts` Makes PS Deploys Safe

**What the LLM generates:** A deploy command with `--ignore-conflicts` as a general solution for permission set deployment errors, or the claim that this flag prevents permission loss.

**Why it happens:** `--ignore-conflicts` is a flag that handles source-tracking conflicts, not Metadata API full-replace behavior. LLMs confuse the two different failure modes.

**Correct pattern:**

```bash
# WRONG: --ignore-conflicts does not prevent permission wipeout
sf project deploy start \
  --metadata "PermissionSet:My_PS" \
  --ignore-conflicts \
  --target-org production

# CORRECT: only retrieve-first prevents permission wipeout
sf project retrieve start --metadata "PermissionSet:My_PS" --target-org production
# merge changes into retrieved XML
sf project deploy start --metadata "PermissionSet:My_PS" --target-org production
```

**Detection hint:** Any suggestion to use `--ignore-conflicts` as a remedy for permission set deployment safety. The flag resolves source tracking conflicts; it does not affect what the Metadata API writes to the org.
