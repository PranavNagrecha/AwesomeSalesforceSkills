# Gotchas — Compound Field Patterns

Non-obvious platform behaviors that bite once you're past the
basic "SELECT compound works, DML compound doesn't" rules. These
are the second-order quirks that surface during integration
work, package installs, and FLS reviews — the ones that don't
appear in the SKILL.md table but cost half-days to track down.

## Gotcha 1: Enabling State & Country Picklists silently doubles every address's component count

**What happens:** Before State & Country Picklists are enabled,
`Account.BillingAddress` exposes five text components plus
lat/lon: `BillingStreet`, `BillingCity`, `BillingState`,
`BillingPostalCode`, `BillingCountry`. After enabling the
feature, the platform adds `BillingStateCode` and
`BillingCountryCode` (picklist-backed) alongside the original
text fields — every address compound on every standard object
(Account, Contact, Lead, User, Contract, Quote, Order) now has
*seven* components. The text fields don't disappear; they
become derived values that the platform populates from the
code lookup.

**When it occurs:** Most often during a Salesforce data hygiene
project — the team enables State & Country Picklists in a sandbox
to standardize values, runs an integration that writes to
`BillingState = 'CA'`, and discovers in production that the
integration now needs to write to `BillingStateCode = 'CA'`
instead. Direct writes to the text field after picklists are
enabled save the literal string but leave the `-Code` field
null, which breaks any downstream filter or report that uses
the code. The picklist-vs-text drift is invisible in Schema
Builder unless you specifically inspect the field list.

