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
*seven* components. The Object Reference field table confirms the
gating: `StateCode` "is available only when state and
country/territory picklists are enabled in your organization",
and the same applies to `CountryCode` on standard addresses
(object_reference.txt L2705–L2722). The text fields don't
disappear; they become derived values that the platform populates
from the code lookup. UNVERIFIED (2026-09-04): the back-fill
direction — code populates text — is not stated in the extracted
Object Reference, Metadata API, Apex Reference or Data Loader
PDFs; what those files do ground is that `Address.getStateCode()`
returns null when the picklists are off (apexrefguide.txt
L199256–L199258). Confirm the back-fill in a sandbox with the
verification query in `metadata-examples.md` §9 before designing
around it.

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
4. **Selecting the raw compound value is surface-scoped.** The
   current wording is "Compound fields are accessible only through
   SOAP API, REST API, and Apex. The compound versions of fields
   aren't accessible anywhere in the Salesforce user interface"
   (object_reference.txt L2913–L2914) — Apex is included, so
   `Address addr = acct.BillingAddress;` is legitimate. Older
   guidance that named only SOAP and REST is stale. What stays out
   of reach is every UI surface: report columns, Visualforce,
   formulas, Data Loader export. `DISTANCE`/`GEOLOCATION` are also
   unavailable in `GROUP BY` (object_reference.txt L2969–L2970), so
   bucketing records by distance band in a single aggregate query
   isn't possible.

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


---

## Gotcha 7: Data Loader *errors* on a compound field instead of ignoring it, and the error names the field, not the rule

**What happens:** Select "Billing Address" in the Data Loader
export field picker and the export fails. The guide is blunt
about it: "If you select compound fields for export in the Data
Loader, they cause error messages. To export values, use
individual field components" (salesforce_data_loader.txt L918–L919;
the same sentence appears in the Object Reference limitations
list at object_reference.txt L2931–L2932). This is the *export*
direction. On the import side there is no `MailingAddress` column
to map at all — the compound never appears in the mapping dialog —
so the same practitioner meets two different symptoms for one
rule and concludes the tool is inconsistent.

**When it occurs:** During a migration dry run, almost always.
Someone builds the extract query in the Data Loader UI by
ticking every field that looks relevant, hits the compound, and
loses an afternoon to what reads like a permissions or session
error. It also bites automated extracts: a saved `.sdl` mapping
built before State and Country/Territory Picklists were enabled
keeps referencing `MailingState` after the flip, and the load
succeeds while writing to the non-authoritative column.

**How to avoid:** Enumerate components explicitly in the extract
SOQL and in the mapping file — `MailingStreet`, `MailingCity`,
`MailingStateCode`, `MailingPostalCode`, `MailingCountryCode`,
`MailingLatitude`, `MailingLongitude` — and never let the field
picker choose for you. `references/metadata-examples.md` §6
carries both CSV headers, picklists-on and picklists-off. For the
load-planning workflow around this, see `data/soql-query-optimization`
for the extract query and `admin/data-model-documentation` for how
to record a compound in a field inventory.

---

## Gotcha 8: `enableCustomAddressField` is a one-way door, and it propagates through sandbox refreshes

**What happens:** `CustomAddressFieldSettings.enableCustomAddressField`
turns the `Address` custom field type on for the org. The guide
states the constraint in the field description itself: "Custom
Address Fields can't be disabled. When `enableCustomAddressField`
is set to `true`, you can't change the value to `false`"
(api_meta.txt L113905–L113909). There is no "we'll try it in a
sandbox and back it out" path — and a sandbox refreshed from a
production org that has it on comes back with it on.

**When it occurs:** A team evaluating whether to model a second
address as a compound rather than five text fields deploys the
settings file into a developer sandbox to "have a look". The
setting is now permanent in that sandbox. If someone then
promotes the settings file as part of a bundled deploy — settings
files travel as a directory, and `--source-dir
force-app/main/default/settings` sweeps all of them — production
inherits it without anyone deciding.

**How to avoid:** Deploy settings files by explicit path, never
by sweeping the `settings` directory, and always with `--dry-run`
first. Retrieve `Settings:CustomAddressField` from production
before any deploy that touches settings and diff it. Note also
what custom address fields do *not* inherit: `GeocodeAccuracy`
"is only available for standard address fields on standard
objects" (object_reference.txt L2740–L2743), and automatic
geocoding covers only Account, Contact, Lead, and WorkOrder
(object_reference.txt L2943–L2948). Their one advantage over a
standard address is that `CountryCode` "is always available,
whether or not state and country/territory picklists are enabled"
(object_reference.txt L2705–L2707).

---

## Gotcha 9: Three formula functions accept a compound; validation rules accept none — but `DISTANCE` formulas are allowed in four places

**What happens:** Three overlapping rules that people collapse
into one wrong rule ("compound fields don't work in formulas"):

