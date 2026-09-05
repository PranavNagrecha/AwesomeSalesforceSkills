# Metadata Examples — Contract and Renewal Management

Deployable shapes for the **standard** Contract and Order metadata this skill produces:
the org-level `ContractSettings` and `OrderSettings`, the `ContractStatus` standard
value set that carries the Draft / InApproval / Activated status categories, a
Contract validation rule that refuses activation without both signature dates, the
custom fields a renewal desk actually tracks on, and the scheduled-flow intent plus
the SOQL behind a renewal reminder.

Element names, enum values, and the settings skeletons come from the Metadata API
Developer Guide (`ContractSettings`, `OrderSettings`, `StandardValueSet`,
`StandardValue` / `CustomValue`, `ValidationRule`, `CustomField`, `FlowStart`,
`FlowSchedule` sections) and the Object Reference (`Contract`, `ContractStatus`,
`ContractContactRole`, `ContractLineItem`, `Order`, `OrderItem`). The worked
examples extend the guide's own sample definitions to a realistic renewal desk.

- Metadata API Developer Guide — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

**Scope.** Everything on this page is the standard Contract / Order object graph.
Salesforce CPQ (`SBQQ__*`), Subscription Management and Revenue Cloud objects are
a managed-package layer on top of it and are **not** described in either guide —
see `admin/cpq-product-catalog-setup`, `architect/subscription-management-architecture`
and `architect/revenue-cloud-architecture` for those.

Lint whatever you write with:

```bash
python3 skills/admin/contract-and-renewal-management/scripts/check_contract_and_renewal_management.py \
    --manifest-dir force-app/main/default
```

---

## Where the files live

| Type | package.xml `<name>` / `<members>` | File in a DX project |
|---|---|---|
| Contract org settings | `Settings` / `Contract` | `settings/Contract.settings-meta.xml` |
| Order org settings | `Settings` / `Order` | `settings/Order.settings-meta.xml` |
| Contract status picklist | `StandardValueSet` / `ContractStatus` | `standardValueSets/ContractStatus.standardValueSet-meta.xml` |
| Order status picklist | `StandardValueSet` / `OrderStatus` | `standardValueSets/OrderStatus.standardValueSet-meta.xml` |
| Contract validation rule | `ValidationRule` / `Contract.Require_Both_Signatures_Before_Activation` | `objects/Contract/validationRules/Require_Both_Signatures_Before_Activation.validationRule-meta.xml` |
| Contract custom field | `CustomField` / `Contract.Renewal_Owner__c` | `objects/Contract/fields/Renewal_Owner__c.field-meta.xml` |
| Renewal reminder flow | `Flow` / `Contract_Renewal_Reminder` | `flows/Contract_Renewal_Reminder.flow-meta.xml` |

There is one contract settings file, named `Contract.settings`, in the `settings`
directory, and one `OrderSettings` component in a file named `Order.settings` in the
same folder; the `.settings` files differ from other named components because there
is only one settings file per settings component (api_meta.txt L113215,
L123651). All org settings metadata types are addressed in package.xml
through the `Settings` name (api_meta.txt L113211, L123647). `ContractSettings` is
available in API version 27.0 and later (L113220); `OrderSettings` in 30.0 and later
(L123656).

---

## 1. Contract org settings

The guide documents exactly **two** fields on `ContractSettings` (api_meta.txt
L113225–L113231). Do not invent others — the deploy fails on an unknown element.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ContractSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- true: Contract.EndDate is calculated from StartDate + ContractTerm and is
         read-only. false: EndDate becomes editable. (api_meta.txt L113225;
         object_reference.txt L81153-L81160) -->
    <autoCalculateEndDate>true</autoCalculateEndDate>

    <!-- Emails account and contract owners when a contract expires.
         (api_meta.txt L113228-L113229) -->
    <notifyOwnersOnContractExpiration>true</notifyOwnersOnContractExpiration>
