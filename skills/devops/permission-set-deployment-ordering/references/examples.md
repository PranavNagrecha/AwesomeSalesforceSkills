# Examples — Permission Set Deployment Ordering

## Example 1: Silent Permission Loss During Sandbox-to-Sandbox Deployment

**Context:** A developer creates a new permission set in a developer sandbox to grant access to three new custom fields. They package the permission set into a deployment package and deploy to a full copy sandbox where the permission set already exists with 25 existing field permissions.

**Problem:** After deployment, users report they can no longer access 22 fields they previously could. The developer only intended to add three new field permissions, but the PermissionSet XML in the deploy package only contained those three fields. The Metadata API performed a full-replace, wiping out the 22 existing permissions silently.

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

**Why it works:** By retrieving the target org's authoritative state and merging the new permissions into it, the deployed XML is a complete superset. The full-replace now replaces with the complete intended set, preserving all previous grants.

---

## Example 2: ConnectedApp Cross-Reference Error Blocking Production Deploy

**Context:** A DevOps team is releasing a new integration feature. The release package includes: (a) a new ConnectedApp for the integration's OAuth configuration, and (b) a PermissionSet that grants users access to that ConnectedApp. Both are in the same deployment job run via `sf project deploy start`.

**Problem:** The deploy fails with a cross-reference id error on the PermissionSet. This is a known platform bug: when a ConnectedApp and a PermissionSet or PSG referencing it are deployed in the same batch, the reference cannot be resolved during validation.

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

**Why it works:** Separating the ConnectedApp into its own deploy allows it to be fully committed before the PermissionSet's reference to it is evaluated. The platform can resolve the cross-reference when the ConnectedApp already exists.

---

## Anti-Pattern: Deploying Permission Sets Built From Scratch Without Retrieving Current State

**What practitioners do:** Build a PermissionSet XML file from scratch (or use only the permissions they want to add), then deploy it to a target org where that permission set already has other permissions configured.

**What goes wrong:** The Metadata API treats the deployed XML as the complete truth. All permissions in the target org that are not in the deployed XML are silently deleted. This is especially dangerous for PSets with many field-level security grants or object permissions built up over time.

**Correct approach:** Always retrieve the current PermissionSet from the target org first. Use the retrieved XML as the base. Add or modify only the permissions you intend to change. Deploy the resulting merged XML.
