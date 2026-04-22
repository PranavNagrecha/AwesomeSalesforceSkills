# LLM Anti-Patterns — Compound Field Patterns

Common mistakes AI coding assistants make when working with Name/Address/Geolocation compound fields.

## Anti-Pattern 1: Filtering WHERE clause by compound field

**What the LLM generates:** `SELECT Id FROM Account WHERE BillingAddress = :address`

**Why it happens:** Model treats compound like a regular field.

**Correct pattern:**

```
Filter by components:
SELECT Id FROM Account
WHERE BillingCity = :city AND BillingState = :state AND BillingPostalCode = :zip

Compound fields are not queryable in WHERE (except DISTANCE on Geolocation).
```

**Detection hint:** SOQL `WHERE <Address field name> =` where the field is a known compound (BillingAddress, MailingAddress, ShippingAddress, OtherAddress).

---

## Anti-Pattern 2: Assigning the compound in DML

**What the LLM generates:**

```
c.MailingAddress = new Address(...);
update c;
```

**Why it happens:** Model mirrors the read pattern for writes.

**Correct pattern:**

```
Compound fields are read-only for DML. Assign components:
c.MailingStreet = '1 Main St';
c.MailingCity = 'SF';
c.MailingState = 'CA';
update c;
```

**Detection hint:** Apex assigning `record.<name>Address = ...` or `record.Name = ...` on standard objects.

---

## Anti-Pattern 3: Updating Name on a standard object

**What the LLM generates:** `acc.Name = 'Acme Inc'; update acc;` — fine on Account but `contact.Name = 'Jane Doe';` on Contact fails.

**Why it happens:** Model generalizes from one object to all.

**Correct pattern:**

```
Contact.Name is compound (FirstName + LastName + Salutation) and
cannot be set directly. Assign components:
c.FirstName = 'Jane'; c.LastName = 'Doe';

Account.Name and Custom__c.Name are plain text and can be assigned.
```

**Detection hint:** Apex assigning `Contact.Name`, `Lead.Name`, `Opportunity.Name` (Opportunity.Name IS text — tricky), `User.Name`.

---

## Anti-Pattern 4: Computing haversine distance in Apex

**What the LLM generates:** A 40-line Apex method computing great-circle distance between two geolocations.

**Why it happens:** Model doesn't know about the SOQL DISTANCE function.

**Correct pattern:**

```
SELECT Id, Name, DISTANCE(Location__c, GEOLOCATION(:lat, :lon), 'km') dist
FROM Store__c
ORDER BY DISTANCE(Location__c, GEOLOCATION(:lat, :lon), 'km')
LIMIT 10

DISTANCE works in SELECT, ORDER BY, and WHERE. Platform-optimized.
```

**Detection hint:** Apex class with `Math.cos`, `Math.sin`, `Math.sqrt` and latitude/longitude arguments.

---

## Anti-Pattern 5: Round-tripping address JSON via compound serialization

**What the LLM generates:** `JSON.serialize(c.MailingAddress)` sent to an API; API response deserialized back into `c.MailingAddress`.

**Why it happens:** Model assumes compound serialization is round-trippable.

**Correct pattern:**

```
Map to/from component fields explicitly in integration code:
{
  "street": c.MailingStreet,
  "city": c.MailingCity,
  ...
}

The compound's serialized form is not a documented contract and may
drop fields (geocode, stateCode) silently. Explicit mapping is stable.
```

**Detection hint:** Integration code serializing a compound field directly and deserializing back into the compound.
