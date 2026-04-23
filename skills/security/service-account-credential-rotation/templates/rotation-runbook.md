# Credential Rotation Runbook

## Credential

- Type (user password / client secret / JWT cert / named credential):
- Owner:
- Consumers:
- Storage locations (vault paths):

## Pre-Rotation

- [ ] Inventory up to date.
- [ ] Consumer list confirmed.
- [ ] Change ticket opened.
- [ ] Maintenance window (if needed) scheduled.
- [ ] Backout plan documented.

## Rotation Steps

1. Generate new credential.
2. Publish to vault.
3. Activate (add cert / issue secret) on Salesforce.
4. Cutover or grace-window start.
5. Confirm consumers using new credential.
6. Revoke old credential at window close.

## Post-Rotation Verification

- [ ] Login history shows successful auth with new credential.
- [ ] Business transaction smoke test passed.
- [ ] No 401/403 spikes in consumer telemetry.
- [ ] Old credential revoked and confirmed invalid.

## Follow-Up

- Next rotation date:
- Detector entry confirmed (stale-credential job):
