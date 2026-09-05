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

The controlling sentence is one line of the Object Reference:
"Compound fields are accessible only through SOAP API, REST API,
and Apex. The compound versions of fields aren't accessible
anywhere in the Salesforce user interface" (object_reference.txt
L2913–L2914). Everything below follows from it.

| Surface | Compound works? | Components work? | Recommendation |
|---|---|---|---|
| SOQL `SELECT` | Yes — returns Address/Location object | Yes — explicit list | Compound when you want all fields; components when you want a subset or API < 30.0 compatibility |
| SOQL `WHERE` as a *filter value* | No — "Address fields aren't filterable" (L2950) | Yes | Always components |
| SOQL `WHERE`/`ORDER BY` as a *location operand* | Yes — inside `DISTANCE(...)`, for both Geolocation and standard Address compounds (L2836–L2841) | Yes — via `GEOLOCATION(lat, lon)` on the components | `DISTANCE` with the location field first and a literal `'mi'`/`'km'` |
| SOQL `GROUP BY` | No — `DISTANCE`/`GEOLOCATION` unsupported (L2969–L2970) | Yes | Always components; no single-query distance bucketing |
| Apex DML | No — read-only on the compound (L2912) | Yes | Always components |
| Apex read | Yes — `System.Address` / `System.Location`, assigned to a local first | Yes — typed primitives | Compound for display; components for logic and every write |
| LWC `getRecord` (UI API) | Yes — returns `displayValue` formatted | Yes — explicit field paths | Compound for display; components for editing |
| Report column | No — no UI surface reaches the compound | Yes — individual columns | Always components |
| Report filter | No | Yes | Always components |
| Visualforce `<apex:outputField>` | No (L2929–L2930) | Yes | Always components |
| Data Loader export | No — "cause error messages" (L2931) | Yes | Always components |
| JSON.serialize | Yes — but shape is undocumented | Yes — explicit DTO | Always components via DTO (see gotcha 5) |
| Formula function argument | `ISBLANK`, `ISCHANGED`, `ISNULL` only (L2936–L2939) | Yes | Components for anything comparative |
| Validation Rule | No — the feature refuses compounds entirely (api_meta.txt L45369) | Yes | Components; `DISTANCE` formulas are the one supported compound-derived expression |
| Lookup filter | Only as a `DISTANCE` range, "in the Metadata API only" (L2934–L2935) | Yes | Components in Setup; distance filters through metadata |
| Custom settings / dashboards / Schema Builder | No for geolocation (L2954–L2955) | Latitude/longitude components, where the surface allows | Do not model geolocation into custom settings |
| Salesforce to Salesforce | No — geolocation and standard-address lat/lon unsupported (L2963) | No | Exclude from S2S mappings |

A second tradeoff: **standard Address fields vs custom Address
fields**. Standard Address compounds (e.g., `BillingAddress`)
have years of platform tooling behind them — Report Builder
columns, LWC `lightning-input-address`, automatic geocoding via
Salesforce's Data.com / Maps integration. Custom Address fields
(enabled org-wide through `CustomAddressFieldSettings`, API
version 55.0 and later — api_meta.txt L113898–L113901) give you a
compound shape on objects that don't have one natively, but lose
`GeocodeAccuracy`, which is "only available for standard address
fields on standard objects" (object_reference.txt L2740–L2743),
and lose automatic geocoding, which the platform provides only for
Account, Contact, Lead, and WorkOrder (object_reference.txt
L2943–L2948). They gain one thing: `CountryCode` "is always
available, whether or not state and country/territory picklists
are enabled" (object_reference.txt L2705–L2707). The enablement is
irreversible (gotcha 8), which makes it an architecture decision
rather than an experiment. Use custom Address fields only
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
   faster; use it in SELECT, WHERE, and ORDER BY — remembering
   that in WHERE it accepts only `<` / `>` (never `=`) and takes
   a literal `'mi'` / `'km'` unit. When both points are already
   in memory and a query would be a second round trip, use
   `System.Location.getDistance(a, b, unit)`, which the Apex
   Reference documents as "an approximation of the haversine
   formula" — that is the supported in-memory path, not a
   hand-written one.