</ContractSettings>
```

> UNVERIFIED (2026-09-05): the Setup UI for Contract Settings also exposes contract
> auto-expiration (an "expire contracts N days after end date" toggle and delay).
> No `autoExpireContracts`, `autoExpirationDelay` or `autoExpirationRecipient`
> element appears anywhere in api_meta.txt (0 hits each), so this file cannot
> confirm an API name for them. Configure auto-expiration in Setup and treat it as
> org state that source control does not carry, or verify the element names against
> the Metadata API coverage page for your API version before adding them here.

---

## 2. Order org settings

Extended from the guide's own sample definition (api_meta.txt L123711–L123721).
Every element below is in the `OrderSettings` field table (L123660–L123705).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OrderSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Master switch. Every other flag below requires this to be true. -->
    <enableOrders>true</enableOrders>

    <!-- Reduction orders: the supported way to reduce quantity on an activated
         order. Requires enableOrders. (api_meta.txt L123698-L123700) -->
    <enableReductionOrders>true</enableReductionOrders>

    <!-- Order products with quantity 0. Default false. Requires enableOrders. -->
    <enableZeroQuantity>false</enableZeroQuantity>

    <!-- Order products with quantity below zero. Requires enableOrders. -->
    <enableNegativeQuantity>false</enableNegativeQuantity>

    <!-- OrderStatusChangedEvent platform events. -->
    <enableOrderEvents>true</enableOrderEvents>

    <!-- Orders without price books. B2B Commerce licences only; incompatible
         with reduction orders. (object_reference.txt L197105-L197120) -->
    <enableOptionalPricebook>false</enableOptionalPricebook>

    <!-- Salesforce Order Management licence only. Default false. -->
    <enableEnhancedCommerceOrders>false</enableEnhancedCommerceOrders>

    <!-- Order items across multiple price books. Requires enableOrders AND
         enableEnhancedCommerceOrders. API 60.0+. (api_meta.txt L123689-L123693) -->
    <enableOrderWithMultiplePriceBooks>false</enableOrderWithMultiplePriceBooks>
</OrderSettings>
```

**How to read it**

- `enableOrders` is the gate. `enableNegativeQuantity`, `enableReductionOrders` and
  `enableZeroQuantity` each state "To enable this preference, `enableOrders` must be
  set to `true`" (api_meta.txt L123668, L123700, L123704). Deploying a dependent
  flag with `enableOrders` false is the most common failure on this file.
- `enableOrderWithMultiplePriceBooks` needs **two** parents: `enableOrders` *and*
  `enableEnhancedCommerceOrders` (L123692–L123693).
- `enableEnhancedCommerceOrders` is available only in orgs with the Salesforce Order
  Management licence (L123661–L123665). It will not deploy to a plain Sales Cloud org.
- `enableOptionalPricebook` and `enableReductionOrders` are mutually exclusive in
  practice: "Orders without price books don't support reduction orders or change
  orders" (object_reference.txt L197116).
- The `*` wildcard does not apply to feature settings in package.xml; it applies only
  when retrieving *all* settings (api_meta.txt L113243–L113246).

---

## 3. Contract status value set

`ContractStatus` is the standard value set behind `Contract.Status` (api_meta.txt
L142098). Each entry is a `standardValue` — `StandardValue` extends `CustomValue`,
so `fullName`, `default`, `isActive`, `label` and `description` are the fields you
have (api_meta.txt L47474–L47530, L47532–L47534).

The point of this file is that **`Status` is a label picklist and `StatusCode` is
the category behind it**. A contract's `Status` picklist may contain many values
that all sit inside the `Activated` status category — the Object Reference's own
example is "Ready to Ship, Shipped, Received as values within the Activated
StatusCode" (object_reference.txt L81474–L81477).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>ContractStatus</fullName>
    <sorted>false</sorted>
    <standardValue>
        <fullName>Draft</fullName>
        <default>true</default>
        <label>Draft</label>
        <description>Editable. Client applications must create contracts in a non-Activated state.</description>
    </standardValue>
    <standardValue>
        <fullName>In Approval Process</fullName>
        <default>false</default>
        <label>In Approval Process</label>
        <description>StatusCode category InApproval. Still deletable.</description>
    </standardValue>
    <standardValue>
        <fullName>Activated</fullName>
        <default>false</default>
        <label>Activated</label>
        <description>StatusCode category Activated. Status can no longer be changed and the record cannot be deleted.</description>
    </standardValue>
    <standardValue>
        <fullName>Activated - Renewal Pending</fullName>
        <default>false</default>
        <label>Activated - Renewal Pending</label>
        <description>Custom label inside the Activated status category; renewal desk uses it as a work queue.</description>
    </standardValue>
