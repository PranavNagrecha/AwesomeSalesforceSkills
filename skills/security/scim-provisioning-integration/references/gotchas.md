# SCIM Provisioning — Gotchas

## 1. Salesforce Deactivates, Never Deletes

SCIM `DELETE` or `PATCH active=false` deactivates the user. Users with any record ownership cannot be deleted outright.

## 2. OAuth Tokens Survive Deactivation

Active connected app tokens can continue to work after a user is deactivated. Revoke tokens explicitly in the deprovisioning runbook.

## 3. Permission Set License vs Permission Set

Assigning a Permission Set that requires a PSL will fail silently if the PSL is not pre-assigned. SCIM mapping must handle both.

## 4. Role Hierarchy Is Outside SCIM

Role Hierarchy (a Salesforce concept) is not in the SCIM model. If roles drive sharing, you need a downstream Apex or Flow layer.

## 5. Freeze ≠ Deactivate

Freezing blocks new logins instantly. Deactivation releases the license and blocks API token use — but can lag a few minutes. For tight SLAs, freeze first.