1. **Formula functions.** "The only formula functions that you
   can use with compound fields are `ISBLANK`, `ISCHANGED`, and
   `ISNULL`. You can't use `BLANKVALUE`, `CASE`, `NULLVALUE`,
   `PRIORVALUE`, or the equality and comparison operators with
   compound fields" — the excluded operators are enumerated as
   `=`, `==`, `<>`, `!=`, `<`, `>`, `<=`, `>=`, `&&`, `||`
   (object_reference.txt L2936–L2939).
2. **Validation rules.** Independently of (1), the whole feature
   refuses them: "As of API version 20.0, validation rules can't
   have compound fields. Examples of compound fields include
   addresses, first and last names, dependent picklists, and
   dependent lookups" (api_meta.txt L45369–L45371). So
   `ISBLANK(BillingAddress)` is a legal *function* call and still
   an illegal *validation rule*.
3. **`DISTANCE` formulas.** These are explicitly supported in
   entry criteria for workflow rules and approval processes,
   field update actions in those, custom validation rules, and
   lookup filters — the last "in the Metadata API only"
   (object_reference.txt L2957–L2961, L2934–L2935).

**When it occurs:** The most-requested address validation rule —
"Billing Address is required before an Account can be activated"
— fails at compile time in Setup, with an error that names the
field rather than the category. A developer who then reads only
rule (1) writes `ISBLANK(BillingAddress)` into a validation rule
and hits rule (2). Someone who reads only rule (2) concludes
geolocation can never appear in a validation rule and hand-rolls
a proximity check in a trigger, missing rule (3).

**How to avoid:** For "the address is filled in", validate the
components — `admin/validation-rules` carries the component-level
rewrite in its "Compound Fields Cannot Be Used in a Validation
Rule at All" gotcha. For "this record is within N miles of X",
use a `DISTANCE` formula, which is supported in a custom
validation rule. For a distance-bounded lookup filter, write it
through the Metadata API; the Setup UI has no path to it.

---

## Gotcha 10: `DescribeFieldResult.isFilterable()` returns `true` for address fields and the query still fails

**What happens:** The describe API reports address compound
fields as filterable. SOQL rejects them. The Object Reference
says so in as many words: "Address fields can't be used in WHERE
statements in SOQL. Address fields aren't filterable, but the
`isFilterable()` method of the `DescribeFieldResult` Apex class
erroneously returns `true` for address fields"
(object_reference.txt L2950–L2951). It is documented as a bug
that will not be fixed, because fixing it would break callers
that already compensate.

**When it occurs:** In dynamic query builders and generic list
components — anything that walks `getDescribe()` to decide which
fields to offer as filters. The compound sails through the
`isFilterable()` gate, lands in a `WHERE` clause, and the query
throws `MALFORMED_QUERY` at runtime for one specific object
while working everywhere the developer tested. It also breaks
generated code: an assistant asked to "only filter on filterable
fields" will produce exactly this bug and its reasoning will look
correct.

**How to avoid:** Add an explicit compound exclusion in front of
the `isFilterable()` check rather than trusting it. Two
serviceable tests: `getSOAPType()` is `System.SOAPType.ADDRESS`
for an address compound, and `getCompoundFieldName()` is non-null
on the *components* of a compound. The single exception to the
exclusion is `DISTANCE(...)`, which is a function call, not a
field filter — build it as a separate branch. `scripts/check_compound_field_patterns.py`
flags a bare compound in `WHERE` as an ERROR precisely because no
describe flag will.

---

## Gotcha 11: Dot notation through the parent field does not compile, and `Address` / `Location` collide with standard object names

**What happens:** Two Apex-only traps that produce compile errors
whose text points at the wrong thing.

First, you cannot chain from the record into a compound's
components: "You can't use dot notation to access compound
fields' subfields directly on the parent field. Instead, assign
the parent field to a variable of type `Address`, and then access
its components" (apexrefguide.txt L199180–L199182; the same
instruction for `Location` at L221916–L221918). So
`myAccount.BillingAddress.City` is invalid and
`Address addr = myAccount.BillingAddress; String c = addr.City;`
is the documented form.

Second, `Address` and `Location` are both standard *object* names
as well as compound field types. The guide's instruction is to
disambiguate explicitly: "'Address' in Salesforce can also refer
to the Address standard object… always use `Schema.Address`
instead of `Address`… you can differentiate between the two by
using `System.Address` for the field and `Schema.Address` for the
object" (apexrefguide.txt L199187–L199190), with the identical
warning for `Location` (apexrefguide.txt L221921–L221924).

**When it occurs:** The dot-notation trap surfaces the first time
someone inlines an address read into a string concatenation or a
map literal. The name collision surfaces later and worse: a class
that compiled for years starts failing after an org enables a
feature that exposes the `Address` or `Location` standard object,
and the error — an unexpected type mismatch on a variable
declaration — gives no hint that a namespace changed underneath
it.

**How to avoid:** Declare compound locals as `System.Address` and
`System.Location` everywhere, not as bare `Address` / `Location`,
even in code that compiles today. Assign the parent field to that
local before reading any component. Writes still go to the
component fields directly — `acct.BillingCity`,
`acct.Store_Location__Latitude__s` — never through the typed
local, which is read-only. `references/metadata-examples.md` §5
carries the full read-and-write class.
