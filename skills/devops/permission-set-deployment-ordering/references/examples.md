# Examples — Permission Set Deployment Ordering

## Example 1: Permission Loss During Sandbox-to-Sandbox Deployment

**Context:** A developer creates a new permission set in a developer sandbox to grant access to three new custom fields. They package the permission set into a deployment package and deploy to a full copy sandbox where the permission set already exists with 25 existing field permissions.

**Problem:** After deployment, users report they can no longer access 22 fields they previously could. The developer only intended to add three new field permissions, but the PermissionSet XML in the deploy package only contained those three fields. The guide warns that a deploy must include all of the set's metadata "to avoid accidentally overwriting the permission set's contents" (api_meta 264 L97417-97418); here the 22 existing permissions were lost. UNVERIFIED (2026-10-20): that the loss is silent (no warning).

**Solution:**

```bash
# Step 1: Retrieve the current state from the target org
sf project retrieve start \
  --metadata "PermissionSet:My_PS" \
  --target-org full-sandbox

# Step 2: Open the retrieved XML, add the new field permissions

# Step 3: Deploy the merged XML back
sf project deploy start \
  --metadata "PermissionSet:My_PS" \
  --target-org full-sandbox

# Step 4: Post-deploy verify by retrieving again and diffing
sf project retrieve start \
  --metadata "PermissionSet:My_PS" \
  --target-org full-sandbox
```

**Why it works:** By retrieving the target org's authoritative state and merging the new permissions into it, the deployed XML is a complete superset. The deploy now carries all of the set's metadata, as the guide requires (api_meta 264 L97417-97418), so previous grants are preserved.

---

## Example 2: ConnectedApp Cross-Reference Error Blocking Production Deploy

**Context:** A DevOps team is releasing a new integration feature. The release package includes: (a) a new ConnectedApp for the integration's OAuth configuration, and (b) a PermissionSet that grants users access to that ConnectedApp. Both are in the same deployment job run via `sf project deploy start`.

**Problem:** The deploy fails with a cross-reference id error on the PermissionSet. UNVERIFIED (2026-10-20): that this is a known platform bug for a ConnectedApp and a PermissionSet or PSG referencing it in one batch; neither corpus describes it, so the split below is a precaution.

**Solution:**

```bash
# Stage 1: Deploy ConnectedApp only
sf project deploy start \
  --metadata "ConnectedApp:Integration_App" \
  --target-org production \
  --wait 30

# Stage 2: Deploy PermissionSet and all other metadata
# Only run after Stage 1 completes successfully
sf project deploy start \
  --metadata "PermissionSet:Integration_PS" \
  --target-org production \
  --wait 30
```

**Why it works:** UNVERIFIED (2026-10-20): the resolution mechanism is not in either corpus. Deploys submitted one at a time after the previous one succeeds do run in order (api_meta 264 L4246-4249).

---

## Anti-Pattern: Deploying Permission Sets Built From Scratch Without Retrieving Current State

**What practitioners do:** Build a PermissionSet XML file from scratch (or use only the permissions they want to add), then deploy it to a target org where that permission set already has other permissions configured.

**What goes wrong:** The deployed XML is meant to carry all of the permission set's metadata (api_meta 264 L97416-97418); permissions in the target that are not in it are lost. UNVERIFIED (2026-10-20): "silently deleted". This is especially dangerous for PSets with many field-level security grants or object permissions built up over time.

**Correct approach:** Always retrieve the current PermissionSet from the target org first. Use the retrieved XML as the base. Add or modify only the permissions you intend to change. Deploy the resulting merged XML.
