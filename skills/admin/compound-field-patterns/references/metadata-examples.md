# Metadata Examples — Compound Field Patterns

Deployable metadata and queries for the three compound shapes. `admin/custom-field-creation` owns
the general `CustomField` element set (`label`, `required`, `description`, `trackHistory`, the
`FieldType` enum, the DX-vs-zip file forms); nothing below repeats it. What is here is only what
changes because the field is *compound*: the `Location` type and its two display elements, the two
org-level settings that create or reshape address components, and the query and load patterns that
have to address components instead of the compound.

## How to read it

- **A compound field is never created directly.** You create a `Location` custom field, or you
  enable a feature that adds components to an existing standard address. There is no
  `<type>Geolocation</type>` and no metadata element that names a compound.
- **`Location` is the type name.** The `FieldType` enum lists `Location (use for geolocation
  fields)` (api_meta.txt L45760). `Geolocation` is not a valid value; neither is `GeoLocation`.
- **`scale` and `displayLocationInDecimal` are the two elements that matter here.** `scale` is
  "the number of digits to the right of the decimal point in a number" (api_meta.txt
  L43608–L43612). `displayLocationInDecimal` "indicates how the geolocation values of a custom
  Location field appear in the user interface. If `true`, the geolocation values appear in decimal
  notation. If `false`, the geolocation values appear as degrees, minutes, and seconds"
  (api_meta.txt L43364–L43368).
- **`fullName` is object-qualified in a package-format file, bare in a DX-decomposed file.** The
  guide's examples of the qualified form: `MyCustomObject__c.MyCustomField__c`,
  `Account.MyAcctCustomField__c` (api_meta.txt L43222–L43226).
- **The two `.settings` files are org-wide and singular.** `AddressSettings` lives in
  `Address.settings`, `CustomAddressFieldSettings` in `CustomAddressField.settings`; both are
  retrieved and deployed under the manifest name `Settings`, and "there's only one settings file
  for each settings component" (api_meta.txt L109609–L109611, L113894–L113897).
- **Every XML block below is a complete, well-formed document** — copy whole, do not splice.

---

## 1. Custom geolocation field — `Location`

`force-app/main/default/objects/Store__c/fields/Store_Location__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Store_Location__c</fullName>
    <description>Geocoded position of the storefront. Written by the nightly geocoding job from the mailing address; never edited by hand. Consumed by the store-locator LWC via SOQL DISTANCE.</description>
    <displayLocationInDecimal>true</displayLocationInDecimal>
    <inlineHelpText>Latitude and longitude in decimal degrees. Blank means the address has not been geocoded yet.</inlineHelpText>
    <label>Store Location</label>
    <required>false</required>
    <scale>5</scale>
    <trackHistory>false</trackHistory>
    <type>Location</type>
</CustomField>
```

The same field inside a package-format `objects/Store__c.object`, for a Metadata API zip deploy:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <fields>
        <fullName>Store_Location__c</fullName>
        <displayLocationInDecimal>true</displayLocationInDecimal>
        <label>Store Location</label>
        <required>false</required>
        <scale>5</scale>
        <type>Location</type>
    </fields>
</CustomObject>
```

What this one field costs and exposes:

| Consequence | Source |
|---|---|
| Three custom fields against the org limit — latitude, longitude, and one for internal use | object_reference.txt L2874–L2876 |
| Two queryable component fields: `Store_Location__Latitude__s`, `Store_Location__Longitude__s` | object_reference.txt L2915–L2917 |
| One read-only compound value, reachable from SOAP API, REST API, and Apex only | object_reference.txt L2651, L2913–L2914 |
| Not available in dashboards or Schema Builder; not supported in custom settings | object_reference.txt L2954–L2955 |
| Not an available custom field type on external objects | api_meta.txt L43233–L43245 |

`scale` is what decides precision on disk. Five decimal places of latitude is roughly a metre;
choose it deliberately, because widening `scale` later rewrites stored values.

---

## 2. Enabling custom address fields — `CustomAddressFieldSettings`

`force-app/main/default/settings/CustomAddressField.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomAddressFieldSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableCustomAddressField>true</enableCustomAddressField>
</CustomAddressFieldSettings>
```

This is the guide's own sample definition (api_meta.txt L113917–L113922), available in API version
55.0 and later. Read the field description before you deploy it: "Indicates whether the Address
Field Type is available for custom fields (`true`) or not (`false`). The default value is `false`.
Custom Address Fields can't be disabled. When `enableCustomAddressField` is set to `true`, you
can't change the value to `false`" (api_meta.txt L113903–L113909). Treat this as a one-way door in
every org it reaches, including sandboxes you refresh from.

Once it is on, `Address` is a valid `CustomField` `type` (api_meta.txt L45719) and the field
appears in Object Manager: "If you enabled Custom Address Fields, the Address field type is
available in Object Manager when you add a custom field" (object_reference.txt L2745–L2747). A
custom address field's `CountryCode` component "is always available, whether or not state and
country/territory picklists are enabled in your organization" — unlike a standard address, where
`CountryCode` and `StateCode` are picklist-gated (object_reference.txt L2705–L2722).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Site_Address__c</fullName>
    <description>Physical address of the serviced site, distinct from the account's billing address.</description>
    <label>Site Address</label>
    <required>false</required>
    <type>Address</type>
</CustomField>
```

