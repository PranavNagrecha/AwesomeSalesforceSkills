# Snapshot Operations Reference

One page for the operational facts a snapshot pipeline depends on. All values are from the Salesforce DX Developer Guide (Summer '26); see `well-architected.md` for line references.

## Allocations

| Dev Hub edition | Active and daily snapshot allocation |
|---|---|
| Developer Edition | 3 |
| Enterprise Edition | 40 |
| Unlimited Edition | 100 |
| Performance Edition | 100 |

Check remaining allocation with `sf org list limits -o <dev-hub>` and read `ActiveOrgSnapshots` and `DailyOrgSnapshots`.

## Lifecycle and status

| Stage | What to know |
|---|---|
| Create | `sf org create snapshot --name <15 alphanumeric> --source-org <scratch> --target-dev-hub <hub> --description <text>` |
| Status | `OrgSnapshot.Status`: `New` → `In Progress` → `Active` (or `Error`); later `Expired`. The CLI prints `InProgress`. |
| Use | Only once `Active`; the scratch org's Dev Hub must be the snapshot's Dev Hub |
| Update | Not possible in place: delete and create another |
| Expiry | 90 days; licence freed immediately on expiry or delete; data deleted later |

Poll in CI with SOQL against the Dev Hub:

```bash
sf data query --target-org my-dev-hub --json \
  --query "SELECT SnapshotName, Status, ExpirationDate FROM OrgSnapshot ORDER BY CreatedDate DESC"
```

## Permissions for non-admin users

Dev Hub admins can create and manage snapshots by default. Other users need a Salesforce, Salesforce Platform, or Salesforce Limited Access license and a permission set granting Org Snapshots object access (View All Records to see others' snapshots; Modify All Records, Salesforce licence only, to delete them), plus access to the scratch org objects.

## Release-version behaviour

| Dev Hub release | Snapshot release | Scratch org release |
|---|---|---|
| Current | Current | Current |
| Current | Preview | Preview |
| Preview | Current | Current |
| Preview | Preview | Preview |

Rebuild the snapshot when a preview window opens or closes if the CI org must match the Dev Hub's release.
