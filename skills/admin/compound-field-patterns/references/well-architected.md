# Well-Architected Notes — Compound Field Patterns

## Relevant Pillars

Compound fields look like a convenience feature — one field that
holds an address or a name — but the way the platform exposes
them differs across SOQL, DML, LWC, Reports, and integrations.
The architectural risk is not in any single surface; it's that
the same field behaves differently on each one, and code that
doesn't respect those differences fails in non-obvious ways.
Four pillars carry the most weight.

- **Reliability** — The leading source of compound-field
  failures is silent data inconsistency: writes succeed but
  populate the wrong field (text vs `-Code` after State &
  Country Picklists), or compound serialization round-trips
  drop optional keys (geocodeAccuracy, latitude). Neither
  pattern raises an exception; both surface weeks later as
  "the report is missing records." Reliability here means
  designing every read and every write to be component-aware
  from day one, not retrofitting after the first incident.
- **Performance** — Geolocation proximity queries are the
  canonical example of the platform doing heavy lifting if you
  let it: SOQL `DISTANCE(...) ORDER BY DISTANCE(...) LIMIT 10`
  uses indexed bounding-box math at the database tier and
  returns in tens of milliseconds for 100K+ records. The
  equivalent in Apex (pull all rows, compute Haversine, sort)
  is two orders of magnitude slower and chews through SOQL row
  and CPU governor limits. Letting the platform compute beats
  hand-rolling it.
- **Security** — FLS gates each compound component
  independently. A profile can grant `MailingCity` and deny
  `MailingCountryCode`, and SOQL returns the compound with the
  inaccessible component silently `null`. In LWC the missing
  components vanish from the payload entirely. Reviewing FLS
  per-compound (treating "the address" as one access decision)
  is the only way to stop the rendered output from looking like
  bad data.
- **Operational Excellence** — The set of fields exposed by a
  compound is configuration-dependent: enabling State & Country
  Picklists adds `-Code` components to every address on every
  standard object simultaneously. Enabling Person Accounts
  flips `Account.Name` from text to compound at the record
  level. Both changes are irreversible in production and
  silently break existing code that didn't account for them.
  An operational discipline of "what config flags can change
  the field shape, and what depends on the current shape" is
  the only way to stage these enables without an outage.

## Architectural Tradeoffs

The defining tradeoff is **how you read and write addresses
across systems**: as the compound (one logical field, platform
chooses the shape) or as components (explicit per-field reads
and writes). The honest answer is "compound for reads, components
for writes" — but the matrix is more nuanced once you cross
surfaces.

| Surface | Compound works? | Components work? | Recommendation |
|---|---|---|---|
| SOQL `SELECT` | Yes — returns Address/Location object | Yes — explicit list | Compound when you want all fields; components when you want a subset |
| SOQL `WHERE` | No (except `DISTANCE` on Geolocation) | Yes | Always components; the one exception is `DISTANCE` |
| SOQL `ORDER BY` | No (except `DISTANCE` on Geolocation) | Yes | Always components or `DISTANCE` |
| SOQL `GROUP BY` | No | Yes | Always components |
| Apex DML | No — read-only on the compound | Yes | Always components |
| Apex read | Yes — typed Address/Location | Yes — typed primitives | Compound for display; components for logic |
| LWC `getRecord` | Yes — returns `displayValue` formatted | Yes — explicit field paths | Compound for display; components for editing |
| Report column | Yes — renders block | Yes — individual columns | Compound for display layouts; components when columns need sorting/filtering |
| Report filter | No | Yes | Always components |
| JSON.serialize | Yes — but shape is undocumented | Yes — explicit DTO | Always components via DTO (see gotcha 5) |
| Formula field reference | No (compound is not referenceable) | Yes | Always components |
| Validation Rule | No | Yes | Always components |

A second tradeoff: **standard Address fields vs custom Address
fields**. Standard Address compounds (e.g., `BillingAddress`)
have years of platform tooling behind them — Report Builder
columns, LWC `lightning-input-address`, automatic geocoding via
Salesforce's Data.com / Maps integration. Custom Address fields
(introduced as a custom field type, available since Winter '23
on some objects) give you a compound shape on objects that
don't have one natively, but lose the auto-geocoding and many
of the standard UI affordances. Use custom Address fields only
when (a) you need a second address on an object that already
has one, or (b) the object has no standard Address at all and
you want compound semantics rather than rolling your own with
five text fields.

A third tradeoff: **Geolocation compound vs separate Lat/Lon
custom fields**. Geolocation compound enables `DISTANCE()` and
`GEOLOCATION()` functions in SOQL — the platform indexes the
field for proximity. Two independent `Decimal(9,6)` fields
named `lat__c` and `lon__c` don't enable `DISTANCE()`. If
proximity is on the roadmap (even theoretically), use
Geolocation compound from the start; converting two decimals
into a Geolocation later requires a one-time data migration
and breaks every integration that touches the old field names.

## Anti-Patterns

1. **Filtering by the compound field name in WHERE or report
   filters.** Compound fields are not filterable except for the
   single `DISTANCE` exception on Geolocation. The pattern
   surfaces in both hand-written SOQL (where it errors at
   query time) and Report Builder (where the field doesn't
   appear in the filter picker, leading to "address filtering
   doesn't work" tickets). Always filter by components.
2. **Assigning a compound in Apex DML.** Compounds are read-
   only for DML across every object — `c.MailingAddress =
   new Address(...)` throws `INVALID_FIELD_FOR_INSERT_UPDATE`.
   Always assign components individually.
3. **Computing Haversine distance in Apex when SOQL `DISTANCE`
   exists.** Pulling all rows and computing distance client-side
   wastes SOQL governor budget and Apex CPU. The platform's
   `DISTANCE` function is indexed and orders of magnitude
   faster; use it in SELECT, WHERE, and ORDER BY.
4. **Writing to the State text field when State & Country
   Picklists are enabled.** Direct writes to `MailingState =
   'CA'` save the string but leave `MailingStateCode` null,
   silently breaking every downstream filter that uses the
   code. Always assign the `-Code` field when picklists are on;
   let the platform back-fill the text field.
5. **Serializing compound fields as the wire format for
   integrations.** `JSON.serialize(c.MailingAddress)` produces
   a JSON shape that is not a documented contract — the keys,
   casing, and presence of optional fields (stateCode,
   geocodeAccuracy) vary by API version and org config.
   Integrations that round-trip through compound serialization
   break unpredictably on platform updates. Always map to an
   explicit DTO.

## Official Sources Used

- Compound Fields — Object Reference:
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/compound_fields.htm
- Address Compound Fields — Object Reference:
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/compound_fields_address.htm
- Geolocation Compound Field — Object Reference:
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/compound_fields_geolocation.htm
- SOQL SELECT with Compound Fields:
  https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_compound_fields.htm
- Location-Based SOQL Queries (DISTANCE, GEOLOCATION):
  https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_geolocate.htm
- Geolocation Custom Field overview:
  https://help.salesforce.com/s/articleView?id=platform.custom_field_geolocate_overview.htm&type=5
- Configure State and Country/Territory Picklists:
  https://help.salesforce.com/s/articleView?id=sf.admin_state_country_picklists_configure.htm&type=5
- Impact on Apex Code if State and Country Picklists Feature is Enabled:
  https://help.salesforce.com/s/articleView?id=000385749&type=1
- Considerations for Using Person Accounts:
  https://help.salesforce.com/s/articleView?id=sales.account_person_behavior.htm&type=5
- Apex Address Class Reference:
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_system_Address.htm