<!-- UNVERIFIED (2026-09-04): the Metadata API guide names `Address` in the FieldType enum and the
Object Reference confirms the type appears in Object Manager once Custom Address Fields is enabled,
but neither file carries a sample CustomField definition of type Address. The four elements above
are the generic CustomField elements; any address-specific element (component labels, per-component
required flags) is documented only in the separate Custom Address Fields Developer Guide, which is
not in the extracted set. -->

The two guarantees custom address fields do **not** carry: `GeocodeAccuracy` — "like its parent,
the compound Address field, the `GeocodeAccuracy` field is only available for standard address
fields on standard objects" (object_reference.txt L2740–L2743) — and automatic geocoding, which
Salesforce provides only "for Account, Contact, Lead, and WorkOrder records" via the geo data
integration rule (object_reference.txt L2943–L2948).

---

## 3. State and country/territory picklists — `AddressSettings`

`force-app/main/default/settings/Address.settings-meta.xml`, trimmed from the guide's sample
(api_meta.txt L109751–L109826):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AddressSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <countriesAndStates>
        <countries>
            <country>
                <active>true</active>
                <integrationValue>United States</integrationValue>
                <isoCode>US</isoCode>
                <label>United States</label>
                <orgDefault>true</orgDefault>
                <standard>true</standard>
                <states>
                    <state>
                        <active>true</active>
                        <integrationValue>California</integrationValue>
                        <isoCode>CA</isoCode>
                        <label>California</label>
                        <standard>true</standard>
                        <visible>true</visible>
                    </state>
                </states>
                <visible>true</visible>
            </country>
            <country>
                <active>true</active>
                <integrationValue>Greenland</integrationValue>
                <isoCode>GL</isoCode>
                <label>Greenland</label>
                <standard>true</standard>
                <visible>false</visible>
            </country>
        </countries>
    </countriesAndStates>
</AddressSettings>
```

`integrationValue` is the value integrations send and receive; `isoCode` is what
`MailingStateCode` stores; `visible` `false` with `active` `true` — the Greenland row — makes a
country available to the API but not to users in the UI. Available in API version 27.0 and later.
The guide is explicit about the ceiling: "You can use the Metadata API to edit existing states,
countries, and territories in state and country/territory picklists. You can't use the Metadata
API to create or delete new states, countries, or territories" (api_meta.txt L109630–L109633).
With Salesforce CLI the type name is `Settings:Address` (api_meta.txt L109624–L109626).

---

## 4. SOQL

```soql
-- (a) The compound value. SOAP API, REST API, and Apex only.
SELECT Name, BillingAddress FROM Account

-- (b) The components. Portable to API versions earlier than 30.0.
SELECT Name, BillingStreet, BillingCity, BillingState, BillingPostalCode,
       BillingCountry, BillingLatitude, BillingLongitude
FROM Account

-- (c) A custom geolocation, compound then components.
SELECT Store_Location__c FROM Store__c
SELECT Store_Location__Latitude__s, Store_Location__Longitude__s FROM Store__c

-- (d) Proximity: DISTANCE in SELECT, WHERE, and ORDER BY, with a literal unit.
--     The location operand comes first; GEOLOCATION second.
SELECT Id, Name, DISTANCE(Store_Location__c, GEOLOCATION(37.775,-122.418), 'mi') dist
FROM Store__c
WHERE DISTANCE(Store_Location__c, GEOLOCATION(37.775,-122.418), 'mi') < 25
ORDER BY DISTANCE(Store_Location__c, GEOLOCATION(37.775,-122.418), 'mi')
LIMIT 10