</StandardValueSet>
```

**How to read it**

- `Contract.Status` valid values out of the box are `Activated`, `Draft` and
  `In Approval Process` (object_reference.txt L81478–L81481). `Contract.StatusCode`
  valid values are `Activated`, `Draft`, `InApproval` (L81487–L81490) — note the
  **different spelling** of the approval value between the two fields.
- `Contract.StatusCode` properties are `Filter, Group, Restricted picklist, Sort` —
  **no Create and no Update** (object_reference.txt L81486–L81487). You set the
  category by picking a `Status` label that belongs to it; you never write
  `StatusCode` directly. `Order.StatusCode` is different: its properties include
  `Update` (object_reference.txt L196833–L196836).
- The `ContractStatus` *object* additionally defines `Terminated` and `Expired`
  status codes, and the guide says both "are defined but are not available for use
  via the API" (object_reference.txt L82295–L82296). Do not model contract
  termination as a `StatusCode` — model it with your own `Status` label or a custom
  field.
- Adding the fourth value above is how a renewal desk gets a work queue without
  breaking activation semantics — it is a new *label*, still in the `Activated`
  category. This is also why a validation rule that tests
  `ISPICKVAL(Status, "Activated")` alone is wrong the moment anyone adds a label
  (see §4).
- When you deploy a `StandardValueSet`, the `standardValue` array must contain at
  least one picklist value or you get an error (api_meta.txt L130771–L130772), and
  picklist values missing from a component definition are **deactivated** on deploy
  (api_meta.txt L47482–L47483). Always retrieve the live value set before editing it.

The order-side equivalent, for the same reason:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>OrderStatus</fullName>
    <sorted>false</sorted>
    <standardValue>
        <fullName>Draft</fullName>
        <default>true</default>
        <label>Draft</label>
    </standardValue>
    <standardValue>
        <fullName>Activated</fullName>
        <default>false</default>
        <label>Activated</label>
    </standardValue>
</StandardValueSet>
```

`OrderStatus` is the standard value set name for the order status picklist and has
no pre-38.0 field-name equivalent (api_meta.txt L142689). `Order.StatusCode` valid
values are `Draft`, `Activated` and — for Revenue Cloud Advanced in API 64.0 and
later — `Superseded` (object_reference.txt L196846–L196850).

---

## 4. Contract validation rule: no activation without both signature dates

`ValidationRule` requires `active`, `errorConditionFormula` and `errorMessage`; the
error message must be 255 characters or less, and `errorDisplayField` puts the error
next to a field instead of at the top of the page (api_meta.txt L45380–L45402).

`CompanySignedDate` is "the date your organization signed the contract" and
`CustomerSignedDate` is "the date when the customer signed the contract"
(object_reference.txt L81063–L81069, L81109–L81115). Both are plain `date` fields
with no platform-enforced relationship to activation — that guard is yours to write.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Require_Both_Signatures_Before_Activation</fullName>
    <active>true</active>
    <description>A contract cannot enter an Activated-category status until both the company and the customer signature dates are recorded. Add every Activated-category Status label to the ISPICKVAL list when one is created.</description>
    <errorConditionFormula>AND(
  OR(
    ISPICKVAL(Status, "Activated"),
    ISPICKVAL(Status, "Activated - Renewal Pending")
  ),
  OR(
    ISBLANK(CompanySignedDate),
    ISBLANK(CustomerSignedDate)
  )
)</errorConditionFormula>
    <errorDisplayField>CustomerSignedDate</errorDisplayField>
    <errorMessage>Record both the Company Signed Date and the Customer Signed Date before activating this contract.</errorMessage>
