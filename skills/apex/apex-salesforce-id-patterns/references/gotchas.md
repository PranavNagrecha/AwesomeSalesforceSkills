# Gotchas — Apex Salesforce Id Patterns

Non-obvious Salesforce platform behaviors that cause real production problems.

## Gotcha 1: 15-Char Ids Are Case-Sensitive, 18-Char Are Not

**What happens:** A `Set<String>` of 15-char Ids behaves differently from a `Set<String>` of 18-char Ids. Lookup fails silently for what looks like the same record.

**When it occurs:** CSV imports, report exports, URL parameters, or legacy integrations that send 15-char Ids.

**How to avoid:** Always cast through `Id` or store as `Set<Id>`. Never compare raw 15-char string to 18-char string.

---

## Gotcha 2: `Id.valueOf(str)` Throws `System.StringException`, Not `IllegalArgumentException`

**What happens:** Apex developers coming from Java wrap in `catch (IllegalArgumentException)` expecting it to catch — it never does, because Apex raises `System.StringException` (a subclass of `System.Exception`).

**When it occurs:** Any validation helper that handles invalid Id input.

**How to avoid:** Use `catch (System.StringException e)` or the broader `catch (Exception e)` at a trust boundary.

---

## Gotcha 3: Managed Package Prefixes Collide With Standard Objects

**What happens:** A managed package installed in the org uses a custom object with prefix `a00` — but the code hardcoded `a00` to mean a specific customer object. String-prefix routing sends records to the wrong handler.

**When it occurs:** Installing an AppExchange package, or cloning code between orgs with different custom object topologies.

**How to avoid:** Never hardcode custom prefixes. Use `Schema.SObjectType` comparisons via `getSobjectType()`.

---

## Gotcha 4: `getSobjectType()` Returns Null For `Id` Fields Obtained From `SELECT Id` On A Polymorphic Relationship Only If The Row Is Null

**What happens:** Uncommon, but if you cast a null `Id` field you get `null`, not an exception. `.getSobjectType()` then NPEs.

**When it occurs:** Polymorphic `WhoId`/`WhatId` on Task/Event, or optional lookup fields.

**How to avoid:** Null-check before type detection: `if (idValue != null && idValue.getSobjectType() == Contact.SObjectType) ...`.

---

## Gotcha 5: `Id` Does Not Validate Against Actual Record Existence

**What happens:** `Id.valueOf('001000000000000AAA')` succeeds — the prefix is valid for Account and the checksum is valid — but the record may not exist.

**When it occurs:** Anywhere you accept an Id and assume a downstream SOQL will find a record.

**How to avoid:** Never assume. Always SOQL with error handling, or check existence explicitly before the work.

---

## Gotcha 6: Serializing `Id` To JSON Drops The Type

**What happens:** `JSON.serialize(myAccount)` produces `"Id":"001..."` — a string. On deserialization, the field is a string until you cast back, losing type safety mid-flight.

**When it occurs:** REST APIs, Platform Event payloads, Aura-enabled methods returning wrappers.

**How to avoid:** In wrapper classes, type the Id field as `Id` (Apex deserialization honors this). In REST DTOs where you return `String`, document that callers must re-type.

---

## Gotcha 7: `String.isBlank(someId)` Compiles For `Id` Type

**What happens:** `Id myId = null; String.isBlank(myId);` compiles and returns true, but developers expect type-specific guards.

**When it occurs:** Defensive coding in helpers.

**How to avoid:** Use `myId == null` directly. `String.isBlank` is for user input, not typed Ids.

---

## Gotcha 8: External Id Fields Are Not Salesforce Ids

**What happens:** A developer treats `Account.External_Key__c` (marked External Id) as an Id and casts it. `StringException` at runtime.

**When it occurs:** Integrations that merge "Id" semantically (upsert keys) with the Salesforce Id primitive.

**How to avoid:** External Id fields are regular `String` / `Number`. Only use Apex `Id` type for actual 15/18-char Salesforce record identifiers.