-- (e) A standard address compound used as the location operand.
SELECT Id, Name, BillingAddress FROM Account
WHERE DISTANCE(BillingAddress, GEOLOCATION(37.775,-122.418), 'mi') < 20
ORDER BY DISTANCE(BillingAddress, GEOLOCATION(37.775,-122.418), 'mi')
LIMIT 10
```

Queries (b), (d) and (e) are the guide's own samples (object_reference.txt L2764–L2768,
L2836–L2841, L2981–L2983). What the guide forbids, in the same words:

| Rejected | Rule | Source |
|---|---|---|
| `WHERE BillingAddress = :addr` | "Address fields can't be used in WHERE statements in SOQL. Address fields aren't filterable" | object_reference.txt L2950–L2951 |
| `WHERE DISTANCE(...) = 5`, `>= 5`, `<= 5` | "DISTANCE supports only the logical operators > and <, returning values within (<) or beyond (>) a specified radius" | object_reference.txt L2979 |
| `DISTANCE(GEOLOCATION(37.775,-122.418), Store_Location__c, 'km')` | "the geolocation field must precede the latitude and longitude coordinates" | object_reference.txt L2980–L2983 |
| `DISTANCE(Store_Location__c, GEOLOCATION(10,10), :units)` | "Apex bind variables aren't supported for the units parameter in the DISTANCE function" | object_reference.txt L2984–L2990 |
| `GROUP BY DISTANCE(...)` | "DISTANCE and GEOLOCATION are supported in WHERE and ORDER BY clauses in SOQL, but not in GROUP BY. DISTANCE is supported in SELECT clauses" | object_reference.txt L2969–L2970 |

---

## 5. Apex — reading and writing components

```apex
public with sharing class SiteAddressService {

    // READ: assign the parent field to a typed variable, then read components.
    // Dot notation straight through the parent field does not compile.
    public static Map<String, Object> describe(Id accountId) {
        Account acct = [
            SELECT Id, BillingAddress, Store_Location__c
            FROM Account WHERE Id = :accountId WITH USER_MODE LIMIT 1
        ];

        System.Address addr = acct.BillingAddress;
        System.Location loc = acct.Store_Location__c;

        return new Map<String, Object>{
            'city'      => addr == null ? null : addr.city,           // == addr.getCity()
            'state'     => addr == null ? null : addr.state,
            // getStateCode() returns null unless state/country picklists are enabled
            'stateCode' => addr == null ? null : addr.stateCode,
            'accuracy'  => addr == null ? null : addr.getGeocodeAccuracy(),
            'lat'       => loc  == null ? null : loc.latitude,
            'lon'       => loc  == null ? null : loc.longitude
        };
    }

    // WRITE: components only. Assigning acct.BillingAddress does not save.
    public static void relocate(Id accountId, Decimal lat, Decimal lon, String stateIso) {
        Account acct = new Account(Id = accountId);
        acct.BillingStateCode              = stateIso;   // 'CA', not 'California'
        acct.Store_Location__Latitude__s   = lat;
        acct.Store_Location__Longitude__s  = lon;
        update acct;
    }

    // In-memory distance, when both points are already loaded and a query
    // would be a second round trip. Same approximation the platform uses.
    public static Double milesBetween(Account a, Decimal lat, Decimal lon) {
        System.Location here  = System.Location.newInstance(lat, lon);
        System.Location there = a.Store_Location__c;
        return there == null ? null : there.getDistance(here, 'mi');
    }
}
```

`System.Address` and `System.Location` are spelled out on purpose: "'Address' in Salesforce can
also refer to the Address standard object… always use `Schema.Address` instead of `Address`… you
can differentiate between the two by using `System.Address` for the field and `Schema.Address` for
the object" (apexrefguide.txt L199187–L199190); the identical warning covers `Location`
(apexrefguide.txt L221921–L221924). `getDistance` is documented as using "an approximation of the
haversine formula and the specified unit", with `mi` or `km` as the unit (apexrefguide.txt
L221955–L221962, L221983–L221996).

---

## 6. Data Loader and reports

**Data Loader export.** Map component fields, one column each. The compound is not exportable:
"If you select compound fields for export in the Data Loader, they cause error messages. To export
values, use individual field components" (salesforce_data_loader.txt L918–L919, repeating
object_reference.txt L2931–L2932).

A CSV header for a Contact mailing-address load, State and Country/Territory Picklists **enabled**:

```csv
Id,MailingStreet,MailingCity,MailingStateCode,MailingPostalCode,MailingCountryCode
003xx0000012ABCAA2,"1 Market St",San Francisco,CA,94105,US
```

The same load with picklists **disabled** — the code columns do not exist:

```csv
Id,MailingStreet,MailingCity,MailingState,MailingPostalCode,MailingCountry
003xx0000012ABCAA2,"1 Market St",San Francisco,California,94105,United States
```

There is no `MailingAddress` column in either file, and no `MailingGeocodeAccuracy` column in a
load file — the accuracy subfield "is populated only when an address is geocoded", by the geocoding
service, not by your CSV (object_reference.txt L2948).

**Reports.** Add component columns, not the compound. The compound value is unreachable from every
UI surface — "the compound versions of fields aren't accessible anywhere in the Salesforce user
interface" (object_reference.txt L2913–L2914) — so a report shows Billing City, Billing
State/Province, Billing Zip/Postal Code as separate columns, each independently sortable and
filterable. Geolocation fields specifically "aren't available in dashboards or Schema Builder"
(object_reference.txt L2954–L2955).

**Limits.** The Salesforce App Limits Cheat Sheet carries no compound-field or geolocation entry;
the only numeric limit that applies is the org custom-field cap, against which one geolocation
field counts three (object_reference.txt L2874–L2876).

---

## 7. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Store__c.Store_Location__c</members>
        <members>Account.BillingStateCode</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Address</members>
        <members>CustomAddressField</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

The `CustomField` members use the object-qualified form the guide documents for retrieving named
fields (api_meta.txt L43258–L43266). Both settings go under the single `Settings` name
(api_meta.txt L109605–L109607). The wildcard `*` does not work for feature settings — "the
wildcard applies only when retrieving all settings, not for an individual setting" (api_meta.txt
L113946–L113949) — so list them.

---

## 8. Retrieve and deploy

```bash
# Pull the field and both settings before changing anything.
sf project retrieve start \
  --metadata "CustomField:Store__c.Store_Location__c" \
  --metadata "Settings:Address" \
  --metadata "Settings:CustomAddressField" \
  --target-org my-sandbox

