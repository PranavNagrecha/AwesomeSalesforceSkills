# Gotchas — Mutual TLS Callouts

## Gotcha 1: CSR generated externally

**What happens:** Private key material uploaded; weaker security.

**When it occurs:** IT generated keypair on a workstation.

**How to avoid:** Generate CSR in Setup → SSL Certificate.


---

## Gotcha 2: Missing intermediate chain

**What happens:** Handshake fails.

**When it occurs:** Partner requires intermediate CA.

**How to avoid:** Import full chain into Certificate record.


---

## Gotcha 3: No expiry alert

**What happens:** Outage Friday night.

**When it occurs:** Default setup.

**How to avoid:** Scheduled probe + alert.

