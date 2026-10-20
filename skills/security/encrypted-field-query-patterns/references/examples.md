# Encrypted Field Query — Examples

## Example 1: Customer SSN (Display Only)

- Field: `SSN__c` on Contact.
- Queries: none — the field is displayed in a detail view, never filtered.
- Scheme: **probabilistic**.
- Indexing: none.

## Example 2: National ID (Lookup By Exact Value)

- Field: `NationalId__c` on Person Account.
- Queries: `SELECT Id FROM Account WHERE NationalId__c = :value`.
- Scheme: **deterministic case-sensitive** (national IDs are
  case-stable).
- Indexing: custom index requested, unique.

## Example 3: Customer Email Address

- Field: `Email__c`.
- Queries: exact match case-insensitive (`jane@foo.com` == `Jane@Foo.com`).
- Scheme: **deterministic case-insensitive**.
- Indexing: custom index.

## Example 4: Transaction Amount

- Field: `Amount__c`.
- Queries: `WHERE Amount__c > 10000`, SUM in reports.
- Scheme: **do not encrypt**. Encryption blocks range and aggregate
  (UNVERIFIED (2026-10-20): see SKILL.md Scheme Matrix).
- Alternative: leave unencrypted; enforce FLS + masking for non-privileged
  users.

## Example 5: Customer Last Name With LIKE Search

- Field: `LastName` (standard).
- Queries: `WHERE LastName LIKE 'Sm%'`.
- Scheme: encryption blocks LIKE (UNVERIFIED (2026-10-20): see SKILL.md
  Scheme Matrix). Options:
  1. Skip encryption (accept risk).
  2. Encrypt AND add a one-way hashed `LastNameTokenPrefix__c`
     populated in a trigger with
     `EncodingUtil.convertToHex(Crypto.generateDigest('SHA-256', Blob.valueOf(LastName.left(3).toUpperCase())))`
     — Apex has no `HASH()`; `generateDigest` "Computes a secure, one-way hash
     digest" (apexref 262 L203794-203795; SHA-256 is a valid value, L203816). Filter on the hash field for prefix search (imperfect).
  3. Store only under pseudonym; keep lookup separate.

## Example 6: Mixed-Permission Test Plan

- User A: FLS Read granted on the encrypted field.
- User B: FLS Read removed on the encrypted field.
- For each flow: list view, report, Apex dashboard, LWC detail — verify
  A sees plaintext and B cannot retrieve the field at all, with no
  functional error.
- Do **not** build this matrix on "View Encrypted Data". That permission
  is Classic Encryption only (secguide 262 L2548); toggling it changes
  nothing for a Shield-encrypted field (UNVERIFIED (2026-10-20): Help only).

## Example 7: Schema Decision Log

```text
| Field              | Scheme                   | Reason                          |
|--------------------|--------------------------|---------------------------------|
| Contact.SSN__c     | Probabilistic            | display only                    |
| Account.NationalId | Deterministic CS         | exact lookup, case-stable       |
| Contact.Email      | Deterministic CI         | case-insensitive exact lookup   |
| Opp.Amount__c      | Not encrypted            | range + aggregate incompatible  |
```