</ValidationRule>
```

**How to read it**

- The formula enumerates every `Status` **label** in the `Activated` category, not
  the `StatusCode`. That is deliberate: `StatusCode` is not writable and the label
  set is org-specific (§3). Each time someone adds an Activated-category label, this
  rule must be extended — the checker in `scripts/` flags labels it cannot find in
  the rule.
- The guide's own inline sample nests the rule inside a `CustomObject` and uses a
  `<validationMessage>` element (api_meta.txt L45441); the `ValidationRule`
  field table names the element `errorMessage` (L45402). Use `errorMessage` in a
  standalone `.validationRule-meta.xml` file, which is what a DX project deploys.
- This rule fires on the update that sets `Status` to an activated label. That is
  the *only* field you can change on that update — "the `Status` field is the only
  field you can update when activating the Contract" (object_reference.txt
  L81520–L81522) — so the signature dates must already be on the record. A rule that
  expects the user to fill signatures *and* flip status in one save can never pass
  through the API.
- Validation rules cannot use compound fields as of API 20.0 (api_meta.txt
  L45369–L45370), so do not reference `Contract.BillingAddress` here; use
  `BillingStreet`, `BillingCity` and friends.

---

## 5. Custom fields for renewal tracking

The standard object gives you `EndDate`, `ContractTerm`, `OwnerExpirationNotice`,
`RenewalTerm2` and `RenewalTermUnit`. What it does not give you is *who works the
renewal*, *what the renewal outcome was*, and *how many days are left* as a
reportable number. Those three are the fields worth adding.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Renewal_Owner__c</fullName>
    <label>Renewal Owner</label>
    <type>Lookup</type>
    <referenceTo>User</referenceTo>
    <relationshipName>ContractsToRenew</relationshipName>
    <relationshipLabel>Contracts To Renew</relationshipLabel>
    <deleteConstraint>SetNull</deleteConstraint>
    <required>false</required>
    <trackHistory>true</trackHistory>
    <inlineHelpText>Renewal desk owner. Distinct from OwnerId, which stays with the closing rep.</inlineHelpText>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Days_To_Expiry__c</fullName>
    <label>Days To Expiry</label>
    <type>Number</type>
    <precision>18</precision>
    <scale>0</scale>
    <formula>IF(ISBLANK(EndDate), null, EndDate - TODAY())</formula>
    <formulaTreatBlanksAs>BlankAsBlank</formulaTreatBlanksAs>
    <inlineHelpText>Negative once the contract end date has passed. Formula, so it is always current in reports and list views but cannot be filtered on by a scheduled Flow Get Records without a full scan.</inlineHelpText>
</CustomField>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Renewal_Outcome__c</fullName>
    <label>Renewal Outcome</label>
    <type>Picklist</type>
    <trackHistory>true</trackHistory>
    <valueSet>
        <restricted>true</restricted>
        <valueSetDefinition>
            <sorted>false</sorted>
            <value>
                <fullName>Not Started</fullName>
                <default>true</default>
                <label>Not Started</label>
            </value>
            <value>
                <fullName>Renewed</fullName>
                <default>false</default>
                <label>Renewed</label>
            </value>
            <value>
                <fullName>Churned</fullName>
                <default>false</default>
                <label>Churned</label>
            </value>
            <value>
                <fullName>Renegotiating</fullName>
                <default>false</default>
                <label>Renegotiating</label>
            </value>
        </valueSetDefinition>
    </valueSet>
</CustomField>
```

**How to read it**

- `formula` "represents a formula on the field" and `formulaTreatBlanksAs` takes
  `BlankAsBlank` or `BlankAsZero` (api_meta.txt L43422–L43425). `BlankAsZero` on
  `Days_To_Expiry__c` would make every contract with no end date look like it
  expires today — pick `BlankAsBlank` deliberately.
- `trackHistory` requires `enableHistory` to be `true` on the object as well
  (api_meta.txt L43675–L43679). Setting it on the field alone deploys nothing useful.
- `Renewal_Owner__c` is a separate lookup rather than a reuse of `OwnerId` because
  `OwnerId` drives Contract record sharing (`ContractOwnerSharingRule`). Reassigning
  ownership to a renewal desk silently changes who can see the contract; a custom
  lookup does not.
- `Days_To_Expiry__c` is a **formula**, so it is not indexed and not queryable as a
  filter in a scheduled Flow's entry criteria. Filter on `EndDate` instead (§6).

---

## 6. Renewal reminder: flow intent and the query behind it

A renewal reminder is a **schedule-triggered flow**, not a Workflow Rule.
`FlowStart.triggerType` = `Scheduled` "starts the flow at the scheduled time"
(api_meta.txt L72496; the `Scheduled` enum value at L72543) and `schedule` is required
when `triggerType` is `Scheduled` (api_meta.txt L72462). `FlowSchedule.frequency`
takes `Once`, `Daily` or `Weekly` for a record-scheduled flow (api_meta.txt
L71352–L71362).

