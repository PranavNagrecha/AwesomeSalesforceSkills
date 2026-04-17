# Gotchas — Private Connect Setup

## Gotcha 1: Region mismatch

**What happens:** Setup step fails with 'region not supported'.

**When it occurs:** SFDC POD in different region than your VPC.

**How to avoid:** Confirm POD region first.


---

## Gotcha 2: DNS resolution

**What happens:** Callout resolves to public IP.

**When it occurs:** DNS override missing.

**How to avoid:** Use private endpoint DNS in Named Credential host.


---

## Gotcha 3: Billing surprise

**What happens:** Charges not expected.

**When it occurs:** Tenants assume Private Connect is included.

**How to avoid:** Confirm pricing in contract.