# Validate. Never skip this for AddressSettings or CustomAddressFieldSettings —
# enableCustomAddressField cannot be set back to false once deployed.
sf project deploy start \
  --source-dir force-app/main/default/objects/Store__c \
  --source-dir force-app/main/default/settings \
  --dry-run \
  --target-org production

sf project deploy start \
  --source-dir force-app/main/default/objects/Store__c \
  --source-dir force-app/main/default/settings \
  --target-org production
```

---

## 9. Verification

Confirm the shape the org actually has, not the shape you deployed.

```bash
# The Location field: type, scale, and the two component fields it created.
sf sobject describe --sobject Store__c --target-org my-sandbox --json \
  | jq '.result.fields[]
        | select(.name | test("Store_Location"))
        | {name, type, scale, filterable, createable, updateable}'

# The address components: does StateCode exist, i.e. are picklists on?
sf sobject describe --sobject Account --target-org my-sandbox --json \
  | jq '.result.fields[] | select(.name | startswith("Billing")) | {name, type, updateable}'
```

Expect exactly one row of `type: "location"` (the compound, `updateable: false`) plus
`Store_Location__Latitude__s` and `Store_Location__Longitude__s` as `double` and updateable. A
`BillingStateCode` row present means picklists are enabled and your writes must target it; absent
means write `BillingState`.

Then confirm the data landed on the authoritative column, not just the text one:

```soql
SELECT Id, BillingState, BillingStateCode, BillingCountry, BillingCountryCode,
       BillingLatitude, BillingLongitude
FROM Account
WHERE BillingStateCode = NULL AND BillingState != NULL
LIMIT 50
```

Rows returned means something wrote the text component directly while picklists were enabled —
the failure mode in gotcha 1. Zero rows is the pass condition.

`sf` flag spellings above follow the same CLI surface used in `admin/custom-field-creation`
§11–§12; re-check with `sf project deploy start --help` if your CLI is older.