6. **Trusting `isFilterable()` to decide what can go in a WHERE
   clause.** The describe result reports address compound fields
   as filterable and the query still fails (gotcha 10). Dynamic
   query builders and generated code get this wrong in exactly
   the same way. Exclude compounds explicitly before the
   filterable check.

7. **Sweeping the `settings` directory into a deploy.**
   `enableCustomAddressField` cannot be set back to `false` once
   deployed (gotcha 8). Deploy settings files by explicit path,
   after a `--dry-run` and a diff against what production has.
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
- Winter '13 — Using Apex and SOQL with Geolocation (introduction):
  https://developer.salesforce.com/blogs/developer-relations/2012/10/winter-13-using-apex-and-soql-with-geolocation
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

Extracted-PDF sources used for this revision, with the line ranges each claim rests on:

- Object Reference (Summer '26 / v62 PDF), "Compound Fields",
  "Address Compound Fields", "Geolocation Compound Field",
  "Compound Field Considerations and Limitations" —
  object_reference.txt L2647–L2993. Grounds the component table
  (L2684–L2726), the three-surface accessibility rule
  (L2913–L2914), the read-only rule (L2912), the `__latitude__s` /
  `__longitude__s` component convention (L2915–L2917), the
  three-fields-against-the-limit count (L2874–L2876), the
  Data Loader export error (L2931–L2932), the formula-function
  allow-list (L2936–L2939), the `isFilterable()` defect
  (L2950–L2951), the four `DISTANCE` constraints (L2969–L2990),
  and the `DISTANCE` formula support list (L2957–L2961).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Metadata API Developer Guide (v62 PDF), `CustomField` —
  api_meta.txt L43204–L43266 (`fullName` forms, package.xml field
  retrieval, `Location` unavailable on external objects),
  L43364–L43368 (`displayLocationInDecimal`), L43608–L43612
  (`scale`); Metadata Field Types L45719–L45765 (`FieldType`
  enum, `Address` and `Location (use for geolocation fields)`).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide, `AddressSettings` — api_meta.txt
  L109599–L109830. Grounds the `Address.settings` file location,
  API 27.0 availability, the `Settings:Address` CLI type name, the
  "can't create or delete states or countries" ceiling, and the
  sample XML reproduced in `metadata-examples.md` §3.
- Metadata API Developer Guide, `CustomAddressFieldSettings` —
  api_meta.txt L113885–L113950. Grounds the API 55.0 availability,
  the irreversibility of `enableCustomAddressField`, the sample
  definition, and the no-wildcard-for-settings rule.
- Metadata API Developer Guide, `ValidationRule` — api_meta.txt
  L45363–L45371. Grounds "As of API version 20.0, validation rules
  can't have compound fields."
- Apex Reference Guide (v62 PDF), `Address` class — apexrefguide.txt
  L199169–L199260. Grounds the no-dot-notation rule, the
  `System.Address` vs `Schema.Address` disambiguation, and
  `getStateCode()` / `getCountryCode()` returning null when state
  and country/territory picklists are off.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Reference Guide, `Location` class — apexrefguide.txt
  L221898–L222070. Grounds `newInstance(latitude, longitude)`,
  both `getDistance` overloads, the `mi`/`km` unit parameter, and
  the "approximation of the haversine formula" description.
- Data Loader Guide (v62 PDF) — salesforce_data_loader.txt L918–L919.
  Grounds the compound-field export error and the
  use-individual-components instruction.
- Salesforce App Limits Cheat Sheet (v62 PDF) — searched for
  "compound" and "geolocation"; no entry exists. The only numeric
  limit that applies to this skill is the org custom-field cap,
  against which a geolocation field counts three
  (object_reference.txt L2874–L2876).
