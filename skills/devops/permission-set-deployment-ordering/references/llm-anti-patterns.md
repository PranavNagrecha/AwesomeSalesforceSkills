# LLM Anti-Patterns — Permission Set Deployment Ordering

Common mistakes AI coding assistants make when generating or advising on permission set deployment ordering.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting to Deploy a Permission Set Without Retrieving First

**What the LLM generates:** Instructions to create a PermissionSet XML from scratch and deploy it directly to any target org, without mentioning that this will overwrite all existing permissions.

**Why it happens:** LLMs model the "add permissions" task as a straightforward write operation, analogous to writing a config file. They are not aware that the guide requires a permission set deploy to "include all of its metadata to avoid accidentally overwriting the permission set's contents" (api_meta 264 L97417-97418); field-by-field replace-versus-merge semantics are UNVERIFIED (2026-10-20).

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

**Why it happens:** LLMs optimize for "deploy everything at once" as the simplest instruction. The ConnectedApp cross-reference bug is itself UNVERIFIED (2026-10-20), so treat the split as a precaution, not a documented requirement.

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

**Why it happens:** LLMs assume deployment ordering is handled automatically, similar to how build systems resolve dependencies. The guide says ordered deploys must be submitted one at a time after the previous one succeeds (api_meta 264 L4246-4249).

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

## Anti-Pattern 4: Treating Profile Deployment Like Permission Set Deployment

**What the LLM generates:** Advice that a Profile deploy replaces the target's profile the way a PermissionSet deploy is described to, or that removing a permission from profile XML revokes it.

**Why it happens:** LLMs sometimes conflate profiles and permission sets or treat profiles as less risky to overwrite.

**Correct pattern:**

They differ. A PermissionSet deploy must carry all of the set's metadata "to avoid accidentally overwriting" it (api_meta 264 L97417-97418). A Profile deploy is designed "to overlay the existing Profile settings", so a disabled permission is not exported and stays in the target unless the XML says `<value>false</value>` (L100265-100268); deleting login hours needs an explicit empty `loginHours` tag (L100743-100744).

**Detection hint:** Any instruction that calls a Profile deploy a full-replace, or that removes a permission from profile XML and expects the target to lose it.

---

## Anti-Pattern 5: Assuming `--ignore-conflicts` Makes PS Deploys Safe

**What the LLM generates:** A deploy command with `--ignore-conflicts` as a general solution for permission set deployment errors, or the claim that this flag prevents permission loss.

**Why it happens:** `--ignore-conflicts` is a flag that handles source-tracking conflicts (it overwrites the conflicting org or local copy, sfdx_dev 264 L12089-12100), not the overwrite risk the Metadata API guide describes for permission set deploys (api_meta 264 L97417-97418). LLMs confuse the two different failure modes.

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