**How to avoid:** Treat State & Country Picklists as a
breaking change for every integration that writes addresses.
Audit `MetadataAPI` for every Apex class, Flow, Process Builder,
data load template, and external integration that assigns
`BillingState`, `ShippingState`, `MailingState`, or `Country`
text fields. Switch each one to the `-Code` equivalent before
flipping the feature on in production. The official guidance
("Impact on Apex code if State and Country Picklists feature is
enabled") explicitly warns that any code referencing the text
field by API name continues to compile but produces inconsistent
data; there is no compile-time check.

---

## Gotcha 2: `Name` is plain text on Account and Custom Objects, compound on Contact/Lead/User

**What happens:** `Account.Name` is a single text field — you
can assign it directly (`acc.Name = 'Acme Corp'`) and DML works
fine. `Contact.Name`, `Lead.Name`, and `User.Name` are compound
fields composed of `FirstName`, `LastName`, and `Salutation`
(plus `Suffix` and `MiddleName` if those middle-name and suffix
features are enabled). Assigning `contact.Name = 'Jane Doe'`
fails with `INVALID_FIELD_FOR_INSERT_UPDATE, Name: Name is
not createable`. Custom object `Name` fields are plain text
unless explicitly defined as the "Person Name" type during
custom object creation (uncommon).

**When it occurs:** Most frequently in generic data-copy code
that loops across multiple SObjects and copies "all fields" —
the developer writes `target.Name = source.Name` assuming
symmetry across objects, and the code works on Account but
silently breaks on Contact. The Contact failure happens at DML
time, often after the Account copies have succeeded, leaving
the transaction half-committed if the records were processed
in separate DML statements. Also surfaces with LLMs that
generate code based on patterns from one object type.

**How to avoid:** Hard-code a per-object check before copying
the `Name` field. The pragmatic rule:

| Object | Name behavior | DML assignment |
|---|---|---|
| Account (non-Person) | Plain text | `acc.Name = 'X'` works |
| Account (Person) | Compound, see Gotcha 3 | `acc.FirstName = 'X'` |
| Contact, Lead, User | Compound | `c.FirstName = 'X'; c.LastName = 'Y'` |
| Opportunity, Case | Plain text | `o.Name = 'X'` works |
| Custom__c (default) | Plain text | `r.Name = 'X'` works |

When in doubt, check `Schema.DescribeFieldResult.getSOAPType()`
on the `Name` field — `STRING` means text, `STRING` with
`isNameField() == true` and `getCompoundFieldName() != null`
means compound.

---

## Gotcha 3: Person Account `Name` flips between plain-text and compound based on RecordType

**What happens:** Person Accounts are an Account with a
RecordType that uses the IsPersonAccount = TRUE flag. For a
business-Account record, `Name` behaves as plain text (Gotcha 2
table). For a Person-Account record on the SAME object, `Name`
behaves as a compound field built from `FirstName` and
`LastName`. The schema metadata returns the *business-account*
shape — `Account.Name` is reported as a text field — but DML
against a Person Account record rejects `Name` assignments with
the same compound-field error as Contact. The behavior depends
on the runtime record, not the metadata.

**When it occurs:** Mixed-mode orgs that use both business
Accounts and Person Accounts hit this constantly. A trigger
that touches `Account.Name` works in unit tests (which usually
create one type or the other, not both) and breaks in production
the first time it processes a mixed batch. The error message —
"Name: Name is not createable" — is identical to the Contact
error and gives no hint that Person Account is the cause.

**How to avoid:** Guard every `Account.Name` write with
`if (acc.IsPersonAccount == false)`. For Person Accounts,
write to `FirstName` and `LastName` instead. In bulk code,
partition the batch into two collections by `IsPersonAccount`
and DML each separately:

```apex
List<Account> personAccts = new List<Account>();
List<Account> businessAccts = new List<Account>();
for (Account a : scope) {
    if (a.IsPersonAccount) personAccts.add(a);
    else                    businessAccts.add(a);
}
// Apply different field maps to each
```

The `IsPersonAccount` field is null on the object in orgs where
Person Accounts have never been enabled, so add a null-safe
check (`a.IsPersonAccount == true`) to keep the code portable
across orgs.

---

## Gotcha 4: FLS gates each component independently, not the compound as a whole

**What happens:** A profile or permission set can grant
read/edit on `MailingCity` but deny read/edit on `MailingCountry`
— and the platform enforces this independently. SOQL
`SELECT MailingAddress FROM Contact` returns a compound where
the inaccessible component is silently `null`, not blocked. The
record looks like it has no country. In LWC,
`@wire(getRecord, { fields: ['Contact.MailingAddress'] })`
returns the compound with the inaccessible components missing
from the response payload entirely (not even a `null` key).

**When it occurs:** Most commonly in regulated industries
(financial services, healthcare) where field-level security is
locked down at the component level for compliance reasons. A
developer building a "Contact Card" LWC sees the rendered
address missing the State and Country lines for some users,
assumes the field is empty in the database, and creates a data-
quality ticket — when the actual problem is FLS on
`MailingStateCode` and `MailingCountryCode` for the user's
profile. The bug is invisible to the developer (who's testing
as System Administrator) and visible only to the affected
business users.

**How to avoid:** When designing FLS for address-bearing
objects, treat all components of a compound field as a single
unit — either grant access to all of them or revoke all of
them. Document this rule in your permission-set governance.
For diagnostics, use the User Access tool (`Setup → Users →
[user] → View All` then "Sharing"/"Field Accessibility") to
audit component-level FLS. In Apex, prefer
`Schema.SObjectField.getDescribe().isAccessible()` per
component over assuming the compound rolls up.

---

## Gotcha 5: `JSON.serialize(compoundField)` output is not a documented contract and changes silently

**What happens:** `JSON.serialize(contact.MailingAddress)`
returns a JSON object that *looks* stable —
`{"city":"SF","state":"CA","street":"1 Main",...}` — but the
property names, casing, and presence of optional keys
(`geocodeAccuracy`, `latitude`, `longitude`, `stateCode`,
`countryCode`) vary by API version, by whether State & Country
Picklists are enabled, and occasionally between releases. The
shape has never been published as a stable API contract; it's a
side effect of how the runtime introspects the Address class.
Code that round-trips through this serialization (serialize
locally, send to an external system, get the same JSON back,
deserialize into an `Address`) breaks unpredictably on org-
config changes.

**When it occurs:** Integration patterns that "just pass
addresses around" — webhook payloads, mock data fixtures, and
inter-system caching layers are the usual victims. A version
bump on the Salesforce side or a state-country-picklist enable
in a sandbox produces a JSON shape the downstream parser
doesn't recognize. The failure manifests as missing fields, not
errors, so the integration silently degrades.

**How to avoid:** Never serialize a compound field as the wire
format. Always map components to your own DTO with named
properties you control:

```apex
public class AddressDTO {
    public String street, city, state, postalCode, country;
    public Decimal latitude, longitude;

    public static AddressDTO fromContact(Contact c) {
        AddressDTO dto = new AddressDTO();
        dto.street     = c.MailingStreet;
        dto.city       = c.MailingCity;
        dto.state      = c.MailingState;
        dto.postalCode = c.MailingPostalCode;
        dto.country    = c.MailingCountry;
        dto.latitude   = c.MailingLatitude;
        dto.longitude  = c.MailingLongitude;
        return dto;
    }
}
String wire = JSON.serialize(AddressDTO.fromContact(c));
```

The explicit DTO makes the wire format reviewable, versionable,
and immune to platform-side shape changes. The same rule
applies to `Name` and Geolocation compound fields — never wire-
serialize the compound; always map to components first.

---

## Gotcha 6: `DISTANCE` has four constraints that look like ordinary SOQL but aren't

**What happens:** `DISTANCE` and `GEOLOCATION` read like normal
functions, so it's easy to write variants the parser rejects at
query time — or that the platform simply refuses. Four rules from
the location-based SOQL reference are non-obvious:

1. **`DISTANCE` in `WHERE` supports only `>` and `<`.** The docs
   state it "supports only the logical operators > and <,
   returning values within (<) or beyond (>) a specified radius."
   There is no `=`, `>=`, or `<=` — the value is an approximate
   floating-point distance, so equality is meaningless.
   `WHERE DISTANCE(...) = 5` fails.
2. **The unit must be a literal.** Supported units are `'mi'`
   (miles) and `'km'` (kilometers) only, and "Apex bind variables
   aren't supported for the units parameter in the DISTANCE
   function." You can bind the coordinates
   (`GEOLOCATION(:lat, :lon)`) but not the unit — `DISTANCE(
   Location__c, GEOLOCATION(:lat, :lon), :unit)` won't compile.
3. **Argument order is fixed.** "If you use a location field and
   a GEOLOCATION value, the location field must be the first
   variable and the GEOLOCATION must be the second variable."
   Reversing them — `DISTANCE(GEOLOCATION(...), Location__c,
   'mi')` — is invalid.
4. **Selecting the raw compound value is API-scoped.** The same
   reference notes "Compound fields can only be used in SOQL
   queries made through the SOAP and REST APIs." The `DISTANCE`
   and `GEOLOCATION` *functions* run fine in Apex inline SOQL (see
   examples.md, Example 2), and a query that returns the whole
   compound value is served through the SOAP and REST APIs; in
   Apex, read the individual `__Latitude__s` / `__Longitude__s`
   components. `DISTANCE`/`GEOLOCATION` are also unavailable in
   `GROUP BY`, so bucketing records by distance band in a single
   aggregate query isn't possible.

**When it occurs:** Store-locator and territory-assignment
features are the usual triggers. A developer parameterizes a
query for reuse — binding the unit so the same method serves both
a US (`'mi'`) and an EU (`'km'`) audience — and the class won't
compile. Or a query author writes `WHERE DISTANCE(...) = 0` to
find records "at" a point and gets a malformed query. Or a
generated method flips the `GEOLOCATION` value ahead of the
location field and the query is rejected only at runtime.

**How to avoid:** Treat the unit as a compile-time constant —
branch in Apex and emit a separate literal query string per unit
if you truly need both. Filter radii with `<` (within) or `>`
(beyond) only; there is no equality test. Keep the location field
first and `GEOLOCATION` second. When you need the compound value
itself rather than a distance, go through the SOAP or REST API, or
read the individual latitude/longitude components in Apex.