| Flow element | Setting | Why |
|---|---|---|
| `start.triggerType` | `Scheduled` | Renewal windows are date-driven; nothing changes on the record to trigger a record-triggered flow |
| `start.schedule.frequency` | `Daily` | The 60-day window moves every day; weekly runs miss contracts by up to six days |
| `start.schedule.startDate` / `startTime` | early morning, org time zone | Owners get one digest before the working day |
| `start.object` | `Contract` | One flow interview per matching contract |
| `start.filterLogic` + `conditions` | `StatusCode` equals `Activated` **and** `EndDate` less-or-equal `{!$Flow.CurrentDate}` + 60 | Entry criteria on an indexed date field, not on the formula field |
| `start.filterFormula` | alternative to `conditions` when the window is expressed as a formula | `filterFormula` "is used to filter what records execute the flow" (api_meta.txt L72390) |
| Decision | skip when `Renewal_Outcome__c` is `Renewed` or `Churned` | Stops re-notifying on contracts the desk already closed out |
| Send Email / Custom Notification | recipient `Renewal_Owner__c`, fallback `OwnerId` | Renewal desk first, closing rep as backstop |

The query the flow's entry criteria is standing in for — run this first to see how
many interviews the schedule will create:

```sql
SELECT OwnerId, Owner.Name, Owner.Email, COUNT(Id) contractCount
FROM Contract
WHERE StatusCode = 'Activated'
  AND EndDate >= TODAY
  AND EndDate <= :cutoffDate
GROUP BY OwnerId, Owner.Name, Owner.Email
ORDER BY COUNT(Id) DESC
```

and the per-contract detail behind a digest:

```sql
SELECT Id, ContractNumber, Account.Name, OwnerId, Owner.Email,
       StartDate, ContractTerm, EndDate, Status, StatusCode,
       OwnerExpirationNotice, RenewalTerm2, RenewalTermUnit,
       CompanySignedDate, CustomerSignedDate, Renewal_Owner__c, Renewal_Outcome__c
FROM Contract
WHERE StatusCode = 'Activated'
  AND EndDate >= TODAY
  AND EndDate <= :cutoffDate
ORDER BY OwnerId, EndDate
```

**How to read it**

- The filter is on `EndDate`, a real date column, not on `Days_To_Expiry__c`. Filter
  on the formula and every daily run scans the whole Contract table.
- `StatusCode = 'Activated'` rather than `Status = 'Activated'` is the whole point of
  §3: `StatusCode` is the category, so the query keeps working when someone adds an
  Activated-category label. `StatusCode` carries `Filter, Group, Sort` properties on
  Contract (object_reference.txt L81486–L81487), so it is legal in `WHERE`,
  `GROUP BY` and `ORDER BY`.
- `:cutoffDate` is an Apex/Flow bind. In a report or list-view filter the equivalent
  relative literal is `NEXT_N_DAYS:60`. **UNVERIFIED (2026-09-05):** `NEXT_N_DAYS`
  does not appear in any of the extracted guides (0 hits in object_reference.txt,
  api_meta.txt, api_rest.txt, apexdev.txt); its sibling `LAST_N_DAYS:n` is attested
  (api_rest.txt L15223, L18558; apexdev.txt L20476), so the `<LITERAL>:n` form is
  confirmed but the specific `NEXT_N_DAYS` spelling is not — check the SOQL and SOSL
  Reference before shipping it in a saved report.
- `OwnerExpirationNotice` is the platform's own reminder hook and takes only
  15, 30, 45, 60, 90 or 120 days (object_reference.txt L81230–L81236). If the desk
  wants any other window, the flow above is the only route; do not expect to write
  75 into that field.

---

## 7. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Contract</members>
        <members>Order</members>
        <name>Settings</name>
    </types>
    <types>
        <members>ContractStatus</members>
        <members>OrderStatus</members>
        <name>StandardValueSet</name>
    </types>
    <types>
        <members>Contract.Renewal_Owner__c</members>
        <members>Contract.Days_To_Expiry__c</members>
        <members>Contract.Renewal_Outcome__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Contract.Require_Both_Signatures_Before_Activation</members>
        <name>ValidationRule</name>
    </types>
    <types>
        <members>Contract_Renewal_Reminder</members>
        <name>Flow</name>
    </types>
    <version>62.0</version>
</Package>
```

The settings block follows the guide's own package.xml sample for `OrderSettings`,
which lists `<members>Order</members>` under `<name>Settings</name>` (api_meta.txt
L123724–L123731). Neither `StandardValueSet` nor `ValidationRule` supports the `*`
wildcard in package.xml (api_meta.txt L130827, L45448), so both must
be listed by name.

---

## 8. Deploy order

Deploy in this order; each step depends on the one before it.

1. **`Settings` (Contract, Order)** — `enableOrders` must be true before any Order
   metadata resolves, and `autoCalculateEndDate` decides whether `EndDate` is
   writable, which changes how every later step behaves.
2. **`StandardValueSet` (ContractStatus, OrderStatus)** — the `Status` labels must
   exist before a validation rule can name them in `ISPICKVAL`.
3. **`CustomField` (Contract.\*)** — `Renewal_Owner__c` and `Renewal_Outcome__c` must
   exist before the flow references them.
4. **`ValidationRule`** — after the value set, before any data load. Deploy it
   inactive (`<active>false</active>`) if you have existing activated contracts with
   missing signature dates; those records fail on their next save otherwise.
5. **`Flow`** — last, and activate it only after step 6 confirms the window is sane.

Commands:

```bash
# Retrieve what is live before you change any of it — the StandardValueSet deploy
# deactivates every value you omit.
sf project retrieve start \
  --metadata "Settings:Contract" \
  --metadata "Settings:Order" \
  --metadata "StandardValueSet:ContractStatus" \
  --metadata "StandardValueSet:OrderStatus" \
  --target-org my-sandbox

# Validate-only against the target first.
sf project deploy start \
  --manifest manifest/package.xml \
  --dry-run \
  --target-org my-sandbox

sf project deploy start \
  --manifest manifest/package.xml \
  --target-org my-sandbox
```

---

## 9. Verification

**a. The settings actually landed.** Setup → Contract Settings and Setup → Order
Settings, or re-retrieve and diff:

```bash
sf project retrieve start --metadata "Settings:Contract" --metadata "Settings:Order" \
  --target-org my-sandbox
git diff -- force-app/main/default/settings/
```

**b. `EndDate` is being calculated, not typed.** Create a draft contract with a
`StartDate` and a `ContractTerm` of 12 and confirm `EndDate` comes back populated
and read-only:

```sql
SELECT Id, ContractNumber, StartDate, ContractTerm, EndDate, Status, StatusCode
FROM Contract
WHERE ContractNumber = '00000101'
```

`EndDate` is "Read-only. Calculated end date of the contract. This value is
calculated by adding the `ContractTerm` to the `StartDate`" and becomes editable
only when the auto-calculate setting is disabled (object_reference.txt
L81153–L81160). A null `EndDate` on a contract with a `StartDate` means
`ContractTerm` is blank — nothing else produces that.

**c. The validation rule blocks the right save.** Attempt an activation with one
signature date missing and confirm the error, then confirm a fully signed contract
activates:

```sql
SELECT Id, ContractNumber, Status, StatusCode, ActivatedById, ActivatedDate,
       CompanySignedDate, CustomerSignedDate
FROM Contract
WHERE StatusCode = 'Activated'
  AND (CompanySignedDate = NULL OR CustomerSignedDate = NULL)
```

Any row returned is a contract that was activated before the rule went live. There
is no supported way to walk it back — `Status` cannot be changed once a contract is
activated (object_reference.txt L81523–L81525) — so fix the signature dates in place
and record the exception.

**d. Nothing is stranded outside the Activated category.** This is the query the
renewal reminder depends on:

```sql
SELECT StatusCode, Status, COUNT(Id) contractCount
FROM Contract
GROUP BY StatusCode, Status
ORDER BY StatusCode
```

Every `Status` label the business treats as live must show `StatusCode = Activated`.
A label sitting under `Draft` will never appear in the reminder query no matter what
the label says.

**e. Order activation left the order alone.** After activating a test order:

```sql
SELECT Id, OrderNumber, Status, StatusCode, ContractId, EffectiveDate, EndDate,
       IsReductionOrder, ActivatedById, ActivatedDate, TotalAmount
FROM Order
WHERE OrderNumber = '00000101'
```

and confirm the order products are intact:

```sql
SELECT Id, OrderItemNumber, Product2Id, Quantity, UnitPrice, AvailableQuantity,
       ServiceDate, EndDate, OriginalOrderItemId
FROM OrderItem
WHERE OrderId = :orderId
```

`AvailableQuantity` is "the amount of an order product that is available to be
reduced" and an order product is reducible only while it is greater than 0
(object_reference.txt L199127–L199135). If it reads 0 on a freshly activated order,
either the order is itself a reduction order — where the value is always 0 — or the
quantity has already been reduced elsewhere.
