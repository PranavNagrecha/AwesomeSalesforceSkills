# Salesforce Channel Revenue Management
Source: https://developer.salesforce.com/docs/
Downloaded: 2026-04-03

names and marks. Other marks appearing herein may be trademarks of their respective owners.


CHANNEL PARTNER INVENTORY TRACKING
Track channel partner inventory based on sales and resale data. Leverage point-of-sale data to calculate partner inventory and improve
downstream processes, such as ship and debit claims and price protection.
Available in: Enterprise, Professional, and Unlimited Editions with the Channel Revenue Management add on
Channel Partner Inventory Tracking Standard Objects
Channel Partner Inventory Tracking data model provides objects and fields to monitor partner inventory levels, manage stock
movements, and track product consumption. Use these objects to improve supply chain visibility and reduce revenue leakage by
optimizing partner stock.
Channel Partner Inventory Tracking Metadata API Types
Metadata API enables you to access some types and feature settings that you can customize in the user interface. For more information
about Metadata API and to find a complete reference of existing metadata types, see Metadata API Developer Guide.
Channel Partner Inventory Tracking Standard Objects
Channel Partner Inventory Tracking data model provides objects and fields to monitor partner
EDITIONS
inventory levels, manage stock movements, and track product consumption. Use these objects to
improve supply chain visibility and reduce revenue leakage by optimizing partner stock.
Available in: Lightning
Experience
AccountLeadTime
Available in: Enterprise,
Represents the estimated lead time for an account for a specific activity type. The business
Professional, and Unlimited
specifies this value to indicate the time needed to complete the activity. This object is available Editions
in API version 65.0 and later.
PartnerStagedData
Represents data from partners, such as point of sale and reported inventory data, stored for further processing before being used in
downstream processes such as inventory tracking, inventory reconciliation, and ship and debit claim validation. This object is available
in API version 64.0 and later.
PartnerUnsoldInvLedger
Monitors the deduction details and links credit and debit transactions. This object is available in API version 64.0 and later.
PartnerUnsoldInventory
Tracks the product quantities available with a partner at a specific price. This object is available in API version 64.0 and later.
PtnrInvItmRecon
Represents a partner reported inventory reconciliation for a product at a location for a particular price. This object is available in API
PtnrInvItmReconTrace
Represents the source of a partner's calculated unsold inventory on a specific date. This object is available in API version 64.0 and
later.

Channel Partner Inventory Tracking AccountLeadTime
PtnrInvRecon
Represents the reconciliation of a partner's reported inventory with the partner's calculated unsold inventory on a specific date. This
object is available in API version 64.0 and later.
TransitTime
Represents the expected duration for a movement between locations. The business specifies the transit time required for inventory
to move between two locations. This object is available in API version 65.0 and later.
Rebate Management Object in Channel Partner Inventory Tracking
Rebate Management provides access to a standard objects that you can use in Channel Partner Inventory Tracking for the transactions
that need to be processed for a rebate program
AccountLeadTime
Represents the estimated lead time for an account for a specific activity type. The business specifies this value to indicate the time needed
to complete the activity. This object is available in API version 65.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccountId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
Required. Represents the account associated with this specific lead time record.
This field is a relationship field.
Relationship Name
Account
Refers To
Account
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the currency ISO code for the currency fields.
Possible values are:

Channel Partner Inventory Tracking AccountLeadTime
Field Details
• INR—Indian Rupee
• KWD—Kuwaiti Dinar
• USD—U.S. Dollar
The default value is USD.
Duration
Type
int
Properties
Create, Filter, Group, Sort, Update
Description
Required. The time taken for the inventory to be shipped from the source to the destination.
DurationType
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Required. Specifies how the duration is measured.
Possible values are:
• Days
• Months
• Weeks
The default value is Days.
LeadTimeType
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Required. Specifies the purpose of the lead time, such as transit, service, or fulfillment, for
this record.
Possible values are:
• Service
• Transit
The default value is Transit.
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort

Channel Partner Inventory Tracking AccountLeadTime
Field Details
Description
The name of the account lead time record.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
The owner of the account lead time record.
This field is a polymorphic relationship field.
Relationship Name
Owner
Refers To
Group, User
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Required. Specifies the status of the record.
Possible values are:
• Active
• Inactive
The default value is Active.
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
AccountLeadTimeHistory on page 348
History is available for tracked fields of the object.
AccountLeadTimeOwnerSharingRule on page 349
Sharing rules are available for the object.
AccountLeadTimeShare on page 351
Sharing is available for the object.

Channel Partner Inventory Tracking PartnerStagedData
PartnerStagedData
Represents data from partners, such as point of sale and reported inventory data, stored for further processing before being used in
downstream processes such as inventory tracking, inventory reconciliation, and ship and debit claim validation. This object is available
in API version 64.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccountId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The account ID of the partner that shares the data.
This field is a relationship field.
Relationship Name
Account
Refers To
Account
AccountName
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The account name of the partner that shares the data.
ActivityDate
Type
date
Properties
Create, Filter, Group, Sort, Update
Description
Required. The activity date for the partner staged data record, such as a transaction date or
an inventory reported as of date.
CurrencyIsoCode
Type
picklist

Channel Partner Inventory Tracking PartnerStagedData
Field Details
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the currency ISO code for the currency fields.
Possible values are:
• INR—Indian Rupee
• KWD—Kuwaiti Dinar
• USD—U.S. Dollar
The default value is USD.
ExternalRecordIdentifier
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The identifier for the partner staged data record in an external system.
LocationId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The location ID that's associated with the partner staged data record.
This field is a relationship field.
Relationship Name
Location
Refers To
Location
LocationName
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The location name that's associated with the partner staged data record.
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort

Channel Partner Inventory Tracking PartnerStagedData
Field Details
Description
The name of the partner staged data record.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
The name of the location that's associated with the partner staged data record.
This field is a polymorphic relationship field.
Relationship Name
Owner
Refers To
Group, User
ProductId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The product ID associated with the partner staged data record.
This field is a relationship field.
Relationship Name
Product
Refers To
Product2
ProductName
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The name of the product that's associated with the partner staged data record.
Quantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The quantity of the product in a sale transaction or an inventory report.

Channel Partner Inventory Tracking PartnerStagedData
Field Details
ResalePrice
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The price at which a partner sells a product to a customer.
SalePrice
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The price at which a manufacturer sells a product to a partner.
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Required. Specifies the status of the partner staged data record.
Possible values are:
• Failed
• New
• Processed
The default value is New.
StatusMessage
Type
textarea
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
A message with the details of the partner stage data record's status.
Type
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Required. The type of the partner staged data record.
Possible values are:

Channel Partner Inventory Tracking PartnerUnsoldInvLedger
Field Details
• PartnerReportedInventoryDocument
• PointOfSaleDocument
• PointOfSaleReturnDocument
• SaleDocument
The default value is SaleDocument.
UsageType
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Required. The usage type of the partner staged data record.
Possible values are:
• ChannelRevenueManagement
The default value is ChannelRevenueManagement.
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PartnerStagedDataHistory on page 348
History is available for tracked fields of the object.
PartnerStagedDataOwnerSharingRule on page 349
Sharing rules are available for the object.
PartnerStagedDataShare on page 351
Sharing is available for the object.
PartnerUnsoldInvLedger
Monitors the deduction details and links credit and debit transactions. This object is available in API version 64.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()

Channel Partner Inventory Tracking PartnerUnsoldInvLedger
Fields
Field Details
AvailableDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Specifies the date the unsold inventory was made available.
Comment
Type
textarea
Properties
Create, Nillable, Update
Description
Specifies the details of the ledger entry.
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the currency ISO code for the currency fields.
Possible values are:
• INR—Indian Rupee
• KWD—Kuwaiti Dinar
• USD—U.S. Dollar
The default value is USD.
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
The name of the partner unsold inventory ledger record.
PartnerUnsoldInventoryId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Specifies the unsold quantity of inventory available with the partner.

Channel Partner Inventory Tracking PartnerUnsoldInvLedger
Field Details
This field is a relationship field.
Relationship Name
PartnerUnsoldInventory
Relationship Type
Master-detail
Refers To
PartnerUnsoldInventory (the master object)
Quantity
Type
double
Properties
Create, Filter, Sort
Description
Required. Specifies the quantity of unsold inventory being used.
RebateClaimConsumedQuantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Specifies the quantity of the partner unsold inventory ledger that's consumed to calculate
a rebate claim's amount.
RebateClaimId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Specifies the rebate claim ID for the point of sale that's associated with the partner unsold
inventory ledger.
This field is a relationship field.
Relationship Name
RebateClaim
Refers To
RebateClaim
SourceType
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort

Channel Partner Inventory Tracking PartnerUnsoldInvLedger
Field Details
Description
Specifies the type of source for creating the ledger record.
Possible values are:
• ManualAdjustment
• PartnerReturn
• PointOfSale
• PointOfSaleReturn
• PriceProtection
• SaleDocument
Status
Type
picklist
Properties
Create, Filter, Group, Restricted picklist, Sort, Update
Description
Required. Specifies the status of the ledger entry.
Possible values are:
• Approved
• InTransit
• Moved
• OnHold
• Rejected
TransactionDate
Type
date
Properties
Create, Filter, Group, Sort
Description
Required. Specifies the date of the transaction.
TransactionReferenceId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort
Description
Required. Specifies the reference to the transaction that decides whether the transaction is
debit or credit.
This field is a polymorphic relationship field.
Relationship Name
TransactionReference

Channel Partner Inventory Tracking PartnerUnsoldInvLedger
Field Details
Refers To
PartnerUnsoldInventory, PriceProtectExecLineItem, PtnrInvItmRecon, TransactionJournal
TransactionType
Type
picklist
Properties
Create, Filter, Group, Restricted picklist, Sort
Description
Required. Specifies whether the transaction type is debit or credit.
Possible values are:
• Credit
• Debit
TransitDrtnReferenceRecordId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The transit duration for inventory movement between locations.
This field is a polymorphic relationship field.
Relationship Name
TransitDrtnReferenceRecord
Refers To
AccountLeadTime, TransitTime
UnitPrice
Type
currency
Properties
Filter, Nillable, Sort
Description
Specifies the per unit price of the unsold inventory.
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PartnerUnsoldInvLedgerHistory on page 348
History is available for tracked fields of the object.

Channel Partner Inventory Tracking PartnerUnsoldInventory
PartnerUnsoldInventory
Tracks the product quantities available with a partner at a specific price. This object is available in API version 64.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccountId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
Required. The ID of the partner or the distributor account for which the sale has happened.
Relationship Name
Account
Refers To
Account
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the currency ISO code for the currency fields.
Possible values are:
• INR—Indian Rupee
• KWD—Kuwaiti Dinar
• USD—U.S. Dollar
The default value is USD.
ExecutionReferenceNumber
Type
string
Properties
Create, Filter, Group, idLookup, Nillable, Sort, Update
Description
The unique execution reference number for the unsold inventory.

Channel Partner Inventory Tracking PartnerUnsoldInventory
Field Details
InTransitQuantity
Type
double
Properties
Filter, Nillable, Sort
Description
The inventory quantity that's currently in transit.
This field is a calculated field.
LocationId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The location of partner to which this sale is received.
This field is a relationship field.
Relationship Name
Location
Refers To
Location
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
The name of the partner unsold inventory record.
OnHoldCreditQuantity
Type
double
Properties
Filter, Nillable, Sort
Description
The inventory quantity that's on hold for being credited. This quantity is a sum of the quantity
of all related partner unsold inventory ledgers with the Credit transaction type and the On
Hold status.
This field is a calculated field.
OnHoldQuantity
Type
double
Properties
Filter, Nillable, Sort

Channel Partner Inventory Tracking PartnerUnsoldInventory
Field Details
Description
The quantity of inventory kept on hold for a product that has been ordered but not yet
shipped.
This field is a calculated field.
OrigUnsoldInventoryValue
Type
currency
Properties
Filter, Nillable, Sort
Description
The total value of the original quantity of unsold units that's calculated by multiplying the
original number of unsold units with the unit price.
This field is a calculated field.
OriginalQuantity
Type
double
Properties
Create, Filter, Sort
Description
Required. The total value of the original quantity.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
The ID of the user or group that owns the partner unsold inventory record.
This field is a polymorphic relationship field.
Relationship Name
Owner
Refers To
Group, User
PriceProtectionExpiryDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The date from when the price protection option expires for the inventory.

Channel Partner Inventory Tracking PartnerUnsoldInventory
Field Details
PriceProtectionStartDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The date from when the price protection option is valid for the inventory.
PriceType
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Required. The type of price at which the item is sold.
Possible values are:
• ContractPrice
• ListPrice
ProcessingStatus
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The asynchronous processing status, which is used to determine the eligibility for price
protection.
Possible values are:
• Error
• Processed
ProcessingStatusReason
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The reason for the status of the asynchronous process.
ProductId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The ID of the product that is being sold.

Channel Partner Inventory Tracking PartnerUnsoldInventory
Field Details
This field is a relationship field.
Relationship Name
Product
Refers To
Product2
RebatePartnerSpecialPrcTrmId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The rebate partner special pricing term that's used to determine the start and end date of
the ship and debit program that's associated with the partner unsold inventory.
This field is a relationship field.
Relationship Name
RebatePartnerSpecialPrcTrm
Refers To
RebatePartnerSpecialPrcTrm
RebateTypeId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ID of the rebate type which is associated with the partner unsold inventory record.
This field is a relationship field.
Relationship Name
RebateType
Refers To
ProgramRebateType
RemainingQuantity
Type
double
Properties
Filter, Nillable, Sort
Description
The remaining quantity, which is updated based on the debits point of sale.
This field is a calculated field.
RmnUnsoldInventoryValue
Type
currency

Channel Partner Inventory Tracking PartnerUnsoldInventory
Field Details
Properties
Filter, Nillable, Sort
Description
The total value of the leftover quantity of unsold units that's calculated by multiplying the
number of leftover unsold units with the unit price.
This field is a calculated field.
ShipAndDebitPgmEndDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The date when the ship and debit program ends.
ShipAndDebitPgmStartDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The date when the ship and debit program starts.
SourcePartnerUnsoldInvId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The source partner unsold inventory record that's used to create a new partner unsold
inventory record containing the updated product price.
This field is a relationship field.
Relationship Name
SourcePartnerUnsoldInv
Refers To
PartnerUnsoldInventory
TotalRebateClaimConsumedQty
Type
double
Properties
Filter, Nillable, Sort

Channel Partner Inventory Tracking PartnerUnsoldInventory
Field Details
Description
The total quantity of the partner unsold inventory that's consumed to calculate amounts of
rebate claims. It's the sum of the rebate claim consumed quantities of the partner unsold
inventory ledgers that are related to a partner unsold inventory.
This field is a calculated field.
TransactionDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The transaction date of the sale.
TransactionReferenceId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The reference ID for the credit transaction to the partner.
This field is a polymorphic relationship field.
Relationship Name
TransactionReference
Refers To
TransactionJournal
UnitPrice
Type
currency
Properties
Create, Filter, Sort, Update
Description
Required. The price at which the product is sold.
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PartnerUnsoldInventoryHistory on page 348
History is available for tracked fields of the object.
PartnerUnsoldInventoryOwnerSharingRule on page 349
Sharing rules are available for the object.

Channel Partner Inventory Tracking PtnrInvItmRecon
PartnerUnsoldInventoryShare on page 351
Sharing is available for the object.
PtnrInvItmRecon
Represents a partner reported inventory reconciliation for a product at a location for a particular price. This object is available in API
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccountId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
Required. The account of the partner whose inventory is reconciled.
This field is a relationship field.
Relationship Name
Account
Refers To
Account
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the currency ISO code for the currency fields.
Possible values are:
• INR—Indian Rupee
• KWD—Kuwaiti Dinar
• USD—U.S. Dollar
The default value is USD.
ExecutionReferenceNumber
Type
string

Channel Partner Inventory Tracking PtnrInvItmRecon
Field Details
Properties
Create, Filter, Group, idLookup, Nillable, Sort, Update
Description
A reference number in an execution process, such as a data processing engine defintion,
that's used to match the partner inventory item reconciliaiton with its related partner inventory
item reconciliation traceabilities.
LastSynchronizationDateTime
Type
dateTime
Properties
Create, Filter, Nillable, Sort, Update
Description
The most recent data and time when an execution process, such as a data processing engine
definition, is launched to reconcile the partner's reported inventory with the calculated
inventory.
LocationId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The location ID of the partner's inventory.
This field is a relationship field.
Relationship Name
Location
Refers To
Location
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
The name of the partner's inventory.
ProductId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
Required. The product ID for which the partner's inventory is reconciled.

Channel Partner Inventory Tracking PtnrInvItmRecon
Field Details
This field is a relationship field.
Relationship Name
Product
Refers To
Product2
PtnrInvReconId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Required. The partner inventory reconciliation ID that's associated with the partner inventory
item reconciliation.
This field is a relationship field.
Relationship Name
PtnrInvRecon
Relationship Type
Master-detail
Refers To
PtnrInvRecon (the master object)
QuantityDifference
Type
double
Properties
Filter, Nillable, Sort
Description
The difference between the total unsold quantity and the reported quantity.
This field is a calculated field.
ReportedQuantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The quantity that's reported by the partner for a product in their inventory. The reported
quantity is reconciled against the total unsold quantity.
SourceReferenceRecordId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update

Channel Partner Inventory Tracking PtnrInvItmRecon
Field Details
Description
The record that's the source of the partner inventory item reconciliation.
This field is a polymorphic relationship field.
Relationship Name
SourceReferenceRecord
Refers To
PartnerStagedData
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Specifies the status of the partner inventory item reconciliation.
Possible values are:
• Closed
• InProgress
• New
The default value is New.
TotalUnsoldQuantity
Type
double
Properties
Filter, Nillable, Sort
Description
The total unsold quantity of a product in the partner's inventory that's calculated based on
the partner's sales transactions. The total unsold quantity is a sum of the unsold quantity in
all partner inventory item reconciliation traceability associated with the partner inventory
item reconciliation.
This field is a calculated field.
UnitPrice
Type
currency
Properties
Create, Filter, Sort, Update
Description
The unit price of the product for which the partner's inventory is reconciled.

Channel Partner Inventory Tracking PtnrInvItmReconTrace
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PtnrInvItmReconHistory on page 348
History is available for tracked fields of the object.
PtnrInvItmReconTrace
Represents the source of a partner's calculated unsold inventory on a specific date. This object is available in API version 64.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the currency ISO code for the currency fields.
Possible values are:
• INR—Indian Rupee
• KWD—Kuwaiti Dinar
• USD—U.S. Dollar
The default value is USD.
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
The name of the partner's inventory.
PartnerUnsoldInventoryId
Type
reference
Properties
Create, Filter, Group, Sort, Update

Channel Partner Inventory Tracking PtnrInvRecon
Field Details
Description
Required. The partner unsold inventory associated with the partner inventory item
reconciliation traceability.
This field is a relationship field.
Relationship Name
PartnerUnsoldInventory
Refers To
PartnerUnsoldInventory
PtnrInvItmReconId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Required. The partner inventory item reconciliation associated with the partner inventory
item reconciliation traceability.
Relationship Name
PtnrInvItmRecon
Relationship Type
Master-detail
Refers To
PtnrInvItmRecon (the master object)
UnsoldQuantity
Type
double
Properties
Create, Filter, Sort, Update
Description
Required. The unsold quantity of the partner's inventory.
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
PtnrInvItmReconTraceHistory on page 348
History is available for tracked fields of the object.
PtnrInvRecon
Represents the reconciliation of a partner's reported inventory with the partner's calculated unsold inventory on a specific date. This
object is available in API version 64.0 and later.

Channel Partner Inventory Tracking PtnrInvRecon
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccountId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Required. The account ID of the partner whose inventory is reconciled.
This field is a relationship field.
Relationship Name
Account
Refers To
Account
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the currency ISO code for the currency fields.
Possible values are:
• INR—Indian Rupee
• KWD—Kuwaiti Dinar
• USD—U.S. Dollar
The default value is USD.
ExecutionReferenceNumber
Type
string
Properties
Create, Filter, Group, idLookup, Nillable, Sort, Update
Description
A reference number in an execution process, such as a data processing engine defintion,
that's used to match the partner inventory reconciliaiton with its related partner inventory
item reconciliations.

Channel Partner Inventory Tracking PtnrInvRecon
Field Details
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
The name of the partner inventory reconcilation record.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
The ID of the user or group that owns the partner inventory reconcilation record.
This field is a polymorphic relationship field.
Relationship Name
Owner
Refers To
Group, User
ReportedAsOfDate
Type
date
Properties
Create, Filter, Group, Sort
Description
Required. The date as of which the partner reported their inventory.
Status
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Specifies the status of the partner inventory reconciliation.
Possible values are:
• Closed
• In ProgressKuwaiti Dinar
• New

Channel Partner Inventory Tracking TransitTime
TransitTime
Represents the expected duration for a movement between locations. The business specifies the transit time required for inventory to
move between two locations. This object is available in API version 65.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the currency ISO code for the currency fields.
Possible values are:
• INR—Indian Rupee
• KWD—Kuwaiti Dinar
• USD—U.S. Dollar
The default value is USD.
DestinationLocationId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
Required. The location to which inventory is shipped.
This field is a relationship field.
Relationship Name
DestinationLocation
Refers To
Location
Duration
Type
int
Properties
Create, Filter, Group, Sort, Update

Channel Partner Inventory Tracking TransitTime
Field Details
Description
Required. The estimated time taken for the inventory to move from the source location to
the destination location.
DurationType
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Required. Specifies how the duration is measured.
Possible values are:
• Days
• Months
• Weeks
The default value is Days.
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
The name of the transit time record.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
The owner of the transit time record.
This field is a polymorphic relationship field.
Relationship Name
Owner
Refers To
Group, User
SourceLocationId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
Required. The location from which inventory is shipped.

Channel Partner Inventory Tracking Rebate Management Object in Channel Partner Inventory
Tracking
Field Details
This field is a relationship field.
Relationship Name
SourceLocation
Refers To
Location
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Required. Specifies the status of the transit time record.
Possible values are:
• Active
• Inactive
The default value is Active.
UsageType
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Required. Specifies the process, feature, or application that uses the record.
Possible values are:
• ChannelPartnerInventory
The default value is ChannelPartnerInventory.
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
TransitTimeShare on page 351
Sharing is available for the object.
Rebate Management Object in Channel Partner Inventory Tracking
Rebate Management provides access to a standard objects that you can use in Channel Partner Inventory Tracking for the transactions
that need to be processed for a rebate program
For more information about the Rebate Management object, refer to this resource.
• TransactionJournal on page 209

Channel Partner Inventory Tracking Channel Partner Inventory Tracking Metadata API Types
Channel Partner Inventory Tracking Metadata API Types
Metadata API enables you to access some types and feature settings that you can customize in the user interface. For more information
about Metadata API and to find a complete reference of existing metadata types, see Metadata API Developer Guide.
Flow for Channel Revenue Management
Represents the metadata associated with a flow. With Flow, you can create an application that navigates users through a series of
screens to query and update records in the database. You can also execute logic and provide branching capability based on user
input to build dynamic applications.
Settings
Represents the organization settings related to a feature. For example, your password policies, session settings and network access
controls are all available in the SecuritySettings component type. For more information, see Settings.
Flow for Channel Revenue Management
Represents the metadata associated with a flow. With Flow, you can create an application that navigates users through a series of screens
to query and update records in the database. You can also execute logic and provide branching capability based on user input to build
dynamic applications.
FlowActionCall
Channel Revenue Management exposes additional actionType values for the FlowActionCall Metadata type. For more information on
Flow and FlowActionCall Metadata Type, see Flow.
Field Name Field Type Description
actionType InvocableActionType Required. The action type. Additional valid values only for Channel
(enumeration of Revenue Management include:
type string)
• adjustPartnerInvShipAndDebit— Adjusts the point of
sale during ship and debit claim processing to a different partner
unsold inventory. Available in API version 64.0 and later.
• adjustPartnerUnsoldInventory— Adjusts the partner
unsold inventory quantities and prices. Available in API version 64.0
and later.
Settings
Represents the organization settings related to a feature. For example, your password policies, session settings and network access
controls are all available in the SecuritySettings component type. For more information, see Settings.
IndustriesChannelPartnerInventorySettings
Represents the setting for enabling Channel Revenue Management feature like Channel Partner Inventory Tracking.

Channel Partner Inventory Tracking Settings
IndustriesChannelPartnerInventorySettings
Represents the setting for enabling Channel Revenue Management feature like Channel Partner Inventory Tracking.
Parent Type and Manifest Access
This type extends the Metadata metadata type and inherits its fullName field.
In the package manifest, all the settings metadata types for the org are accessed using the “Settings” name. See Settings for more details.
File Suffix and Directory Location
IndustriesChannelPartnerInventorySettings values are stored in the
IndustriesChannelPartnerInventorySettings.settings file in the settings folder. The .settings files
are different from other named components, because there is only one settings file for each settings component.
Version
IndustriesChannelPartnerInventorySettings components are available in API version 63.0 and later.
Fields
Field Name Description
enableChannelPartnerInventoryTracking
Field Type
boolean
Description
Indicates whether the Channel Partner Inventory Tracking feature of Channel Revenue
Management is enabled (true) or disabled (false) for your org. The default value
is false.
Declarative Metadata Sample Definition
The following is an example of an IndustriesChannelPartnerInventorySettings component.
<?xml version="1.0" encoding="UTF-8"?>
<IndustriesChannelPartnerInventorySettings xmlns="http://soap.sforce.com/2006/04/metadata">
<enableChannelPartnerInventoryTracking>true</enableChannelPartnerInventoryTracking>
</IndustriesChannelPartnerInventorySettings>
The following is an example package.xml that references the previous definition.
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
<types>
<members>IndustriesChannelPartnerInventorySettings</members>
<name>Settings</name>
</types>
<version>63.0</version>
</Package>

Channel Partner Inventory Tracking Settings
Wildcard Support in the Manifest File
The wildcard character * (asterisk) in the package.xml manifest file doesn’t apply to metadata types for feature settings. The wildcard
applies only when retrieving all settings, not for an individual setting. For details, see Settings. For information about using the manifest
file, see Deploying and Retrieving Metadata with the Zip File.

DESIGN REGISTRATION
Enable partners to register designs and capture key details through the vendor portal for improved sales visibility. Allow channel managers
to review and approve submissions to track partner contributions and increase accountability.
Design Registration Standard Objects
Design Registration data model provides objects and fields to enable partners to register designs and capture key sales details
through a vendor portal. Use these objects to facilitate design submission, allow channel managers to approve contributions, and
enhance sales visibility.
Design Registration Standard Objects
Design Registration data model provides objects and fields to enable partners to register designs
EDITIONS
and capture key sales details through a vendor portal. Use these objects to facilitate design
submission, allow channel managers to approve contributions, and enhance sales visibility.
Available in: Lightning
Experience
Account
Available in: Enterprise,
Represents an individual account, which is an organization or person involved with your business
Professional, and
(such as customers, competitors, and partners). Unlimited, Editions
DealIndirectPartner
Represents an indirect partner’s involvement in a deal. This object is available in API version
63.0 and later.
Lead
Represents a prospect or lead.
Opportunity
Represents an opportunity, which is a sale or pending deal.
OpportunityLineItem
Represents an opportunity line item, which is a member of the list of Product2 products associated with an Opportunity.
Pricebook2
Represents a price book that contains the list of products that your org sells.
Product2
Represents a product that your company sells.
Rebate Management Object in Design Registration
Rebate Management provides access to a standard object that you can use in Design Registration to manage a relationship between
accounts.
Account
Represents an individual account, which is an organization or person involved with your business (such as customers, competitors, and
partners).

Design Registration Account
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), merge(),
query(), retrieve(), search(), undelete(), update(), upsert()
Special Access Rules
Experience Cloud site or Customer Portal users can access their own accounts and any account shared with them.
Fields
Field Name Details
AccountNumber
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Account number assigned to this account (not the unique, system-generated ID assigned
during creation). Maximum size is 40 characters.
AccountSource
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The source of the account record. For example, Advertisement or Trade Show.
The source is selected from a picklist of available values, which are set by an administrator.
Each picklist value can have up to 40 characters.
ActivityMetricId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
When Einstein Activity Capture with Activity Metrics is enabled, the ID of the related activity
metric.
This field is a relationship field.
Relationship Name
ActivityMetric
Refers To
ActivityMetric
ActivityMetricRollupId
Type
reference

Design Registration Account
Field Name Details
Properties
Filter, Group, Nillable, Sort
Description
When Einstein Activity Capture with Activity Metrics is enabled, the ID of the related activity
metric rollup.
This field is a relationship field.
Relationship Name
ActivityMetricRollup
Refers To
ActivityMetricRollup
AnnualRevenue
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
Estimated annual revenue of the account.
BillingAddress
Type
address
Properties
Filter, Nillable
Description
The compound form of the billing address. Read-only. For details on compound address
fields, see Address Compound Fields.
BillingCity
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Details for the billing address of this account. Maximum size is 40 characters.
BillingCountry
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Details for the billing address of this account. Maximum size is 80 characters.

Design Registration Account
Field Name Details
BillingCountryCode
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ISO country code for the account’s billing address.
BillingGeocodeAccuracy
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Accuracy level of the geocode for the billing address. For details on geolocation compound
fields, see Compound Field Considerations and Limitations.
BillingLatitude
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Used with BillingLongitude to specify the precise geolocation of a billing address.
Acceptable values are numbers between –90 and 90 with up to 15 decimal places. For details
on geolocation compound fields, see Compound Field Considerations and Limitations.
BillingLongitude
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Used with BillingLatitude to specify the precise geolocation of a billing address.
Acceptable values are numbers between –180 and 180 with up to 15 decimal places. See
Compound Field Considerations and Limitations for details on geolocation compound fields.
BillingPostalCode
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Details for the billing address of this account. Maximum size is 20 characters.
BillingState
Type
string

Design Registration Account
Field Name Details
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Details for the billing address of this account. Maximum size is 80 characters.
BillingStateCode
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ISO state code for the account’s billing address.
BillingStreet
Type
textarea
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Street address for the billing address of this account.
ChannelProgramLevelName
Type
string
Properties
Group, Nillable
Description
Read only. Name of the channel program level the account has enrolled. If this account has
enrolled more than one channel program level, the oldest channel program name is displayed.
ChannelProgramName
Type
string
Properties
Group, Nillable
Description
Read only. Name of the channel program the account has enrolled. If this account has enrolled
more than one channel program, the oldest channel program name is displayed.
CleanStatus
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Indicates the record’s clean status as compared with Data.com..

Design Registration Account
Field Name Details
Possible values are:
• AcknowledgedThe label on the account record detail page is Reviewed.
• Different
• Inactive
• Matched—The label on the account record detail page is In Sync.
• NotFound
• PendingThe label on the account record detail page is Not Compared.
• SelectMatch
• Skipped
ConnectionReceivedId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
ID of the PartnerNetworkConnection that shared this record with your organization. This
field is available if you enabled Salesforce to Salesforce.
ConnectionSentId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
ID of the PartnerNetworkConnection that you shared this record with. This field is available
if you enabled Salesforce to Salesforce. This field is supported using API versions earlier than
15.0. In all other API versions, this field’s value is null. You can use the new
PartnerNetworkRecordConnection object to forward records to connections.
Description
Type
textarea
Properties
Create, Nillable, Update
Description
Text description of the account. Limited to 32,000 KB.
DunsNumber
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update

Design Registration Account
Field Name Details
Description
The Data Universal Numbering System (D-U-N-S) number is a unique, nine-digit number
assigned to every business location in the Dun & Bradstreet database that has a unique,
separate, and distinct operation. D-U-N-S numbers are used by industries and organizations
around the world as a global standard for business identification and tracking. Maximum
size is 9 characters. This field is available on business accounts, not person accounts.
Note: This field is only available to organizations that use Data.com Prospector or
Data.com Clean.
Fax
Type
phone
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Fax number for the account.
Industry
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
An industry associated with this account. For example, Biotechnology. Maximum size
is 40 characters.
IsBuyer
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates that the account is enabled as a buyer for Lightning B2B Commerce. The default
value is false. This field is available in API version 48.0 and later.
Note: This field is only available to organizations that have the B2B Commerce license
enabled.
IsCustomerPortal
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether the account has at least one contact enabled to use the org's Experience
Cloud site or Customer Portal (true) or not (false). This field is available if Customer
Portal is enabled OR digital experiences is enabled.

Design Registration Account
Field Name Details
If your org is enabled to use Content Security Policy (CSP) features, then this field is visible
on the Account object even if those features are later disabled.
If you change this field's value from true to false, you can disable up to 100 Experience
Cloud site or Customer Portal users associated with the account and permanently delete all
of the account's site roles and groups. You can't restore deleted site roles and groups.
Exclude this field when merging accounts.
This field can be updated in API version 16.0 and later.
Tip: We recommend that you update up to 50 contacts simultaneously when
changing the accounts on contacts enabled for an Experience Cloud site. We also
recommend that you make this update after business hours.
IsPartner
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether the account has at least one contact enabled to use the org's partner
portal (true) or not (false). This field is available if partner relationship management
(partner portal) is enabled OR digital experiences is enabled and you have partner portal
licenses.
If you change this field's value from true to false, you can disable up to 15 partner
portal users associated with the account and permanently delete all of the account's partner
portal roles and groups. You can't restore deleted partner portal roles and groups.
Disabling a partner portal user in the Salesforce user interface or the API doesn’t change this
field's value from true to false.
Even if this field's value is false, you can enable a contact on an account as a partner
portal user via the API.
Exclude this field when merging accounts.
This field can be updated in API version 16.0 and later.
Tip: We recommend that you update up to 50 contacts simultaneously when
changing the accounts on contacts enabled for an Experience Cloud site. We also
recommend that you make this update after business hours.
IsPersonAccount
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Read only. Label is Is Person Account. Indicates whether this account has a record type of
Person Account (true) or not (false).

Design Registration Account
Field Name Details
IsPriorityRecord
Type
boolean
Properties
Defaulted on create, Group
Description
Shows whether the user has marked the account as important (True) or not (False). The
default value is false. Available in API version 60.0 and later.
Jigsaw
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
References the ID of a company in Data.com. If an account has a value in this field, it means
that the account was imported from Data.com. If the field value is null, the account was
not imported from Data.com. Maximum size is 20 characters. Available in API version 22.0
and later. Label is Data.com Key. This field is available on business accounts, not person
accounts.
Important: The Jigsaw field is exposed in the API to support troubleshooting for
import errors and reimporting of corrected data. Do not modify the value in the
Jigsaw field.
JigsawCompanyId
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The ID of the company in reference to Jigsaw.
Important: The Jigsaw field is exposed in the API to support troubleshooting for
import errors and reimporting of corrected data. Don’t modify the value in the
Jigsaw field.
LastActivityDate
Type
date
Properties
Filter, Group, Nillable, Sort
Description
Value is one of the following, whichever is the most recent:
• Due date of the most recent event logged against the record.
• Due date of the most recently closed task associated with the record.

Design Registration Account
Field Name Details
LastReferencedDate
Type
datetime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last accessed this record indirectly, for example,
through a list view or related record.
LastViewedDate
Type
datetime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate), but
not viewed it.
MasterRecordId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
If this object was deleted as the result of a merge, this field contains the ID of the record that
was kept. If this object was deleted for any other reason, or has not been deleted, the value
is null.
This is a relationship field.
Relationship Name
MasterRecord
Relationship Type
Lookup
Refers To
Account
NaicsCode
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The six-digit North American Industry Classification System (NAICS) code is the standard
used by business and government to classify business establishments into industries,
according to their economic activity for the purpose of collecting, analyzing, and publishing

Design Registration Account
Field Name Details
statistical data related to the U.S. business economy. Maximum size is 8 characters. This field
is available on business accounts, not person accounts.
Note: This field is only available to organizations that use Data.com Prospector or
Data.com Clean.
NaicsDesc
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
A brief description of an org’s line of business, based on its NAICS code. Maximum size is 120
characters. This field is available on business accounts, not person accounts.
Note: This field is only available to organizations that use Data.com Prospector or
Data.com Clean.
Name
Type
string
Properties
Create, Filter, Group, Sort, Update
Description
Required. Label is Account Name. Name of the account. Maximum size is 255 characters.
If the account has a record type of Person Account:
• This value is the concatenation of the FirstName, MiddleName, LastName, and
Suffix of the associated person contact.
• You can't modify this value.
NumberOfEmployees
Type
int
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Label is Employees. Number of employees working at the company represented by this
account. Maximum size is eight digits.
OperatingHoursId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The operating hours associated with the account. Available only if Field Service is enabled.
This is a relationship field.

Design Registration Account
Field Name Details
Relationship Name
OperatingHours
Relationship Type
Lookup
Refers To
OperatingHours
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
The ID of the user who currently owns this account. Default value is the user logged in to
the API to perform the create.
If you have set up account teams in your org, updating this field has different consequences
depending on your version of the API:
• For API version 12.0 and later, sharing records are kept, as they are for all objects.
• For API version before 12.0, sharing records are deleted.
• For API version 16.0 and later, users must have the “Transfer Record” permission in order
to update (transfer) account ownership using this field.
This is a relationship field.
Relationship Name
Owner
Relationship Type
Lookup
Refers To
User
Ownership
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Ownership type for the account, for example Private, Public, or Subsidiary.
ParentId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
ID of the parent object, if any.

Design Registration Account
Field Name Details
This is a relationship field.
Relationship Name
Parent
Relationship Type
Lookup
Refers To
Account
PersonActionCadenceAssigneeId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
The ID of the sales rep designated to work the lead through their assigned cadence. This
field is available in API version 47.0 and later when the Sales Engagement license is enabled.
To see this field, the user also needs the Sales Engagement User or Sales Engagement Quick
Cadence Creator user permission set.
This field is a polymorphic relationship field.
Relationship Name
PersonActionCadenceAssignee
Refers To
Group, User
PersonActionCadenceId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
The ID of the lead’s assigned cadence. This field is available in API version 46.0 and later when
the Sales Engagement license is enabled. To see this field, the user also needs the Sales
Engagement User or Sales Engagement Quick Cadence Creator user permission set.
This is a relationship field.
Relationship Name
PersonActionCadence
Refers To
ActionCadence
PersonActionCadenceState
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort

Design Registration Account
Field Name Details
Description
The state of the current action cadence tracker. This field is available in API version 50.0 and
later when the Sales Engagement license is enabled. To see this field, the user also needs
the Sales Engagement User or Sales Engagement Quick Cadence Creator user permission
set.
Possible values are:
• Complete
• Error
• Initializing
• Paused
• Processing
• Running
PersonIndividualId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
ID of the data privacy record associated with this person’s account. This field is available if
you enabled Data Protection and Privacy in Setup.
Available in API version 42.0 and later.
PersonScheduledResumeDateTime
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The date and time when the action cadence tracker is going to resume after it’s paused or
on a wait step. This field is available in API version 54.0 and later when the Sales Engagement
license is enabled. To see this field, the user also needs the Sales Engagement User or Sales
Engagement Quick Cadence Creator user permission set.
Phone
Type
phone
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Phone number for this account. Maximum size is 40 characters.
PhotoUrl
Type
url

Design Registration Account
Field Name Details
Properties
Filter, Group, Nillable, Sort
Description
Path to be combined with the URL of a Salesforce instance (for example,
https://yourInstance.salesforce.com/) to generate a URL to request the social network
profile image associated with the account. Generated URL returns an HTTP redirect (code
302) to the social network profile image for the account.
Blank if Social Accounts and Contacts isn't enabled for the org or if Social Accounts and
Contacts is disabled for the requesting user.
Rating
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The account’s prospect rating, for example Hot, Warm, or Cold.
RecordTypeId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
ID of the record type assigned to this object.
Salutation
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Honorific added to the name for use in letters, etc. This field is available on person accounts.
ShippingAddress
Type
address
Properties
Filter, Nillable
Description
The compound form of the shipping address. Read-only. See Address Compound Fields for
details on compound address fields.
ShippingCity
Type
string

Design Registration Account
Field Name Details
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Details of the shipping address for this account. City maximum size is 40 characters
ShippingCountry
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Details of the shipping address for this account. Country maximum size is 80 characters.
ShippingCountryCode
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ISO country code for the account’s shipping address.
ShippingGeocodeAccuracy
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Accuracy level of the geocode for the shipping address. For details on geolocation compound
fields, see Compound Field Considerations and Limitations.
ShippingLatitude
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Used with ShippingLongitude to specify the precise geolocation of a shipping address.
Acceptable values are numbers between –90 and 90 with up to 15 decimal places. For details
on geolocation compound fields, see Compound Field Considerations and Limitations.
ShippingLongitude
Type
double
Properties
Create, Filter, Nillable, Sort, Update

Design Registration Account
Field Name Details
Description
Used with ShippingLatitude to specify the precise geolocation of an address.
Acceptable values are numbers between –180 and 180 with up to 15 decimal places. For
details on geolocation compound fields, see Compound Field Considerations and Limitations.
ShippingPostalCode
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Details of the shipping address for this account. Postal code maximum size is 20 characters.
ShippingState
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Details of the shipping address for this account. State maximum size is 80 characters.
ShippingStateCode
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ISO state code for the account’s shipping address.
ShippingStreet
Type
textarea
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The street address of the shipping address for this account. Maximum of 255 characters.
Sic
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Standard Industrial Classification code of the company’s main business categorization, for
example, 57340 for Electronics. Maximum of 20 characters. This field is available on business
accounts, not person accounts.

Design Registration Account
Field Name Details
SicDesc
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
A brief description of an org’s line of business, based on its SIC code. Maximum length is 80
characters. This field is available on business accounts, not person accounts.
Site
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Name of the account’s location, for example Headquarters or London. Label is
Account Site. Maximum of 80 characters.
TickerSymbol
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The stock market symbol for this account. Maximum of 20 characters. This field is available
on business accounts, not person accounts.
Tradestyle
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
A name, different from its legal name, that an org may use for conducting business. Similar
to “Doing business as” or “DBA”. Maximum length is 255 characters. This field is available on
business accounts, not person accounts.
Note: This field is only available to organizations that use Data.com Prospector or
Data.com Clean.
Type
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Type of account, for example, Customer, Competitor, or Partner.

Design Registration Account
Field Name Details
Website
Type
url
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The website of this account. Maximum of 255 characters.
YearStarted
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The date when an org was legally established. Maximum length is 4 characters. This field is
available on business accounts, not person accounts.
Note: This field is only available to organizations that use Data.com Prospector or
Data.com Clean.
IsPersonAccount Fields
These fields are the subset of person account fields that are contained in the child person contact record of each person account. If the
IsPersonAccount field has the value false, the following fields have a null value and can't be modified. If true, the fields can
be modified.
Person account fields only show when person accounts are enabled. Person accounts are disabled by default.
Field Name Details
FirstName
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
First name of the person for a person account. Maximum size is 40 characters.
LastName
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Last name of the person for a person account. Required if the record type is a person account
record type. Maximum size is 80 characters.

Design Registration Account
Field Name Details
MiddleName
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Middle name of the person for a person account. Maximum size is 40 characters.
PersonAssistantName
Type
string
Properties
Create, Filter, Nillable, Update
Description
The person account’s assistant name. Label is Assistant. Maximum size is 40 characters.
PersonAssistantPhone
Type
phone
Properties
Create, Filter, Nillable, Update
Description
The person account’s assistant phone. Label is Asst. Phone. Maximum size is 40 characters.
PersonBirthDate
Type
date
Properties
Create, Filter, Nillable, Update
Description
The birthday of the contact associated with this person account. Label is Birthdate. The year
portion of the PersonBirthDate field is ignored in filter criteria, including report filters,
list view filters, and SOQL queries. For example, the following SOQL query returns person
accounts with birthdays later in the year than today:
SELECT FirstName, LastName, PersonBirthDate
FROM Account
WHERE Birthdate > TODAY
PersonContactId
Type
reference
Properties
Filter, Nillable, Update
Description
The ID for the contact associated with this person account. Label is Contact ID.

Design Registration Account
Field Name Details
PersonDepartment
Type
string
Properties
Create, Filter, Nillable, Update
Description
The department. Label is Department. Maximum size is 80 characters.
PersonEmail
Type
email
Properties
Create, Filter, Nillable, Update
Description
Email address for this person account. Label is Email.
PersonEmailBouncedDate
Type
dateTime
Properties
Create, Filter, Nillable, Update
Description
If bounce management is activated and an email sent to the person account bounces, the
date and time the bounce occurred.
PersonEmailBouncedReason
Type
string
Properties
Create, Filter, Nillable, Update
Description
If bounce management is activated and an email sent to the person account bounces, the
reason the bounce occurred
PersonGenderIdentity
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The person’s internal experience of their gender, which may or may not correspond to the
person’s designated sex at birth. Label is Gender Identity.
PersonHasOptedOutOfEmail
Type
boolean
Properties
Create, Filter, Nillable, Update

Design Registration Account
Field Name Details
Description
Indicates whether the person account has opted out of email (true) or not (false). Label
is Email Opt Out.
PersonHomePhone
Type
phone
Properties
Create, Filter, Nillable, Update
Description
The home phone number for this person account. Label is Home Phone.
PersonLeadSource
Type
picklist
Properties
Create, Filter, Nillable, Update
Description
The person account’s lead source. Label is Lead Source.
PersonMailingAddress
Type
address
Properties
Filter, Nillable
Description
The compound form of the person account mailing address. Read-only. For details on
compound address fields, see Address Compound Fields.
• PersonMailingCity Type
string
• PersonMailingCountry
• PersonMailingPostalCode Properties
Create, Filter, Nillable, Update
• PersonMailingState
Description
Details about the mailing address for this person account. Labels are Mailing City, Mailing
Country, Postal Code, and State. Maximum size for city and country is 40 characters.
Maximum size for postal code and state is 20 characters.
• PersonMailingCountryCode Type
picklist
• PersonMailingStateCode
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ISO country or state code for the mailing address of the person account.

Design Registration Account
Field Name Details
PersonMailingGeocodeAccuracy
Type
picklist
Properties
Retrieve, Query, Restricted picklist, Nillable
Description
Accuracy level of the geocode for the person’s mailing address. For details on geolocation
compound fields, see Compound Field Considerations and Limitations.
PersonMailingLatitude
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Used with PersonMailingLongitude to specify the precise geolocation of a person
account’s mailing address. Acceptable values are numbers between –90 and 90 with up to
15 decimal places. For details on geolocation compound fields, see Compound Field
Considerations and Limitations.
PersonMailingLongitude
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Used with PersonMailingLatitude to specify the precise geolocation of a person
account’s mailing address. Acceptable values are numbers between –180 and 180 with up
to 15 decimal places. For details on geolocation compound fields, see Compound Field
Considerations and Limitations.
PersonMailingStreet
Type
textarea
Properties
Create, Filter, Nillable, Update
Description
The mailing street address for this person account. Label is Mailing Street. Maximum size
is 255 characters.
PersonMobilePhone
Type
phone
Properties
Create, Filter, Nillable, Update
Description
The mobile phone number for this person account. Label is Mobile.

Design Registration Account
Field Name Details
• PersonOtherCity Type
string
• PersonOtherCountry
• PersonOtherPostalCode Properties
Create, Filter, Nillable, Update
• PersonOtherState
Description
Details about the alternate address for this person account. Labels are Other City, Other
Country, Other Zip/Postal Code, and Other State.
• PersonOtherCountryCode Type
picklist
• PersonOtherStateCode
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ISO country or state code for the alternate address of the person account.
PersonOtherLatitude
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Used with PersonOtherLongitude to specify the precise geolocation of a person
account’s alternate address. Acceptable values are numbers between –90 and 90 with up
to 15 decimal places. For details on geolocation compound fields, see Compound Field
Considerations and Limitations.
PersonOtherLongitude
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Used with PersonOtherLatitude to specify the precise geolocation of a person
account’s alternate address. Acceptable values are numbers between –180 and 180 with up
to 15 decimal places. For details on geolocation compound fields, see Compound Field
Considerations and Limitations.
PersonOtherPhone
Type
phone
Properties
Create, Filter, Nillable, Update
Description
The alternate phone number for this person account. Label is Other Phone.

Design Registration Account
Field Name Details
PersonOtherStreet
Type
textarea
Properties
Create, Filter, Nillable, Update
Description
The person account’s alternate street address. Label is Other Street.
PersonPronouns
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The individual’s personal pronouns, reflecting their gender identity. Others can use these
pronouns to refer to the individual in the third person. The entry is selected from a picklist
of available values, which the administrator sets. Maximum 40 characters. Label is Pronouns.
Possible values are:
• He/Him
• He/They
• Not Listed
• She/Her
• She/They
• They/Them
PersonReportsToId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort Update
Description
ID of the person account or contact that this person account reports to.
This field doesn't appear if enableReportsToOnPersonAccount in the
AccountSettings metadata type is false.
Available in API version 62.0 and later.
This is a relationship field.
Relationship Name
PersonReportsTo
Relationship Type
Lookup
Refers To
Contact

Design Registration Account
Field Name Details
PersonTitle
Type
string
Properties
Create, Filter, Nillable, Update
Description
The person account’s title. Label is Title. Maximum size is 80 characters. When converting a
lead to a person account, the conversion fails if the lead’s Title field contains more than 80
characters.
Suffix
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Name suffix of the person for a person account. Maximum size is 40 characters.
Note: When importing account data, users need the Set Audit Fields upon Record Creation permission to assign values to audit
fields such as CreatedDate. Audit fields are automatically updated during API operations unless you set these fields yourself.
Usage
Use this object to query and manage accounts in your org. Client applications can create, update, delete, or query Attachment records
associated with an account via the API.
Client applications can also create or update account objects by converting a Lead via the convertLead() call.
If the values in the IsPersonAccount Fields are not null, you can't change IsPersonAccount to false or an error occurs.
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
AccountChangeEvent (API version 44.0)
Change events are available for the object.
AccountFeed (API version 18.0)
Feed tracking is available for the object.
AccountHistory (API version 11.0)
History is available for tracked fields of the object.
AccountOwnerSharingRule
Sharing rules are available for the object.
AccountShare
Sharing is available for the object.

Design Registration DealIndirectPartner
DealIndirectPartner
Represents an indirect partner’s involvement in a deal. This object is available in API version 63.0 and later.
A DealIndirectPartner record can be created manually or through automation when a partner is associated with an opportunity, lead,
or account, capturing role and contact information.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccountId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The account associated with the indirect partner on the deal.
This field is a relationship field.
Relationship Name
Account
Refers To
Account
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the record was last referenced by the user or system.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
Date and the timestamp when the record was last viewed in the Salesforce UI. Helps monitor
user access and engagement.
LeadId
Type
reference

Design Registration DealIndirectPartner
Field Details
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Reference to a lead associated with this indirect partner record.
This field is a relationship field.
Relationship Name
Lead
Refers To
Lead
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
System-generated unique identifier for the record, used for lookup and reference purposes.
OpportunityId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Opportunity associated with the indirect partner.
This field is a relationship field.
Relationship Name
Opportunity
Refers To
Opportunity
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
User or group that owns this record.
This field is a polymorphic relationship field.
Relationship Name
Owner
Refers To
Group, User

Design Registration DealIndirectPartner
Field Details
PartnerName
Type
string
Properties
Create, Filter, Group, Sort, Update
Description
Name of the indirect partner participating in the deal. This field captures the business or
entity name.
PartnerRoleType
Type
picklist
Properties
Create, Filter, Group, Sort, Update
Description
The role played by the indirect partner in the deal. Common values might include Reseller,
Distributor, and so on.
PrimaryContactFirstName
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
First name of the primary contact at the partner organization.
PrimaryContactLastName
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Last name of the primary contact at the partner organization.
PrimaryContactName
Type
string
Properties
Filter, Group, Nillable, Sort
Description
Full name of the primary contact. This field may be auto-generated by combining first and
last names or used for reporting purposes.
PrimaryContactSalutation
Type
picklist

Design Registration Lead
Field Details
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Salutation for the primary contact.
Possible values are:
• Dr.
• Mr.
• Mrs.
• Ms.
• Mx.
• Prof.
Lead
Represents a prospect or lead.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), merge(),
query(), retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
ActionCadenceAssigneeId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
The ID of the sales rep designated to work the lead through their assigned cadence. This
field is available in API version 48.0 and later when the Sales Engagement license is enabled.
To see this field, the user also needs the Sales Engagement User or Sales Engagement Quick
Cadence Creator user permission set.
ActionCadenceId
Type
reference
Properties
Filter, Group, Nillable, Sort

Design Registration Lead
Field Details
Description
The ID of the lead’s assigned cadence. This field is available in API version 48.0 and later when
the Sales Engagement license is enabled. To see this field, the user also needs the Sales
Engagement User or Sales Engagement Quick Cadence Creator user permission set.
ActionCadenceState
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
The state of the current action cadence tracker. This field is available in API version 50.0 and
later when the Sales Engagement license is enabled. To see this field, the user also needs
the Sales Engagement User or Sales Engagement Quick Cadence Creator user permission
set.
Possible values are:
• Complete
• Error
• Initializing
• Paused
• Processing
• Running
ActiveTrackerCount
Type
int
Properties
Filter, Group, Nillable, Sort
Description
The number of cadences that are actively running on this lead. This field is available in API
user also needs the Sales Engagement User or Sales Engagement Quick Cadence Creator
user permission set.
ActivityMetricId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
When Einstein Activity Capture with Activity Metrics is enabled, the ID of the related activity
metric.
This field is a relationship field.
This field is available in API version 41.0 and later.

Design Registration Lead
Field Details
Relationship Name
ActivityMetric
Refers To
ActivityMetric
ActivityMetricRollupId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
When Einstein Activity Capture with Activity Metrics is enabled, the ID of the related activity
metric rollup.
This field is a relationship field.
This field is available in API version 41.0 and later.
Relationship Name
ActivityMetricRollup
Refers To
ActivityMetricRollup
Address
Type
address
Properties
Filter, Nillable
Description
The compound form of the address. Read-only. For details on compound address fields, see
Address Compound Fields.
AnnualRevenue
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
Annual revenue for the lead’s company.
City
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
City for the lead’s address.

Design Registration Lead
Field Details
CleanStatus
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Indicates the record's clean status compared with Data.com. .
Several values for CleanStatus appear with different labels on the lead record.
Values include:
• Acknowledged - Reviewed
• Different
• Inactive
• Matched - In Sync
• NotFound - Not Found
• Pending - Not Compared
• SelectMatch - Select Match Skipped
Company
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Required. The lead’s company.
If person account record types have been enabled, and if the value of Company is null, the
lead converts to a person account.
CompanyDunsNumber
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The Data Universal Numbering System (D-U-N-S) number, which is a unique, nine-digit
number assigned to every business location in the Dun & Bradstreet database that has a
unique, separate, and distinct operation. Industries and companies use D-U-N-S numbers
as a global standard for business identification and tracking. Maximum size is 9 characters.
This field is only available to organizations that use Data.com Prospector or Data.com Clean.
ConvertedAccountId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort

Design Registration Lead
Field Details
Description
Object reference ID that points to the account into which the lead converted.
This is a relationship field.
Relationship Name
ConvertedAccount
Relationship Type
Lookup
Refers To
Account
ConvertedContactId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort
Description
Object reference ID that points to the contact into which the lead converted.
This is a relationship field.
Relationship Name
ConvertedContact
Relationship Type
Lookup
Refers To
Contact
ConvertedDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort
Description
Date on which this lead was converted.
ConvertedOpportunityId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort
Description
Object reference ID that points to the opportunity into which the lead has been converted.
This is a relationship field.
Relationship Name
ConvertedOpportunity

Design Registration Lead
Field Details
Relationship Type
Lookup
Refers To
Opportunity
ConnectionReceivedId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
ID of the PartnerNetworkConnection that shared this record with your org. This field is
available when Salesforce to Salesforce is enabled.
ConnectionSentId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
ID of the PartnerNetworkConnection that this record is shared with. This field is available
Salesforce to Salesforce is enabled. In API version 16.0 and later, this value is null. Use
PartnerNetworkRecordConnection object to forward records to connections.
Country
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The lead’s country.
CountryCode
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ISO country code for the lead’s address.
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update

Design Registration Lead
Field Details
Description
Available only for organizations with the multicurrency feature enabled. Contains the ISO
code for any currency allowed by the organization.
DandBCompanyId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Reference ID to a Dun & Bradstreet® company record, associated with an account added
from Data.com.
Relationship Name
DandbCompany
Refers To
DandbCompany
Description
Type
textarea
Properties
Create, Nillable, Update
Description
The lead’s description.
Division
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
A logical segment of your organization's data. For example, if your company is organized
into different business units, you could create a division for each business unit, such as North
America, Healthcare, or Consulting. Available only when the Division permission is enabled.
Email
Type
email
Properties
Create, Filter, Group, idLookup, Nillable, Sort, Update
Description
The lead’s email address.
EmailBouncedDate
Type
dateTime

Design Registration Lead
Field Details
Properties
Filter, Nillable, Sort, Update
Description
If bounce management is activated and an email sent to the lead bounced, the date and
time of the bounce. Email bounce functionality isn't triggered by record updates, including
updates to this field.
EmailBouncedReason
Type
string
Properties
Filter, Group, Nillable, Sort, Update
Description
If bounce management is activated and an email sent to the lead bounced, the reason for
the bounce. Email bounce functionality isn't triggered by record updates, including updates
to this field.
ExportStatus
Type
picklist
Properties
Filter, Restricted picklist, Sort
Description
Derived field for the record map for Partner Connect. The export status of this opportunity
to the partner’s connected org. To see this field, enable Partner Connect and add the Export
Vendor Records to an Authorized Partner Org user permission to the cosell export user. See
Set Up Partner Connect as a Vendor in Salesforce Help. Available in API version 62.0 and later.
Fax
Type
phone
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The lead’s fax number.
FirstCallDateTime
Type
datetime
Properties
Filter, Nillable, Sort
Description
The date and time of the first call placed to the lead. This field is available in API version 48.0
when the Sales Engagement license is enabled. To see this field, the user also needs the Sales
Engagement User or Sales Engagement Quick Cadence Creator user permission set.

Design Registration Lead
Field Details
FirstEmailDateTime
Type
datetime
Properties
Filter, Nillable, Sort
Description
The date and time of the first email sent to the lead. This field is available in API version 48.0
when the Sales Engagement license is enabled. To see this field, the user also needs the Sales
Engagement User or Sales Engagement Quick Cadence Creator user permission set.
FirstName
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The lead’s first name up to 40 characters.
GeocodeAccuracy
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Accuracy level of the geocode for the address. For details on geolocation compound fields,
see Compound Field Considerations and Limitations.
GenderIdentity
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The lead’s internal experience of their gender, which may or may not correspond to their
designated sex at birth.
HasOptedOutOfEmail
Type
boolean
Properties
Create, Defaulted on create, Filter, Update
Description
Indicates whether the lead doesn’t want to receive email from Salesforce (true) or does
(false). Label is Email Opt Out.
HasOptedOutOfFax
Type
boolean

Design Registration Lead
Field Details
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether the lead doesn’t want to receive faxes from Salesforce (true) or does
(false). Label is FaxOpt Out.
IndividualId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
ID of the data privacy record associated with this lead. This field is available if you enabled
Data Protection and Privacy in Setup.
Relationship Name
Individual
Relationship Type
Lookup
Refers To
Individual
Industry
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Industry in which the lead works.
IsConverted
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort
Description
Indicates whether the lead has been converted (true) or not (false). Label is Converted.
IsDeleted
Type
boolean
Properties
Defaulted on create, Filter
Description
Indicates whether the object has been moved to the Recycle Bin (true) or not (false).
Label is Deleted.

Design Registration Lead
Field Details
IsPriorityRecord
Type
boolean
Properties
Defaulted on create, Group
Description
Shows whether the user has marked the lead as important (True) or not (False). The
default value is false. Available in API version 59.0 and later.
IsUnreadByOwner
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
If true, lead has been assigned, but not yet viewed. See Unread Leads for more information.
Label is Unread By Owner.
Jigsaw
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
References the ID of a contact in Data.com. If a lead has a value in this field, it means that a
contact was imported as a lead from Data.com. If the contact (converted to a lead) wasn’t
imported from Data.com, the field value is null. Maximum size is 20 characters. Available in
API version 22.0 and later. Label is Data.com Key.
Important: The Jigsaw field is exposed in the API to support troubleshooting for
import errors and reimporting of corrected data. Don’t modify the value in the
Jigsaw field.
JigsawContactId
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The ID of the contact in reference to Jigsaw.
Important: The Jigsaw field is exposed in the API to support troubleshooting for
import errors and reimporting of corrected data. Don’t modify the value in the
Jigsaw field.
LastActivityDate
Type
date

Design Registration Lead
Field Details
Properties
Filter, Group, Nillable, Sort
Description
Value is the most recent of either:
• Due date of the most recent event logged against the record.
• Due date of the most recently closed task associated with the record.
LastName
Type
string
Properties
Create, Filter, Group, Sort, Update
Description
Required. Last name of the lead up to 80 characters.
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
LastViewedDate
Type
datetime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
Latitude
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Used with Longitude to specify the precise geolocation of an address. Acceptable values
are numbers between –90 and 90 up to 15 decimal places. For details on geolocation
compound fields, see Compound Field Considerations and Limitations
LeadSource
Type
picklist

Design Registration Lead
Field Details
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The origin or source of the lead.
Longitude
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Used with Latitude to specify the precise geolocation of an address. Acceptable values
are numbers between –180 and 180 up to 15 decimal places. For details on geolocation
compound fields, see Compound Field Considerations and Limitations.
MasterRecordId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
If this record was deleted as the result of a merge, this field contains the ID of the record that
was kept. If this record was deleted for any other reason, or hasn’t been deleted, the value
is null.
When using Apex triggers to determine which record was deleted in a merge event, this
field’s value is the ID of the record that remains in Trigger.old. In Trigger.new,
the value is null.
This is a relationship field.
Relationship Name
MasterRecord
Relationship Type
Lookup
Refers To
Lead
MiddleName
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The lead’s middle name. Maximum size is 40 characters.
MobilePhone
Type
phone

Design Registration Lead
Field Details
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The lead’s mobile phone number.
Name
Type
string
Properties
Filter, Group, Sort
Description
Concatenation of FirstName, MiddleName, LastName, and Suffix up to 203
characters, including whitespaces.
NumberOfEmployees
Type
int
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Number of employees at the lead’s company. Label is Employees.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
ID of the lead’s owner.
This is a polymorphic relationship field.
Relationship Name
Owner
Relationship Type
Lookup
Refers To
Group, User
PartnerAccountId
Type
reference
Properties
Filter, Group, Nillable, Sort

Design Registration Lead
Field Details
Description
ID of the partner account for the partner user that owns this lead. Available if Partner
Relationship Management is enabled or if digital experiences is enabled and you have partner
portal licenses.
In API version 16.0 and later, the Partner Account field is set to the appropriate account
for the partner user that owns the lead. If the owner of the lead isn’t a partner user, this field
has no value.
Phone
Type
phone
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The lead’s phone number.
PhotoUrl
Type
url
Properties
Filter, Group, Nillable, Sort
Description
Path to be combined with the URL of a Salesforce instance (Example:
https://yourInstance.salesforce.com/) to generate a URL to request the social network
profile image associated with the lead. Generated URL returns an HTTP redirect (code 302)
to the social network profile image for the lead.
PostalCode
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Postal code for the address of the lead. Label is Zip/Postal Code.
Pronouns
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The lead’s personal pronouns, reflecting their gender identity. Others can use these pronouns
to refer to the lead in the third person. The entry is selected from a picklist of available values,
which the administrator sets. Maximum 40 characters.
Possible values are:
• He/Him

Design Registration Lead
Field Details
• He/They
• Not Listed
• She/Her
• She/They
• They/Them
Rating
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Rating of the lead.
RecordTypeId
Type
reference
Properties
Create, Filter, Nillable, Update
Description
ID of the record type assigned to this object.
Salutation
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Salutation for the lead.
ScheduledResumeDateTime
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The date and time when the action cadence tracker is going to resume after it’s paused or
on a wait step. This field is available in API version 54.0 and later when the Sales Engagement
license is enabled. To see this field, the user also needs the Sales Engagement User or Sales
Engagement Quick Cadence Creator user permission set.
ScoreIntelligenceId
Type
reference
Properties
Filter, Group, Nillable, Sort

Design Registration Lead
Field Details
Description
The ID of the intelligent field record that contains lead score.
State
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
State for the address of the lead.
StateCode
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ISO state code for the lead’s address.
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Status code for this converted lead. Status codes are defined in Status and represented
in the API by the LeadStatus object.
Street
Type
textarea
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Street number and name for the address of the lead.
Suffix
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The lead’s name suffix. Maximum size is 40 characters.
Title
Type
string

Design Registration Lead
Field Details
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Title for the lead, such as CFO or CEO. The maximum size is 128 characters. When converting
a lead to a person account, the conversion fails if the lead Title field contains more than 80
characters.
Website
Type
url
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Website for the lead.
Note: When importing lead data, users need the Set Audit Fields upon Record Creation permission to assign values to audit fields
such as CreatedDate. Audit fields are automatically updated during API operations unless you set these fields yourself.
Converted Leads
Leads have a special state to indicate that they’ve been converted into an account, a contact, and an opportunity. Your client application
can convert leads via the convertLead() call. Users can also convert leads in Salesforce. After a lead has been converted, it’s read
only. However, you can query converted lead records. Only users with the View and Edit Converted Leads permission can update
converted lead records.
Leads have several fields that indicate their converted status. These special fields are set when converting the lead in the user interface.
• ConvertedAccountId
• ConvertedContactId
• ConvertedDate
• ConvertedOpportunityId
• IsConverted
• Status
Unread Leads
Leads have a special state to indicate that they haven’t been viewed or edited by the lead owner. In Salesforce, it’s helpful for users to
know which leads have been assigned to them but that they haven’t touched yet. IsUnreadByOwner is true if the lead owner
hasn’t yet viewed or edited the lead, and false if the lead owner has viewed or edited the lead at least one time.
Lead Status Picklist
Each Status value corresponds to either a converted or unconverted status in the lead status picklist, as defined in the user interface.
To obtain the lead status values in the picklist, a client application can query LeadStatus.

Design Registration Lead
You can't convert a lead via the API by changing Status to one of the converted lead status values. When you convert qualified leads
into an account, contact, and opportunity, you can select one of the converted status types for the lead. Leads with a converted status
type are no longer available in the Leads tab, although you can include them in reports.
Usage
If lead data is imported and you need to set the value for an audit field, such as CreatedDate, contact Salesforce Support. Audit
fields are automatically updated during API operations unless you request to set these fields yourself.
To update a lead or to convert one with convertLead(), log in to your client application with the Edit permission on leads.
When you create, update, or upsert a lead, your client application can have the lead assigned to multiple user records based on assignment
rules that have been configured in Salesforce.
To use this feature, your client application needs to set either of these options (but not both) in the AssignmentRuleHeader used in
create or update:
Field Field Type Details
assignmentRuleId reference ID of the assignment rule to use. Can be an inactive assignment rule. If unspecified
and useDefaultRule is true, then the default assignment rule is used.
To find the ID for a given assignment rule, query the AssignmentRule object
(specifying RuleType="leadAssignment"), iterate through the returned
AssignmentRule records, find the one you want to use, retrieve its ID, and then
specify its ID in this field in the AssignmentRuleHeader.
useDefaultRule boolean Specifies whether to use the default rule for rule-based assignment (true) or
not (false). Default rules are assigned in the user interface.
Java Sample
The following Java sample shows how to automatically assign a newly created lead.
package wsc;
import com.sforce.soap.enterprise.Connector;
import com.sforce.soap.enterprise.EnterpriseConnection;
import com.sforce.ws.ConnectionException;
import com.sforce.ws.ConnectorConfig;
import com.sforce.soap.enterprise.sobject.Lead;
import com.sforce.soap.enterprise.QueryResult;
import com.sforce.soap.enterprise.SaveResult;
import com.sforce.soap.enterprise.sobject.SObject;
public class LeadAssignment {
static final String USERNAME = "REPLACE USER NAME";
static final String PASSWORD = "REPLACE PASSWORD";
static EnterpriseConnection connection;
static LeadAssignment _leadAssignment;
// Main

Design Registration Lead
public static void main(String[] args)
{
// Establish connection and login
ConnectorConfig config = new ConnectorConfig();
config.setUsername(USERNAME);
config.setPassword(PASSWORD);
try {
connection = Connector.newConnection(config);
System.out.println("Logged in, endpoint: " + config.getAuthEndpoint());
} catch (ConnectionException e1) {
e1.printStackTrace();
}
// Create lead
_leadAssignment = new LeadAssignment();
try {
_leadAssignment.CreateLead();
} catch (Exception e) {
e.printStackTrace();
}
// Logout
try {
connection.logout();
System.out.println("Logged out");
} catch (ConnectionException ce) {
ce.printStackTrace();
}
}
public void CreateLead() throws ConnectionException
{
// Create a new Lead and assign various properties
Lead lead = new Lead();
lead.setFirstName("Joe");
lead.setLastName("Smith");
lead.setCompany("ABC Corporation");
lead.setLeadSource("API");
// The lead assignment rule will assign any new leads that
// have "API" as the LeadSource to a particular user
// In this sample we will look for a particular rule and if found
// use the id for the lead assignment. If it is not found we will
// instruct the call to use the current default rule. You can't use
// both of these values together.
QueryResult qr = connection.query("SELECT Id FROM AssignmentRule WHERE Name = " +
"'Mass Mail Campaign' AND SobjectType = 'Lead'");
if (qr.getSize() == 0) {
connection.setAssignmentRuleHeader(null, true);
} else {
connection.setAssignmentRuleHeader(qr.getRecords()[0].getId(), false);
}

Design Registration Lead
// Every operation that results in a new or updated lead will
// use the specified rule until the header is removed from the
// connection.
SaveResult[] sr = connection.create(new SObject[] {lead});
for (int i=0;i<sr.length;i++) {
if (sr[i].isSuccess()) {
System.out.println("Successfully created lead with id of: " +
sr[i].getId() + ".");
} else {
System.out.println("Error creating lead: " +
sr[i].getErrors()[0].getMessage());
}
}
// This call effectively removes the header, the next lead will
// be assigned to the default lead owner.
connection.clearAssignmentRuleHeader();
}
}
C# Sample
The following C# sample shows how to automatically assign a newly created lead.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.ServiceModel;
using LeadSample.sforce;
namespace LeadSample
{
class LeadAssignment
{
private static SoapClient client;
private static SoapClient apiClient;
private static SessionHeader header;
private static LoginResult loginResult;
private static readonly string Username = "REPLACE USERNAME";
private static readonly string Password = "REPLACE PASSWORD AND SECURITY TOKEN";
// Create the proxy binding and login
private LeadAssignment()
{
client = new SoapClient();
try
{
loginResult = client.login(null, Username, Password);
}
catch (Exception e)

Design Registration Lead
{
Console.WriteLine("Unexpected login error: " + e.Message);
Console.WriteLine(e.StackTrace);
return;
}
// Access API endpoint and create new client
header = new SessionHeader();
header.sessionId = loginResult.sessionId;
apiClient = new SoapClient("Soap", loginResult.serverUrl);
}
[STAThread]
static void Main(string[] args)
{
LeadAssignment leadAssignment = new LeadAssignment();
try
{
leadAssignment.CreateLead();
}
catch (Exception e)
{
Console.WriteLine(e.Message);
Console.WriteLine(e.StackTrace);
Console.WriteLine(e.InnerException);
}
// logout
client.logout(header);
}
public void CreateLead()
{
// Create a new Lead and assign various properties
Lead lead = new Lead();
lead.FirstName = "John";
lead.LastName = "Brown";
lead.Company = "ABC Corporation";
lead.LeadSource = "Advertisement";
// Setting the lead source for a pre-existing lead assignment rule. This
// rule was created outside of this sample and will assign any new leads
// that have "Advertisement" as the LeadSource to a particular user.
// Create the assignment rule header and add it to the proxy binding
AssignmentRuleHeader arh = new AssignmentRuleHeader();
// In this sample we will look for a particular rule and if found
// use the id for the lead assignment. If it is not found we will
// instruct the call to use the current default rule. Both these
// values can't be used together.
QueryResult qr = null;
string query = "SELECT Id FROM AssignmentRule WHERE Name = " +
"'Mass Mail Campaign' AND SobjectType = 'Lead'";
try
{

Design Registration Lead
LimitInfo[] limitArray = apiClient.query(
header, // sessionheader
null, // queryoptions
null, // mruheader
null, // packageversionheader
query, // SOQL query
out qr);
}
catch (Exception e)
{
Console.WriteLine("Unexpected query error: " + e.Message);
Console.WriteLine(e.StackTrace);
}
if (qr.size == 0)
{
arh.useDefaultRule = true;
}
else
{
arh.assignmentRuleId = qr.records[0].Id;
}
// Create the lead using our Assignment Rule header
LimitInfo[] li;
SaveResult[] sr;
apiClient.create(
header, // sessionheader
arh, // assignmentruleheader
null, // mruheader
null, // allowfieldtrunctionheader
null, // disablefeedtrackingheader
null, // streamingenabledheader
null, // allornoneheader
null, // duplicateruleheader
null, // localeoptions
null, // debuggingheader
null, // packageversionheader
null, // emailheader
new sObject[] { lead },
out li,
out sr);
foreach (SaveResult s in sr)
{
if (s.success)
{
Console.WriteLine("Successfully created Lead with ID: {0}", s.id);
}
else
{
Console.WriteLine("Error creating Lead: {0}", s.errors[0].message);
}
}
}

Design Registration Opportunity
}
}
Associated Objects
This object has these associated objects. If the API version isn’t specified, they’re available in the same API versions as this object. Otherwise,
they’re available in the specified API version and later.
LeadChangeEvent (API version 44.0)
Change events are available for the object.
LeadFeed (API version 18.0)
Feed tracking is available for the object.
LeadHistory
History is available for tracked fields of the object.
LeadOwnerSharingRule
Sharing rules are available for the object.
LeadShare
Sharing is available for the object.
Opportunity
Represents an opportunity, which is a sale or pending deal.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Field Type
AccountId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
ID of the account associated with this opportunity.
This is a relationship field.
Relationship Name
Account
Relationship Type
Lookup
Refers To
Account

Design Registration Opportunity
Field Field Type
ActivityMetricId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
When Einstein Activity Capture with Activity Metrics is enabled, the ID of the related activity
metric.
This field is a relationship field.
Relationship Name
ActivityMetric
Refers To
ActivityMetric
ActivityMetricRollupId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
When Einstein Activity Capture with Activity Metrics is enabled, the ID of the related activity
metric rollup.
This field is a relationship field.
Relationship Name
ActivityMetricRollup
Refers To
ActivityMetricRollup
AgeInDays
Type
int
Properties
Aggregate, Filter, Group, Nillable, Sort
Description
The number of days since the opportunity was created, calculated by the current date minus
the created_date field. This field is available in API version 52.0 and later if you enabled
Pipeline Inspection.
Amount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update

Design Registration Opportunity
Field Field Type
Description
Estimated total sale amount. For opportunities with products, the amount is the sum of the
related products. Any attempt to update this field, if the record has products, will be ignored.
The update call will not be rejected, and other fields will be updated as specified, but the
Amount will be unchanged.
CampaignId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
ID of a related Campaign. This field is defined only for those organizations that have the
campaign feature Campaigns enabled. The User must have read access rights to the
cross-referenced Campaign object in order to create or update that campaign into this field
on the opportunity.
This is a relationship field.
Relationship Name
Campaign
Relationship Type
Lookup
Refers To
Campaign
CloseDate
Type
date
Properties
Create, Filter, Group, Sort, Update
Description
Required. Date when the opportunity is expected to close.
ConnectionReceivedId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
ID of the PartnerNetworkConnection that shared this record with your organization. This
field is available if you enabled Salesforce to Salesforce.
ConnectionSentId
Type
reference
Properties
Filter, Group, Nillable, Sort

Design Registration Opportunity
Field Field Type
Description
ID of the PartnerNetworkConnection that you shared this record with. This field is available
if you enabled Salesforce to Salesforce. This field is supported using API versions earlier than
15.0. In all other API versions, this field’s value is null. You can use the new
PartnerNetworkRecordConnection object to forward records to connections.
ContactId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort
Description
ID of the contact associated with this opportunity, set as the primary contact. Read-only field
that is derived from the opportunity contact role, which is created at the same time the
opportunity is created. This field can only be populated when it’s created, and can’t be
updated. To update the value in this field, change the IsPrimary flag on the
OpportunityContactRole associated with this opportunity. Available in API version 46.0 and
later.
ContractId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
ID of the contract that’s associated with this opportunity.
This is a relationship field.
Relationship Name
Contract
Relationship Type
Lookup
Refers To
Contract
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Available only for organizations with the multicurrency feature enabled. Contains the ISO
code for any currency allowed by the organization.
If the organization has multicurrency and a Pricebook2 is specified on the opportunity (that
is, the Pricebook2Id field is not blank), then the currency value of this field must match

Design Registration Opportunity
Field Field Type
the currency of the PricebookEntry records that are associated with any opportunity line
items it has.
Description
Type
textarea
Properties
Create, Nillable, Update
Description
Text description of the opportunity. Limit: 32,000 characters.
ExpectedRevenue
Type
currency
Properties
Filter, Nillable, Sort
Description
Read-only field that is equal to the product of the opportunity Amount field and the
Probability. You can’t directly set this field, but you can indirectly set it by setting the
Amount or Probability fields.
ExportStatus
Type
picklist
Properties
Filter, Restricted picklist, Sort
Description
Derived field for the record map for Partner Connect. The export status of this opportunity
to the partner’s connected org. To see this field, enable Partner Connect and add the Export
Vendor Records to an Authorized Partner Org user permission to the cosell export user. See
Set Up Partner Connect as a Vendor in Salesforce Help. Available in API version 62.0 and later.
Fiscal
Type
string
Properties
Filter, Group, Nillable, Sort
Description
If fiscal years are not enabled, the name of the fiscal quarter or period in which the opportunity
CloseDate falls. Use YYYY Q format, for example, '2006 1' for first quarter of 2006.
FiscalQuarter
Type
int
Properties
Filter, Group, Nillable, Sort

Design Registration Opportunity
Field Field Type
Description
Represents the fiscal quarter. Valid values are 1, 2, 3, or 4.
FiscalYear
Type
int
Properties
Filter, Group, Nillable, Sort
Description
Represents the fiscal year, for example, 2006.
ForecastCategory
Type
picklist
Properties
Filter, Group, Restricted picklist, Sort
Description
Restricted picklist field. It is implied, but not directly controlled, by the StageName field.
You can override this field to a different value than is implied by the StageName value.
The values of this field are fixed enumerated values. The field labels are localized to the
language of the user performing the operation, if localized versions of those labels are
available for that language in the user interface.
In API version 12.0 and later, the value of this field is automatically set based on the value of
the ForecastCategoryName and can’t be updated any other way. The field properties
Create, Defaulted on create, Nillable, and Update are not available in version 12.0.
Possible values are:
• BestCase
• Closed
• Forecast
• MostLikely
• Omitted
• Pipeline
ForecastCategoryName
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The name of the forecast category. It is implied, but not directly controlled, by the
StageName field. You can override this field to a different value than is implied by the
StageName value. Available in API version 12.0 and later.
Possible values are:
• Best Case

Design Registration Opportunity
Field Field Type
• Closed
• Commit
• Most Likely
• Omitted
• Pipeline
HasOpenActivity
Type
boolean
Properties
Defaulted on create, Group,
Description
Indicates whether an opportunity has an open event or task (true) or not (false). Available
in API version 35.0 and later.
HasOpportunityLineItem
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Read-only field that indicates whether the opportunity has associated line items. A value of
true means that Opportunity line items have been created for the opportunity. An
opportunity can have opportunity line items only if the opportunity has a price book. The
opportunity line items must correspond to PricebookEntry objects that are listed in the
opportunity Pricebook2. However, you can insert opportunity line items on an opportunity
that does not have an associated Pricebook2. For the first opportunity line item that you
insert on an opportunity without a Pricebook2, the API automatically sets the
Pricebook2Id field, if the opportunity line item corresponds to a PricebookEntry in an
active Pricebook2 that has a CurrencyIsoCode field that matches the
CurrencyIsoCode field of the opportunity. If the Pricebook2 is not active or the
CurrencyIsoCode fields do not match, then the API returns an error. You can’t update
the Pricebook2Id or PricebookId fields if opportunity line items exist on the
Opportunity. You must delete the line items before attempting to update the
PricebookId field.
HasOverdueTask
Type
boolean
Properties
Defaulted on create, Group,
Description
Indicates whether an opportunity has an overdue task (true) or not (false). Available in
API version 35.0 and later.

Design Registration Opportunity
Field Field Type
IqScore
Type
int
Properties
Aggregate, Filter, Group, Nillable, Sort
Description
The likelihood, measured on a scale of 1 to 99, that an opportunity will be won. Einstein
Opportunity Scoring must be enabled. Available in API version 41.0 and later. Label is
Opportunity Score.
IsClosed
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Directly controlled by StageName. You can query and filter on this field, but you can’t
directly set it in a create, upsert, or update request. It can only be set via StageName. Label
is Closed.
IsDeleted
Type
boolean
Properties
Defaulted on create, Filter
Description
Indicates whether the object has been moved to the Recycle Bin (true) or not (false).
Label is Deleted.
IsExcludedFromTerritory2Filter
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Used for Filter-Based Opportunity Territory Assignment (Pilot in Spring ’15 / API version 33).
Indicates whether the opportunity is excluded (True) or included (False) each time the
APEX filter is executed.
IsPriorityRecord
Type
boolean
Properties
Defaulted on create, Group
Description
Shows whether the user has marked the opportunity as important (True) or not (False).
The default value is false. Available in API version 53.0 and later.

Design Registration Opportunity
Field Field Type
IsPrivate
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
If true, only the opportunity owner, users above that role in the hierarchy, and admins can
view the opportunity or query it via the API. When you mark opportunities as private,
opportunity teams, opportunity splits, and sharing are removed. Label is Private. The default
value is False.
IsSplit
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Read-only field that indicates whether credit for the opportunity is split between opportunity
team members. Label is IsSplit. This field is available in versions 14.0 and later for
organizations that enabled Opportunity Splits during the pilot period.
This field should not be used. However, it’s documented for the benefit of pilot customers
who find references to IsSplit in code.
IsWon
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Directly controlled by StageName. You can query and filter on this field, but you can’t
directly set the value. It can only be set via StageName. Label is Won.
LastActivityDate
Type
date
Properties
Filter, Group, Nillable, Sort
Description
Value is one of the following, whichever is the most recent:
• Due date of the most recent event logged against the record.
• Due date of the most recently closed task associated with the record.
LastActivityInDays
Type
int
Properties
Aggregate, Filter, Group, Nillable, Sort

Design Registration Opportunity
Field Field Type
Description
The number of days since the last completed event or task for the record, calculated by the
current date minus the last_activity field. If the last_activity field is null,
this field is null. This field is available in API version 52.0 and later if you enabled Pipeline
Inspection.
LastAmountChangedHistoryId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
ID of the OpportunityHistory record that contains information about when the opportunity
Amount field was last updated in Winter ’21 or later. Information includes the date and time
of the change and the user who made the change. Available in API version 50.0 and later.
This is a relationship field.
Relationship Name
LastAmountChangedHistory
Relationship Type
Lookup
Refers To
OpportunityHistory
LastCloseDateChangedHistoryId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
ID of the OpportunityHistory record that contains information about when the opportunity
Close Date field was last updated in Winter ’21 or later. Information includes the date and
time of the change and the user who made the change. Available in API version 50.0 and
later.
This is a relationship field.
Relationship Name
LastCloseDateChangedHistory
Relationship Type
Lookup
Refers To
OpportunityHistory
LastReferencedDate
Type
datetime

Design Registration Opportunity
Field Field Type
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
LastStageChangeDate
Type
datetime
Properties
Aggregate, Filter, Nillable, Sort
Description
The date of the last change made to the Stage field on this opportunity record. This field
is available in API version 52.0 and later.
LastStageChangeInDays
Type
int
Properties
Aggregate, Filter, Group, Nillable, Sort
Description
The number of days since the last change was made to the Stage field on the opportunity
record, calculated by the current date minus the last_stage_change_date field. If
the last_stage_change_date is null, then this field contains the value for
AgeInDays. This field is available in API version 52.0 and later if you enabled Pipeline
Inspection.
LastViewedDate
Type
datetime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last viewed this record or list view. If this value is null,
the user might have only accessed this record or list view (LastReferencedDate) but
not viewed it.
LeadSource
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Source of this opportunity, such as Advertisement or Trade Show.

Design Registration Opportunity
Field Field Type
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Required. A name for this opportunity. Limit: 120 characters.
NextStep
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Description of next task in closing opportunity. Limit: 255 characters.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
ID of the User who has been assigned to work this opportunity.
If you update this field, the previous owner's access becomes Read Only or the access specified
in your organization-wide default for opportunities, whichever is greater.
If you have set up opportunity teams in your organization, updating this field has different
consequences depending on your version of the API:
• For API version 12.0 and later, sharing records are kept, as they are for all objects. (All
previous opportunity team members are kept on the opportunity team.)
• For API version before 12.0, sharing records are deleted. (All previous opportunity team
members are removed from the opportunity team.)
• For API version 16.0 and later, users must have the Transfer Record permission in order
to update (transfer) account ownership using this field.
This is a relationship field.
Relationship Name
Owner
Relationship Type
Lookup
Refers To
User
PartnerAccountId
Type
reference

Design Registration Opportunity
Field Field Type
Properties
Filter, Group, Nillable, Sort
Description
ID of the partner account for the partner user that owns this opportunity. Available if Partner
Relationship Management is enabled or if digital experiences is enabled and you have partner
portal licenses.
If you are uploading opportunities using API version 15.0 or earlier, and one of the
opportunities in the batch has a partner user as the owner, the Partner Account field
on all opportunities in the batch is set to that partner user’s account regardless of whether
the partner user is the owner. In version 16.0, the Partner Account field is set to the
appropriate account for the partner user that owns the opportunity. If the owner of the
opportunity is not a partner user, this field remains empty.
Pricebook2Id
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
Description
ID of a related Pricebook2 object. The Pricebook2Id field indicates which Pricebook2
applies to this opportunity. The Pricebook2Id field is defined only for those organizations
that have products enabled as a feature. You can specify values for only one field
(Pricebook2Id or PricebookId)—not both fields. For this reason, both fields are
declared nillable.
This is a relationship field.
Relationship Name
Pricebook2
Relationship Type
Lookup
Refers To
Pricebook2
PricebookId
Type
reference
Properties
Create, Defaulted on create, Filter, Nillable, Update
Description
Unavailable as of version 3.0. As of version 8.0, the Pricebook object is no longer available.
Use the Pricebook2Id field instead, specifying the ID of the Pricebook2 record.
Probability
Type
percent

Design Registration Opportunity
Field Field Type
Properties
Create, Defaulted on create, Filter, Nillable, Sort, Update
Description
Percentage of estimated confidence in closing the opportunity. It is implied, but not directly
controlled, by the StageName field. You can override this field to a different value than
what is implied by the StageName.
If you're changing the Probability field through the API using a partner WSDL call, or
an Apex before trigger, and the value may have several decimal places, we recommend
rounding the value to a whole number. For example, the following Apex in a before
trigger uses the round method to change the field value: o.probability =
o.probability.round();
PushCount
Type
int
Properties
Filter, Group, Nillable, Sort
Description
The number of times an opportunity’s close date has been pushed out by one calendar
month. For example, moving a close date from April to May counts as one push, but moving
from April 1 to April 30 doesn't count. The total is not decreased when the close date is
moved in. Available in API version 53.0 and later.
RecordTypeId
Type
reference
Properties
Create, Filter, Nillable, Update
Description
ID of the record type assigned to this object.
StageName
Type
picklist
Properties
Create, Filter, Group, Sort, Update
Description
Required. Current stage of this record. The StageName field controls several other fields
on an opportunity. Each of the fields can be directly set or implied by changing the
StageName field. In addition, the StageName field is a picklist, so it has additional
members in the returned describeSObjectResult to indicate how it affects the other fields.
To obtain the stage name values in the picklist, query the OpportunityStage object. If the
StageName is updated, then the ForecastCategoryName, IsClosed, IsWon,
and Probability are automatically updated based on the stage-category mapping.

Design Registration Opportunity
Field Field Type
SyncedQuoteID
Type
reference
Properties
Create, Filter, Nillable, Update
Description
Read only in an Apex trigger. The ID of the Quote that syncs with the opportunity. Setting
this field lets you start and stop syncing between the opportunity and a quote. The ID has
to be for a quote that is a child of the opportunity.
Territory2Id
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ID of the territory that is assigned to the opportunity. Available only if Enterprise Territory
Management has been enabled for your organization. Users who have full access to an
opportunity’s account can assign any territory from the active model to the opportunity.
Users who do not can assign only a territory that is also assigned to the opportunity’s account.
The same restriction applies to territory assignments made via Apex in system mode.
TotalOpportunityQuantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Number of items included in this opportunity. Used in quantity-based forecasting.
Type
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Type of opportunity. For example, Existing Business or New Business. Label is Opportunity
Type.
Note: When importing opportunity data, users need the Set Audit Fields upon Record Creation permission to assign values to
audit fields such as CreatedDate. Audit fields are automatically updated during API operations unless you set these fields
yourself.

Design Registration Opportunity
Usage
Use the Opportunity object to manage information about a sale or pending deal. You can also sync this object with a child Quote. To
update an Opportunity, your client application needs Edit permission on opportunities. You can create, update, delete, and query
Attachment records associated with an opportunity via the API. To split credit for an opportunity among multiple opportunity team
members, use the OpportunitySplit object.
Client applications can also create or update opportunity objects by converting a Lead with convertLead().
Note: On opportunities and opportunity products, the workflow rules, validation rules, and Apex triggers fire when an update to
a child opportunity product or schedule causes an update to the parent record. This means your custom application logic is
enforced when there are updates to the parent record, ensuring higher data quality and compliance with your organization’s
business policies.
Sample Code—Java
This code starts the sync between an object and a child quote.
public void startQuoteSync() {
Opportunity opp = new Opportunity();
opp.setId(new ID("006D000000CpOSy"));
opp.setSyncedQuoteId(new ID("0Q0D000000002OZ"));
// Invoke the update call and save the results
try {
SaveResult[] saveResults = binding.update(new SObject[] {opp});
// check results and do more processing after the update call ...
}
catch (Exception ex) {
System.out.println("An unexpected error has occurred." + ex.getMessage());
return;
}
}
This code stops the sync between an object and a child quote.
public void stopQuoteSync() {
Opportunity opp = new Opportunity();
opp.setId(new ID("006D000000CpOSy"));
opp.setFieldsToNull(new String[] {"SyncedQuoteId"} );
// Invoke the update call and save the results
try {
SaveResult[] saveResults = binding.update(new SObject[] {opp});
// check results and do more processing after the update call ...
}
catch (Exception ex) {
System.out.println("An unexpected error has occurred." + ex.getMessage());
return;
}
}
Associated Objects
This object has these associated objects. Unless noted, they are available in the same API version as this object.

Design Registration OpportunityLineItem
OpportunityChangeEvent (API version 44.0)
Change events are available for the object.
OpportunityFeed (API version 18.0)
Feed tracking is available for the object.
OpportunityHistory
History is available for tracked fields of the object.
OpportunityOwnerSharingRule
Sharing rules are available for the object.
OpportunityShare
Sharing is available for the object.
Additional Considerations
If you are using before triggers to set Stage and Forecast Category for an opportunity record, the behavior is as follows:
• If you set Stage and Forecast Category, the opportunity record contains those exact values.
• If you set Stage but not Forecast Category, the Forecast Category value on the opportunity record defaults to
the one associated with trigger Stage.
• If you reset Stage to a value specified in an API call or incoming from the user interface, the Forecast Category value
should also come from the API call or user interface. If no value for Forecast Category is specified and the incoming Stage
is different than the trigger Stage, the Forecast Category defaults to the one associated with trigger Stage. If the trigger
Stage and incoming Stage are the same, the Forecast Category is not defaulted.
If you are cloning an opportunity with products, the following events occur in order:
Note: If errors occur on an opportunity product, you must return to the opportunity and fix the errors before cloning.
If any opportunity products contain unique custom fields, you must null them out before cloning the opportunity.
• The parent opportunity is saved according to the order of execution.
• The opportunity products are saved according to the order of execution.
OpportunityLineItem
Represents an opportunity line item, which is a member of the list of Product2 products associated with an Opportunity.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), update(), upsert()
Special Access Rules
The user must have the “Edit” permission on Opportunity records to create or update opportunity line items on an opportunity.

Design Registration OpportunityLineItem
Fields
Field Details
CanUseQuantitySchedule
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates whether the opportunity product can have a quantity schedule (true) or not
(false). This field is read-only.
CanUseRevenueSchedule
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates whether the opportunity product can have a revenue schedule (true) or not
(false). This field is read-only.
ConnectionReceivedId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
ID of the PartnerNetworkConnection that shared this record with your organization. This
field is available if you enabled Salesforce to Salesforce.
ConnectionSentId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
ID of the PartnerNetworkConnection that you shared this record with. This field is available
if you enabled Salesforce to Salesforce. This field is supported using API versions earlier than
15.0. In all other API versions, this field’s value is null. You can use the new
PartnerNetworkRecordConnection object to forward records to connections.
CurrencyIsoCode
Type
picklist
Properties
Defaulted on create, Filter, Group, Restricted picklist, Sort

Design Registration OpportunityLineItem
Field Details
Description
Available only for organizations with the multicurrency feature enabled. Contains the ISO
code for any currency allowed by the organization.
If the organization has multicurrency enabled, and a Pricebook2 isn’tspecified on the parent
opportunity (that is, the Pricebook2Id field is blank on the opportunity referenced by
this object’s OpportunityId), then the value of this field must match the currency of
the CurrencyIsoCode field on the PricebookEntry records that are associated with this
object.
Description
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Text description of the opportunity line item. Limit: 255 characters.
Discount
Type
percent
Properties
Create, Filter, Nillable, Sort, Update
Description
Discount for the product as a percentage.
When updating these records:
• If you specify Discount without specifying TotalPrice, the TotalPrice is
adjusted to accommodate the new Discount value, and the UnitPrice is held
constant.
• If you specify both Discount and Quantity, you must also specify either
TotalPrice or UnitPrice so the system knows which one to automatically
adjust.
HasQuantitySchedule
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Read-only. Indicates whether a quantity schedule has been created for this object (true)
or not (false).
HasRevenueSchedule
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort

Design Registration OpportunityLineItem
Field Details
Description
Indicates whether a revenue schedule has been created for this object (true) or not
(false).
If this object has a revenue schedule, the Quantity and TotalPrice fields can’t be
updated. In addition, the Quantity field can’t be updated if this object has a quantity
schedule. Update requests aren’t rejected but the updated values are ignored.
HasSchedule
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
If either HasQuantitySchedule or HasRevenueSchedule is true, this field is
also true.
LastReferencedDate
Type
datetime
Properties
Filter, Nillable, Sort
Description
The timestamp for when the current user last viewed a record related to this record. Available
in API version 50.0 and later.
LastViewedDate
Type
datetime
Properties
Filter, Nillable, Sort
Description
The timestamp for when the current user last viewed this record. If this value is null, this
record might only have been referenced (LastReferencedDate) and not viewed. Available in
API version 50.0 and later.
ListPrice
Type
currency
Properties
Filter, Nillable, Sort
Description
Corresponds to the UnitPrice on the PricebookEntry that is associated with this line
item, which can be in the standard price book or a custom price book. A client application
can use this information to show whether the unit price (or sales price) of the line item differs
from the price book entry list price.

Design Registration OpportunityLineItem
Field Details
Name
Type
string
Properties
Filter, Nillable, Sort
Description
The opportunity line item name (known as “Opportunity Product” in the user interface). This
read-only field is available in API version 30.0 and later.
OpportunityId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Required. ID of the associated Opportunity.
This is a relationship field.
Relationship Name
Opportunity
Relationship Type
Lookup
Refers To
Opportunity
PricebookEntryId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort
Description
Required. ID of the associated PricebookEntry. Exists only for those organizations that have
Products enabled as a feature. In API versions 1.0 and 2.0, you can specify values for either
this field or ProductId, but not both. For this reason, both fields are declared nillable. In
API version 3.0 and later, you must specify values for this field instead of ProductId.
This is a relationship field.
Relationship Name
PricebookEntry
Relationship Type
Lookup
Refers To
PricebookEntry
ProductId
Type
reference

Design Registration OpportunityLineItem
Field Details
Properties
Create, Filter, Nillable
Description
ID of the related Product record. This field is unavailable as of version 3.0 and is only provided
for backward compatibility. The Product object is unavailable beginning with version 8.0.
Use the PricebookEntryId field instead, specifying the ID of the PricebookEntry record.
This is a relationship field.
Relationship Name
Product2
Relationship Type
Lookup
Refers To
Product2
Product2Id
Type
reference
Properties
Create, Filter, Group, Nillable, Sort
Description
The ID of the related Product2 record. This is a read-only field available in API version 30.0
and later.
Use the PricebookEntryId field instead, specifying the ID of the PricebookEntry record.
ProductCode
Type
string
Properties
Filter, Group, Nillable, Sort
Description
This read-only field is available in API version 30.0 and later. It references the value in the
ProductCode field of the related Product2 record.
Quantity
Type
double
Properties
Create, Filter, Sort, Update
Description
Read-only if this record has a quantity schedule, a revenue schedule, or both a quantity and
a revenue schedule.
When updating these records:

Design Registration OpportunityLineItem
Field Details
• If you specify Quantity without specifying the UnitPrice, the UnitPrice
value is adjusted to accommodate the new Quantity value, and the TotalPrice
is held constant.
• If you specify both Discount and Quantity, you must also specify either TotalPrice
or UnitPrice so the system can determine which one to automatically adjust.
RecalculateTotalPrice
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Changes behavior of OpportunityLineItem calculations when a line item has child schedule
rows for the Quantity value. When enabled, if the rollup quantity changes, then the
quantity rollup value is multiplied against the sales price to change the total price. Product2
flag must be set to true.
ServiceDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Date when the product revenue will be recognized and the product quantity will be shipped.
• Opportunity Close Date—ServiceDate is ignored.
• Product Date—ServiceDate is used if not null.
• Schedule Date—ServiceDate is used if not null and there are no revenue
schedules present for this line item, that is, there are no OpportunityLineItemSchedule
records with a field Type value of Revenue that are children of this record.
SortOrder
Type
int
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Number indicating the sort order selected by the user. Client applications can use this to
match the sort order in Salesforce.
Subtotal
Type
currency
Properties
Filter, Nillable, Sort

Design Registration OpportunityLineItem
Field Details
Description
Difference between standard and discounted pricing. Converted currency amounts when
the opportunity's currency is different from the user's currency.
TotalPrice
Type
currency
Properties
Create, Defaulted on create, Filter, Nillable, Sort, Update
Description
This field is available only for backward compatibility. It represents the total price of the
OpportunityLineItem.
If you don’t specify UnitPrice, this field is required. If you specify Discount and
Quantity, this field or UnitPrice is required. When updating these records, you can
change either this value or the UnitPrice, but not both at the same time.
This field is nillable, but you can’t set both TotalPrice and UnitPrice to null in the
same update request. To insert the TotalPrice via the API (given only a unit price and
the quantity), calculate this field as the unit price multiplied by the quantity. This field is
read-only if the opportunity line item has a revenue schedule. If the opportunity line item
doesn’t have a schedule or only has a quantity schedule, this field can be updated.
UnitPrice
Type
currency
Properties
Create, Defaulted on create, Filter, Nillable, Sort, Update
Description
The unit price for the opportunity line item. In the Salesforce user interface, this field’s value
is calculated by dividing the total price of the opportunity line item by the quantity listed for
that line item. Label is Sales Price.
This field or TotalPrice is required. You can’t specify both.
If you specify Discount and Quantity, this field or TotalPrice is required.
Usage
An Opportunity can have associated OpportunityLineItem records only if the Opportunity has a Pricebook2. An OpportunityLineItem
must correspond to a Product2 that is listed in the opportunity's Pricebook2. For information about inserting OpportunityLineItem for
an opportunity that doesn’t have an associated Pricebook2 or any existing line items, see Effects on Opportunities.
This object is defined only for orgs with products enabled as a feature. If the products feature isn’t enabled, this object doesn’t appear
in the describeGlobal() call, and you can’t use describeSObjects() or query the OpportunityLineItem object.
For a visual diagram of the relationships between OpportunityLineItem and other objects, see the Product & Price Book diagram.

Design Registration Pricebook2
Note:
• If the multicurrency option is enabled, the CurrencyIsoCode field is present. It can’t be modified, and is always set to
the value of the CurrencyIsoCode of the parent Opportunity.
• If customizable product schedules are enabled, you can use custom fields in default schedules and customize their layout. But
if you’ve applied validation rules or Apex triggers, they’re bypassed when they’re first inserted.
Effects on Opportunities
Opportunities with associated OpportunityLineItem records are affected in the following ways:
• Creating an OpportunityLineItem increments the Opportunity Amount value by the TotalPrice of the OpportunityLineItem.
Additionally, inserting an OpportunityLineItem increments the ExpectedRevenue on the opportunity by the TotalPrice
times the opportunity Probability.
• The Opportunity Amount becomes a read-only field when the opportunity has line items. The API ignores any attempt to update
this field on an opportunity with line items. Update requests aren’t rejected, but the updated value is ignored.
• You can’t update the PricebookId field or the CurrencyIsoCode field on the opportunity if line items exist. The API rejects
any attempt to update these fields on an opportunity with line items.
• When you create or update an OpportunityLineItem, the API verifies that the line item corresponds to a PricebookEntry in the
Pricebook2 associated with the opportunity.
– If the opportunity has an associated active or inactive Pricebook2, the OpportunityLineItem is created or updated.
– If the opportunity doesn’t have an associated Pricebook2, but the OpportunityLineItem corresponds to a PricebookEntry in an
active Pricebook2 where the PricebookEntry has a CurrencyIsoCode value that matches the CurrencyIsoCode
value of the opportunity, the API automatically sets this PriceBook2 on the opportunity.
– If the opportunity doesn’t have an associated Pricebook2, but the line item corresponds to a PricebookEntry in a Pricebook2 that
isn’t active or that has a CurrencyIsoCode value that does not match the CurrencyIsoCode value of the opportunity,
an error is returned.
• The Opportunity HasOpportunityLineItem field is set to true when an OpportunityLineItem is inserted for that Opportunity.
• When OpportunityLineItem records are directly deleted, they aren’t sent to the recycle bin and can’t be undeleted. The
getDeleted() call shows deleted OpportunityLineItem records until they’re purged, which is usually within the same day or
the next day.
• In Lightning, the ListPrice, Name, and ProductCode fields aren’t populated before insert because their values are computed
after the OpportunityLineItem.Product2Id value is saved. To access a value from these fields, use an After Insert trigger.
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
OpportunityLineItemChangeEvent (API version 60.0)
Change events are available for the object.
Pricebook2
Represents a price book that contains the list of products that your org sells.
Note: Price books are represented by Pricebook2 objects. As of API version 8.0, the Pricebook object is no longer available. Requests
containing Pricebook are refused, and responses don’t contain the Pricebook object.

Design Registration Pricebook2
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
Description
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Text description of the price book.
IsActive
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether the price book is active (true) or not (false). Inactive price books are
hidden in many areas in the user interface. You can change this field’s value as often as
necessary. Label is Active.
IsArchived
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates whether the price book has been archived (true) or not (false). This field is read
only.
IsDeleted
Type
boolean
Properties
Defaulted on create, Filter
Description
Indicates whether the price book has been moved to the Recycle Bin (true) or not (false).
Label is Deleted.
IsStandard
Type
boolean

Design Registration Pricebook2
Field Details
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates whether the price book is the standard price book for the org (true) or not
(false). Every org has one standard price book—all other price books are custom price
books.
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp for when the current user last viewed a record related to this record.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp for when the current user last viewed this record. If this value is null, it’s
possible that this record was referenced (LastReferencedDate) and not viewed.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Required. Name of this object. This field is read-only for the standard price book. Label is
Price Book Name.
ValidFrom
Type
dateTime
Properties
Create, Filter, Nillable, Sort, Update
Description
The date and time when a Commerce price book is initially valid. If this field is null, the
price book is valid immediately when active. Available in API version 48.0 and later.
ValidTo
Type
dateTime
Properties
Create, Filter, Nillable, Sort, Update

Design Registration Pricebook2
Field Details
Description
The date and time when a Commerce price book is valid to. If this field is null, the price
book is valid until it’s deactivated. Available in API version 48.0 and later.
Usage
A price book is a list of products that your org sells.
• Each org has one standard price book that defines the standard or generic list price for each product or service that it sells.
• An org can have multiple custom price books to use for specialized purposes, such as for discounts, different channels or markets,
or select accounts or opportunities. While your client application can create, delete, and update custom price books, your client
application can only update the standard price book.
• For some orgs, the standard price book is the only price needed. If you set up other price books, you can reference the standard
price book when setting up list prices in custom price books.
Use this object to query standard and custom price books that have been configured for your org. A common use of this object is to
allow your client application to obtain valid Pricebook2 object IDs for use when configuring PricebookEntry records via the API.
Your client application can perform the following tasks on PricebookEntry objects:
• Query
• Create for the standard price book or custom price books.
• Update
• Delete
• Change the IsActive field when creating or updating records
PriceBook2, Product2, and PricebookEntry Relationships
In the API:
• Price books are represented by Pricebook2 records (as of version 8.0, the Pricebook object is no longer available).
• Products are represented by Product2 records (as of version 8.0, the Product object is no longer available).
• Each price book contains zero or more entries (represented by PricebookEntry records) that specify the products that are associated
with the price book. A price book entry defines the price for which you sell a product at a particular currency.
These objects are defined only for those orgs that have products enabled as a feature. If the org doesn’t have the products feature
enabled, the Pricebook2 object doesn’t appear in the describeGlobal() call, and you can’t access it via the API.
If you delete a Pricebook2 while a line item references PricebookEntry in the price book, the line item is unaffected, but the Pricebook2
is archived and unavailable from the API.
For a visual diagram of the relationships between Pricebook2 and other objects, see Product and Schedule Objects.
Price Book Setup
The process of setting up a price book via the API usually means:
1. Load product data into Product2 records (creating one Product2 record for each product that you want to add).

Design Registration Pricebook2
2. For each Product2 record, create a PricebookEntry that links the Product2 record to the standard Pricebook2. Define a standard price
for a product at a given currency (if you have multicurrency enabled) before defining a price for that product in the same currency
in a custom price book.
3. Create a Pricebook2 record to represent a custom price book.
4. For each Pricebook2 record, creating a PricebookEntry for every Product2 that you want to add, specifying unique properties for
each PricebookEntry (such as the UnitPrice and CurrencyIsoCode) as needed.
Code Sample—Java
public void pricebookSample() {
try {
//Create a custom pricebook
Pricebook2 pb = new Pricebook2();
pb.setName("Custom Pricebok");
pb.setIsActive(true);
SaveResult[] saveResults = connection.create(new SObject[]{pb});
pb.setId(saveResults[0].getId());
// Create a new product
Product2 product = new Product2();
product.setIsActive(true);
product.setName("Product");
saveResults = connection.create(new SObject[]{product});
product.setId(saveResults[0].getId());
// Add product to standard pricebook
QueryResult result = connection.query(
"select Id from Pricebook2 where isStandard=true"
);
SObject[] records = result.getRecords();
String stdPbId = records[0].getId();
// Create a pricebook entry for standard pricebook
PricebookEntry pbe = new PricebookEntry();
pbe.setPricebook2Id(stdPbId);
pbe.setProduct2Id(product.getId());
pbe.setIsActive(true);
pbe.setUnitPrice(100.0);
saveResults = connection.create(new SObject[]{pbe});
// Create a pricebook entry for custom pricebook
pbe = new PricebookEntry();
pbe.setPricebook2Id(pb.getId());
pbe.setProduct2Id(product.getId());
pbe.setIsActive(true);
pbe.setUnitPrice(100.0);
saveResults = connection.create(new SObject[]{pbe});
} catch (ConnectionException ce) {
ce.printStackTrace();
}
}

Design Registration Product2
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
Pricebook2ChangeEvent (API version 48.0)
Change events are available for the object.
Pricebook2History
History is available for tracked fields of the object.
Product2
Represents a product that your company sells.
This object has several fields that are used only for quantity and revenue schedules (for example, annuities). Schedules are available only
for orgs that have enabled the products and schedules features. If these features aren’t enabled, the schedule fields don’t appear , and
you can’t query, create, or update the fields.
Note: As of API version 8.0, the Product object is no longer available. Requests that contain Product are refused, and responses
don’t contain the Product object. Use the Products2 object instead.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Special Access Rules
The ConfigureDuringSale and IsSoldOnlyWithOtherProds fields are available in version 58.0 and later when Industry Automotive or
Subscription Management is enabled.
Fields
Field Details
BillingPolicyId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ID of the related billing policy. This field is available when Subscription Management is
enabled. This field is available in API version 55.0 and later.
This field is a relationship field.
Relationship Name
BillingPolicy
Relationship Type
Lookup

Design Registration Product2
Field Details
Refers To
BillingPolicy
CanUseQuantitySchedule
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether the product can have a quantity schedule (true) or not (false). Label
is Quantity Scheduling Enabled.
CanUseRevenueSchedule
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether the product can have a revenue schedule (true) or not (false). Label
is Revenue Scheduling Enabled.
ConnectionReceivedId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
ID of the PartnerNetworkConnection that shared this record with your org. This field is
available when Salesforce to Salesforce is enabled.
ConnectionSentId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
ID of the PartnerNetworkConnection that this record is shared with. This field is available
Salesforce to Salesforce is enabled. In API version 16.0 and later, this value is null. Use
PartnerNetworkRecordConnection object to forward records to connections.
ConfigureDuringSale
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Determines whether a user can edit a configuration when creating a bundle order or quote.

Design Registration Product2
Field Details
This field is available in API version 58.0 and later.
This field is available when Industries Automotive or Subscription Management is enabled.
Possible values are:
• Allowed— Changes are allowed while adding line items to a bundle; for example,
when adding products or editing quantity.
• NotAllowed—Changes aren’t allowed.
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Available only for orgs with the multicurrency feature enabled. Contains the ISO code for
any currency allowed by the org.
Description
Type
textarea
Properties
Create, Filter, Nillable, Sort, Update
Description
A text description of this record. Label is Product Description.
DisplayUrl
Type
url
Properties
Create, Filter, Nillable, Sort, Update
Description
URL leading to a specific version of a record in the linked external data source.
ExternalDataSourceId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
ID of the related external data source.
ExternalId
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update

Design Registration Product2
Field Details
Description
The unique identifier of a record in the linked external data source. For example, ID #123.
Family
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Name of the product family associated with this record. Product families are configured as
picklists in the user interface. To obtain a list of valid values, call describeSObjects()
and process the result for the values associated with the Family field. Label is Product
Family.
IsActive
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether this record is active (true) or not (false). Inactive Product2 records
are hidden in many areas in the user interface. You can change the IsActive flag on a
Product2 object as often as necessary. Label is Active.
IsArchived
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Describes whether the product is archived. The default value is false.
IsDeleted
Type
boolean
Properties
Defaulted on create, Filter
Description
Indicates whether the object has been moved to the Recycle Bin (true) or not (false).
Label is Deleted.
IsSerialized
Type
boolean
Properties
Create, Filter, Group, Sort, Update

Design Registration Product2
Field Details
Description
Indicates if a product is a serialized product (true) or not (false). Label is Serialized.
IsSoldOnlyWithOtherProds
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Determines whether the product can be sold independently or only as part of a bundle.
This field is available in API version 58.0 and later. This field is available when Industries
Automotive or Subscription Management is enabled. The default value is false, which
means that the product can be sold independently.
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last interacted with this record, directly or indirectly.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last viewed this record or list view. If this value is null,
it's possible that the user only accessed this record or list view (LastReferencedDate),
but not viewed it.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Required. Default name of this record. Label is Product Name.
NumberOfQuantityInstallments
Type
int
Properties
Create, Filter, Group, Nillable, Sort, Update

Design Registration Product2
Field Details
Description
If the product has a quantity schedule, the number of installments.
NumberOfRevenueInstallments
Type
int
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
If the product has a revenue schedule, the number of installments.
ProductClass
Type
picklist
Properties
Defaulted on create, Filter, Group, Restricted picklist, Sort
Description
This field is read-only. Its value is determined by the value of the Type field and whether
the product is associated with a ProductAttribute record. It describes whether a
product is a bundle, set, or simple product, a variation parent, or a product variation. Possible
values are:
• Bundle—This product is a parent or component in a product bundle.
• Set—This product is included in a product set.
• Simple—This product has no variations
• VariationParent—This product is a variation parent. It’s the base product for one
or more product variations and, though it has its own stock-keeping unit (SKU), isn’t a
sellable entity. Instead, it’s the parent of sellable entities—its variations.
• Variation—This product is a variation of a parent product. Each variation has its
own SKU.
When the value of ProductClass = VariationParent, it never changes. The
value of ProductClass changes between Simple and Variation when you attach
or detach a ProductAttribute record to the product.
If you attach a ProductAttribute record to a product, then the product’s
ProductClass value changes to Variation. Conversely, when you detach all
ProductAttribute records from a product, the ProductClass value changes to
Simple.
The default value is Simple.
This field is available in API version 50.0 and later. It was introduced to support of B2B and
B2C Commerce implementations.
ProductCode
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update

Design Registration Product2
Field Details
Description
Default product code for this record. Your org defines the product’s code-naming pattern.
QuantityInstallmentPeriod
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
If the product has a quantity schedule, the amount of time covered by the schedule.
QuantityScheduleType
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The type of the quantity schedule, if the product has one.
QuantityUnitOfMeasure
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Unit of the product; for example, kilograms, liters, or cases. This field comes with only one
value, Each, so consider creating your own. The QuantityUnitOfMeasure field on
ProductItem inherits this field’s values.
RecalculateTotalPrice
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Changes behavior of OpportunityLineItem calculations when a line item has child schedule
rows for the Quantity value. When enabled, if the rollup quantity changes, then the
quantity rollup value is multiplied against the sales price to change the total price.
RevenueInstallmentPeriod
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
If the product has a revenue schedule, the time period covered by the schedule.

Design Registration Product2
Field Details
RevenueScheduleType
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The type of the revenue schedule, if the product has one.
StockCheckMethod
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The method for how a product's inventory is checked. Stock checks on parent products are
common when bundles are prepackaged and individual child components can't be sold
separately. Stock checks on child products are common when bundles aren't prepackaged
and must be put together during fulfillment. If bundles aren’t prepackaged, child components
can usually be sold separately.
Possible values are:
• Null—Check stock on the product SKU.
• DoNotCheck —The stock shouldn't be check.
• ParentProduct —If the product is a parent of a bundle, check stock on the parent
product.
• ChildProducts —If the product is a parent of a bundle, check stock on the child
components.
StockKeepingUnit
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The SKU for the product. Use in tandem with or instead of the ProductCode field. For
example, you can track the manufacturer’s identifying code in the Product Code field and
assign the product a SKU when you resell it.
TaxPolicyId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ID of the related tax policy.
This field is available when Subscription Management is enabled. This field is available in API

Design Registration Product2
Field Details
This field is a relationship field.
Relationship Name
TaxPolicy
Relationship Type
Lookup
Refers To
TaxPolicy
TransferRecordMode
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
If serialized, indicates when the serial number is recorded. This field is visible based on
field-level security.
The value affects the read-only value of the Product2TransferMode field on the
ProductTransfer object.
Possible values are:
• SendAndReceive —The serial number is recorded when sending or receiving.
• ReceiveOnly —The serial number is recorded when receiving only.
Type
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort
Description
The type of product. This field's value affects the read-only value of the ProductClassfield
on the Product2 object. The following mappings define how the Type selection updates
the ProductClass.
• Base—When Type = Base, then ProductClass = VariationParent.
• Null—When Type = Null, then ProductClass = Simple for standalone
products.
• Null—When Type = Null, then ProductClass = Variation for variation
products.
• Bundle—When Type = Bundle, then ProductClass = Bundle.
• Set—When Type = Set, then ProductClass = Set.
Note:
• Revenue Cloud doesn't support products with these specific combinations: Type
= Base and ProductClass = VariationParent or Type = Null
and ProductClass = Variation.

Design Registration Product2
Field Details
• Values Null, Base, Bundle, and Set are available in environments where
both Commerce and Revenue Cloud co-exist.
• The Type field can only be updated from Null to Bundle for products with a Simple
ProductClass
This field is available when Revenue Cloud, B2B Commerce, B2C Commerce, or other clouds
with PCM add-on is enabled.
This field is available in API version 50.0 and later.
UnitOfMeasureId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The ID of the unit of measure associated with the product.
This field is a relationship field.
This field is available when Revenue Cloud is enabled.
This field is available in API version 63.0 and later.
Relationship Name
UnitOfMeasure
Refers To
UnitOfMeasure
Schedule Enabled Flags
When enabling the schedules feature, you can decide whether to enable quantity schedules, revenue schedules, or both. In addition,
you can use the API to control quantity and revenue scheduling at the product level via the CanUseQuantitySchedule and
CanUseRevenueSchedule flags. A value of true for either flag indicates that the product and any OpportunityLineItems
can have a schedule of that type. These flags can be set when creating or updating Product2 records.
Default Schedule Fields
The remaining schedule fields for this object define default schedules. Default schedule values are used to create an
OpportunityLineItemSchedule when an OpportunityLineItem is created for the Product.
The default schedule fields support the following valid values (all fields are also nillable).
Field Valid Values
RevenueScheduleType Divide, Repeat
RevenueInstallmentPeriod Daily, Weekly, Monthly, Quarterly, Yearly
NumberOfRevenueInstallments Integer from 1 to 150, inclusive.

Design Registration Product2
Field Valid Values
QuantityScheduleType Divide, Repeat
QuantityInstallmentPeriod Daily, Weekly, Monthly, Quarterly, Yearly
NumberOfQuantityInstallments Integer from 1 to 150, inclusive
When you attempt to set the schedule fields when creating or updating, the API applies cross-field integrity checks. The integrity
requirements are:
• If the schedule type is nil, the installment period and number of installments must be nil.
• If the schedule type is set to any value, then the installment period and number of installments must be non-nil.
Any create or update that fails these integrity checks is rejected with an error.
These default schedule fields, CanUseQuantitySchedule, and CanUseRevenueSchedule, are restricted picklist fields and
are available only if the org has the schedules feature enabled.
Usage
Use this object to define the default product information for your org. This object is associated by reference with Pricebook2 objects via
PricebookEntry objects. The same product can be represented in different price books as price book entries. In fact, the same product
can be represented multiple times (as separate PricebookEntry records) in the same price book with different prices or currencies. A
product can only have one price for a given currency within the same price book. To be used in custom price books, all standard prices
must be added as price book entries to the standard price book.
Note: Note: You can’t create lookup fields to Product2 object, which have Required check box set to true or the Don't Allow
Deletion" radio button selected, as the platform would otherwise interpret this and throw an error that you cannot create a
master-detail relationship to the object.
You can query the products that have been configured for your org. For example, you can allow your client application to obtain valid
product IDs for use when configuring PricebookEntry records via the API. Your client application can perform the following tasks on
PricebookEntry objects:
• Query
• Create for the standard price book or custom price books.
• Update
• Delete
• Change the IsActive field when creating or updating records
This object is defined only for those orgs that have products enabled as a feature. If the org doesn’t have the products feature, this object
doesn’t appear in the describeGlobal call, and you can't describe or query this object.
If you try to delete a product via the API but there's an opportunity that uses that product, the delete fails. The workaround is to delete
the product in the user interface, which gives you an option to archive the product.
Note: On opportunities and opportunity products, the workflow rules, validation rules, and Apex triggers fire when an update to
a child opportunity product or schedule causes an update to the parent record. This means your custom application logic is
enforced when there are updates to the parent record, ensuring higher data quality and compliance with your organization’s
business policies.

Design Registration Rebate Management Object in Design Registration
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
Product2ChangeEvent (API version 44.0)
Change events are available for the object.
Product2Feed (API version 18.0)
Feed tracking is available for the object.
Product2History
History is available for tracked fields of the object.
Product2OwnerSharingRule (API version 50.0)
Sharing rules are available for the object.
Rebate Management Object in Design Registration
Rebate Management provides access to a standard object that you can use in Design Registration to manage a relationship between
accounts.
For more information about these Rebate Management object, refer to this resource.
• AccountAccountRelation on page 145

PRICE PROTECTION
Manage Price Protection programs for partners and distributors to ensure margin stability amid price fluctuations.
Price Protection Standard Objects
Price Protection data model provides objects and fields to manage price protection programs for partners and distributors. Use these
objects to ensure partner margin stability amidst market price fluctuations.
Price Protection Standard Objects
Price Protection data model provides objects and fields to manage price protection programs for
EDITIONS
partners and distributors. Use these objects to ensure partner margin stability amidst market price
fluctuations.
Available in: Lightning
Experience
PriceProtectExecLineItem
Available in: Enterprise,
Represents a line item created as part of a Price Protection Execution. This object is available in
Professional, and
API version 63.0 and later. Unlimited, Editions
PriceProtectionExecution
Represents an instance of running the price protection process, capturing execution time, status,
and the effective date of price changes. This object is available in API version 63.0 and later.
PriceProtectionTerm
Represents a configuration record that defines the rules, types, and eligible conditions for price protection. This object is available
in API version 63.0 and later.
ProductDetectedPriceChange
Represents a detected change in price for a product associated with a partner account. This object is available in API version 63.0
and later.
Rebate Management Objects in Price Protection
Rebate Management provides access to some standard objects that you can use in Price Protection to create and manage rebate
programs and manage payouts and transactions.
PriceProtectExecLineItem
Represents a line item created as part of a Price Protection Execution. This object is available in API version 63.0 and later.
A PriceProtectExecLineItem record is automatically generated by the Data Processing Engine when eligible product transactions are
processed for price protection. It links to execution records, products, and pricing terms, and stores per-unit pricing, eligibility, and
calculation details.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()

Price Protection PriceProtectExecLineItem
Fields
Field Details
AccountId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
References the partner account related to the transaction being evaluated for price protection.
This field is a relationship field.
Relationship Name
Account
Refers To
Account
CalculatedAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
Total protected amount calculated based on the applicable price difference and quantity.
CalculationReferenceRecordId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
References the rebate or pricing rule used to compute the claim.
This field is a relationship field.
Relationship Name
CalculationReferenceRecord
Refers To
ProgramRebateType
ClaimReferenceId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Links to the related rebate claim, if one has been generated.
This field is a polymorphic relationship field.

Price Protection PriceProtectExecLineItem
Field Details
Relationship Name
ClaimReference
Refers To
RebateClaim
HasWarnings
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates if the execution line item has associated warnings.
The default value is false.
InTransitQuantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Quantity of the product in transit.
IsEligible
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether the record qualifies for price protection.
The default value is false.
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the record was last referenced by a user or system.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
Date and timestamp when the record was last opened in the UI.

Price Protection PriceProtectExecLineItem
Field Details
LocationId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
References the inventory or sales location relevant to the line item.
This field is a relationship field.
Relationship Name
Location
Refers To
Location
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
Auto-generated identifier for the line item record.
NewSalePricePerUnit
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The new sale price per unit after the price change.
NewSalePriceType
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Type of sale price applied post-adjustment (e.g., List Price, Net Price).
PriceDifference
Type
currency
Properties
Filter, Nillable, Sort
Description
Difference between the old and new sale price per unit.
This field is a calculated field.

Price Protection PriceProtectExecLineItem
Field Details
PriceProtectionExecutionId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Links to the parent Price Protection Execution record.
This field is a relationship field.
Relationship Name
PriceProtectionExecution
Relationship Type
Master-detail
Refers To
PriceProtectionExecution (the master object)
PriceProtectionTermId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
References the Price Protection Term used for evaluating eligibility and calculations.
This field is a relationship field.
Relationship Name
PriceProtectionTerm
Refers To
PriceProtectionTerm
ProductId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
References the product involved in the price protection claim.
This field is a relationship field.
Relationship Name
Product
Refers To
Product2
RemainingQuantity
Type
double

Price Protection PriceProtectExecLineItem
Field Details
Properties
Create, Filter, Sort, Update
Description
Quantity of product still eligible for claim after partial adjustments.
SalePricePerUnit
Type
currency
Properties
Create, Filter, Sort, Update
Description
Original sale price per unit before the price adjustment.
SalePriceType
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Type of sale price recorded during the original transaction.
Status
Type
picklist
Properties
Create, Filter, Group, Restricted picklist, Sort, Update
Description
Current processing state of the line item.
Possible values are:
• Complete
• Error
• New
• ReadyForClaim—Ready For Claim
• ReadyForPricing—Ready For Pricing
• ReadyForSimulation—Ready For Simulation
StatusReason
Type
string
Properties
Create, Filter, Nillable, Sort, Update
Description
Additional explanation or message associated with the current status.

Price Protection PriceProtectionExecution
Field Details
TransactionDate
Type
date
Properties
Create, Filter, Group, Sort, Update
Description
Date when the original sale or transaction occurred.
TransactionReferenceId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Reference to the transaction record from which this line item originates.
This field is a polymorphic relationship field.
Relationship Name
TransactionReference
Refers To
PartnerUnsoldInventory
WarningMessage
Type
string
Properties
Create, Filter, Nillable, Sort, Update
Description
Descriptive warning associated with this line item, if applicable.
PriceProtectionExecution
Represents an instance of running the price protection process, capturing execution time, status, and the effective date of price changes.
This object is available in API version 63.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()

Price Protection PriceProtectionExecution
Fields
Field Details
ExecutionJobId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Data processing engine instance responsible for creating price protection records.
This field is a relationship field.
Relationship Name
ExecutionJob
Refers To
BatchCalcJobDefinition
ExecutionReferenceNumber
Type
string
Properties
Create, Filter, Group, idLookup, Nillable, Sort, Update
Description
Unique reference number generated by the Data Processing Engine for this execution. This
can be used to associate related line items to the same execution.
LastExecutionTime
Type
dateTime
Properties
Create, Filter, Nillable, Sort, Update
Description
Date and time when the price protection execution was last performed by the Data Processing
Engine.
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the record was last referenced. This is used internally to optimize
performance and user experience.
LastViewedDate
Type
dateTime

Price Protection PriceProtectionExecution
Field Details
Properties
Filter, Nillable, Sort
Description
Date and timestamp when the record was last viewed in the Salesforce UI. Helps track user
engagement.
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
Auto-generated name for the price protection execution record. Used as the primary identifier
within the system.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Identifier for the user or group that owns this record.
This field is a polymorphic relationship field.
Relationship Name
Owner
Refers To
Group, User
PriceChangeEffectiveDate
Type
date
Properties
Create, Filter, Group, Sort, Update
Description
Date when the new price goes into effect as part of the price protection execution.
Status
Type
picklist
Properties
Create, Filter, Group, Restricted picklist, Sort, Update
Description
Represents the current lifecycle status of the price protection execution process.
Possible values are:

Price Protection PriceProtectionTerm
Field Details
• Completed
• New
• Processing
PriceProtectionTerm
Represents a configuration record that defines the rules, types, and eligible conditions for price protection. This object is available in API
A PriceProtectionTerm record is referenced during claims processing to calculate supported price and quantity adjustments based on
predefined terms.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
CalculationReferenceRecordId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
Rebate type that's applicable for the claim amount calculation. This field is a relationship
field.
Relationship Name
CalculationReferenceRecord
Refers To
ProgramRebateType
IsPayable
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether the inventory is eligible for payment or refund after a price protection
adjustment.
The default value is false.

Price Protection PriceProtectionTerm
Field Details
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the record was last referenced by the current user. Useful for activity
tracking.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
Date and the timestamp when the record was last viewed by the user. Helps in understanding
record engagement.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Unique name for the Price Protection Term. This is typically used as a primary identifier for
UI display or business logic.
NewSalePriceType
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Defines the type of new sale price applicable after a price protection scenario. This helps
classify how the adjusted sale price can be handled.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Identifier for the user or group who owns the record.
This field is a polymorphic relationship field.
Relationship Name
Owner

Price Protection PriceProtectionTerm
Field Details
Refers To
Group, User
PriceProtectionType
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Defines the type of price protection applied.
Possible values are:
• PriceProtection—Price Protection
• ReversePriceProtection—Reverse Price Protection
The default value is PriceProtection.
SalePriceType
Type
picklist
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Specifies the type of sale price before price protection is applied. This helps calculate the
protection delta during claim processing.
SupportedPricePercent
Type
percent
Properties
Create, Defaulted on create, Filter, Nillable, Sort, Update
Description
Indicates the percentage of the price that is supported for price protection. Helps calculate
eligible claim amounts.
SupportedQuantityPercent
Type
percent
Properties
Create, Defaulted on create, Filter, Nillable, Sort, Update
Description
Indicates the percentage of quantity that is eligible for price protection. Used to determine
prorated reimbursement.

Price Protection ProductDetectedPriceChange
ProductDetectedPriceChange
Represents a detected change in price for a product associated with a partner account. This object is available in API version 63.0 and
later.
A ProductDetectedPriceChange record is automatically created when the system identifies a change in product pricing that can require
price protection evaluation or further processing.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccountId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
References the partner account for which the price change was detected.
This field is a relationship field.
Relationship Name
Account
Refers To
Account
EffectiveDate
Type
date
Properties
Create, Filter, Group, Sort, Update
Description
Date when the new price becomes effective for the product.
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the record was last referenced by the current user. Useful for activity
tracking.

Price Protection ProductDetectedPriceChange
Field Details
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
Date and the timestamp the record was last referenced by a user or system process.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Unique name or identifier for the price change record.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
User or group that owns this record. This is a polymorphic relationship field.
This field is a polymorphic relationship field.
Relationship Name
Owner
Refers To
Group, User
ProcessingStatus
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Indicates the current processing stage of the price change.
Possible values are:
• Completed
• Inactive
• New
• Processing—In Progress
ProductId
Type
reference

Price Protection Rebate Management Objects in Price Protection
Field Details
Properties
Create, Filter, Group, Sort, Update
Description
References the product for which the price change was detected.
This field is a relationship field.
Relationship Name
Product
Refers To
Product2
Rebate Management Objects in Price Protection
Rebate Management provides access to some standard objects that you can use in Price Protection to create and manage rebate
programs and manage payouts and transactions.
For more information about these Rebate Management objects, refer to these resources.
• ProgramRebateType
• ProgramRebateTypeProduct on page 167
• RebateClaim on page 169
• RebateProgram on page 196
• RebateProgramMember on page 199

REBATE MANAGEMENT
Use Rebate Management to create rebate programs and define an incentive structure with benefits and corresponding qualification
thresholds.
Rebate Management is available in Lightning Experience.
Available in: Enterprise, Professional, and Unlimited Editions that have Rebate Management enabled.
Rebate Management Standard Objects
Rebate Management data model provides objects and fields to create and manage rebate programs and manage payouts and
transactions. Use the objects to optimize the incentives offered to build a mutually profitable relationship with your partners.
Rebate Management Standard Invocable Actions
Add members to a rebate program, calculate rebate amounts and upsert payouts, generate rebate payout periods, process rebate
calculation batch jobs, and process a rebate CSV file for Rebate Management. For more information on standard invocable actions,
see REST API Developer Guide and Actions Developer Guide.
Rebate Management Metadata API Types
Metadata API enables you to access some types and feature settings that you can customize in the user interface. For more information
about Metadata API and to find a complete reference of existing metadata types, see Metadata API Developer Guide.
Rebate Management Business APIs
Rebate Management Business APIs use REST endpoints. These REST APIs follow similar conventions as Connect REST APIs.
Data Processing Engine, Batch Management, and Monitor Workflow Services
Data Processing Engine and Batch Management help automate your business processes. Use objects, APIs, Platform Events, and
invocable actions to define, run, and review Data Processing Engine definitions and Batch Management jobs.
Rebate Management Standard Objects
Rebate Management data model provides objects and fields to create and manage rebate programs and manage payouts and transactions.
Use the objects to optimize the incentives offered to build a mutually profitable relationship with your partners.
Rebate Management is available in Lightning Experience.
Available in: Enterprise, Unlimited, and Developer Editions.
AccountAccountRelation
Represents a relationship between accounts, such as a relationship between a distributor account and a ship-to account. This object
is available in API version 58.0 and later.
PartyRoleRelation
Represents information about the type of relationship between the participants in a relationship. This object is available in API version
58.0 and later.

Rebate Management Rebate Management Standard Objects
ProgramRebateType
Provide the rebate types that are part of this program. For example, volume rebate, revenue rebate, or rebate on every transaction.
This object is available in API version 51.0 and later.
ProgramRebateTypeBenefit
Defines the benefit matrix for the rebate type. For example, 5% or $200. This object is available in API version 51.0 and later.
PgmRebateTypBnftMapping
If benefit table is extended, defines mapping of benefit field to the aggregate object fields. This object is available in API version 51.0
and later.
ProgramRebateTypeFilter
The definition that filters the transaction journals eligible for a rebate type. This filter definition is used in the rebates data processing
engines. This object is available in API version 51.0 and later.
ProgramRebateTypePayout
The payout given to a member for a particular rebate type. For example, volume rebate payout in Jan'19 for ABC enterprises is $560,
petrol engine payout for ABC in Jan'19 is $440. This object is available in API version 51.0 and later.
ProgramRebateTypPayoutSrc
The rebate amount and the tier applied calculated for each row in the aggregate. There is a 1 to 1 relation between payout source
and aggregate. This object is available in API version 51.0 and later.
ProgramRebateTypeProduct
Represents a junction between a program rebate type and a product. This object is available in API version 53.0 and later.
ProgramRebateTypeReference
Represents the association between the contract, opportunity, or any eligible standard or custom object, and rebate type. This object
is available in API version 52.0 and later.
RebateClaim
Represents information about the claim submitted by the end customer or distributor for a ship and debit program. This object is
available in API version 54.0 and later.
RebateClaimAdjustment
Represents information about the adjustments made to the rebate claim. This object is available in API version 58.0 and later.
RebateMemberAggregateItem
Represents a junction between a rebate member product aggregate and a transaction journal. This object is available in API version
54.0 and later.
RebateMemberClaimAggregate
Represents information about the aggregated claim quantity and amount for a rebate member per product. This object is available
in API version 58.0 and later.
RebateMemberProductAggregate
Stores the post calculation summary of journal transactions by member, period, and rebate type. For example, ABC enterprises for
May 2021 against Vol Rebate on Radius category, did a total quantity of 150 units and transaction amount of $80,000. This object is
available in API version 65.0 and later.
RebatePartnerSpecialPrcTrm
Represents information about the special pricing term for a ship and debit program. This object is available in API version 58.0 and
later.
RebatePayment
Tracks if the payment has been generated for this member for back end processing. This object is available in API version 51.0 and
later.

Rebate Management AccountAccountRelation
RebatePayoutAdjustment
Rebate amount adjustment that needs to be given manually. An adjustment is an amount added or subtracted to the calculated
rebate amount. This object is available in API version 51.0 and later.
RebateProgram
The rebate program your organization runs with a single account, all accounts, or specific list of accounts. This object is available in
API version 51.0 and later.
RebateProgramMember
The member of a rebate program. By virtue of being a member, the partner or business account is eligible to get rebate payments.
For example, ABC Enterprises and HVAC Corp are members of GoldStone Volume Rebate Program. This object is available in API
RebateProgramMemberPayout
The payout calculated for a member for the period. For example, $1000 Jan'21 payout for ABC enterprises. This object is available in
API version 51.0 and later.
RebateProgramPayoutPeriod
The period of the payout calculation. For example, 1st to 31st Jan, or 1st Dec to 14th Dec. This object is available in API version 51.0
and later.
RebatePtnrSpclPrcTrmBnft
Represents information about the benefit tier in a rebate partner special pricing term. This object is available in API version 58.0 and
later.
ReceivedDocument
Allows partners to upload .CSV document. This object is available in API version 51.0 and later.
TransactionJournal
The transactions that need to be processed for a rebate program. For example, order line for 1000 units of $1200 for member ABC
enterprises. This object is available in API version 51.0 and later.
UnitOfMeasureConversion
Represents the information used to convert a measurement value from a unit of measure to another. This object is available in API
AccountAccountRelation
Represents a relationship between accounts, such as a relationship between a distributor account and a ship-to account. This object is
available in API version 58.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccountId
Type
reference

Rebate Management AccountAccountRelation
Field Details
Properties
Create, Filter, Group, Sort, Update
Description
ID of the account associated with this account account relationship.
This field is a relationship field.
Relationship Name
Account
Relationship Type
Lookup
Refers To
Account
EndDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The date when the relationship ends.
HierarchyType
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the hierarchy between accounts that are related.
Possible values are:
• Child
• Parent
• Peer
The default value is Peer.
IsActive
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether the account is actively involved with the related account (true) or not
(false).
The default value is false.

Rebate Management AccountAccountRelation
Field Details
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last viewed this record or list view.
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
Name of the account account relationship.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
ID of the owner of this object.
This field is a polymorphic relationship field.
Relationship Name
Owner
Relationship Type
Lookup
Refers To
Group, User
PartyRoleRelationId
Type
reference
Properties
Create, Filter, Group, Sort, Update

Rebate Management AccountAccountRelation
Field Details
Description
The relationship between two accounts.
This field is a relationship field.
Relationship Name
PartyRoleRelation
Relationship Type
Lookup
Refers To
PartyRoleRelation
RelatedAccountId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The related account in the relationship.
This field is a relationship field.
Relationship Name
RelatedAccount
Relationship Type
Lookup
Refers To
Account
RelatedInverseRecordId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The record that specifies the inverse relationship between the accounts.
This field is a relationship field.
Relationship Name
RelatedInverseRecord
Relationship Type
Lookup
Refers To
AccountAccountRelation
StartDate
Type
date

Rebate Management PartyRoleRelation
Field Details
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The date when the relationship starts.
PartyRoleRelation
Represents information about the type of relationship between the participants in a relationship. This object is available in API version
58.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last accessed this record, a record related to this record,
or a list view.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last viewed this record or list view.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Name of the party role relationship.

Rebate Management PartyRoleRelation
Field Details
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
ID of the owner of this object.
This field is a polymorphic relationship field.
Relationship Name
Owner
Relationship Type
Lookup
Refers To
Group, User
RelatedInverseRecordId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The record that specifies the inverse relationship between the roles.
This field is a relationship field.
Relationship Name
RelatedInverseRecord
Relationship Type
Lookup
Refers To
PartyRoleRelation
RelatedRoleName
Type
string
Properties
Create, Filter, Group, Sort, Update
Description
The role that's related to another role in the relationship.
RelationshipObjectName
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
The object that's associated with the relationship.

Rebate Management ProgramRebateType
Field Details
Possible values are:
• Account_Account_Relationship—Account Account Relationship
• Contact_Contact_Relationship—Contact Contact Relationship
The default value is Account_Account_Relationship.
RoleName
Type
string
Properties
Create, Filter, Group, Sort, Update
Description
The name of the role in the relationship.
ShouldCreaInversRoleAuto
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort
Description
Indicates whether a role record should be created automatically for the relationship (true)
or not (false).
The default value is false.
ProgramRebateType
Provide the rebate types that are part of this program. For example, volume rebate, revenue rebate, or rebate on every transaction. This
object is available in API version 51.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccrualRate
Type
double
Properties
Create, Filter, Nillable, Sort, Update

Rebate Management ProgramRebateType
Field Details
Description
The rate you want to accrue at for the rebate program member. This rate is in the same units
as the specified measure type, for example percent or amount. This field is available in API
AggregateObjectName
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Name of the custom aggregation entity. For example, RebateMemberProductAggregate.
BenefitQualifierField
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Represents an attribute in the aggregate object whose value will be used, in conjunction
with Aggregate Field and Rebate Type Benefit Field attributes from the
PgmRebateTypBnftMapping entity, to determine the Benefit Value from the
ProgramRebateTypeBenefit entity.
Possible values are:
• GrowthAmount—Rebate Member Product Aggregate:Growth Amount.
• GrowthAmountPercent—Rebate Member Product Aggregate:Growth Amount
Percent.
• GrowthQuantity—Rebate Member Product Aggregate:Growth Quantity.
• GrowthQuantityPercent—Rebate Member Product Aggregate:Growth Quantity
Percent.
• PriorTotalQuantity—Rebate Member Product Aggregate:Prior Total Quantity.
• PriorTotalTransactionAmount—Rebate Member Product Aggregate:Prior
Total Transaction Amount.
• TotalQuantity—Rebate Member Product Aggregate:Total Quantity.
• TotalTransactionAmount—Rebate Member Product Aggregate:Total Transaction
Amount.
CalcObjectId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Specifies the data processing engine definition used for the calculation. Only active data
processing engine definitions can be used.

Rebate Management ProgramRebateType
Field Details
Possible values are:
• Aggregate By Member
• Aggregate By Product
• Account Hierarchy Member Aggregate
• Process Per Transaction
• Ship and Debit Member Aggregate
• Year on Year Growth
CalculationBasis
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specify the basis for rebate amount calculation. This field is available in API version 52.0 and
later.
Possible values are:
• Accrual: Accrual rate, if provided, or the benefit setup is used to calculate the rebate
amount.
• Payout: Benefit setup is used to calculate the rebate amount.
• PayoutAndAccrual—Payout and Accrual: Benefit setup is used for payout , and
accrual rate for accrual amount.
The default value is 'Payout'.
CalculationMethod
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the rule for calculating rebate benefits.
Possible values are:
• Retrospective
• Stepped
CalculationType
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Type of calculation for the rebate type.
Possible values are:

Rebate Management ProgramRebateType
Field Details
• AggregateBased
• Custom
• GrowthBased
• PerTransaction
FilterCriteria
Type
textarea
Properties
Nillable
Description
Stores the rebate type filter definition in JSON format, which will be consumed by the Calc
object.
FilterLogic
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Contains the filter criteria options that are offered - AND, OR, Custom.
IsInTransitQtyApplicable
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Determine eligibility to include or exclude in-transit quantities
The default value is false.
IsIntegratable
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
This field determines if the rebate type record is of type template or not, based on which the
record can be associated with an opportunity,contract, quote, or any other eligible object.
The default value is 'false'.
MeasureField
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update

Rebate Management ProgramRebateType
Field Details
Description
Stores the reference to the aggregate object that will be used for rebate amount calculations
based on the measure type selected and the benefit value fetched.
Possible values are:
• GrowthAmount—Rebate Member Product Aggregate:Growth Amount.
• GrowthAmountPercent—Rebate Member Product Aggregate:Growth Amount
Percent.
• GrowthQuantity—Rebate Member Product Aggregate:Growth Quantity.
• GrowthQuantityPercent—Rebate Member Product Aggregate:Growth Quantity
Percent.
• PriorTotalQuantity—Rebate Member Product Aggregate:Prior Total Quantity.
• PriorTotalTransactionAmount—Rebate Member Product Aggregate:Prior
Total Transaction Amount.
• TotalQuantity—Rebate Member Product Aggregate:Total Quantity.
• TotalTransactionAmount—Rebate Member Product Aggregate:Total Transaction
Amount.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Name of the program rebate type.
ProductFilterType
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The criteria to be applied for the products present in the Included or Excluded Products list.
Possible values are:
• ExcludeProducts—Exclude Products
• IncludeProducts—Include Products
RebateMeasureType
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Type of rebate.

Rebate Management ProgramRebateType
Field Details
Possible values are:
• AmountperUnit
• Custom
• FixedAmount
• PercentageOfRevenue
RebateProgramId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
Reference to the rebate program.
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Status of the rebate type.
Possible values are:
• Active
• Inactive
UnitOfMeasureId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The unit of measure associated with the program rebate type. This field is available in API
This is a relationship field.
Relationship Name
UnitOfMeasure
Relationship Type
Lookup
Refers To
UnitOfMeasure
ValidityDuration
Type
int

Rebate Management ProgramRebateTypeBenefit
Field Details
Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
Description
Duration for which the inventory is eligible for price protection/Duration of inventory eligibility
for price protection
ValidityDurationType
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The unit of measure for the validity duration.
Possible values are:
• Days
• Months
• Years
The default value is Years.
Usage
Each program can have multiple rebate types. For example, buy 100 units and get 2% revenue back, buy 10 units of petrol engines and
get 1% rebate, and so on. If you want to give tiered benefits, select the Benefit Qualifier Field. For example, to give a tiered benefit of $5
for 0–100 units and $10 for 101–500 units, select Total Quantity in the Benefit Qualifier Field when the Measure Type is Total Quantity.
ProgramRebateTypeBenefit
Defines the benefit matrix for the rebate type. For example, 5% or $200. This object is available in API version 51.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
BenefitValue
Type
double
Properties
Create, Filter, Sort, Update

Rebate Management ProgramRebateTypeBenefit
Field Details
Description
Rebate benefit at a level. For example, 3%, $3000.
EffectiveEndDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The date until when the program rebate type benefit is effective. If the date does not match
a payout period end date, it isn’t picked.
EffectiveStartDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The date from when the program rebate type benefit is effective. If the date does not match
a payout period start date, it isn’t picked.
MaximumMeasureFieldValue
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Cap the measure value at a certain figure. For example, pay 1% on $100,000 even when the
members do more than that.
MaximumQualifyingValue
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Upper limit of quantity or revenue at a level.
MinimumQualifyingValue
Type
double
Properties
Create, Filter, Sort, Update
Description
Minimum quantity or revenue required to qualify to a level.

Rebate Management PgmRebateTypBnftMapping
Field Details
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Name of the qualification. For example, Tier 1/2/3, Gold/Silver.
ProductId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Use this if the benefits vary by products. For example, Product A has a tier from 1- 100 units
for $20 and Product B has 1-100 units at $19.
To use product or any dimension to the benefits, add that field in benefit mapping
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Status of the program rebate type benefit.
Possible values are:
• Active
• Inactive
Usage
The benefit table can be extended with custom columns, for example, Region. The benefits can then be configured as: APAC 3%, USA
2%, and so on.
PgmRebateTypBnftMapping
If benefit table is extended, defines mapping of benefit field to the aggregate object fields. This object is available in API version 51.0
and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()

Rebate Management PgmRebateTypBnftMapping
Fields
Field Details
AggregateField
Type
picklist
Properties
Create, Filter, Group, Restricted picklist, Sort, Update
Description
Used to describe the join conditions between the aggregate object and the Program Rebate
Type Benefit entity.
Possible values are:
• RebateMemberProductAggregate.GrowthAmount—Growth Amount
• RebateMemberProductAggregate.GrowthAmountPercent—Growth
Amount Percent
• RebateMemberProductAggregate.GrowthQuantity—Growth Quantity
• RebateMemberProductAggregate.GrowthQuantityPercent—Growth
Quantity Percent
• RebateMemberProductAggregate.LastReferencedDate—Last
Referenced Date
• RebateMemberProductAggregate.LastViewedDate—Last Viewed Date
• RebateMemberProductAggregate.PriorTotalQuantity—Prior Total
Quantity
• RebateMemberProductAggregate.PriorTotalTransactionAmount—Prior
Total Transaction Amount
• RebateMemberProductAggregate.ProductId—Product ID
• RebateMemberProductAggregate.ProgramRebateTypeId—Program
Rebate ID
• RebateMemberProductAggregate.RebateProgramMemberId—Rebate
Program Member ID
• RebateMemberProductAggregate.RebateProgramPayoutPeriodId—Rebate
Program Payout Period ID
• RebateMemberProductAggregate.TotalQuantity—Total Quantity
• RebateMemberProductAggregate.TotalTransactionAmount—Total
Transaction Amount
• RebateMemberProductAggregate.TransactionJournalId— ID
ProgramRebateTypeId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Parent identifier

Rebate Management ProgramRebateTypeFilter
Field Details
RebateTypeBenefitField
Type
picklist
Properties
Create, Filter, Group, Restricted picklist, Sort, Update
Description
Used to describe the join conditions between the aggregate object and the Program Rebate
Type Benefit entity.
Possible values are:
• ProductId—ID of the Product
ProgramRebateTypeFilter
The definition that filters the transaction journals eligible for a rebate type. This filter definition is used in the rebates data processing
engines. This object is available in API version 51.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
FilterField
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The field name to use for the program rebate type filter.
Possible values are:
• ActivityDate—Activity date.
• CloneSourceId—Cloned source ID.
• CreatedById—Created by.
• CreatedDate—Created date.
• ExternalTransactionNumber—External transaction ID.
• Id— ID
• IsDeleted—Deleted.
• JournalDate—Journal date.
• LastModifiedById—Last modified by.

Rebate Management ProgramRebateTypeFilter
Field Details
• LastModifiedDate—The most recent date on which a user modified this record.
• LastReferencedDate—The most recent date on which a user referenced this
record.
• LastViewedDate—The most recent date on which a user viewed this record.
• MemberId—Program Member
• Name
• OrderId—Order
• OrderItemId—Order Product.
• ProductCategoryId—Product Category
• ProductId—Product
• Quantity
• QuantityUnitOfMeasureId—Quantity Unit
• SystemModstamp—System Modstamp
• TransactionAmount—Transaction Amount.
• UsageType—Usage Type.
• UserRecordAccessId—Object Access Level.
Operator
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The filter operator.
Possible values are:
• Contains—in
• Equals—equals
• GreaterThan—greater than
• GreaterThanOrEquals—greater or equal
• LessThan—less than
• LessThanOrEquals—less or equal
• NotEquals—not equal to
ProgramRebateTypeId
Type
reference
Properties
Create, Filter, Group, Sort
Description
The parent program rebate type associated with the filter.

Rebate Management ProgramRebateTypePayout
Field Details
Sequence
Type
int
Properties
Create, Filter, Group, Sort, Update
Description
The unique sequence number for each condition within the program rebate type filter.
Value
Type
string
Properties
Create, Filter, Group, Sort, Update
Description
The value for filtering the program rebate type.
ProgramRebateTypePayout
The payout given to a member for a particular rebate type. For example, volume rebate payout in Jan'19 for ABC enterprises is $560,
petrol engine payout for ABC in Jan'19 is $440. This object is available in API version 51.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccruedAmount
Type
currency
Properties
Filter, Nillable, Sort
Description
The accrued amount for the program rebate type payout.
This is a calculated field.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update

Rebate Management ProgramRebateTypePayout
Field Details
Description
Name of the program rebate type.
ProgramRebateTypeId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Unique identifier for the program rebate type.
RebateAmount
Type
currency
Properties
Filter, Nillable, Sort
Description
Rebate amount.
This is a calculated field.
RebateProgramMemberPayoutId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Unique identifier of the rebate program member payout.
TotalBenefitQualifierValue
Type
double
Properties
Filter, Nillable, Sort
Description
Roll-up summary of the Benefit Qualifier Value from the Program Rebate Type Payout Source
entity.
This is a calculated field.
TotalMeasureValue
Type
double
Properties
Filter, Nillable, Sort
Description
Roll-up summary for the Measure Value field from the Program Rebate Type Payout Source
entity.

Rebate Management ProgramRebateTypPayoutSrc
Field Details
This is a calculated field.
ProgramRebateTypPayoutSrc
The rebate amount and the tier applied calculated for each row in the aggregate. There is a 1 to 1 relation between payout source and
aggregate. This object is available in API version 51.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccrualRate
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The accrual rate for the program rebate type payout source. This field is available in API
AccruedAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The accrued amount for the program rebate type payout source. This field is available in API
AggregateIdentifierId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Unique identifier for the aggregate row.
BenefitQualifierValue
Type
double

Rebate Management ProgramRebateTypPayoutSrc
Field Details
Properties
Create, Filter, Nillable, Sort, Update
Description
Value of the attribute from the aggregate object that is set up as Benefit Qualifier.
MeasureValue
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
Value of the attribute from the aggregate object that is set up as Measure Field.
MemberId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Unique identifier for the member.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Name of the rebate program member.
ProgramRebateTypeBenefitId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Program rebate type benefit identifier.
ProgramRebateTypePayoutId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Unique identifier of the program rebate type payout.
RebateAmount
Type
currency

Rebate Management ProgramRebateTypeProduct
Field Details
Properties
Create, Filter, Nillable, Sort, Update
Description
Rebate amount calculated by invocable actions.
ProgramRebateTypeProduct
Represents a junction between a program rebate type and a product. This object is available in API version 53.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
ProductId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The product associated with the record.
This is a relationship field.
Relationship Name
Product
Relationship Type
Lookup
Refers To
Product2
ProgramRebateTypeId
Type
reference
Properties
Create, Filter, Group, Sort
Description
The program rebate type associated with the product.
This is a relationship field.
Relationship Name
ProgramRebateType

Rebate Management ProgramRebateTypeReference
Field Details
Relationship Type
Lookup
Refers To
ProgramRebateType
ProgramRebateTypeReference
Represents the association between the contract, opportunity, or any eligible standard or custom object, and rebate type. This object is
available in API version 52.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), undelete(), update(), upsert()
Fields
Field Details
ProgramRebateTypeId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The program rebate type associated with the record.
This is a relationship field.
Relationship Name
ProgramRebateType
Relationship Type
Lookup
Refers To
ProgramRebateType
ProgramRebateTypeSrcId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The source program rebate type associated to the contract, opportunity, or quote, or any
other eligible standard or custom object.
This is a relationship field.

Rebate Management RebateClaim
Field Details
Relationship Name
ProgramRebateTypeSrc
Relationship Type
Lookup
Refers To
ProgramRebateType
ReferenceObjectId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The contract, opportunity, quote, or any other eligible standard or custom object associated
with the program rebate type.
This is a polymorphic relationship field.
Relationship Name
ReferenceObject
Relationship Type
Lookup
Refers To
Contract, Opportunity, Order, SalesAgreement
RebateClaim
Represents information about the claim submitted by the end customer or distributor for a ship and debit program. This object is available
in API version 54.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
ApprovedAmount
Type
currency
Properties
Filter, Nillable, Sort

Rebate Management RebateClaim
Field Details
Description
The approved rebate claim amount. Available in API version 58.0 and later.
CalculatedAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The calculated rebate claim amount. Available in API version 58.0 and later.
ClaimAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The amount for which rebate is claimed.
ClaimDate
Type
dateTime
Properties
Create, Filter, Nillable, Sort, Update
Description
The date when the claim is submitted by the claimant.
ClaimType
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the type of the rebate claim. Available in API version 58.0 and later.
Possible values are:
• ShipAndDebit—Ship and Debit
• StandardRebate—Standard Rebate
ClaimedByAccountId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The account of the customer or distributor who is submitting the claim.
This field is a relationship field.

Rebate Management RebateClaim
Field Details
Relationship Name
ClaimedByAccount
Relationship Type
Lookup
Refers To
Account
ClaimedByAccountNumber
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The reference number of the account of the customer or distributor who is submitting the
claim.
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
If multiple currencies are enabled, this field contains the currency ISO code associated with
the record.
Possible values are:
• EUR—Euro
• USD—U.S. Dollar
The default value is EUR.
Description
Type
textarea
Properties
Create, Filter, Nillable, Sort, Update
Description
The description of the rebate claim.
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The most recent date on which a user referenced this record.

Rebate Management RebateClaim
Field Details
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The most recent date on which a user viewed this record.
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
Autogenerated name of the rebate claim.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
ID of the rebate claim record owner.
This field is a polymorphic relationship field.
Relationship Name
Owner
Relationship Type
Lookup
Refers To
Group, User
ParticipatingAccountId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The account of a participant in the claim. It can be the ship to/end customer or shipper/
channel partner.
This field is a relationship field.
Relationship Name
ParticipatingAccount
Relationship Type
Lookup

Rebate Management RebateClaim
Field Details
Refers To
Account
ParticipatingAccountNumber
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The reference number of the account of a participant in the claim. It can be the ship to/end
customer or shipper/ channel partner.
ProcessingStatus
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Sort, Update
Description
The processing status of the rebate claim.
Possible values are:
• Approved
• Complete
• In Review
• New
• Rejected
• Reviewed
• System Failed
• System Processed
The default value is New.
ProcessingStatusMessage
Type
string
Properties
Create, Filter, Nillable, Sort, Update
Description
The message with the details of the rebate claim’s processing status when it isn’t completed.
ProductCode
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update

Rebate Management RebateClaim
Field Details
Description
The reference number of the product for which the rebate claim is submitted.
ProductId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The product for which the rebate claim is submitted.
This field is a relationship field.
Relationship Name
Product
Relationship Type
Lookup
Refers To
Product2
ProgramReferenceNumber
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The reference number of the rebate program.
Quantity
Type
double
Properties
Create, Filter, Sort, Update
Description
The quantity of the product for which the rebate claim is submitted.
QuantityUnitOfMeasureId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The unit of measure of the quantity. Available in API version 58.0 and later.
Relationship Name
QuantityUnitOfMeasure
Relationship Type
Lookup

Rebate Management RebateClaim
Field Details
Refers To
UnitOfMeasure
RebateMemberClaimAggregateId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The rebate member claim aggregate record related to the rebate claim. Available in API
Relationship Name
RebateMemberClaimAggregate
Relationship Type
Lookup
Refers To
RebateMemberClaimAggregate
RebatePaymentId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The rebate payment record related to the rebate claim. Available in API version 58.0 and
later.
Relationship Name
RebatePayment
Relationship Type
Lookup
Refers To
RebatePayment
ReceivedDocumentId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The received document that this claim is part of. Available in API version 58.0 and later.
Relationship Name
ReceivedDocument
Relationship Type
Lookup

Rebate Management RebateClaim
Field Details
Refers To
ReceivedDocument
ReferencePricePerUnit
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The price of a product unit that’s agreed upon between the manufacturer and the claimant
by the manufacturer and the distributor or the manufacturer and the customer for the rebate
claim.
ResalePricePerUnit
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The price at which the claimant bought the product.
SalePricePerUnit
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The original price at which a product unit is sold to the customer by the manufacturer.
ShipDate
Type
dateTime
Properties
Create, Filter, Nillable, Sort, Update
Description
The date when the product was shipped to end customer. Available in API version 58.0 and
later.
ShippedTransactionIdentifier
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The identifier of the transaction between distributor and end customer or ship to account.
Available in API version 58.0 and later.

Rebate Management RebateClaimAdjustment
Field Details
TotalAdjustmentAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The total amount adjusted on the rebate claim. Available in API version 58.0 and later.
TransactionIdentifier
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The unique identifier of the transaction between the manufacturer and distributor. Available
in API version 58.0 and later.
UsageType
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort
Description
Specifies the usage type of the rebate claim.
Possible value is:
• Automotive
• Rebates
The default value is Rebates. Available in API version 58.0 and later.
RebateClaimAdjustment
Represents information about the adjustments made to the rebate claim. This object is available in API version 58.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AdjustmentAmount
Type
currency

Rebate Management RebateClaimAdjustment
Field Details
Properties
Create, Filter, Sort, Update
Description
The adjustment amount for the rebate claim.
ApprovedDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The date when the rebate claim adjustment was approved.
Comments
Type
string
Properties
Create, Filter, Group, Sort, Update
Description
The details about the adjustment made to the rebate claim.
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The currency ISO code associated with the record. This is available when multiple currencies
are enabled.
Possible values are:
• EUR—Euro
• USD—U.S. Dollar
The default value is EUR.
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The most recent date on which a user referenced this record.
LastViewedDate
Type
dateTime

Rebate Management RebateClaimAdjustment
Field Details
Properties
Filter, Nillable, Sort
Description
The most recent date on which a user viewed this record.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
The name of the rebate claim adjustment.
RebateClaimId
Type
reference
Properties
Create, Filter, Group, Sort
Description
The rebate claim record to which the adjustment was made.
This field is a relationship field.
Relationship Name
RebateClaim
Relationship Type
Lookup
Refers To
RebateClaim
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The status of the adjustment made to the rebate claim.
Possible values are:
• Approved
• InReview—Under Review
• Rejected
The default value is InReview.

Rebate Management RebateMemberAggregateItem
RebateMemberAggregateItem
Represents a junction between a rebate member product aggregate and a transaction journal. This object is available in API version 54.0
and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate is not null, the user accessed this record or list view indirectly.
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
Name of the rebate member aggregate item.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
ID of the owner of this object.
This field is a polymorphic relationship field.

Rebate Management RebateMemberAggregateItem
Field Details
Relationship Name
Owner
Relationship Type
Lookup
Refers To
Group, User
PriorTransactionAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The transaction amount of the associated transaction journal record that contributes to
aggregation for the configured prior period.
PriorTransactionQuantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The transaction quantity of the associated transaction journal record that contributes to
aggregation for the configured prior period.
RebateAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The rebate amount for the associated transaction journal record.
RebateMemberProductAggregateId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The rebate member product aggregate record associated with the transaction journal record.
This is a relationship field.
Relationship Name
RebateMemberProductAggregate
Relationship Type
Lookup

Rebate Management RebateMemberClaimAggregate
Field Details
Refers To
RebateMemberProductAggregate
TransactionAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The transaction amount for the transaction journal record associated with the aggregate
item record.
TransactionJournalId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The transaction journal associated with the rebate aggregated transaction journal record.
This is a relationship field.
Relationship Name
TransactionJournal
Relationship Type
Lookup
Refers To
TransactionJournal
TransactionQuantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The transaction quantity of the associated transaction journal record.
RebateMemberClaimAggregate
Represents information about the aggregated claim quantity and amount for a rebate member per product. This object is available in
API version 58.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()

Rebate Management RebateMemberClaimAggregate
Fields
Field Details
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The currency ISO code associated with the record. This is available when multiple
currencies are enabled.
Possible values are:
• EUR—Euro
• USD—U.S. Dollar
The default value is EUR.
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The most recent date on which a user referenced this record.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The most recent date on which a user viewed this record.
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
The auto-generated name of the rebate member claim aggregate.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
The ID of the rebate member claim aggregate record owner.

Rebate Management RebateMemberClaimAggregate
Field Details
This field is a polymorphic relationship field.
Relationship Name
Owner
Relationship Type
Lookup
Refers To
Group, User
PriceType
Type
Picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update.
Description
Specifies the basis on which the product was sold in a rebate claim. Used to distinguish
between standard and contract pricing strategies when calculating rebate eligibility.
ProductId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The product for which the rebate claim was made.
This field is a relationship field.
Relationship Name
Product
Relationship Type
Lookup
Refers To
Product2
RebateProgramMemberId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The rebate program member for whom the claim was made.
This field is a relationship field.
Relationship Name
RebateProgramMember
Relationship Type
Lookup

Rebate Management RebateMemberProductAggregate
Field Details
Refers To
RebateProgramMember
TotalClaimedAmount
Type
currency
Properties
Create, Filter, Sort, Update
Description
The total amount that's already claimed.
TotalClaimedQuantity
Type
double
Properties
Create, Filter, Sort, Update
Description
The total product quantity that's already claimed.
RebateMemberProductAggregate
Stores the post calculation summary of journal transactions by member, period, and rebate type. For example, ABC enterprises for May
2021 against Vol Rebate on Radius category, did a total quantity of 150 units and transaction amount of $80,000. This object is available
in API version 65.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AggregateReferenceNumber
Type
string
Properties
Create, Filter, Group, idLookup, Nillable, Sort, Update
Description
A unique reference number of the aggregate record that’s assigned by the Data Processing
Engine when generating Rebate Program Member Aggregate records. This reference number
can be used to relate Rebate Member Aggregate Item records to the aggregate record.
Available in API version 54.0 and later.

Rebate Management RebateMemberProductAggregate
Field Details
GrowthAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The difference between the total amount and the prior amount in the rebate aggregate.
GrowthAmountPercent
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The difference between the total amount and the prior amount in percentage in the rebate
aggregate.
GrowthQuantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The difference between the total quantity and the previous quantity in the transaction journal
associated with the rebate aggregate.
GrowthQuantityPercent
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The quantity growth in percentage.
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the current user last accessed this record indirectly, for example, through
a list view or related record.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort

Rebate Management RebateMemberProductAggregate
Field Details
Description
The timestamp when the current user last viewed this record or list view. If this value is null,
and LastReferenceDate is not null, the user accessed this record or list view indirectly.
Name
Type
string
Properties
Autonumber, Defaulted on create, Filter, idLookup, Sort
Description
Name of the rebate member product aggregate.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
ID of the owner of this object.
This field is a polymorphic relationship field.
Relationship Name
Owner
Relationship Type
Lookup
Refers To
Group, User
PriorTotalQuantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The quantity in the corresponding payout period of the previous rebate cycle.
PriorTotalTransactionAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The total transaction amount corresponding to the prior period.
ProductId
Type
reference

Rebate Management RebateMemberProductAggregate
Field Details
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The product associated with the rebate aggregation.
ProgramRebateTypeId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The program rebate type associated with the rebate aggregation.
RebatePayoutStatus
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The status of the aggregate rebate payout to the member.
Possible values are:
• Error
• InProgress
• Success
The default value is InProgress.
RebatePayoutStatusMessage
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The status message of the aggregate rebate payout to the member.
RebateProgramMemberId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The rebate program member associated with the rebate aggregation.
RebateProgramPayoutPeriodId
Type
reference

Rebate Management RebateMemberProductAggregate
Field Details
Properties
Create, Filter, Group, Sort, Update
Description
The rebate program payout period associated with the rebate aggregation.
RollupProgramMemberId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The immediate parent account in the hierarchy of the account (rebate program member)
associated with the product aggregate. This field is available in API version 52.0 and later.
This is a relationship field.
Relationship Name
RollupProgramMember
Relationship Type
Lookup
Refers To
RebateProgramMember
TotalQuantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The sum of values in transaction journal quantity fields associated with the rebate aggregation.
TotalTransactionAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The sum of values in transaction journal transaction amount fields associated with the rebate
aggregation.
TransactionJournalId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The transaction journal associated with the program rebate type.

Rebate Management RebatePartnerSpecialPrcTrm
RebatePartnerSpecialPrcTrm
Represents information about the special pricing term for a ship and debit program. This object is available in API version 58.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The currency ISO code associated with the record. This is available when multiple currencies
are enabled.
Possible values are:
• EUR—Euro
• USD—U.S. Dollar
The default value is EUR.
Discount
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The agreed discount for a product unit between the manufacturer and the distributor as
part of the special pricing terms for a ship and debit program. Between
ReferencePricePerUnit and Discount, only one field can be added or used.
IsDiscountByPercent
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether the discount is given by percentage (true) or amount (false).
The default value is false.
LastReferencedDate
Type
dateTime

Rebate Management RebatePartnerSpecialPrcTrm
Field Details
Properties
Filter, Nillable, Sort
Description
The most recent date on which a user referenced this record.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The most recent date on which a user viewed this record.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
The user-defined name of the rebate partner special pricing term.
OwnerId
Type
reference
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
The ID of the rebate partner special pricing term.
This field is a polymorphic relationship field.
Relationship Name
Owner
Relationship Type
Lookup
Refers To
Group, User
ProductId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The product associated with the rebate partner special pricing term.
This field is a relationship field.

Rebate Management RebatePartnerSpecialPrcTrm
Field Details
Relationship Name
Product
Relationship Type
Lookup
Refers To
Product2
ProductQtyUnitOfMeasureId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The unit of measure associated with the product quantity.
This field is a relationship field.
Relationship Name
ProductQtyUnitOfMeasure
Relationship Type
Lookup
Refers To
UnitOfMeasure
ProductQuantity
Type
double
Properties
Create, Filter, Sort, Update
Description
The threshold quantity for a product agreed between the manufacturer and the distributor
as part of the special pricing terms for a ship and debit program.
RebateProgramMemberId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The rebate program member associated with the rebate partner special pricing term.
This field is a relationship field.
Relationship Name
RebateProgramMember
Relationship Type
Lookup

Rebate Management RebatePayment
Field Details
Refers To
RebateProgramMember
ReferencePricePerUnit
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The price of a product unit that’s agreed upon between the manufacturer and the distributor
as part of the special pricing term. Between ReferencePricePerUnit and Discount, only one
field can be added or used.
SalePricePerUnit
Type
currency
Properties
Create, Filter, Sort, Update
Description
The actual price of each unit of the product that's sold to the partner by the manufacturer.
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The status of the rebate partner special pricing term.
Possible values are:
• Active
• Draft
• Inactive
The default value is Draft.
RebatePayment
Tracks if the payment has been generated for this member for back end processing. This object is available in API version 51.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()

Rebate Management RebatePayoutAdjustment
Fields
Field Details
Amount
Type
currency
Properties
Create, Filter, Sort, Update
Description
Amount to be paid out.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Name of the rebate program.
PaymentDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Date when payment is issued.
Status
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Status of the payout.
Possible values are:
• Generated
• Paid
• Rejected
RebatePayoutAdjustment
Rebate amount adjustment that needs to be given manually. An adjustment is an amount added or subtracted to the calculated rebate
amount. This object is available in API version 51.0 and later.

Rebate Management RebatePayoutAdjustment
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AdjustmentAmount
Type
currency
Properties
Create, Filter, Sort, Update
Description
Value of the adjustment.
ApprovedDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Approved date of the adjustment.
Comments
Type
string
Properties
Create, Filter, Group, Sort, Update
Description
Notes for adjustment.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Name of the rebate program.
RebateProgramMemberPayoutId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Rebate program member payout identifier.

Rebate Management RebateProgram
Field Details
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Status of adjustment.
Possible values are:
• Approved
• InReview—Under Review
• Rejected
RebateProgram
The rebate program your organization runs with a single account, all accounts, or specific list of accounts. This object is available in API
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
Description
Type
textarea
Properties
Create, Filter, Nillable, Sort, Update
Description
The description of the rebate program.
EndDate
Type
date
Properties
Create, Filter, Group, Sort, Update
Description
The end date of the rebate program.
Frequency
Type
picklist

Rebate Management RebateProgram
Field Details
Properties
Create, Filter, Group, Restricted picklist, Sort, Update
Description
The frequency of rebate program.
Possible values are:
• Annually
• Biannually
• CustomPeriods
• Monthly
• OnDemand
• ProgramStartAndEndDate
• Quarterly
GracePeriodDayCount
Type
int
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Number of days from end date of an instance of a payout period. Transactions submitted
until this day are considered for rebate calculation. For example, a value of 5 implies that
channel partners can submit transactions for a monthly period before the 5th of the next
month. This isn’t enforced in the system but can be used as information for channel partners.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Name of the rebate program.
PayoutCalculationDayCount
Type
int
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Number of days from period end date. The payment will be calculated after this date. For
example, a payout calculation day count of 14 means 14 days after period end date.
ProgramReferenceNumber
Type
string

Rebate Management RebateProgram
Field Details
Properties
Create, Filter, Group, idLookup, Nillable, Sort, Update
Description
The reference number assigned to this rebate program. This field is unique within your
organization. This field is available in API version 52.0 and later.
RebateProgramUrl
Type
url
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
URL of the rebate program.
StartDate
Type
date
Properties
Create, Filter, Group, Sort, Update
Description
Start date of rebate program.
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Possible states of rebate program.
Possible values are:
• Active
• Draft
• Inactive
Type
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The type of the rebate program. Available in API version 58.0 and later.
Possible values are:
• ShipAndDebit
• Standard

Rebate Management RebateProgramMember
Field Details
The default value is Standard.
RebateProgramMember
The member of a rebate program. By virtue of being a member, the partner or business account is eligible to get rebate payments. For
example, ABC Enterprises and HVAC Corp are members of GoldStone Volume Rebate Program. This object is available in API version 51.0
and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccountId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
Unique identifier for the account who’s a member of the program.
CumulativePayoutAmount
Type
currency
Properties
Filter, Nillable, Sort
Description
Total rebate amount for a member. Sum of Total Payout Amount values from
RebateProgramMemberPayout object that are not rejected.
This is a calculated field.
IsPayoutCalcSkipped
Type
boolean
Properties
Description
Specifies whether the rebate payout calculation should be skipped for the rebate program
member. This field is available in API version 52.0 and later.
LastActivationDate
Type
date

Rebate Management RebateProgramMember
Field Details
Properties
Filter, Group, Nillable, Sort
Description
The latest date on which the program member was activated.
LastDeactivationDate
Type
date
Properties
Filter, Group, Nillable, Sort
Description
The latest date on which the program member was deactivated.
MemberStatus
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Status of membership.
Possible values are:
• Active
• Inactive
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Name of the member.
RebateProgramId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
Reference to rebate program identifier.
ShipToAccountId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update

Rebate Management RebateProgramMemberPayout
Field Details
Description
The ship to account. Use this when the rebate is applicable only when the member ships to
this account. This field is available in API version 52.0 and later.
This is a relationship field.
Relationship Name
ShipToAccount
Relationship Type
Lookup
Refers To
Account
RebateProgramMemberPayout
The payout calculated for a member for the period. For example, $1000 Jan'21 payout for ABC enterprises. This object is available in API
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
AccruedAmount
Type
currency
Properties
Filter, Nillable, Sort
Description
The payout amount accrued by the rebate program member.
This is a calculated field.
CalculatedRebateAmount
Type
currency
Properties
Filter, Nillable, Sort
Description
Total amount calculated.
This is a calculated field.

Rebate Management RebateProgramMemberPayout
Field Details
CalculationDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Date on which the calculation happened.
MemberId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Program member ID.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Name of the rebate program.
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Status of payout.
Possible values are:
• Approved
• Interim—Calculation In progress.
• Pending—Under review.
• Rejected
• SystemCalculated—Calculated.
TotalApprovedAdjustmentAmount
Type
currency
Properties
Filter, Nillable, Sort
Description
Summarized payout adjustment amount.

Rebate Management RebateProgramPayoutPeriod
Field Details
This is a calculated field.
TotalRebateAmount
Type
currency
Properties
Filter, Nillable, Sort
Description
Summarized payout amount.
This is a calculated field.
RebateProgramPayoutPeriod
The period of the payout calculation. For example, 1st to 31st Jan, or 1st Dec to 14th Dec. This object is available in API version 51.0 and
later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
EndDate
Type
date
Properties
Create, Filter, Group, Sort, Update
Description
End date of the period. The system picks transactions between start date and end date of
the period for rebate calculations.
LastCalculationDate
Type
date
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Last date on which the rebate amount calculation for that period for all the relevant aggregate
records was completed successfully.
MemberPayoutCount
Type
int

Rebate Management RebateProgramPayoutPeriod
Field Details
Properties
Filter, Group, Nillable, Sort
Description
Used to track total number of payouts that happened in a period for a particular rebate
program.
PayoutCalculationDate
Type
date
Properties
Create, Filter, Group, Sort, Update
Description
Date on or after which the payout calculation for this period is set to Closed.
RebateProgramId
Type
reference
Properties
Create, Filter, Group, Sort
Description
Rebate program identifier.
StartDate
Type
date
Properties
Create, Filter, Group, Sort, Update
Description
Start date of the period.
Status
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Restricted picklist, Sort, Update
Description
Used to track if a payout period is active or inactive.
Possible values are:
• Active
• Closed
• Inactive
TotalApprovedAmount
Type
currency

Rebate Management RebatePtnrSpclPrcTrmBnft
Field Details
Properties
Filter, Nillable, Sort
Description
Total approved member payout amount.
TotalRejectedAmount
Type
currency
Properties
Filter, Nillable, Sort
Description
Total rejected amount.
TransactionGracePeriodDate
Type
date
Properties
Create, Filter, Group, Sort, Update
Description
Cut-off date before which the transactions are accepted for the period.
RebatePtnrSpclPrcTrmBnft
Represents information about the benefit tier in a rebate partner special pricing term. This object is available in API version 58.0 and
later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
CurrencyIsoCode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The currency ISO code associated with the record. This is available when multiple currencies
are enabled.
Possible values are:

Rebate Management RebatePtnrSpclPrcTrmBnft
Field Details
• EUR—Euro
• USD—U.S. Dollar
The default value is EUR.
Discount
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The discount that's applicable for the rebate partner special pricing term benefit.
EffectiveEndDate
Type
dateTime
Properties
Create, Filter, Nillable, Sort, Update
Description
The date until when the rebate partner special pricing term benefit is effective.
EffectiveStartDate
Type
dateTime
Properties
Create, Filter, Nillable, Sort, Update
Description
The date from when the rebate partner special pricing term benefit is effective.
IsDiscountByPercent
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether the discount is given by percentage (true) or amount (false).
The default value is false.
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The most recent date on which a user referenced this record.

Rebate Management RebatePtnrSpclPrcTrmBnft
Field Details
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The most recent date on which a user viewed this record.
MaximumQuantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The maximum quantity of product sold that is eligible for the rebate partner special pricing
term benefit.
MinimumQuantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The minimum quantity of product sold that is eligible for the rebate partner special pricing
term benefit.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
The name of the rebate partner special pricing term benefit.
RebatePartnerSpecialPrcTrmId
Type
reference
Properties
Create, Filter, Group, Sort
Description
The rebate partner special pricing term that's associated with the rebate partner special
pricing term benefit.
This field is a relationship field.
Relationship Name
RebatePartnerSpecialPrcTrm

Rebate Management ReceivedDocument
Field Details
Relationship Type
Lookup
Refers To
RebatePartnerSpecialPrcTrm
ReferencePricePerUnit
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The reference price per unit that’s applicable for the rebate partner special pricing term
benefit.
ReceivedDocument
Allows partners to upload .CSV document. This object is available in API version 51.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
FailedRecordsFileId
Type
reference
Properties
Filter, Group, Nillable, Sort, Update
Description
Lookup to the error file.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
The name of the received document.
Status
Type
picklist

Rebate Management TransactionJournal
Field Details
Properties
Create, Filter, Group, Restricted picklist, Sort, Update
Description
Current stage of processing.
Possible values are:
• APPROVED—Approved
• ARCHIVED—Archived
• DRAFT—Draft
• IN_REVIEW—In Review
• OBSOLETE—Obsolete
• SUBMITTED—Submitted
• SUPERSEDED—Superseded
UnprocessedRecordsFileId
Type
reference
Properties
Filter, Group, Nillable, Sort, Update
Description
Lookup to the skipped file.
TransactionJournal
The transactions that need to be processed for a rebate program. For example, order line for 1000 units of $1200 for member ABC
enterprises. This object is available in API version 51.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), undelete(), update(), upsert()
Fields
Field Details
AccountId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The account for which the transaction is made.

Rebate Management TransactionJournal
Field Details
This is a relationship field.
Relationship Name
Account
Relationship Type
Lookup
Refers To
Account
ActivityDate
Type
dateTime
Properties
Create, Filter, Sort, Update
Description
Date the transaction happened.
ErrorDescription
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
Description of the error in the journal record.
JournalDate
Type
dateTime
Properties
Create, Filter, Nillable, Sort, Update
Description
Date the transaction was received.
MemberId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
Polymorphic key to RebateProgramMember or LoyaltyMember.
ProductId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update

Rebate Management TransactionJournal
Field Details
Description
The product associated with the transaction.
Quantity
Type
double
Properties
Create, Filter, Nillable, Sort, Update
Description
The order quantity.
QuantityUnitOfMeasureId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The unit of measure associated with the record.
This is a relationship field.
Relationship Name
QuantityUnitOfMeasure
Relationship Type
Lookup
Refers To
UnitOfMeasure
RebatePgmReferenceNumber
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The reference number of the rebate program. This field is available in API version 52.0 and
later.
ShipToAccountId
Type
reference
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The account for which the additional benefit is being offered for ship and debit program.
This field is available in API version 52.0 and later.
This is a relationship field.

Rebate Management UnitOfMeasureConversion
Field Details
Relationship Name
ShipToAccount
Relationship Type
Lookup
Refers To
Account
TransactionAmount
Type
currency
Properties
Create, Filter, Nillable, Sort, Update
Description
The total amount of the transaction.
UsageType
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort
Description
Type of journal record.
Possible values are:
• Loyalty
• Rebates
UnitOfMeasureConversion
Represents the information used to convert a measurement value from a unit of measure to another. This object is available in API version
52.0 and later.
Supported Calls
create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(), search(), undelete(), update(), upsert()
Fields
Field Details
ConversionFactor
Type
double

Rebate Management UnitOfMeasureConversion
Field Details
Properties
Create, Filter, Sort, Update
Description
The conversion factor for the conversion.
FromUnitOfMeasureId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The unit of measure to be converted.
This is a relationship field.
Relationship Name
FromUnitOfMeasure
Relationship Type
Lookup
Refers To
UnitOfMeasure
ToUnitOfMeasureId
Type
reference
Properties
Create, Filter, Group, Sort, Update
Description
The unit of measure to be converted to.
This is a relationship field.
Relationship Name
ToUnitOfMeasure
Relationship Type
Lookup
Refers To
UnitOfMeasure
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
UnitOfMeasureConversionFeed
Feed tracking is available for the object.

Rebate Management Rebate Management Standard Invocable Actions
UnitOfMeasureConversionHistory
History is available for tracked fields of the object.
UnitOfMeasureConversionOwnerSharingRule
Sharing rules are available for the object.
UnitOfMeasureConversionShare
Sharing is available for the object.
Rebate Management Standard Invocable Actions
Add members to a rebate program, calculate rebate amounts and upsert payouts, generate rebate payout periods, process rebate
calculation batch jobs, and process a rebate CSV file for Rebate Management. For more information on standard invocable actions, see
REST API Developer Guide and Actions Developer Guide.
Add Rebate Member List
Add a list of members to a rebate program. The list of rebate members is based on the accounts in the specified account list view.
Calculate Rebate Amount and Upsert Payout
Calculate the rebate amount and upsert the rebate payout for the specified aggregate record.
Calculate Projected Rebate Amount
Calculate the projected rebate amount for rebate types associated with a specified transaction reference ID.
Generate Rebate Payout Periods
Generate payout periods for a rebate program based on the frequency specified in the program.
Get Benefit and Calculate Rebate Amount
Get the details benefits and optionally calculate the rebate amount for the specified aggregate record.
Get Eligible Program Rebate Types
Retrieve the eligible program rebate types for a mapped object.
Process Program Rebate Type Products
Insert or delete the records in the Program Rebate Type Product object. The inserted products participate as inclusion or exclusion
as defined in the Product Filter Type option on Program Rebate Type.
Process Rebate Batch Calculation Jobs
Process a rebate batch calculation job from the Data Processing Engine.
Process Rebate CSV Files
Process an uploaded CSV file using Bulk API 2.0 and convert the file’s data into records in the target object.
Upsert Custom Rebate Payout
Upsert the custom calculated rebate payout for a specified aggregate record.
Add Rebate Member List
Add a list of members to a rebate program. The list of rebate members is based on the accounts in the specified account list view.
This object is available in API version 51.0 and later for users with Rebate Management license.

Rebate Management Add Rebate Member List
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/standard/addRebateMemberList
Formats
JSON, XML
HTTP Methods
GET, HEAD, POST
Authentication
Authorization: Bearer token
Inputs
Input Details
listViewId
Type
string
Description
Required. The ID of the account list that’s specified to add rebate members.
notificationPreference
Type
string
Description
A text value that indicates whether notifications should be sent for successful and unsuccessful
rebate member additions. Valid values include BlockSuccessEmails, BlockFailureEmails,
BlockAllEmails, and AllowAllNotifications.
rebateProgramId
Type
string
Description
Required. The ID of the rebate program to which specified account list view is added.
status
Type
string
Description
Required. The status of the rebate members for the accounts in the specified list view.
Usage
Sample Request
{
"inputs":[{
"listViewId":"a07B0000007qbQOIAY",
"rebateProgramId":"x18Z1236547qbQOBCV",

Rebate Management Calculate Rebate Amount and Upsert Payout
"status": "Active"
"notificationPreference": "BlockAllEmails"
}]
}
Sample Response
{
"isSuccess":true
}
Calculate Rebate Amount and Upsert Payout
Calculate the rebate amount and upsert the rebate payout for the specified aggregate record.
This object is available in API version 51.0 and later for users with Rebate Management license.
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/standard/calculateRebateAmountAndUpsertPayout
Formats
JSON, XML
HTTP Methods
GET, HEAD, POST
Authentication
Authorization: Bearer token
Inputs
Input Details
aggregateId
Type
ID
Description
Required. The ID of the aggregate record for which you want to calculate the rebate amount
and upsert the rebate payout.
payoutMemberFieldName
Type
String
Description
The name of the field that contains the rebate program member ID for which to perform the
payout calculations.

Rebate Management Calculate Projected Rebate Amount
Outputs
Output Details
programRebateTypePayoutSourceId
Type
ID
Description
The ID of the program rebate type payout source record, which is generated if the request is
successful.
Usage
Sample Request
{
"inputs":[
{"aggregateId":"a00xx000000cCtxAAE"},
{"aggregateId":"a00xx000000cCvZAAU"},
{"aggregateId":"a00xx000000cCxBAAU"}
]
}
Sample Response
{
"errors":null,
"isSuccess":true,
"outputValues":{
"programRebateTypePayoutSourceId":"0ntxx00004000002AAA"
}
}
Calculate Projected Rebate Amount
Calculate the projected rebate amount for rebate types associated with a specified transaction reference ID.
This object is available in API version 54.0 and later.
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/standard/calculateProjectedRebateAmount
Formats
JSON
HTTP Methods
POST
Authentication
Authorization: Bearer token

Rebate Management Calculate Projected Rebate Amount
Inputs
Input Details
programRebateTypeIds
Type
string
Description
Required. The list of program rebate type IDs to calculate the projected rebate amounts for.
referenceRecordId
Type
string
Description
Required. The transaction reference record ID to calculate the projected rebate amounts for.
Outputs
Output Details
calculateProjectedRebateAmount
Type
string
Description
The calculated rebate amount details for the program rebate types associated with the transaction
reference record.
This is an Apex output type that contains nested arrays in JSON format.
calculateProjectedRebateAmount contains an array of the
CalculateProjectedRebateAmountOutputRepresentation Apex class. This
output representation contains an array of the ProjectedRebateAmountCalc fields,
while an array of DetailedProjectedRebateAmountCalc is contained in
ProjectedRebateAmountCalc.
Note: The fields aggregateId, benefitQualifierValue, benefitTier, measureFieldValue,
qualifiedTiers, rebateTypeBenefit, totalProjectedRebateAmount, payoutPeriod,
projectedRebateAmount can appear in the output list. These fields must be ignored because they aren't supported in
the flow for this invocable action. These fields will be deprecated in API version 55.0.
Usage
JSON Sample Request
{
"inputs":[ {
"programRebateTypeIds": ["0hvRM0000004CUt"],
"referenceRecordId": "801RM00000083TeYAI"
} ]
}

Rebate Management Calculate Projected Rebate Amount
JSON Sample Response
{
"projectedRebateAmountCalc": [
{
"programRebateTypeId": "0hvRM0000004CUt",
"referenceRecordId": "801RM00000083TeYAI",
"totalProjectedRebateAmount": 1088000,
"detailedProjectedRebateAmountCalc": [
{
"benefitQualifierValue": 500,
"benefitTier": "0huRM0000004CRC",
"rebateTypeBenefit": "5",
"measureFieldValue": 160000,
"payoutPeriod": "0i7RM0000004CV7",
"projectedRebateAmount": 800000,
"qualifiedTiers": [
"0huRM0000004CRC"
]
},
{
"benefitQualifierValue": 240,
"benefitTier": "0huRM0000004CRC",
"rebateTypeBenefit": "5",
"measureFieldValue": 57600,
"payoutPeriod": "0i7RM0000004CV7",
"projectedRebateAmount": 288000,
"qualifiedTiers": [
"0huRM0000004CRC"
]
}
]
}
]
}
Details of the Apex output type
• projectedRebateAmountCalc—An array of projected rebate amounts. Each item specifies the projected rebate amount
for a passed rebate type and the reference object.
– programRebateTypeId—Specifies the program rebate type ID whose projected rebate amounts are calculated in this
item.
– referenceRecordId—Specifies the transaction reference record ID based on which the projected rebate amounts are
calculated.
– totalProjectedRebateAmount—Specifies the total projected rebate amount for this program rebate type and reference
record.
– detailedProjectedRebateAmountCalc—An array with each item corresponding to each aggregate record that is
found for a combination of rebate type and reference object. For example, if the rebate is computed differently for every product
using a benefit mapping and the reference object (order) has two order lines, this collection has two aggregates, one for each
product.
• benefitQualifierValue—Specifies the total benefit qualifier value calculated from both the aggregate record and
the reference object.

Rebate Management Generate Rebate Payout Periods
• benefitTier—Specifies the benefit tier ID that is determined based on the benefit qualifier value.
• rebateTypeBenefit—Specifies the applied benefit that is granted based on the benefit tier identified.
• measureFieldValue—Specifies the total measure value calculated from both the aggregate record and the reference
object.
• payoutPeriod—Specifies the rebate program payout period that is determined based on the mapped member ID and
activity date. The mapping between reference object and transaction journal is used here. See Map Fields Between Target
Transaction Object and Transaction Journal.
• projectedRebateAmount—Specifies the calculated projected rebate amount based on the benefit tier and the
measure field value.
• qualifiedTiers—List of the eligible benefit tiers that have already been met.
Usage
You must configure the output parameter for the Calculate Projected Rebate Amount Flow Action in Flow Builder. The following screen
illustrates how to use the output parameter in the Flow Builder.
Generate Rebate Payout Periods
Generate payout periods for a rebate program based on the frequency specified in the program.
This object is available in API version 51.0 and later for users with Rebate Management license.
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/standard/generateRebatePayoutPeriods
Formats
JSON, XML

Rebate Management Generate Rebate Payout Periods
HTTP Methods
GET, HEAD, POST
Authentication
Authorization: Bearer token
Inputs
Input Details
rebateProgramId
Type
ID
Description
Required. The ID of the rebate program record for which you want to generate payout periods.
Outputs
Output Details
rebateProgramPayoutPeriods
Type
string
Description
The list of rebate program payout period IDs upserted if the request is successful.
Usage
Sample Request
{
"inputs":[{"rebateProgramId":"0lcxx00004000002AAA"},
{"rebateProgramId":"0lcxx00004000002AAA"}
]
}
Sample Response
{
"errors":null,
"isSuccess":true,
"RebateProgramPayoutPeriodIds":["0ntxx00004000002AAA","0ntxx00004000002AAB"]
},{
"errors":null,
"isSuccess":true,
"RebateProgramPayoutPeriodIds":["0ntxx00004000002AAA","0ntxx00004000002AAB"]
}

Rebate Management Get Benefit and Calculate Rebate Amount
Get Benefit and Calculate Rebate Amount
Get the details benefits and optionally calculate the rebate amount for the specified aggregate record.
This object is available in API version 51.0 and later for users with Rebate Management license.
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/standard/getBenefitAndCalculateRebateAmount
Formats
JSON, XML
HTTP Methods
GET, HEAD, POST
Authentication
Authorization: Bearer token
Inputs
Input Details
aggregateId
Type
ID
Description
Required. The ID of the aggregate record for which you want to calculate the rebate amount.
payoutMemberFieldName
Type
ID
Description
The name of the field that contains the rebate program member ID for which to perform the
payout calculations.
skipRebateCalc
Type
Boolean
Description
Indicates whether to skip calculation of the rebate amount.
Outputs
Output Details
accuralRate
Type
Double

Rebate Management Get Benefit and Calculate Rebate Amount
Output Details
Description
The accrual rate if the request is successful.
accruedAmount
Type
Double
Description
The accrued amount calculated if the request is successful.
aggregateId
Type
ID
Description
The ID of the aggregate record for which you want to calculate the rebate amount.
benefitId
Type
ID
Description
The ID of the applied Program Rebate Type Benefit record if the request is successful.
payoutMemberFieldName
Type
String
Description
The name of the field that contains the rebate program member ID for which to perform the
payout calculations.
qualifyingBenefits
Type
string
Description
The comma-separated list of IDs of the qualified Program Rebate Type Benefit records if the
request is successful.
rebateAmount
Type
double
Description
The rebate amount calculated if the request is successful.
Usage
Sample Request
{
"inputs":[
{"AggregateId": "a00xx000000cCtxAAE",
"SkipRebateCalc": false},

Rebate Management Get Eligible Program Rebate Types
{"AggregateId": "a00xx000000cCvZAAU",
"SkipRebateCalc": false},
{"AggregateId": "a00xx000000cCxBAAU",
"SkipRebateCalc": false}
]
}
Sample Response
{
"errors":null,
"isSuccess":true,
"outputValues":{
"AggregateId":"0ntxx00004000002AAA",
"BenefitId":"0ntxx00004000002AAA",
"RebateAmount":"2000"
}
}
Get Eligible Program Rebate Types
Retrieve the eligible program rebate types for a mapped object.
For more information about how to use the getEligibleProgramRebateTypes action in Flow Builder, see Configure the
Output Parameter for the Get Eligible Program Rebate Types Flow Action in Flow Builder in Salesforce Help.
This object is available in API version 52.0 and later.
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/standard/getEligibleProgramRebateTypes
Formats
JSON
HTTP Methods
POST
Authentication
Authorization: Bearer token
Inputs
Input Details
appliedRebateTypesLimit
Type
integer
Description
The maximum number of search results to be returned for the applied rebate types. The input
value is passed through to the output parameter.
This field is available in API version 54.0 and later.

Rebate Management Get Eligible Program Rebate Types
Input Details
appliedRebateTypesOffset
Type
Input
integer
Description
The input offset for the applied rebate types search results plus the number of applied rebates
types processed. Used to process applied rebate types in a loop. When all applied rebate types
have been processed, zero is returned.
This field is available in API version 54.0 and later.
limit
Type
integer
Description
The maximum number of search results to be returned for the eligible rebate types.
measureTypeFilter
Type
array
Description
Filters the eligible rebate types by the specified measure type.
offset
Type
integer
Description
The offset for the eligible rebate types search results. The offset parameter specifies the end of
the last batch retrieved. For example, to retrieve 100 rebate types at a time:
• Request the first 100 with an offset of 0.
• Request the second 100 with an offset of 100.
• Request the third 100 with an offset of 200.
queryOnlyIntegrableProgram
Type
RebateTypes
boolean
Description
Indicates whether only integrable program rebate types must be queried.
referenceObjectIds
Type
array
Description
Required. The list of IDs of the mapped object for which to get the eligible rebate types.
searchByRebateTypeName
Type
string
Description
Searches the eligible rebate types by the specified name.

Rebate Management Get Eligible Program Rebate Types
Outputs
Output Details
resultantRebateTypes
Type
string
Description
The list of eligible and applied rebate type IDs for the mapped object. Use with API calls.
resultantRebateTypes
Type
ForFlow
string
Description
The list of eligible and applied rebate type IDs for the mapped object. Use with Flow Builder. This
field is available in API version 54.0 and later.
Usage
JSON Sample Request
{
"inputs":[{
"referenceObjectIds":["0lcxx00004000002AAA","0lcxx00004000002AAB"],
"queryOnlyIntegratableProgramRebateTypes": true,
"limit": 10,
"offset": 5
}]
}
JSON Sample Response
{
resultantRebateTypes: {
"isSuccess":true,
"programRebateTypeIDs":[
{ReferenceObjectID: "0lcxx00004000002AAA", eligibleRebateTypes:
[0lcxx00004000003AAA,0lcxx00004000003AAB], appliedRebateTypes:
[0lcxx00004000004AAA,0lcxx00004000004AAB]},
{ReferenceObjectID: "0lcxx00004000002AAB", eligibleRebateTypes:
[0lcxx00004000003AAC,0lcxx00004000003AAD], appliedRebateTypes:
[0lcxx00004000005AAA,0lcxx00004000005AAB]}
],
"limit": 10,
"offset": 13,
"appliedRebateTypesLimit": 5,
"appliedRebateTypesOffset" 9,
"errors":null
},
resultantRebateTypesV2:{
"isSuccess":true,
"programRebateTypeIDs":[
{ReferenceObjectID: "0lcxx00004000002AAA", eligibleRebateTypes:

Rebate Management Process Program Rebate Type Products
[0lcxx00004000003AAA,0lcxx00004000003AAB], appliedRebateTypes:
[0lcxx00004000004AAA,0lcxx00004000004AAB]},
{ReferenceObjectID: "0lcxx00004000002AAB", eligibleRebateTypes:
[0lcxx00004000003AAC,0lcxx00004000003AAD], appliedRebateTypes:
[0lcxx00004000005AAA,0lcxx00004000005AAB]}
],
"limit": 10,
"offset": 13,
"appliedRebateTypesLimit": 5,
"appliedRebateTypesOffset": 9,
"errors":null
}
}
Process Program Rebate Type Products
Insert or delete the records in the Program Rebate Type Product object. The inserted products participate as inclusion or exclusion as
defined in the Product Filter Type option on Program Rebate Type.
For more information about how the processProgramRebateTypeProducts action inserts or deletes records, see Create Payout Calculation
Flows with Flow Actions in Salesforce Help.
This object is available in API version 53.0 and later.
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/standard/processProgramRebateTypeProducts
Formats
JSON
HTTP Methods
POST
Authentication
Authorization: Bearer token
Inputs
Input Details
operationType
Type
string
Description
Required. The type of operation to be performed on the program rebate type product records.
Possible values are:
• Delete—Deletes all program rebate type products for the specified program rebate type
ID.
• Insert—Inserts all products as program rebate type products, preserves the existing ones.

Rebate Management Process Rebate Batch Calculation Jobs
Input Details
productListViewId
Type
string
Description
The ID of the product list view containing the products to be added to the inclusion or exclusion
list of this program rebate type.
Note: This field isn’t used when the type of operation is Delete.
programRebateTypeId
Type
string
Description
Required. The ID of the program rebate type for which the records are being processed.
Usage
JSON Sample Request
{
"inputs":[{
"operationType" : "insert",
"productListViewId": "00BHr00000Q6zqNMAR",
"programRebateTypeId": "0hvHr000000HDQQIA4"
}]
}
Process Rebate Batch Calculation Jobs
Process a rebate batch calculation job from the Data Processing Engine.
This object is available in API version 51.0 and later for users with Rebate Management license.
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/standard/processRebatesBatchCalculationJob
Formats
JSON, XML
HTTP Methods
GET, HEAD, POST
Authentication
Authorization: Bearer token

Rebate Management Process Rebate Batch Calculation Jobs
Inputs
Input Details
calcDefinitionId
Type
ID
Description
Required. The ID of the data processing engine definition record that you want to process.
rebateProgramIds
Type
array
Description
The list of IDs of the rebate program records that the custom batch calculation job processes.
programRebateTypeIds
Type
array
Description
The list of IDs of the program rebate type records that the custom batch calculation job processes.
rebateProgramPayoutPeriodIds
Type
array
Description
The list of IDs of the rebate program payout period records that the custom batch calculation
job processes.
rebateProgramMemberIds
Type
array
Description
The list of IDs of the rebate program member records that the custom batch calculation job
processes.
Outputs
Output Details
batchJobId
Type
ID
Description
The ID of the generated batch job record after the request is successful.
accepted
Type
boolean

Rebate Management Process Rebate CSV Files
Output Details
Description
Indicates whether the rebate batch calculation job is accepted.
Usage
Sample Request
{
"inputs":[{
"calcDefinitionId": "0lcxx00004000002AAA",
"rebateProgramIds": ["0htxx00004000002AAA","0htxx00004000002bAA"],
"programRebateTypeIds": ["0htxx00004000002AAA","0htxx00004000002bAA"],
"rebateProgramPayoutPeriodIds": ["0htxx00004000002AAA","0htxx00004000002bAA"],
"rebateProgramMemberIds": ["0htxx00004000002AAA","0htxx00004000002bAA"]
}]
}
Sample Response
{
"errors":null,
"isSuccess":true,
"outputValues":{
"batchJobId":"0ntxx00004000002AAA",
}
}
Process Rebate CSV Files
Process an uploaded CSV file using Bulk API 2.0 and convert the file’s data into records in the target object.
This object is available in API version 51.0 and later for users with Rebate Management license.
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/standard/rebatesProcessCSV
Formats
JSON, XML
HTTP Methods
GET, HEAD, POST
Authentication
Authorization: Bearer token

Rebate Management Upsert Custom Rebate Payout
Inputs
Input Details
recordId
Type
ID
Description
Required. The ID of the received document record that includes the CSV file to be converted.
entityAPIName
Type
string
Description
Required. The API name of the target object that receives the processed CSV file records.
lineEnding
Type
string
Description
Optional. The line ending request header that specifies whether the line endings can be read
either as line feeds (LFs) or as line feeds (CRLFs) for fields of type Text Area and Text Area (Long).
The default value is LF.
Usage
Sample Request
{
"inputs":[{
"recordId": "0io4S000000TPsyQAG",
"entityAPIName" : "TransactionJournal"
}]
}
Sample Response
{
"errors":null,
"isSuccess":true,
}
Upsert Custom Rebate Payout
Upsert the custom calculated rebate payout for a specified aggregate record.
This object is available in API version 51.0 and later for users with Rebate Management license.

Rebate Management Upsert Custom Rebate Payout
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/standard/upsertCustomRebatePayout
Formats
JSON, XML
HTTP Methods
GET, HEAD, POST
Authentication
Authorization: Bearer token
Inputs
Input Details
accuralRate
Type
Double
Description
The accrual rate used to calculate the accrued amount for the generated program rebate type
payout source record.
accruedAmount
Type
Double
Description
The accrued amount calculated for the generated program rebate type payout source record.
aggregateId
Type
ID
Description
Required. The ID of the aggregate record for which you want to upsert the rebate payout.
benefitId
Type
ID
Description
The ID of the qualified program rebate type benefit record for which you want to upsert the
rebate payout.
payoutMemberFieldName
Type
String
Description
The name of the field that contains the rebate program member ID for which to perform the
payout calculations.
rebateAmount
Type
double

Rebate Management Rebate Management Metadata API Types
Input Details
Description
Required. The rebate amount for which you want to upsert the rebate payout.
Outputs
Output Details
programRebateTypePayoutSourceId
Type
ID
Description
The ID of the program rebate type payout source record, which is generated after the request is
successful.
Usage
Sample Request
{
"inputs":[{
"AggregateId":"0lcxx00004000002AAA",
"BenefitId":"0htxx00004000002AAA",
"RebateAmount":"2000"
}]
}
Sample Response
{
"errors":null,
"isSuccess":true,
"outputValues":{
"programRebateTypePayoutSourceId":"0ntxx00004000002AAA",
}
}
Rebate Management Metadata API Types
Metadata API enables you to access some types and feature settings that you can customize in the user interface. For more information
about Metadata API and to find a complete reference of existing metadata types, see Metadata API Developer Guide.
ObjectHierarchyRelationship
Represents an organization’s custom field mappings between a reference object and eligible rebate types. Fields can be mapped
from Opportunity, OpportunityLineItem, Quote, QuoteLineItem, and Contract to TransactionJournal.

Rebate Management ObjectHierarchyRelationship
ObjectHierarchyRelationship
Represents an organization’s custom field mappings between a reference object and eligible rebate types. Fields can be mapped from
Opportunity, OpportunityLineItem, Quote, QuoteLineItem, and Contract to TransactionJournal.
This type extends the Metadata metadata type and inherits its fullName field.
File Suffix and Directory Location
ObjectHierarchyRelationship components have the suffix ObjectHierarchyRelationship.settings and are stored in
the ObjectHierarchyRelationship folder.
Version
ObjectHierarchyRelationship components are available in API version 51.0 and later.
Fields
Field Name Description
childObjectMapping
Field Type
ObjectMapping
Description
Set of inputObject, mappingFields, and outputObject entries.
inputObjRecordsGrpFieldName
Field Type
string
Description
The field name in the input object used to group the records. This field is available
in API version 55.0 and later.
mappingType
Field Type
ObjHierarchyMappingType (enumeration of type string)
Description
Specifies the type of relationship between two objects.
Valid values are:
• ChildToChild
• ParentToChild
• ParentToParent
• Support
This field is available in API version 55.0 and later.
masterLabel
Field Type
string

Rebate Management ObjectHierarchyRelationship
Field Name Description
Description
Master label name of the mapping definition.
outputPntRelationshipFieldName
Field Type
string
Description
The field name that defines the relationship between a parent and child for the
output object. This field is available in API version 55.0 and later.
parentObjectMapping
Field Type
ObjectMapping
Description
Required.
Set of inputObject, mappingFields, and outputObject entries.
parentRecord
Field Type
string
Description
The parent record for this object hierarchy relationship. This field is available in API
parentRelationshipFieldName
Field Type
string
Description
Name of the field that defines the relationship between the parent and child.
usageType
Field Type
MappingUsageType (enumeration of type string)
Description
Required.
Name of the usage type of an object hierarchy relationship.
Valid value is:
• ConvertToSalesAgreement
• CLMFieldMapping
• EligibleProgramRebateType
• MapJournalToMemberAggregate
• TransformationMapping
ObjectMapping
Represents a set of inputObject, mappingFields, and outputObject entries.

Rebate Management ObjectHierarchyRelationship
Fields
Field Name Description
inputObject
Field Type
string
Description
Required.
Name of the input object type containing the source fields for mapping. For example,
Opportunity or OpportunityLineItem.
Note: You can also use a custom object as the input object type.
mappingFields
Field Type
ObjectMappingField
Description
Mapping of source object input fields to target object.
outputObject
Field Type
string
Description
Required.
Name of the output object type receiving data conversion. For example, TransactionJournal.
ObjectMappingField
Represents a set of inputField and outputField entries.
Fields
Field Name Field Type Description
inputField string
Field Type
string
Description
Required.
Field in the object specified by the inputObject field in ObjectMapping
on page 235. This field is mapped to the field in outputField, which
is a field in the object specified by the outputObject field in
ObjectMapping on page 235.
Note: You can also use custom fields as the input field type.

Rebate Management ObjectHierarchyRelationship
Field Name Field Type Description
outputField string
Field Type
string
Description
Required.
Field in the object specified by the outputObject field in
ObjectMapping on page 235. This field is mapped to the field name in
inputField, which is a field in the object specified by the
inputObject field in ObjectMapping on page 235.
Note: You can also use custom fields as the output field type.
Declarative Metadata Sample Definition
The following are examples of a ObjectHierarchyRelationship component.
Example of mapping between Opportunity and Transaction Journal.
<?xml version="1.0" encoding="UTF-8"?>
<ObjectHierarchyRelationship xmlns="http://soap.sforce.com/2006/04/metadata">
<parentObjectMapping>
<inputObject>Opportunity</inputObject>
<outputObject>TransactionJournal</outputObject>
<mappingFields>
<inputField>AccountId</inputField>
<outputField>MemberId</outputField>
</mappingFields>
</mappingFields>
</parentObjectMapping>
<childObjectMapping>
<inputObject>OpportunityLineItem</inputObject>
<outputObject>TransactionJournal</outputObject>
<mappingFields>
<inputField>Product2Id</inputField>
<outputField>ProductId</outputField>
</mappingFields>
<mappingFields>
<inputField>Quantity</inputField>
<outputField>Quantity</outputField>
</mappingFields>
</childObjectMapping>
<usageType>EligibleProgramRebateType</usageType>
</ObjectHierarchyRelationship>
Example of mapping between Quote and Transaction Journal.
<?xml version="1.0" encoding="UTF-8"?>
<ObjectHierarchyRelationship xmlns="http://soap.sforce.com/2006/04/metadata">
<parentObjectMapping>

Rebate Management ObjectHierarchyRelationship
<inputObject>Quote</inputObject>
<outputObject>TransactionJournal</outputObject>
<mappingFields>
<inputField>AccountId</inputField>
<outputField>MemberId</outputField>
</mappingFields>
</parentObjectMapping>
<childObjectMapping>
<inputObject>QuoteLineItem</inputObject>
<outputObject>TransactionJournal</outputObject>
<mappingFields>
<inputField>Product2Id</inputField>
<outputField>ProductId</outputField>
</mappingFields>
<mappingFields>
<inputField>Quantity</inputField>
<outputField>Quantity</outputField>
</mappingFields>
</childObjectMapping>
<usageType>EligibleProgramRebateType</usageType>
</ObjectHierarchyRelationship>
Example of mapping between Contract and Transaction Journal.
<?xml version="1.0" encoding="UTF-8"?>
<ObjectHierarchyRelationship xmlns="http://soap.sforce.com/2006/04/metadata">
<parentObjectMapping>
<inputObject>Contract</inputObject>
<outputObject>TransactionJournal</outputObject>
<mappingFields>
<inputField>AccountId</inputField>
<outputField>MemberId</outputField>
</mappingFields>
</parentObjectMapping>
<usageType>EligibleProgramRebateType</usageType>
</ObjectHierarchyRelationship>
The following is an example package.xml that references the previous definition.
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
<types>
<members>*</members>
<name>ObjectHierarchyRelationship</name>
</types>
<version>51.0</version>
</Package>
Usage
Use the deploy() call to deploy metadata with a .zip file. Every .zip file contains a project manifest, a file that’s named package.xml,
and a set of directories that contain the components. The manifest file defines the components that you’re trying to retrieve or deploy
in the .zip file. The manifest also defines the API version that’s used for the deployment or retrieval. For more information on the .zip file,

Rebate Management Rebate Management Business APIs
deploying, and retrieving the metadata, see Deploying and Retrieving Metadata with the Zip File. You can also deploy and retrieve the
metadata API using Postman.
Wildcard Support in the Manifest File
This metadata type supports the wildcard character * (asterisk) in the package.xml manifest file. For information about using the
manifest file, see Deploying and Retrieving Metadata with the Zip File.
Rebate Management Business APIs
Rebate Management Business APIs use REST endpoints. These REST APIs follow similar conventions as Connect REST APIs.
To understand the architecture, authentication, rate limits, and how the requests and responses work, see Connect REST API Developer
Guide.
Resources
Here’s a list of Rebate Management Business API resources.
Request Bodies
Here’s a list of Rebate Management Business API request bodies.
Response Bodies
Here’s a list of Rebate Management Business API response bodies.
Resources
Here’s a list of Rebate Management Business API resources.
Program Rebate Type Validation (POST)
Validates the setup, configuration, and applicable rules of a specific program rebate type.
Program Rebate Type Validation (POST)
Validates the setup, configuration, and applicable rules of a specific program rebate type.
Resource
/connect/rebates/rebate-configuration-check
Resource example
https://yourInstance.salesforce.com/services/data/v65.0/connect/rebates/rebate-configuration-check
Available version
65.0
HTTP methods
POST

Rebate Management Request Bodies
Request body for POST
JSON example
{
"programRebateTypeId": "0hvLT0000000GCtYAM"
}
Properties
Name Type Description Required or Available
Optional Version
programRebateTypeId String The ID of the program rebate type for Required. 65.0
which the setup issue is to be validated.
Response body for POST
Program Rebate Type Validation Response
Request Bodies
Here’s a list of Rebate Management Business API request bodies.
Program Rebate Type Validation Input
Contains the parameters to initiate the validation of a program rebate type's setup and configuration.
Program Rebate Type Validation Input
Contains the parameters to initiate the validation of a program rebate type's setup and configuration.
JSON example
{
"programRebateTypeId": "0hvLT0000000GCtYAM"
}
Properties
Name Type Description Required or Available
Optional Version
programRebateTypeId String The ID of the program rebate type for Required. 65.0
which the setup issue is to be validated.
Response Bodies
Here’s a list of Rebate Management Business API response bodies.
Program Rebate Type Validation Response
The result of validating a program rebate type. It includes validation status, messages, and any identified configuration issues.

Rebate Management Response Bodies
Program Rebate Type Validation Error Response
Represents error details for program rebate type setup validation.
Program Rebate Type Validation Results Response
Represents the results details for program rebate type setup validation.
Program Rebate Type Validation Response
The result of validating a program rebate type. It includes validation status, messages, and any identified configuration issues.
JSON example
{
"isSuccess": true,
"errors": [],
"isValid": false,
"results": ["{ResourceName} defined in eligibity criteria is not available in the
data sources in DPE definition : {DPE definition name}"]
}
Properties
Property Name Type Description Filter Group and Available
Version Version
errors Program Rebate Collection of errors found during Big, 65.0 65.0
Type Validation validation.
Error Response[]
isSuccess Boolean Indicates whether the program rebate type Big, 65.0 65.0
validation was successful.
isValid Boolean Indicates the status of the program rebate Big, 65.0 65.0
type setup based on validation rules.
results Program Rebate Collection of setup-related validation Big, 65.0 65.0
Type Validation errors.
Results Response[]
Program Rebate Type Validation Error Response
Represents error details for program rebate type setup validation.
JSON example
{
"errors": [
{
"errorCode": "INVALID_API_INPUT",
"errorMessage": "Please provide a valid program rebate type id."
}
]
}

Rebate Management Response Bodies
Properties
Property Name Type Description Filter Group and Available
Version Version
errorCode String The code of the error due to which the Big, 65.0 65.0
request failed.
errorMessage String The error message that provides the reason Big, 65.0 65.0
the request failed.
Program Rebate Type Validation Results Response
Represents the results details for program rebate type setup validation.
JSON example
{
"results": [
{
"setupWarningDescription": "The payout period isn’t entirely within the effective
dates of the Program Rebate Type Benefit. Update the effective dates and try again.",
"setupWarningResults": [
"Tier 1: April FY 2025"
],
"setupWarningType": "BENEFIT_PAYOUT_PERIOD_MISMATCH"
}
]
}
Properties
Property Name Type Description Filter Group and Available
Version Version
setupWarningDescription String A description of the identified setup issue. Big, 65.0 65.0
setupWarningResults String[] The records or configurations impacted by Big, 65.0 65.0
the setup issue.
setupWarningType String The type of configuration or data-related Big, 65.0 65.0
issue identified in the setup.

Rebate Management Data Processing Engine, Batch Management, and Monitor
Workflow Services
Data Processing Engine, Batch Management, and Monitor Workflow
Services
Data Processing Engine and Batch Management help automate your business processes. Use objects,
EDITIONS
APIs, Platform Events, and invocable actions to define, run, and review Data Processing Engine
definitions and Batch Management jobs.
Available in: Lightning
Here's how both these features can automate your business processes: Experience
• Data Processing Engine: Transform data that's available in your Salesforce org and write back Available in: Data
the transformation results as new or updated records. You can transform the data for standard Processing Engine is
and custom objects. available with Enterprise,
Unlimited, and Performance
• Batch Management: Automate the processing of records in scheduled flows. You can process
Editions with the Financial
a high volume of standard and custom object records.
Services Cloud, Loyalty
Once a Data Processing Engine definition is run or a Batch Management job is run, you can view
Management,
the progress of the run and the results of the run using Monitor Workflow Services. Manufacturing Cloud,
Rebate Management,
Accounting Subledger, or
Data Model
Provider Search in Health
Data Processing Engine, Batch Management, and Monitor Workflow Servics share a data model.
Cloud.
Let's learn about the objects and relationships in this shared data model.
Available in: Batch
Common Tooling API Object
Management is available
BatchJobDefinition is a common Tooling API object that is shared between Data Processing
with Enterprise, Unlimited,
Engine and Batch Management.
and Performance Editions
Common Platform Event with the Loyalty
Batch Management jobs and Data Processing Engine definitions are run using invocable actions Management,
in Flows. Use the BatchJobStatusChanged event to notify subscribers after a Batch Management Manufacturing Cloud,
Rebate Management, or
job or a Data Processing Engine definition is processed in a flow.
Accounting Subledger
Common Business APIs
Common Business APIs are RESTful APIs that are sometimes available as Apex classes and
methods.
Data Processing Engine
Transform data that's available in your Salesforce org and write back the transformation results as new or updated records. You can
transform the data for standard and custom objects. Data Processing Engine consists of a Tooling API object, a standard object, a
Metadata API, and an invocable action. You can use these to view, create, edit, and run Data Processing Engine definitions.
Batch Management
Automate the processing of records in scheduled flows. You can process a high volume of standard and custom object records.
Batch Management consists of three Tooling API objects, a standard object, a Metadata API, and an invocable action. You can use
these resources to view, create, edit, and run Batch Management jobs.
Monitor Workflow Services
The Montior Workflow Services standard objects can be used to track the run of Data Processing Engine definitons and Batch
Management jobs. During a run, you can view details about each part that the run is broken down into. After the run is complete,
you can view its status and the records which weren't processed during the run.

Rebate Management Data Model
Data Model
Data Processing Engine, Batch Management, and Monitor Workflow Servics share a data model.
EDITIONS
Let's learn about the objects and relationships in this shared data model.
Here's the data model: Available in: Lightning
Experience
Available in: Data
Processing Engine is
available with Enterprise,
Unlimited, and Performance
Editions with the Financial
Services Cloud, Loyalty
Management,
Manufacturing Cloud,
Rebate Management,
Accounting Subledger, or
Provider Search in Health
Cloud.
Available in: Batch
Management is available
with Enterprise, Unlimited,
and Performance Editions
with the Loyalty
Management,
Manufacturing Cloud,
Rebate Management, or
Accounting Subledger

Rebate Management Common Tooling API Object
Common Tooling API Object
BatchJobDefinition is a common Tooling API object that is shared between Data Processing Engine
EDITIONS
and Batch Management.
Tooling API objects let you interact with metadata for declarative development. For example, you Available in: Lightning
can create your own version of Setup. Experience
Available in: Data
BatchJobDefinition Processing Engine is
Represents the definition of a batch job. This object is available in API version 51.0 and later. available with Enterprise,
Unlimited, and Performance
Editions with the Financial
BatchJobDefinition Services Cloud, Loyalty
Management,
Represents the definition of a batch job. This object is available in API version 51.0 and later.
Manufacturing Cloud,
Rebate Management,
Note: Where possible, we changed noninclusive terms to align with our company value of
Accounting Subledger, or
Equality. We maintained certain terms to avoid any effect on customer implementations.
Provider Search in Health
Cloud.
Supported SOAP API Calls
Available in: Batch
describeSObjects(), query(), retrieve() Management is available
with Enterprise, Unlimited,
and Performance Editions
Supported REST API Methods
with the Loyalty
GET, HEAD, Query Management,
Manufacturing Cloud,
Rebate Management, or
Fields
Accounting Subledger
Field Details
Description
Type
textarea
Properties
Filter, Group, Nillable, Sort
Description
The description of the batch job definition.
DeveloperName
Type
string
Properties
Filter, Group, Sort
Description
The developer name of the batch job.
Language
Type
picklist

Rebate Management Common Tooling API Object
Field Details
Properties
Filter, Group, Restricted picklist, Sort
Description
The language in which the batch job is created.
Possible values are:
• af—Afrikaans
• am—Amharic
• ar—Arabic
• ar_AE—Arabic (United Arab Emirates)
• ar_BH—Arabic (Bahrain)
• ar_DZ—Arabic (Algeria)
• ar_EG—Arabic (Egypt)
• ar_IQ—Arabic (Iraq)
• ar_JO—Arabic (Jordan)
• ar_KW—Arabic (Kuwait)
• ar_LB—Arabic (Lebanon)
• ar_LY—Arabic (Libya)
• ar_MA—Arabic (Morocco)
• ar_OM—Arabic (Oman)
• ar_QA—Arabic (Qatar)
• ar_SA—Arabic (Saudi Arabia)
• ar_SD—Arabic (Sudan)
• ar_SY—Arabic (Syria)
• ar_TN—Arabic (Tunisia)
• ar_YE—Arabic (Yemen)
• bg—Bulgarian
• bn—Bengali
• bs—Bosnian
• ca—Catalan
• cs—Czech
• cy—Welsh
• da—Danish
• de—German
• de_AT—German (Austria)
• de_BE—German (Belgium)
• de_CH—German (Switzerland)
• de_LU—German (Luxembourg)
• el—Greek

Rebate Management Common Tooling API Object
Field Details
• en_AU—English (Australian)
• en_CA—English (Canadian)
• en_GB—English (UK)
• en_HK—English (Hong Kong)
• en_IE—English (Ireland)
• en_IN—English (Indian)
• en_MY—English (Malaysian)
• en_NZ—English (New Zealand)
• en_PH—English (Phillipines)
• en_SG—English (Singapore)
• en_US—English
• en_ZA—English (South Africa)
• eo—Esperanto (Pseudo)
• es—Spanish
• es_AR—Spanish (Argentina)
• es_BO—Spanish (Bolivia)
• es_CL—Spanish (Chile)
• es_CO—Spanish (Colombia)
• es_CR—Spanish (Costa Rica)
• es_DO—Spanish (Dominican Republic)
• es_EC—Spanish (Ecuador)
• es_GT—Spanish (Guatemala)
• es_HN—Spanish (Honduras)
• es_MX—Spanish (Mexico)
• es_NI—Spanish (Nicaragua)
• es_PA—Spanish (Panama)
• es_PE—Spanish (Peru)
• es_PR—Spanish (Puerto Rico)
• es_PY—Spanish (Paraguay)
• es_SV—Spanish (El Salvador)
• es_US—Spanish (United States)
• es_UY—Spanish (Uruguay)
• es_VE—Spanish (Venezuela)
• et—Estonian
• eu—Basque
• fa—Farsi
• fi—Finnish
• fr—French

Rebate Management Common Tooling API Object
Field Details
• fr_BE—French (Belgium)
• fr_CA—French (Canadian)
• fr_CH—French (Switzerland)
• fr_LU—French (Luxembourg)
• ga—Irish
• gu—Gujarati
• hi—Hindi
• hr—Croatian
• hu—Hungarian
• hy—Armenian
• in—Indonesian
• is—Icelandic
• it—Italian
• it_CH—Italian (Switzerland)
• iw—Hebrew
• iw_EO—Esperanto RTL (Pseudo)
• ja—Japanese
• ka—Georgian
• km—Khmer
• kn—Kannada
• ko—Korean
• lb—Luxembourgish
• lt—Lithuanian
• lv—Latvian
• mi—Te reo
• mk—Macedonian
• ml—Malayalam
• mr—Marathi
• ms—Malay
• mt—Maltese
• my—Burmese
• nl_BE—Dutch (Belgium)
• nl_NL—Dutch
• no—Norwegian
• pl—Polish
• pt_BR—Portuguese (Brazil)
• pt_PT—Portuguese (European)
• rm—Romansh

Rebate Management Common Tooling API Object
Field Details
• ro—Romanian
• ro_MD—Romanian (Moldova)
• ru—Russian
• sh—Serbian (Latin)
• sh_ME—Montenegrin
• sk—Slovak
• sl—Slovene
• sq—Albanian
• sr—Serbian (Cyrillic)
• sv—Swedish
• sw—Swahili
• ta—Tamil
• te—Telugu
• th—Thai
• tl—Tagalog
• tr—Turkish
• uk—Ukrainian
• ur—Urdu
• vi—Vietnamese
• xh—Xhosa
• zh_CN—Chinese (Simplified)
• zh_HK—Chinese (Hong Kong)
• zh_SG—Chinese (Singapore)
• zh_TW—Chinese (Traditional)
• zu—Zulu
MasterLabel
Type
string
Properties
Filter, Group, Sort
Description
The label of the batch job.
ProcessGroup
Type
string
Properties
Filter, Group, Sort

Rebate Management Common Tooling API Object
Field Details
Description
The group or team that's using the batch job. This field is only applicable to Batch
Management jobs.
Status
Type
picklist
Properties
Defaulted on create, Filter, Group, Restricted picklist, Sort
Description
The status of the batch job.
Possible values are:
• Active
• Inactive
Type
Type
picklist
Properties
Defaulted on create, Filter, Group, Restricted picklist, Sort
Description
Specifies the type of batch job.
Possible values are:
• Calc—Data Processing Engine
• Flow
• BulkUpdate
• ConsumptionOveragesCalculation
• DecisionTableRefresh
• DeepCloneSalesAgreement
• EntitlementCreationBatchJob
• HighScaleBreProcess
• IndustriesLSCommercial
• LoyaltyProgramProcess
• ManagerProvisioning
• NetUnitRateCalculation
• PbbToOptyConversion
• ProductCatalogCacheRefresh
• RatableSummaryCreation
• SummaryCreation

Rebate Management Common Platform Event
Field Details
When Data Processing Engine or Batch Management is available in a Salesforce org, the
default values are Calc or Flow respectively. Other types may be available to you
depending on the licenses available in your org.
Common Platform Event
Batch Management jobs and Data Processing Engine definitions are run using invocable actions in
EDITIONS
Flows. Use the BatchJobStatusChanged event to notify subscribers after a Batch Management job
or a Data Processing Engine definition is processed in a flow.
Available in: Lightning
Experience
BatchJobStatusChangedEvent
Available in: Data
Notifies subscribers of when a batch job is completed in a flow. This object is available in API
Processing Engine is
Unlimited, and Performance
Editions with the Financial
BatchJobStatusChangedEvent
Services Cloud, Loyalty
Management,
Notifies subscribers of when a batch job is completed in a flow. This object is available in API version
Manufacturing Cloud,
51.0 and later.
Rebate Management,
Accounting Subledger, or
Supported Calls Provider Search in Health
Cloud.
describeSObjects()
Available in: Batch
Management is available
Supported Subscribers
with Enterprise, Unlimited,
and Performance Editions
Subscriber Supported?
with the Loyalty
Management,
Flows
Manufacturing Cloud,
Rebate Management, or
Accounting Subledger
Fields
Field Details
BatchJob
Type
string
Description
The unique identifier of the batch job.
BatchJobDefinition
Type
string
Properties
Nillable

Rebate Management Common Platform Event
Field Details
Description
The unique identifier of the batch job's definition.
EndDateTime
Type
dateTime
Properties
Nillable
Description
The timestamp for when the batch job execution is complete.
EventUuid
Type
string
Properties
Nillable
Description
A universally unique identifier (UUID) that identifies a platform event message. This field is
available in API version 52.0 and later.
ReplayId
Type
string
Properties
Nillable
Description
Represents an ID value that is populated by the system and refers to the position of the event
in the event stream. Replay ID values aren’t guaranteed to be contiguous for consecutive
events. A subscriber can store a replay ID value and use it on resubscription to retrieve missed
events that are within the retention window.
StartDateTime
Type
dateTime
Properties
Nillable
Description
The timestamp for when the batch job execution is started.
Status
Type
picklist
Properties
Restricted picklist
Description
The status of the batch job.
Possible values are:

Rebate Management Common Business APIs
Field Details
• Canceled—Canceled
• Failure
• Success
Common Business APIs
Common Business APIs are RESTful APIs that are sometimes available as Apex classes and methods.
REST Reference
You can access Common Business APIs using REST endpoints. These REST APIs follow similar conventions as Connect REST APIs.
REST Reference
You can access Common Business APIs using REST endpoints. These REST APIs follow similar conventions as Connect REST APIs.
To understand the architecture, authentication, rate limits, and how the requests and responses work, see Connect REST API Developer
Guide.
Resources
Here’s a list of Common Business API resources.
Response Bodies
Here’s a list of Common Business API response bodies.
SEE ALSO:
Connect REST API Developer Guide
Resources
Here’s a list of Common Business API resources.
Batch Job Cancel
Cancel a batch job of type data processing engine (calc job) and batch management. A batch job with only the status Submitted
or In Progress can be canceled.
Batch Job Cancel
Cancel a batch job of type data processing engine (calc job) and batch management. A batch job with only the status Submitted or In
Progress can be canceled.
Special Access Rules
To use this resource, the following permissions are required:
• Your org must have the Batch Management and Data Processing Engine licenses
• Users in your org require System Administration profile

Rebate Management Common Business APIs
Resource
/connect/batch-job/batchJobId/cancel-job
Resource example
/connect/batch-job/0mdxx00000000fxAAA/cancel-job
Available version
52.0
Requires Chatter
No
HTTP methods
POST
Note: POST doesn’t take request parameters or a request body.
Response body for POST
Returns HTTP 201 on success.
See Batch Job Cancel Output for HTTP code descriptions that are unique to this resource in case of failure of the batch job cancel
request.
Response Bodies
Here’s a list of Common Business API response bodies.
Batch Job Cancel Output
Output representation of the batch job cancel request.
Batch Job Cancel Output
Output representation of the batch job cancel request.
Property Name Type Description Filter Group and Available Version
Version
message String Details about why the batch job cancel Small, 52.0 52.0
request failed.
This table lists HTTP response code descriptions that are unique to this resource.
HTTP Response Code Error Code Description
400 INVALID_STATUS We can't cancel the batch job that doesn't have an active run.
Specify the ID of a batch job with an active run and try again.
400 INVALID_STATUS We can't cancel the batch job that is already canceled or
completed. Specify the ID of a valid batch job with the status
InProgress or Submitted and try again.

Rebate Management Data Processing Engine
HTTP Response Code Error Code Description
400 DELETE_FAILED We can’t cancel the batch job of which the results are already being
written back.
400 DELETE_FAILED We can’t cancel the batch job because of an error in processing
your org’s data. Run the Data Processing Engine definition and try
again.
403 FORBIDDEN You don’t have the permission to cancel a batch job. Ask your
Salesforce admin for help.
404 RESOURCE_NOT_FOUND Specify the ID of a valid batch job and try again.
500 INTERNAL_SERVER_ERROR Something went wrong when we tried to cancel the batch job.
Try again or ask your Salesforce admin for help.
Data Processing Engine
Transform data that's available in your Salesforce org and write back the transformation results as
EDITIONS
new or updated records. You can transform the data for standard and custom objects. Data
Processing Engine consists of a Tooling API object, a standard object, a Metadata API, and an
Available in: Lightning
invocable action. You can use these to view, create, edit, and run Data Processing Engine definitions.
Experience
Available in: Data
Data Processing Engine Tooling API Objects
Processing Engine is
Data Processing Engine consists of one Tooling API object, BatchCalcJobDefinition. Use this available with Enterprise,
object to create and edit a Data Processing Engine definition. Unlimited, and Performance
Editions with the Financial
Data Processing Engine Standard Object
Services Cloud, Loyalty
Data Processing Engine contains one standard object, BatchCalcJobDefinitionView. Use this
Management,
object to view all the Data Processing Engine definitions available in your Salesforce org, including
Manufacturing Cloud,
file-based definitions.
Rebate Management,
Data Processing Engine Metadata API Accounting Subledger, or
Use a Metadata API to create, update, and activate Data Processing Engine definitions. Provider Search in Health
Cloud.
Data Processing Engine Invocable Actions
Run an active Data Processing Engine definition. For more information on custom invocable
actions, see REST API Developer Guide and Actions Developer Guide.

Rebate Management Data Processing Engine
Data Processing Engine Tooling API Objects
Data Processing Engine consists of one Tooling API object, BatchCalcJobDefinition. Use this object
EDITIONS
to create and edit a Data Processing Engine definition.
Tooling API objects let you interact with metadata for declarative development. For example, you Available in: Lightning
can create your own version of Setup. Experience
Available in: Data
BatchCalcJobDefinition Processing Engine is
Represents a Data Processing Engine (DPE) definition. This object is available in API version 51.0 available with Enterprise,
and later. Unlimited, and Performance
Editions with the Financial
Services Cloud, Loyalty
BatchCalcJobDefinition Management,
Manufacturing Cloud,
Represents a Data Processing Engine (DPE) definition. This object is available in API version 51.0
Rebate Management,
and later.
Accounting Subledger, or
Note: Where possible, we changed noninclusive terms to align with our company value of Provider Search in Health
Equality. We maintained certain terms to avoid any effect on customer implementations. Cloud.
Supported SOAP API Calls
create(), delete(), describeSObjects(), query(), retrieve(), update(), upsert()
Supported REST API Methods
DELETE, GET, HEAD, PATCH, POST, Query
Fields
Field Details
BatchJobDefinitionId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
The unique identifier of the associated batch job definition.
This is a relationship field.
Relationship Name
BatchJobDefinition
Relationship Type
Lookup
Refers To
BatchJobDefinition
DataSpaceApiName
Type
string

Rebate Management Data Processing Engine
Field Details
Properties
Filter, Group, Nillable, Sort
Description
The Data Space API name from Data Cloud.
DefinitionRunMode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The execution mode of the Data Processing Engine definition.
Possible values are:
• Batch
• OnDemand—This value is reserved for internal use.
The default value is Batch.
DeveloperName
Type
string
Properties
Filter, Group, Sort
Description
The developer name of the Data Processing Engine definition.
DoesGenAllFailedRecords
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates whether the error file includes a complete list of all failed writeback records (true)
or not (false). The default value is false, and only the first instance of a failure is recorded
in the error file. If set to true, all failed records are recorded in the error file for the writeback
node.
Available in API version 65.0 and later.
ExecutionPlatformObjectType
Type
Picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
Required. The execution platform object type that's used during the read, transform, and
writeback process for the Data Processing Engine definition. Possible values are:

Rebate Management Data Processing Engine
Field Details
• CalculatedInsightsObject
• DataLakeObject
• DataModelObject
• None
Available in API version 65.0 and later.
ExecutionPlatformType
Type
Picklist
Properties
Filter, Group, Restricted picklist, Sort, Not-Nillable
Description
Specifies the platform that's used to run the Data Processing Engine definition. Possible
values:
• CDP—Data Cloud
• CORE—This value is reserved for internal use.
• CRMA—CRM Analytics
FullName
Type
string
Properties
Create, Group, Nillable
Description
The name of the Data Processing Engine definition.
Query this field only if the query result contains no more than one record. Otherwise, an error
is returned. If more than one record exists, use multiple queries to retrieve the records. This
limit protects performance.
IsTemplate
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates whether this is a template Data Processing Engine definition.
Language
Type
picklist
Properties
Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort
Description
The language in which this Data Processing Engine definition is created.

Rebate Management Data Processing Engine
Field Details
ManageableState
Type
ManageableState enumerated list
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
Indicates the manageable state of the specified component that is contained in a package:
• beta
• deleted
• deprecated
• deprecatedEditable
• installed
• installedEditable
• released
• unmanaged
MasterLabel
Type
string
Properties
Filter, Group, Sort
Description
The label of the Data Processing Engine definition.
Metadata
Type
complexvalue
Properties
Create, Nillable, Update
Description
Data Processing Engine definition's metadata.
Query this field only if the query result contains no more than one record. Otherwise, an error
is returned. If more than one record exists, use multiple queries to retrieve the records. This
limit protects performance.
NamespacePrefix
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The namespace prefix associated with this object. Each Developer Edition organization that
creates a managed package has a unique namespace prefix. Limit: 15 characters. You can
refer to a component in a managed package by using the
namespacePrefix__componentName notation.

Rebate Management Data Processing Engine
Field Details
The namespace prefix can have one of the following values:
• In Developer Edition organizations, the namespace prefix is set to the namespace prefix
of the organization for all objects that support it. There’s an exception if an object is in
an installed managed package. In that case, the object has the namespace prefix of the
installed managed package. This field’s value is the namespace prefix of the Developer
Edition organization of the package developer.
• In organizations that aren’t Developer Edition organizations, NamespacePrefix is
only set for objects that are part of an installed managed package. There’s no namespace
prefix for all other objects.
ProcessType
Type
picklist
Properties
Filter, Group, Restricted picklist, Sort
Description
Required. The process type for which the Data Processing Engine definition is created.
Possible values are:
• AccountingPeriodClosure—Legal Entity Accounting Period Closure—Available
in API version 62.0 and later.
• ActionableList
• AdvancedAccountForecast
• BenefitManagement—Available in API version 61.0 and later.
• BillingSchedulesforInvoiceGeneration—Billing Schedules for Invoice
Generation—Available in API version 62.0 and later.
• CDPEnrichment
• ChannelInventoryManagement—Available in API version 63.0 and later.
• CollectionsAndRecovery
• CriteriaBsdSearchAndFilter - Criteria-Based Search And
Filter
• DataProcessingEngine - Standard
• DecisionMatrixDataUpload-This value is available only if you have Business
Rules Engine enabled.
• Decisiontable—Decision table activation—Available in API version 62.0 and later.
• Education
• EmployeeService—Available in API version 63.0 and later.
• FinancialSummaryRollup—Available in API version 63.0 and later.
• ForeignExchangeGainLossCalculations
• FSCHierarchyRollUp
• Fundraising
• FundraisingRollups—Available in API version 63.0 and later.

Rebate Management Data Processing Engine
Field Details
• GeneralLedgerAccountBalancesSummary
• InventoryBatchSearch
• InventorySearch
• InvoiceGeneration—Available in API version 62.0 and later.
• LegalEntityAccountingPeriodClosureAdvanced—Available in API
• LifeSciencesCommercialTerritoryAlignment—Available in API version
63.0 and later.
• LifeSciencesCustomerEngagement
• Loyalty
• LoyaltyPartnerManagement
• LoyaltyPointsAggregation
• NetZero
• NextGenForecasting—Available in API version 62.0 and later.
• PatientServicesProgram
• PnmRosterFileUpload—Available in API version 62.0 and later.
• PriceProtection—Available in API version 62.0 and later.
• ProductCatalogManagement—Available in API version 63.0 and later.
• ProgramBasedBusiness
• ProgramManagementRollups
• Rebates
• RecordAggregation
• RevenueTransactionManagement—Available in API version 63.0 and later.
• AccountingSubledger—This value is reserved for internal use.
• ProviderSearch—This value is reserved for internal use.
• Recruitment—Available in API version 62.0 and later.
• SalesAgreement—Available in API version 63.0 and later.
• StockRotation
• UsageManagement—Available in API version 62.0 and later.
When Data Processing Engine is enabled for a Salesforce org, the default value is 'Standard’.
Other process types may be available to you depending on the licenses available in your
org.

Rebate Management Data Processing Engine
Data Processing Engine Standard Object
Data Processing Engine contains one standard object, BatchCalcJobDefinitionView. Use this object
EDITIONS
to view all the Data Processing Engine definitions available in your Salesforce org, including file-based
definitions.
Available in: Lightning
Experience
BatchCalcJobDefinitionView
Available in: Data
Represents the details of a Data Processing Engine definition. The definition can also be a
Processing Engine is
file-based definition that is available in your Salesforce org. This object is available in API version available with Enterprise,
51.0 and later. Unlimited, and Performance
Editions with the Financial
Services Cloud, Loyalty
BatchCalcJobDefinitionView
Management,
Represents the details of a Data Processing Engine definition. The definition can also be a file-based Manufacturing Cloud,
definition that is available in your Salesforce org. This object is available in API version 51.0 and later. Rebate Management,
Accounting Subledger, or
Note: Where possible, we changed noninclusive terms to align with our company value of Provider Search in Health
Equality. We maintained certain terms to avoid any effect on customer implementations. Cloud.
Supported Calls
describeSObjects(), query()
Fields
Field Details
DataSpaceApiName
Type
string
Properties
Filter, Group, Nillable, Sort
Description
Stores the data space API name from Data Cloud.
DefinitionRunMode
Type
picklist
Properties
Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
The execution mode of the Data Processing Engine definition.
Possible values are:
• Batch
• OnDemand—On Demand
The default value is Batch.

Rebate Management Data Processing Engine
Field Details
Description
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The description of a Data Processing Engine definition.
DurableId
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The unique identifier for the field. Always retrieve this value before using it, as the value isn’t
guaranteed to stay the same from one release to the next. Simplify queries by using this field
instead of making multiple queries.
ExecutionPlatformObjectType
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
Specifies the execution platform object type used to read, transform, and write back processes
during the execution of a Data Processing Engine definition. This field is available in API
Possible values are:
• CalculatedInsightsObject—Calculated Insights Object
• DataLakeObject—Data Lake Object
• DataModelObject—Data Model Object
• None
ExecutionPlatformType
Type
Picklist
Properties
Filter, Group, Restricted picklist, Sort, Not-Nillable
Description
Specifies the platform that's used to run the Data Processing Engine definition. Possible
values:
• CDP—Data Cloud
• CRMA—CRM Analytics

Rebate Management Data Processing Engine
Field Details
InstalledPackageName
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The name of the package used to add the definition to the org.
IsActive
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates whether the definition is active.
IsTemplate
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates whether the definition is a template. You can make a copy of a template definition
and update it based on your requirements.
LastModifiedBy
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The unique identifier of the user who modified the definition last.
ManageableState
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
Indicates the manageable state of the definition if it’s contained in a package.
Possible values are:
• beta—Managed-Beta
• deleted—Managed-Proposed-Deleted
• deprecated—Managed-Proposed-Deprecated
• deprecatedEditable—SecondGen-Installed-Deprecated
• installed—Managed-Installed

Rebate Management Data Processing Engine
Field Details
• installedEditable—SecondGen-Installed-Editable
• released—Managed-Released
• unmanaged—Unmanaged
MasterLabel
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The label of the Data Processing Engine definition.
Name
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The name of the Data Processing Engine definition.
NamespacePrefix
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The namespace prefix associated with this object. Each Developer Edition organization that
creates a managed package has a unique namespace prefix. Limit: 15 characters. You can
refer to a component in a managed package by using the
namespacePrefix__componentName notation.
The namespace prefix can have one of the following values:
• In Developer Edition organizations, the namespace prefix is set to the namespace prefix
of the organization for all objects that support it. There’s an exception if an object is in
an installed managed package. In that case, the object has the namespace prefix of the
installed managed package. This field’s value is the namespace prefix of the Developer
Edition organization of the package developer.
• In organizations that aren’t Developer Edition organizations, NamespacePrefix is only
set for objects that are part of an installed managed package. There’s no namespace
prefix for all other objects.
ProcessType
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort

Rebate Management Data Processing Engine
Field Details
Description
The process type of the definition.
Possible values are:
• AccountingPeriodClosure—Legal Entity Accounting Period Closure—Available
in API version 62.0 and later.
• ActionableList
• AdvancedAccountForecast
• BenefitManagement—Available in API version 61.0 and later.
• BillingSchedulesforInvoiceGeneration—Billing Schedules for Invoice
Generation—Available in API version 62.0 and later.
• CDPEnrichment
• ChannelInventoryManagement—Available in API version 63.0 and later.
• CollectionsAndRecovery
• CriteriaBsdSearchAndFilter - Criteria-Based Search And
Filter
• DataProcessingEngine - Standard
• DecisionMatrixDataUpload-This value is available only if you have Business
Rules Engine enabled.
• Decisiontable—Decision table activation—Available in API version 62.0 and later.
• Education
• EmployeeService—Available in API version 63.0 and later.
• FinancialSummaryRollup—Available in API version 63.0 and later.
• ForeignExchangeGainLossCalculations
• FSCHierarchyRollUp
• Fundraising
• FundraisingRollups—Available in API version 63.0 and later.
• GeneralLedgerAccountBalancesSummary
• InventoryBatchSearch
• InventorySearch
• InvoiceGeneration—Available in API version 62.0 and later.
• LegalEntityAccountingPeriodClosureAdvanced—Available in API
• LifeSciencesCommercialTerritoryAlignment—Available in API version
63.0 and later.
• LifeSciencesCustomerEngagement
• Loyalty
• LoyaltyPartnerManagement
• LoyaltyPointsAggregation
• NetZero

Rebate Management Data Processing Engine
Field Details
• NextGenForecasting—Available in API version 62.0 and later.
• PatientServicesProgram
• PnmRosterFileUpload—Available in API version 62.0 and later.
• PriceProtection—Available in API version 62.0 and later.
• ProductCatalogManagement—Available in API version 63.0 and later.
• ProgramBasedBusiness
• ProgramManagementRollups
• Rebates
• RecordAggregation
• RevenueTransactionManagement—Available in API version 63.0 and later.
• AccountingSubledger—This value is reserved for internal use.
• ProviderSearch—This value is reserved for internal use.
• Recruitment—Available in API version 62.0 and later.
• SalesAgreement—Available in API version 63.0 and later.
• StockRotation
• UsageManagement—Available in API version 62.0 and later.
When Data Processing Engine is enabled for a Salesforce org, the default value is 'Standard’.
Other process types may be available to you depending on your industry solution and
permission sets.
Data Processing Engine Metadata API
Use a Metadata API to create, update, and activate Data Processing Engine definitions.
EDITIONS
BatchCalcJobDefinition Available in: Lightning
Represents a Data Processing Engine definition. Experience
Available in: Data
Processing Engine is
BatchCalcJobDefinition
available with Enterprise,
Represents a Data Processing Engine definition. Unlimited, and Performance
Editions with the Financial
Services Cloud, Loyalty
Parent Type
Management,
This type extends the Metadata metadata type and inherits its fullName field. Manufacturing Cloud,
Rebate Management,
Accounting Subledger, or
File Suffix and Directory Location
Provider Search in Health
BatchCalcJobDefinition components have the suffix .batchCalcJobDefinition and are Cloud.
stored in the batchCalcJobDefinitions folder.

Rebate Management Data Processing Engine
Version
BatchCalcJobDefinition components are available in API version 51.0 and later.
Special Access Rules
To use this metadata type, one of these licenses is required:
• Loyalty Management
• Financial Services Cloud
• Rebate Management
• Manufacturing Cloud
• Net Zero Cloud
Fields
Field Name Field Type Description
aggregates BatchCalcJob Collection of aggregate nodes in a data processing engine.
Aggregate[]
appends BatchCalcJobUnion[] Collection of append nodes in a data processing engine.
atomicWritebacks BatchCalcJobAtomicWriteBack[] Collection of composite writeback nodes in a data processing engine
definition. Available in API version 62.0 and later.
customNodes BatchCalcJobCustomNode[] Collection of custom nodes in a data processing engine. Available in API
dataSpaceApiName string Stores the Data Space API Name from Data 360. Available in API version
60.0 and later.
datasources BatchCalcJob Collection of data source nodes in a data processing engine.
Datasource[]
definitionRunMode BatchCaclJobDefRunMode(enumeratoin Specifies the execution mode in a data processing engine. Valid values
of type string) are:
• Batch
• OnDemand
description string Description of a data processing engine definition.
doesGenAllFailedRecords boolean Indicates whether the error file includes a complete list of all failed
writeback records (true) or not (false). The default value is false,
and only the first instance of a failure is recorded in the error file. If set
to true, all failed records are recorded in the error file for the writeback
node.
Available in API version 65.0 and later.

Rebate Management Data Processing Engine
Field Name Field Type Description
executionPlatformObjectType ExecutoinPaltformObejctType(enumeratoin The execution platform object type that's used during the read, transform,
of type string) and writeback process for the Data Processing Engine definition. Possible
values are:
• CalculatedInsightsObject
• DataLakeObject
• DataModelObject
• None
Available in API version 65.0 and later.
executionPlatformType ExecutoinPaltformType(enumeratoin The platform that's used to run the Data Processing Engine definition.
of type string) Valid values are:
• CRMA
• CDP
• CORE
Available in API version 59.0 and later.
filters BatchCalcJobFilter[] Collection of filter nodes in a data processing engine. definition.
forecasts BatchCalcJobForecast[] Collection of forecast nodes in a data processing engine. definition.
Available in API version 58.0 and later.
hierarchyPaths BatchCalcJobHierarchyPath[] Collection of hierarchy path nodes in a data processing engine definition.
isTemplate boolean Indicates whether it’s a template data processing engine definition.
joins BatchCalcJobSource Collection of join nodes in a data processing engine.
Join[]
label string The label of a data processing engine definition.
parameters BatchCalcJobParameter[] Collection of input variables in a data processing engine.
processType BatchCalcProcessType The process type of a data processing engine. These process types may
(enumeration of be available to you depending on your industry solution and permission
type string) sets. Valid values are:
• AccountingPeriodClosure
• AccountingSubledger—This value is reserved for internal
use.
• ActionableList
• AdvancedAccountForecast
• BenefitManagement
• BillingSchedulesforInvoiceGeneration
• CDPEnrichment
• ChannelInventoryManagement—Available in API version
63.0 and later.

Rebate Management Data Processing Engine
Field Name Field Type Description
• CollectionPlan—Available in API version 65.0 and later.
• CriteriaBsdSearchAndFilter
• DataProcessingEngine
• DecisionMatrixDataUpload
• Decisiontable
• Education
• EmployeeService—Available in API version 63.0 and later.
• FinancialSummaryRollup
• ForeignExchangeGainLossCalculations—Available
in API version 65.0 and later.
• FSCHierarchyRollUp
• Fundraising—Available in API version 64.0 and later.
• FundraisingRollups—Available in API version 63.0 and later.
• GeneralLedgerAccountBalancesSummary—Available
in API version 65.0 and later.
• InventoryBatchSearch—Available in API version 65.0 and
later.
• InventorySearch—Available in API version 65.0 and later.
• InvoiceGeneration
• Loyalty
• LegalEntityAccountingPeriodClosureAdvanced—Available
in API version 63.0 and later.
• LifeSciencbatchcalesCommercialTerritoryAlignment—Available
in API version 63.0 and later.
• LifeSciencesCustomerEngagement—Available in API
• LoyaltyPartnerManagement
• LoyaltyPointsAggregation
• NextGenForecasting—Available in API version 64.0 and
earlier.
• NetZero
• PatientServicesProgram—Available in API version 64.0
and later.
• PnmRosterFileUpload
• PriceProtection
• ProductCatalogManagement
• ProgramBasedBusiness
• ProviderSearch—This value is reserved for internal use.
• Rebates
• Recruitment

Rebate Management Data Processing Engine
Field Name Field Type Description
• RevenueTransactionManagement—Available in API version
63.0 and later.
• SalesAgreement—Available in API version 63.0 and later.
• TestAtomicWritebackScale—Available in API version 64.0
and later.
• TestProcessType
• UsageManagement
status BatchJobDefinition Status of a data processing engine definition. Valid values are:
Status
• Active
(enumeration of
• Inactive
type string)
transforms BatchCalcJobTransform[] Collection of data transformation nodes in a data processing engine.
writebacks BatchCalcJobWriteback Collection of writeback objects in which the results of the data processing
Object[] engine are written back.
BatchCalcJobAggregate
Represents a collection of fields relating to an aggregate node in a data processing engine.
Fields
Field Name Field Type Description
description string Description of an aggregate node.
fields BatchCalcJob Required. Collection of aggregation fields.
AggregateField[]
groupBy string[] Required. Collections of fields used to group data in an aggregate node.
label string Required. Label of an aggregate node.
name string Required. Name of an aggregate node.
sourceName string Required. Name of the source node.
BatchCalcJobAggregateField
Represents a collection of fields relating to an aggregation field in an aggregate node of a data processing engine.

Rebate Management Data Processing Engine
Fields
Field Name Field Type Description
aggregateFunction BatchCalcJobAggregateFunction Required. Function used for aggregation.
(enumeration of type
Valid values are:
string)
• Unique—A count of unique values.
• Sum—The sum of all values.
• Max—The largest value.
• Min—The smallest value.
• Avg—The average value, calculated as the mean.
• Std—The standard deviation.
• Stdp—A standard deviation with population variance.
• Var—The variance.
• VarP—The variance with population.
• Count—The total count of values.
alias string Required. Name that subsequent nodes within the data processing engine use
to refer to the aggregate field.
sourceFieldName string Required. Source node field on which the aggregate is calculated.
BatchCalcJobAtomicWriteback
Represents a node in a DPE definition that stores the details about the relationship between the writeback nodes and the composite
writeback operations between the nodes.
Field Name Field Type Description
description string Description of the composite writeback object.
label string Required. Name of the composite writeback object.
name string Required. API name of the composite writeback object.
writebackObject BatchCaclJobAtomciWrtiebackRealtoinshpi[] Specifies the relationship between the writeback objects that are involved in
Relationships the writeback operation.
writebackSequence int Sequence in which the data processing engine executes the composite write
back node.
BatchCalcJobAtomicWritebackRelationship
Represents the relationships between the writeback objects that are involved in a composite writeback operation. It captures the
relationships between these objects and the sequence in which they should be processed.

Rebate Management Data Processing Engine
Field Name Field Type Description
childWriteback string Field name that's associated with the child writeback object in a composite
ObjectField writeback relationship. Available in API version 63.0 and later.
childWriteback string Name of the child writeback object that's associated with the writeback
ObjectName relationship.
parentWriteback string Field name that's associated with the parent writeback object in a composite
ObjectField writeback relationship. Available in API version 63.0 and later.
parentWriteback string Required. Name of the parent writeback object that's associated with the
ObjectName writeback relationship.
relationshipName string Describes the relationship between the child and parent writeback objects in
a composite writeback node. Available in API version 64.0 and later.
sequenceNumber int Sequence number of the writeback node that's associated with its parent node
in the relationship.
BatchCalcJobCustomNode
Represents a collection of custom nodes in a data processing engine. Use a custom node to add a custom action.
Fields
Field Name Field Type Description
description string Description of a custom node.
extensionName string Required. Name of an extension node.
extensionNamespace string Required. Namespace of an extension node.
label string Required. Label of a custom node.
name string Required. Name of a custom node.
parameters BatchCalcJob The field mappings of an extension node.
CustomNodeParameter[]
sources string[] Sources of an extension node.
BatchCalcJobCustomNodeParameter
Represents the field mappings of an extension node.
Fields
Field Name Field Type Description
name string Required. Name of a parameter.

Rebate Management Data Processing Engine
Field Name Field Type Description
value string Required. Value of a parameter.
BatchCalcJobDatasource
Represents a collection of fields relating to a data source node in a data processing engine.
Fields
Field Name Field Type Description
CSVDelimiter BatchCalcJobCSVDelimiter Specifies the field separator to read fields from a CSV file record.
(enumeration of type
Possible values are:
string)
• COMMA
• BACKQUOTE
• CARET
• PIPE
• SEMICOLON
• TAB
The default value is COMMA.
The same delimiter value used for the CSV file can’t be used within any of the
column values in the file. If you mistakenly use the same delimiter value in
column values, it can cause data parsing issues.
description string Description of a data source node.
fields BatchCalcJob Required. Collection of data source fields.
DatasourceField[]
fileIdentifier string Specifies the source of the file or file storage system.
filePath string The file path for the specified file.
fileSource BatchCalcJobFileSource Specifies the source of the file or file storage system.
(enumeration of type
Possible value is:
string)
• ContentManagement
label string Required. Label of a data source node.
name string Required. Name of a data source node.
sourceName string Required. Name of a standard or custom object from which the data source
node extracts data.
type BatchCalcJobDataSource Required. Type of object for the source object field. Supported values are:
Type (enumeration of
• Analytics
type string)
• CalculatedInsightsObject

Rebate Management Data Processing Engine
Field Name Field Type Description
• CRMObject
• CSV
• DataModelObject
• StandardObject
.
BatchCalcJobDatasourceField
Represents a collection of fields relating to a source object field that are selected in the data source node of a data processing engine.
Fields
Field Name Field Type Description
alias string Name that subsequent nodes within the data processing engine use to refer
to the data source field. Required when the field name is lookup.
dataType BatchCalcJobDataType Specifies the data type of the input field when using a CSV file as a data source.
(enumeration of type
Possible values are:
string)
• Boolean—Available in API version 65.0 and later.
• Date
• DateTime
• MultiValue
• Numeric
• Text
isPrimaryKey boolean Indicates whether a column name is the primary key (true) or not (false)
for the Data Cloud CSV file.
name string Required. Name of the field. Can be either of the following:
• Name of the source field selected in the associated data source object.
• Name from a nested lookup object with three child levels.
BatchCalcJobFilter
Represents a collection of fields relating to a filter node in a data processing engine.
Fields
Field Name Field Type Description
criteria BatchCalcJobFilter Collection of filter criteria in a filter node.
Criteria[]
The field is required when isDynamicFilter is set to False.

Rebate Management Data Processing Engine
Field Name Field Type Description
description string Description of the batch calculation job filter.
filterCondition string Logic that is specified to apply the filter conditions.
The field is required when isDynamicFilter is set to False.
filterParameterName string Name of the parameter of type filter.
isDynamicFilter boolean Indicates whether the filter criteria is dynamic. If value is set to True, filter
criteria is passed in runtime with filterParameterName.
label string Required. Label of the filter node.
name string Required. Name of the filter node.
sourceName string Required. Name of the source node.
BatchCalcJobForecast
Represents a collection of fields relating to a forecast node in a data processing engine. Available in API version 58.0 and later.
Fields
Field Field Type Description
Name
accuracyPercent BatchCalcJobFrcstAccuracy (enumeration of type string)
The interval percentage to
account for errors in
forecasts.
Possible values are:
• Eighty
• NinetyFive
• None
The default value is None.
aggregationFields BtchCalcJobFrcstAggrFld[] The list of fields to
forecast.
dateFieldName string Required.
The date field from the
source node used to
forecast values for the
specified forecast length.
description string The description of the
forecast node.

Rebate Management Data Processing Engine
Field Field Type Description
Name
forecastModelType BatchCalcJobFrcstModel (enumeration of type string) The model used to
forecast data.
Possible values are:
• Additive
• Auto
• Multiplicative
The default value is Auto.
forecastPeriodCount int The number of time
periods to generate
forecast data. For example,
if you select Year-Month
as the forecast period
type, and 4 as the forecast
period count, the forecast
results are generated for
the next 4 months.
The minimum and the
default count is 1, and the
maximum is 100.
forecastPeriodType BatchCalcJobFrcstPeriodType (enumeration of type string) Required.
The type of forecast period
to group date field values
in the forecast results.
Possible values are:
• FiscalYear
• FiscalYearMonth
• FiscalYearQuarter
• FiscalYearWeek
• Year
• YearMonth
• YearMonthDay
• YearQuarter
• YearWeek
groupFields BatchCalcJobFrcstGrpFld[] The source fields for
grouping the data to be
processed by the forecast
node.

Rebate Management Data Processing Engine
Field Field Type Description
Name
label string Required.
The name of the forecast
node in the UI.
name string Required.
A unique name for the
forecast node.
periodStartDateName string Required.
The start date of the
forecast period.
seasonality BatchCalcJobFrcstSeasonality (enumeration of type string)
Represents the periodic
fluctuations that occur
around the same time
every year.
Possible values are:
• Two
• Three
• Four
• Five
• Six
• Seven
• Eight
• Nine
• Ten
• Eleven
• Twelve
• Thirteen
• Fourteen
• Fifteen
• Sixteen
• Seventeen
• Eighteen
• Nineteen
• Twenty
• TwentyOne
• TwentyTwo
• TwentyThree

Rebate Management Data Processing Engine
Field Field Type Description
Name
• TwentyFour
• Auto
• None
The default value is None.
shouldExcludeLastPeriodboolean Indicates whether to
ignore the last period in
the source node when it
has incomplete data
(true) or not (false).
The default value is
false.
sourceName string Required.
The name of the source
node.
A source can be any node
other than the datasink
and register node.
BtchCalcJobFrcstAggrFld
Represents a list of fields to forecast in a forecast node.
Field Name Field Type Description
aggregateFunction BatchCalcJobAggregateFunction Required.
(enumeration of type string)
The function of the aggregate field.
Possible values are:
• Avg
• Count
• Max
• Min
• Std
• StdP
• Sum
• Unique
• Var
• VarP

Rebate Management Data Processing Engine
Field Name Field Type Description
aggregationResultLabel string Required.
The name of the aggregation result generated from
the aggregation function that’s applied to the source
node field.
fieldName string Required.
The name of the source field.
BatchCalcJobFrcstGrpFld
Represents source fields for grouping the data to be processed by the forecast node.
Field Name Field Type Description
fieldName string Required.
The name of the source field to group the data to be processed by the
forecast node.
groupBy string A comma-separated list of values to group data by.
Required when the source field type is Date or DateTime.
Possible values are:
• Second
• Second Epoch
• Minute
• Hour
• Day
• Day Epoch
• Week
•
• Month
• Quarter
• Year
BatchCalcJobHierarchyPath
Represents a collection of hierarchy path nodes in a data processing engine definition.
Fields
Field Name Field Type Description
description string Description of the hierarchy path node.

Rebate Management Data Processing Engine
Field Name Field Type Description
hierarchyFieldName string Required. Field name that contains the hierarchy path.
isSelfFieldValueIncluded boolean Indicates whether the self value is included in the calculated hierarchy path
(True) or not (False).
label string Required. Label of the hierarchy path node.
name string Required. Name of the hierarchy path node.
parentFieldName string Required. Parent field name to calculate hierarchy path.
selfFieldName string Required. Self field name to calculate hierarchy path.
sourceName string Required. Name of the source node.
BatchCalcJobFilterCriteria
Represents a collection of fields relating to a filter condition in a filter node in a data processing engine.
Fields
Field Name Field Type Description
inputVariable string Name of the input variable used as a filter.
operator BatchCalcJobFilter Required. Operator that is specified in the filter condition.
Operator
Valid values are:
(enumeration of type
• Equals
string)
• NotEquals
• GreaterThan
• GreaterThanOrEqual
• LessThan
• LessThanOrEqual
• StartsWith
• EndsWith
• Contains
• DoesNotContain
• IsNull
• IsNotNull
• In
• NotIn
sequence integer Required. Sequence number used to refer the criteria in a filter node.
sourceFieldName string Required. Name of the field from the source node to apply the filter.
value string Value used to filter data from the source node.

Rebate Management Data Processing Engine
BatchCalcJobParameter
Represents a collection of fields relating to an input variable in a data processing engine.
Fields
Field Name Field Type Description
dataType BatchCalcJobParameter Required. Data type of the parameter. Valid values are:
DataType
• Date
(enumeration of type
• DateTime
string)
• Expression
• FileIdentifier
• Filter
• Numeric
• Text
defaultValue string Default value of the parameter.
description string Description of the batch calculation job parameter.
isMultiValue boolean Indicates whether the parameter has different values (True) or not (False).
This field is supported only for the Text data type.
label string Required. Label of the batch calculation job parameter.
name string Required. Name of the batch calculation job parameter.
BatchCalcJobSourceJoin
Represents a collection of fields relating to a join node in a data processing engine.
Fields
Field Name Field Type Description
description string Description of the join node.
fields BatchCalcJobJoin Collection of fields in a join node.
ResultField[]
joinKeys BatchCalcJobJoin Collection of mapping of fields from the primary source node and the second
Key[] source node in a join node.
label string Required. Label of the join node.
name string Required. Name of the join node.
primarySourceName string Required. Name associated with the node as the primary source node.
secondarySourceName string Required. Name associated with the node as the secondary source node.

Rebate Management Data Processing Engine
Field Name Field Type Description
type BatchCalcJobSource Required. Type of join specified between the primary source node and
JoinType secondary source node. Valid values are:
(enumeration of type
• LeftOuter
string)
• RightOuter
• Inner
• Outer
• Lookup
BatchCalcJobJoinKey
Represents a collection of fields relating to a mapping of fields from the first source node and second source node in a join node of a
data processing engine.
Fields
Field Name Field Type Description
primarySourceFieldName string Required. Mapped field name of the primary source node.
secondarySourceFieldName string Required. Mapped field name of the secondary source node.
BatchCalcJobJoinResultField
Represents a collection of fields relating to a set of resultant fields in a join node of a data processing engine.
Fields
Field Name Field Type Description
alias string Required. Name that subsequent nodes within the data processing engine
definition use to refer to the resultant field.
sourceFieldName string Required. Name of field from the primary or secondary data source.
sourceName string Required. Source node of the primary or secondary data source.
BatchCalcJobTransform
Represents a collection of fields relating to a data transformation in a data processing engine.
Fields
Field Name Field Type Description
description string The description of the batch calculation job transform.

Rebate Management Data Processing Engine
Field Name Field Type Description
droppedFields BatchCalcJobTransform The collection of dropped fields in a data transformation. Available when the
DroppedField[] transformation type is Slice.
expressionFields BatchCalcJobTransform The collection of formula fields in a data transformation. Available when the
AddedField[] transformation type is Expression.
label string Required. The label of the batch calculation job transform.
name string Required. The name of the batch calculation job transform.
orderBy BatchCalcJobOrderByField A collection of fields that’s used to sort the records within each partition group.
on page 285[]
partitionBy string[] A group of fields that’s used to partition the source data into partition groups.
sourceName string Required. Name of the source node.
transformType BatchCalcJobTransform Required. The type of transformation.
Type (enumeration of
Valid values are:
type string)
• ComputeRelative—This transformation calculates values based on
values of the same partition group.
• Expression—This transformation calculates values based on existing
values of fields in the same record.
• Slice—This transformation removes fields from the source node.
BatchCalcJobTransformDroppedField
Represents a collection of fields relating to a dropped field in a data transformation of a data processing engine.
Fields
Field Name Field Type Description
sourceFieldName string Required. Name of the field that is dropped.
BatchCalcJobTransformAddedField
Represents a collection of fields relating to a formula in a data transformation of a data processing engine.
Fields
Field Name Field Type Description
alias string Required. Name that subsequent nodes within the data processing engine use
to the transform node.

Rebate Management Data Processing Engine
Field Name Field Type Description
dataType BatchCalcJobDataType Required. Data type of the formula.
(enumeration of type
Valid values are:
string)
• Boolean—Available in API version 65.0 and later.
• Date
• DateTime
• MultiValue
• Numeric
• Text
decimalPlaces integer Number of digits to the right of a decimal point in the value. Required for the
Numeric data type.
expression string Required. Formula defined by the user.
length integer Total length of the value including the decimal places. Required for data types:
Text and Numeric.
BatchCalcJobOrderByField
Represents a collection of fields that are used to sort the partitioned data.
Fields
Field Name Field Type Description
name string Required. Name of the field that is used to sort data.
orderType BatchCalcJobOrderType(enumeration Order in which the data is sorted.
of type string)
Valid values are:
• Ascending
• Descending
BatchCalcJobUnion
Represents a collection of fields relating to the union of data from two nodes in a data processing engine.
Fields
Field Name Field Type Description
description string Description of the batch calculation job union.
isDisjointedSchema boolean Indicates whether the union is of two disjointed datasets (true) or not
(false). Set to True to allow joining of two datasets having no common
fields.

Rebate Management Data Processing Engine
Field Name Field Type Description
label string Required. Label of the batch calculation job union.
name string Required. Name of the batch calculation job union.
sources string[] Names of the source nodes.
BatchCalcJobWritebackObject
Represents a collection of fields relating to the object in which the results of the data processing engine are written back.
Fields
Field Name Field Type Description
canWrtbckToNonEditableFields boolean Indicates whether the non-editable fields are included in field mapping when
the action type is upsert. The default value is false.
Available in API version 64.0 and later.
description string Descriptions of the batch calculation job writeback object.
externalIdFieldName string Unique external field ID for the target object name.
Available in API version 60.0 and later.
fields BatchCalcJobWriteback Collection of the writeback fields.
Mapping[]
filterCondition string The condition that filters the records from a writeback dataset for a user.
Examples of a filter condition include a user ID, stage name, and a security
policy that returns only the records that a user owns.
Available in API version 57.0 and later.
folderName string The folder where the writeback dataset is saved. Available in API version 57.0
and later.
groupBy string Reserved for future use.
isChangedRow boolean Indicates whether a row in the write back object is changed. Set to True to
write back the changed rows.
isExistingDataset boolean Indicates whether a CRM Application (CRMA) dataset or a Data 360 Data Lake
object is present (true) or will be created (false). Available in API version
62.0 and later.
label string Required. Name of the write back object.
name string Required. Name of the batch calculation job write back object.
operationType BatchCalcJobWriteback Type of operation specified.
Opn (enumeration of
Valid values are:
type string)

Rebate Management Data Processing Engine
Field Name Field Type Description
• Delete—This value is available in API version 56.0 and later.
• Insert
• Overwrite—Available only when storageType is
DataLakeObject. This value is available in API version 60.0 and later.
• Update
• Upsert
sharingInheritanceObjectName string The name of the source object from which the row-level sharing inheritance
settings are applied. Available in API version 57.0 and later.
shouldCreateTargetObject boolean Indicates whether target Data Lake Object or Salesforce Object is created in
Salesforce (true) or not (false). Available in API version 65.0 and later.
shouldMngRowLockFor boolean Reserved for future use.
GroupedRec
sourceName string Required. Name of the source node associated with the write back object.
storageType BatchCalcJobWriteback Specifies where you want to use the data stored in the source node. Available
Type (enumeration of in API version 57.0 and later.
type string)
Valid values are:
• Analytics
• DataLakeObject
• sObject
The default value is sObject.
targetObjectName string Required. Object that is inserted or upserted by the data processing engine.
writebackSequence integer Sequence in which the target object is updated by the data processing engine.
writebackUser string ID of the user whose permissions decide which objects and fields of the target
object can be updated.
BatchCalcJobWritebackMapping
Represents a collection of fields relating to the mapping between results and the fields in the target object.
Fields
Field Name Field Type Description
fieldType string Target field type on the writeback object. Valid values are:
• Primary Key
• Qualifier Key
Available in API version 64.0 and later.

Rebate Management Data Processing Engine
Field Name Field Type Description
isAutogenerated boolean Indicates whether the target field value on the writeback object is
autogenerated (true) or not (false).
Available in API version 64.0 and later.
parentName string Name of the lookup object. Required only when the relationshipName
field is defined.
relationshipName string Name of the lookup relationship.
runtimeParameter boolean Indicates whether the source field from runtime parameter is true or false.
The default value is false.
Available in API version 59.0 and later.
sourceFieldName string Required. Name of the field in the source node that is written back.
targetFieldName string Name of the sObject field to which the results are written back.
Declarative Metadata Sample Definition
The following is an example of a BatchCalcJobDefinition component.
<?xml version="1.0" encoding="UTF-8"?>
<BatchCalcJobDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
<aggregates>
<description>Aggregate Description</description>
<fields>
<aggregateFunction>Count</aggregateFunction>
<alias>NameCount</alias>
<sourceFieldName>Name</sourceFieldName>
</fields>
<groupBy>ContactId</groupBy>
<groupBy>Name</groupBy>
<label>AggregateOpportunities</label>
<name>AggregateOpportunities</name>
<sourceName>Opportunity</sourceName>
</aggregates>
<forecasts>
<description>ForecastNode Description</description>
<label>ContactForecast</label>
<name>ContactForecast</name>
<sourceName>Contact</sourceName>
<dateFieldName>CreatedDate</dateFieldName>
<forecastPeriodType>YearMonth</forecastPeriodType>
<shouldExcludeLastPeriod>false</shouldExcludeLastPeriod>
<forecastPeriodCount>12</forecastPeriodCount>
<periodStartDateName>CreatedDateYM</periodStartDateName>
<forecastModelType>Auto</forecastModelType>
<seasonality>None</seasonality>
<accuracyPercent>None</accuracyPercent>
<aggregationFields>
<aggregateFunction>Count</aggregateFunction>

Rebate Management Data Processing Engine
<aggregationResultLabel>CountOfLastName</aggregationResultLabel>
<fieldName>LastName</fieldName>
</aggregationFields>
<groupFields>
<fieldName>LastModifiedDate</fieldName>
<groupBy>Week</groupBy>
</groupFields>
</forecasts>
<appends>
<description>Append desc</description>
<isDisjointedSchema>true</isDisjointedSchema>
<label>AppendAllAccounts</label>
<name>AppendAllAccounts</name>
<sources>AccountsOfManufacturingIndustry</sources>
<sources>ComputeRelativeManufacturingIndustry</sources>
</appends>
<datasources>
<description>Desc Contact</description>
<fields>
<alias>Id</alias>
<name>Id</name>
<isPrimaryKey>false</isPrimaryKey>
<dataType>Text</dataType>
</fields>
<fields>
<alias>LastName</alias>
<name>LastName</name>
<isPrimaryKey>false</isPrimaryKey>
<dataType>Text</dataType>
</fields>
<fields>
<alias>CreatedDate</alias>
<name>CreatedDate</name>
<isPrimaryKey>false</isPrimaryKey>
<dataType>Date</dataType>
</fields>
<fields>
<alias>LastModifiedDate</alias>
<name>LastModifiedDate</name>
<isPrimaryKey>false</isPrimaryKey>
<dataType>Date</dataType>
</fields>
<label>Contact</label>
<name>Contact</name>
<sourceName>Contact</sourceName>
<type>StandardObject</type>
<fileSource>ContentManagement</fileSource>
<fileIdentifier>069xx0000004CAeAAM</fileIdentifier>
<CSVDelimiter>COMMA</CSVDelimiter>
<filePath>parentFolder/childFolder</filePath>
</datasources>
<datasources>
<fields>
<alias>Name</alias>

Rebate Management Data Processing Engine
<name>Name</name>
<isPrimaryKey>false</isPrimaryKey>
<dataType>Text</dataType>
</fields>
<fields>
<alias>ContactId</alias>
<name>ContactId</name>
<isPrimaryKey>false</isPrimaryKey>
<dataType>Text</dataType>
</fields>
<label>Opportunity</label>
<name>Opportunity</name>
<sourceName>Opportunity</sourceName>
<type>StandardObject</type>
<fileSource>ContentManagement</fileSource>
<fileIdentifier>069xx0000004CAeAAM</fileIdentifier>
<CSVDelimiter>COMMA</CSVDelimiter>
<filePath>parentFolder/childFolder</filePath>
</datasources>
<description>Calculates and creates transaction journal records based on the orders
placed by the loyalty program members. The transaction journals are used to accrue points
to the member.</description>
<filters>
<criteria>
<operator>Equals</operator>
<sequence>1</sequence>
<sourceFieldName>LastName</sourceFieldName>
<value>Salesforce</value>
</criteria>
<description>Filter Desc</description>
<filterCondition>1</filterCondition>
<isDynamicFilter>false</isDynamicFilter>
<label>AccountsOfManufacturingIndustry</label>
<name>AccountsOfManufacturingIndustry</name>
<sourceName>AccountOpportunities</sourceName>
</filters>
<hierarchyPaths>
<description>Hierarchy Path Node</description>
<hierarchyFieldName>Hierarchy_Path</hierarchyFieldName>
<isAggregationRequired>true</isAggregationRequired>
<isSelfFieldValueIncluded>true</isSelfFieldValueIncluded>
<label>Get Hierarchy</label>
<name>Get_Hierarchy</name>
<parentFieldName>ContactId</parentFieldName>
<selfFieldName>LastName</selfFieldName>
<sourceName>AppendAllAccounts</sourceName>
<aggregateFields>
<aggregateFunction>Count</aggregateFunction>
<aggregationFieldName>*</aggregationFieldName>
<aggregateFieldAliasName>CountOfLastName</aggregateFieldAliasName>
</aggregateFields>
</hierarchyPaths>
<isTemplate>false</isTemplate>
<executionPlatformObjectType>None</executionPlatformObjectType>

Rebate Management Data Processing Engine
<joins>
<description>Left Outer Join</description>
<fields>
<alias>ContactId</alias>
<sourceFieldName>Id</sourceFieldName>
<sourceName>Contact</sourceName>
</fields>
<fields>
<alias>LastName</alias>
<sourceFieldName>LastName</sourceFieldName>
<sourceName>Contact</sourceName>
</fields>
<fields>
<alias>NameCount</alias>
<sourceFieldName>NameCount</sourceFieldName>
<sourceName>AggregateOpportunities</sourceName>
</fields>
<fields>
<alias>OpportunityName</alias>
<sourceFieldName>Name</sourceFieldName>
<sourceName>AggregateOpportunities</sourceName>
</fields>
<joinKeys>
<primarySourceFieldName>Id</primarySourceFieldName>
<secondarySourceFieldName>ContactId</secondarySourceFieldName>
</joinKeys>
<label>AccountOpportunities</label>
<name>AccountOpportunities</name>
<primarySourceName>Contact</primarySourceName>
<secondarySourceName>AggregateOpportunities</secondarySourceName>
<type>LeftOuter</type>
</joins>
<label>Create Transaction Journals Based on Orders</label>
<parameters>
<dataType>Date</dataType>
<defaultValue>2020-01-01</defaultValue>
<description>Desc TextParameter</description>
<isMultiValue>false</isMultiValue>
<label>DateParameter</label>
<name>DateParameter</name>
</parameters>
<parameters>
<dataType>Filter</dataType>
<defaultValue>{&quot;filterCondition&quot;: &quot;1 AND 2&quot;,
&quot;criteria&quot;: [{&quot;sourceFieldName&quot;:
&quot;NameCount&quot;,&quot;operator&quot;: &quot;GreaterThan&quot;,&quot;value&quot;:
&quot;20&quot;,&quot;sequence&quot;: &quot;1&quot;}, {&quot;sourceFieldName&quot;:
&quot;Name&quot;,&quot;operator&quot;: &quot;Equals&quot;,&quot;value&quot;:
&quot;Salesforce&quot;,&quot;sequence&quot;: &quot;2&quot;}]}</defaultValue>
<isMultiValue>false</isMultiValue>
<label>FilterParameter</label>
<name>FilterParameter</name>
</parameters>
<parameters>

Rebate Management Data Processing Engine
<dataType>Numeric</dataType>
<defaultValue>5000</defaultValue>
<description>Desc TextParameter</description>
<isMultiValue>false</isMultiValue>
<label>NumericParameter</label>
<name>NumericParameter</name>
</parameters>
<parameters>
<dataType>Text</dataType>
<defaultValue>@salesforce.com</defaultValue>
<description>Desc TextParameter</description>
<isMultiValue>false</isMultiValue>
<label>TextParameter</label>
<name>TextParameter</name>
</parameters>
<processType>Rebates</processType>
<definitionRunMode>Batch</definitionRunMode>
<status>Inactive</status>
<transforms>
<description>transforms Desc</description>
<expressionFields>
<alias>NewLastName</alias>
<dataType>Text</dataType>
<expression>TODAY()</expression>
<length>80</length>
</expressionFields>
<label>ManufacturingIndustry</label>
<name>ManufacturingIndustry</name>
<sourceName>AccountsOfManufacturingIndustry</sourceName>
<transformationType>Expression</transformationType>
</transforms>
<transforms>
<droppedFields>
<sourceFieldName>NewLastName</sourceFieldName>
</droppedFields>
<label>MediaIndustry</label>
<name>MediaIndustry</name>
<sourceName>ManufacturingIndustry</sourceName>
<transformationType>Slice</transformationType>
</transforms>
<transforms>
<description>compute relative transforms Desc</description>
<expressionFields>
<alias>NewLastName</alias>
<dataType>Text</dataType>
<expression>rank()</expression>
<length>80</length>
</expressionFields>
<label>ComputeRelativeManufacturingIndustry</label>
<name>ComputeRelativeManufacturingIndustry</name>
<orderBy>
<name>LastName</name>
<orderType>Ascending</orderType>
</orderBy>

Rebate Management Data Processing Engine
<partitionBy>LastName</partitionBy>
<sourceName>MediaIndustry</sourceName>
<transformationType>ComputeRelative</transformationType>
</transforms>
<customNodes>
<name>RebatesCustomNode</name>
<label>Rebates Custom Node</label>
<description>customNodes Desc</description>
<sources>Get_Hierarchy</sources>
<extensionName>RebatesExpression</extensionName>
<extensionNamespace>industries_mfg</extensionNamespace>
<parameters>
<name>inputColumn</name>
<value>LastName</value>
</parameters>
<parameters>
<name>isFilterCriteria</name>
<value>true</value>
</parameters>
<parameters>
<name>outputColumn</name>
<value>GenName</value>
</parameters>
</customNodes>
<writebacks>
<fields>
<sourceFieldName>GenName</sourceFieldName>
<targetFieldName>LastName</targetFieldName>
</fields>
<isChangedRow>false</isChangedRow>
<label>exportToContact</label>
<name>exportToContact</name>
<description>Export To Contact</description>
<operationType>Insert</operationType>
<sourceName>RebatesCustomNode</sourceName>
<targetObjectName>Contact</targetObjectName>
<writebackSequence>1</writebackSequence>
<canWrtbckToNonEditableFields>false</canWrtbckToNonEditableFields>
</writebacks>
<writebacks>
<fields>
<sourceFieldName>CreatedDateYM</sourceFieldName>
<targetFieldName>CreatedDate</targetFieldName>
</fields>
<isChangedRow>false</isChangedRow>
<isExistingDataset>false</isExistingDataset>
<label>exportToContactFC</label>
<name>exportToContactFC</name>
<description>Export To Contact</description>
<operationType>Insert</operationType>
<sourceName>ContactForecast</sourceName>
<targetObjectName>Contact</targetObjectName>
<writebackSequence>2</writebackSequence>
<canWrtbckToNonEditableFields>false</canWrtbckToNonEditableFields>

Rebate Management Data Processing Engine
</writebacks>
</BatchCalcJobDefinition>
The following is an example package.xml that references the previous definition.
<?xml version="1.0" encoding="UTF-8"?>
<!--
~ Copyright 2020 Salesforce, Inc.
~ All Rights Reserved
~ Company Confidential
-->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
<types>
<members>*</members>
<name>BatchCalcJobDefinition</name>
</types>
<version>60.0</version>
</Package>
Wildcard Support in the Manifest File
This metadata type supports the wildcard character * (asterisk) in the package.xml manifest file. For information about using the
manifest file, see Deploying and Retrieving Metadata with the Zip File.
Data Processing Engine Invocable Actions
Run an active Data Processing Engine definition. For more information on custom invocable actions, see REST API Developer Guide
and Actions Developer Guide.
Data Processing Engine Actions
Run an active Data Processing Engine definition. This action executes a Data Processing Engine definition asynchronously.
Data Processing Engine Actions
Run an active Data Processing Engine definition. This action executes a Data Processing Engine definition asynchronously.
A Data Processing Engine definition transforms data from your Salesforce org and writes back the results to your org. For more information
about running Data Processing Engine definitions, see Run a Data Processing Engine Definition in Salesforce Help.
This object is available in API version 51.0 and later.
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/custom/dataProcessingEngineAction
Formats
JSON
HTTP Methods
GET, POST
Authentication
Authorization: Bearer token

Rebate Management Data Processing Engine
Inputs
Use the GET method to retrieve input variables of a Data Processing Engine definition. The input variables of each Data Processing Engine
definition are unique. The Data Processing Engine action uses the input variables to execute the Data Processing Engine definition and
generate a batch job ID.
Note: You can't use this action to start two simultaneous runs of a definition with the same input variables.
Outputs
Output Details
batchJobId
Type
string
Description
ID of the batch job generated after the request is successful. This ID is used to track the progress
of the batch job in Monitor Workflow Services.
Usage
JSON Sample Request to execute PointsAccrual DPE Definition
{
"PointsAccrual" : {
"memberTier" : "Gold",
"minimumPointBalanceRequired" : "50000",
"pointType" : "non-qualifying"
}
}
JSON Sample Response
{
"actionName":"PointsAccrual",
"errors":null,
"isSuccess":true,
"outputValues":{
"batchJobId":"0lMxx0000A000001EAA"
}
}
Example
GET
This example shows how to retrieve input variables of a Data Processing Engine action type.
curl --include --request GET \
--header "Authorization: Authorization: Bearer 00DR...xyz" \
--header "Content-Type: application/json" \
"https://instance.salesforce.com/services/data/v60.0/actions/custom/dataProcessingEngineAction/newinputvardefn"

Rebate Management Batch Management
POST
Here’s a request to retrieve DPE definition
{
"inputs": [
{
"start_date": "26-09-2023",
"end_date": "12-12-2023",
"randomkey": "069SM0000001SgbYAE"
}
]
}
Here’s a response for this action.
[
{
"actionName": "newinputvardefn",
"errors": null,
"invocationID": null,
"isSuccess": true,
"outputValues": {
"batchJobId": "0mdSM0000006EJdYAM",
"accepted": true
},
"version": 1
}
]
Batch Management
Automate the processing of records in scheduled flows. You can process a high volume of standard
EDITIONS
and custom object records. Batch Management consists of three Tooling API objects, a standard
object, a Metadata API, and an invocable action. You can use these resources to view, create, edit,
Available in: Lightning
and run Batch Management jobs.
Experience
Available in: Batch
Batch Management Tooling API Objects
Management is available
You can use the Batch Management Tooling API object to view the settings of Batch with Enterprise, Unlimited,
Management jobs. and Performance Editions
with the Loyalty
Batch Management Standard Objects
Management,
Batch Management contains a standard BatchProcessJobDefinitionView object, which you can
Manufacturing Cloud,
use to view all the batch jobs available in your Salesforce org, including file-based jobs.
Rebate Management, or
Batch Management Metadata API Accounting Subledger
Use a Metadata API to create, update, and activate Batch Management jobs.
Batch Management Invocable Actions
Run an active Batch Management job definition. For more information on custom invocable actions, see REST API Developer Guide
and Actions Developer Guide.

Rebate Management Batch Management
Batch Management Tooling API Objects
You can use the Batch Management Tooling API object to view the settings of Batch Management
EDITIONS
jobs.
Tooling API objects let you interact with metadata for declarative development. For example, you Available in: Lightning
can create your own version of Setup. Experience
Available in: Batch
BatchDataSource Management is available
Represents the source of information from which a batch job retrieves records for processing. with Enterprise, Unlimited,
This object is available in API version 66.0 and later. and Performance Editions
with the Loyalty
BatchDataSrcFilterCriteria
Management,
Represents the details of a condition in the filter criteria used to retrieve records from the data Manufacturing Cloud,
source of a batch job. This object is available in API version 66.0 and later. Rebate Management, or
Accounting Subledger
BatchProcessJobDefinition
Represents the details of a Batch Management job. This object is available in API version 51.0
and later.
BatchDataSource
Represents the source of information from which a batch job retrieves records for processing. This object is available in API version 66.0
and later.
Supported Calls
describeSObjects(), query(), retrieve()
Fields
Field Details
BatchJobDefinitionId
Type
reference
Properties
Filter, Group, Sort
Description
The ID of the batch job definition associated with batch data source.
This field is a relationship field.
Relationship Name
BatchJobDefinition
Relationship Type
Master-detail
Refers To
BatchJobDefinition (the master object)

Rebate Management Batch Management
Field Details
CriteriaJoinCondition
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The logic that's used to decide how data source records are filtered.
CriteriaJoinType
Type
picklist
Properties
Defaulted on create, Filter, Group, Restricted picklist, Sort
Description
Specifies the criteria type used to filter data source records.
Possible values are:
• all—All conditions are met (AND)
• any—Any condition is met (OR)
• custom—Customize the logic
• none—No conditions are met
The default value is all.
DataSourceType
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
Specifies the type of data source.
Possible values are:
• MultipleSobjects
• SingleSobject
RelatedSobjects
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The list of objects that are used as data sources for the batch job definition.
SourceFieldName
Type
string

Rebate Management Batch Management
Field Details
Properties
Filter, Group, Nillable, Sort
Description
The field from the source object that's used to run the batch job.
SourceTableName
Type
string
Properties
Filter, Group, Sort
Description
The name of the object from which records are processed by the batch job.
BatchDataSrcFilterCriteria
Represents the details of a condition in the filter criteria used to retrieve records from the data source of a batch job. This object is available
in API version 66.0 and later.
Supported Calls
describeSObjects(), query(), retrieve()
Fields
Field Details
BatchDataSourceId
Type
reference
Properties
Filter, Group, Sort
Description
The ID of the batch data source associated with the batch data source filter criteria.
This field is a relationship field.
Relationship Name
BatchDataSource
Relationship Type
Master-detail
Refers To
BatchDataSource (the master object)
DomainObjectName
Type
string

Rebate Management Batch Management
Field Details
Properties
Filter, Group, Nillable, Sort
Description
The name of the object that contains the field that's used in the filter criteria condition.
DynamicValueType
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
Specifies the data type of the input variable that's used in the filter criteria condition.
Possible values are:
• boolean
• currency
• date
• datetime
• integer
• picklist
• reference
• string
FieldName
Type
string
Properties
Filter, Group, Sort
Description
The name of the field that's used in the filter criteria condition.
FieldPath
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The patch of the related object field that's used in the filter criteria condition.
FieldValue
Type
string
Properties
Filter, Group, Sort

Rebate Management Batch Management
Field Details
Description
The value of the specified field used to filter records of the data source.
FilterCriteriaSequence
Type
int
Properties
Filter, Group, Sort
Description
The sequence number of the condition in the filter criteria.
IsDynamicValue
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates whether the value of the filter criteria condition is provided by an input variable.
The default value is false.
Operator
Type
picklist
Properties
Filter, Group, Restricted picklist, Sort
Description
Specifies the operator used in the filter criteria condition.
Possible values are:
• equals—Equals
• excludes—Excludes
• greaterThan—Greater Than
• greaterThanOrEqualTo—Greater Than Or Equal To
• in—In
• includes—Includes
• isNotNull—Is Not Null
• isNull—Is Null
• lessThan—Less Than
• lessThanOrEqualTo—Less Than Or Equal To
• like—Like
• notEquals—Not Equals
• notIn—Not In

Rebate Management Batch Management
BatchProcessJobDefinition
Represents the details of a Batch Management job. This object is available in API version 51.0 and later.
Note: Where possible, we changed noninclusive terms to align with our company value of Equality. We maintained certain terms
to avoid any effect on customer implementations.
Data and processes in your org are impacted if you update or delete a BatchProcessJobDefinition record. Update or delete a Batch
Management job using the Metadata API on page 310.
Supported SOAP API Calls
describeSObjects(), query(), retrieve()
Supported REST API Methods
DELETE, GET, HEAD, PATCH, POST, Query
Fields
Field Details
BatchJobDefinitionId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
The unique identifier of the associated batch job definition.
This is a relationship field.
Relationship Name
BatchJobDefinition
Relationship Type
Lookup
Refers To
BatchJobDefinition
BatchJobDefinitionName
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The name of the associated batch job definition.
BatchSize
Type
int
Properties
Filter, Group, Sort

Rebate Management Batch Management
Field Details
Description
Required. The number of records that each Batch Management job part can process. The
maximum number of transaction journal records that a batch management job can process
for flow or loyalty program process is 2000.
Description
Type
textarea
Properties
Filter, Group, Nillable, Sort
Description
The description of the Batch Management job.
DeveloperName
Type
string
Properties
Filter, Group, Sort
Description
The developer name of the Batch Management job.
FlowDefinitionId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
The input variable of the associated flow that uniquely identifies each record that the Batch
Management job processes.
FullName
Type
string
Properties
Create, Group, Nillable
Description
The name of the Batch Management job.
Query this field only if the query result contains no more than one record. Otherwise, an error
is returned. If more than one record exists, use multiple queries to retrieve the records. This
limit protects performance.
Language
Type
picklist
Properties
Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort

Rebate Management Batch Management
Field Details
Description
The language in which the batch job is created.
Possible values are:
• da—Danish
• de—German
• en_US—English
• es—Spanish
• es_MX—Spanish (Mexico)
• fi—Finnish
• fr—French
• it—Italian
• ja—Japanese
• ko—Korean
• nl_NL—Dutch
• no—Norwegian
• pt_BR—Portuguese (Brazil)
• ru—Russian
• sv—Swedish
• th—Thai
• zh_CN—Chinese (Simplified)
• zh_TW—Chinese (Traditional)
ManageableState
Type
ManageableState enumerated list
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
Indicates the manageable state of the specified component that is contained in a package:
• beta
• deleted
• deprecated
• deprecatedEditable
• installed
• installedEditable
• released
• unmanaged
MasterLabel
Type
string

Rebate Management Batch Management
Field Details
Properties
Filter, Group, Sort
Description
The label of the Batch Management job.
Metadata
Type
complexvalue
Properties
Create, Nillable, Update
Description
The Batch Management job's metadata.
Query this field only if the query result contains no more than one record. Otherwise, an error
is returned. If more than one record exists, use multiple queries to retrieve the records. This
limit protects performance.
NamespacePrefix
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The namespace prefix that is associated with this object. Each Developer Edition org that
creates a managed package has a unique namespace prefix. Limit: 15 characters. You can
refer to a component in a managed package by using the
namespacePrefix__componentName notation.
The namespace prefix can have one of the following values.
• In Developer Edition orgs, NamespacePrefix is set to the namespace prefix of the
org for all objects that support it, unless an object is in an installed managed package.
In that case, the object has the namespace prefix of the installed managed package. This
field’s value is the namespace prefix of the Developer Edition org of the package
developer.
• In orgs that are not Developer Edition orgs, NamespacePrefix is set only for objects
that are part of an installed managed package. All other objects have no namespace
prefix.
ProcessGroup
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The group or team for which the Batch Management job processes records.

Rebate Management Batch Management
Field Details
RecordIdVariable
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The unique identifier that identifies each record that must be processed by the Batch
Management job.
RetryCount
Type
int
Properties
Defaulted on create, Filter, Group, Sort
Description
Required. The number of times this Batch Management job must be rerun in case it fails.
RetryInterval
Type
int
Properties
Defaulted on create, Filter, Group, Sort
Description
Required. The number of milliseconds after which the Batch Management job must be rerun
in case it fails. A retry interval can be 1,000–10,000 milliseconds.
Status
Type
picklist
Properties
Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort
Description
The status of the Batch Management job.
Possible values are:
• Active
• Inactive
Type
Type
picklist
Properties
Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort
Description
The type of process for which the Batch Management job processes records.
Possible values are:
• Flow

Rebate Management Batch Management
Field Details
• BulkUpdate
• ConsumptionOveragesCalculation
• DecisionTableRefresh
• DeepCloneSalesAgreement
• EntitlementCreationBatchJob
• HighScaleBreProcess
• IndustriesLSCommercial
• LoyaltyProgramProcess
• ManagerProvisioning
• NetUnitRateCalculation
• PbbToOptyConversion
• ProductCatalogCacheRefresh
• RatableSummaryCreation
• SummaryCreation
The default value is Flow. Other types may be available to you depending on the licenses
available in your org.
This field is available in API version 55.0 and later.
TypeInstance
Type
string
Properties
Filter, Group, Sort
Description
Required. The API name of the process that the Batch Management job must execute.
Batch Management Standard Objects
Batch Management contains a standard BatchProcessJobDefinitionView object, which you can use
EDITIONS
to view all the batch jobs available in your Salesforce org, including file-based jobs.
Available in: Lightning
BatchProcessJobDefView Experience
Represents the details of a Batch Job definition. The definition can also be file-based definitions
Available in: Batch
that are available in your Salesforce org. This object is available in API version 51.0 and later.
Management is available
with Enterprise, Unlimited,
and Performance Editions
BatchProcessJobDefView
with the Loyalty
Represents the details of a Batch Job definition. The definition can also be file-based definitions Management,
that are available in your Salesforce org. This object is available in API version 51.0 and later. Manufacturing Cloud,
Rebate Management, or
Accounting Subledger

Rebate Management Batch Management
Supported Calls
describeSObjects(), query()
Fields
Field Details
DurableId
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The unique identifier for the field. Always retrieve this value before using it, as the value isn’t
guaranteed to stay the same from one release to the next. Simplify queries by using this field
instead of making multiple queries.
IsActive
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates whether the definition is active.
Label
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The label of the Batch Job definition.
Name
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The name of the Batch Job definition.
NamespacePrefix
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The namespace prefix associated with this object. Each Developer Edition organization that
creates a managed package has a unique namespace prefix. Limit: 15 characters. You can

Rebate Management Batch Management
Field Details
refer to a component in a managed package by using the
namespacePrefix__componentName notation.
The namespace prefix can have one of the following values:
• In Developer Edition organizations, the namespace prefix is set to the namespace prefix
of the organization for all objects that support it. There is an exception if an object is in
an installed managed package. In that case, the object has the namespace prefix of the
installed managed package. This field’s value is the namespace prefix of the Developer
Edition organization of the package developer.
• In organizations that are not Developer Edition organizations, NamespacePrefix is only
set for objects that are part of an installed managed package. There is no namespace
prefix for all other objects.
ProcessDefinition
Type
textarea
Properties
Nillable
Description
The name of the process group for the batch process job definition.
ProcessGroup
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The team or group for which the definition processes records.
SourceObjectName
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The API name of the object whose records are processed.
Type
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The type of process for which the Batch Management job processes records.
Possible values are:
• Flow
• LoyaltyProgramProcess

Rebate Management Batch Management
Field Details
This field is available in API version 55.0 and later.
TypeInstance
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The API name of the process that's processed by the Batch Job definition.
Batch Management Metadata API
Use a Metadata API to create, update, and activate Batch Management jobs.
EDITIONS
BatchProcessJobDefinition Available in: Lightning
Represents the details of a Batch Management job definition. Experience
Available in: Batch
Management is available
BatchProcessJobDefinition
with Enterprise, Unlimited,
Represents the details of a Batch Management job definition. and Performance Editions
with the Loyalty
This type extends the Metadata metadata type and inherits its fullName field.
Management,
Important: Where possible, we changed noninclusive terms to align with our company Manufacturing Cloud,
value of Equality. We maintained certain terms to avoid any effect on customer Rebate Management, or
implementations. Accounting Subledger
File Suffix and Directory Location
BatchProcessJobDefinition components have the suffix .batchProcessJobDefinition and are stored in the
batchProcessJobDefinitions folder.
Version
BatchProcessJobDefinition components are available in API version 51.0 and later.
Special Access Rules
To use this metadata type, your Salesforce org must have the Loyalty Management or the Rebate Management license. The Loyalty
Program Process type is only available in orgs that have Loyalty Management enabled.
Fields
Field Name Field Type Description
batchSize integer Required. Number of records that each Batch Management job can
process. Flow type Batch Management jobs can process up to 2000

Rebate Management Batch Management
Field Name Field Type Description
records and Loyalty Program Process type Batch Management jobs can
process up to 250 records.
dataSource BatchDataSource Required. Source of information whose records must be processed by
on page 312[] the Batch Management job.
description string Description of the Batch Management job, up to 255 characters.
executionProcessApiName string API name of process that must be executed by the Batch Management
job. This field is available in API version 55.0 and later.
• If the batch job’s type is Flow, enter the API name of an active flow
that the batch job must execute.
• If the batch job’s type is Loyalty Program Process, enter:
– Transaction_Journals if you want the batch job to process
Transaction Journal records by applying the applicable active
loyalty program process of the type TransactionJournal.
– API name of an active loyalty process of the type TierProcessing
if you want the batch job to run the loyalty program process to
assess the tier of eligible members. The API name consists of the
name of the process, the process type, and the name of the
loyalty program separated by two consecutive underscores. For
example, the process API name is Update Member
Tier__TierProcessing__Inner Circle if the
process name is Update Member Tier, the process type is
TierProcessing, and the loyalty program name is Inner Circle.
You can use database-based APEX classes that let you use flex queues in
the Batch Management job, allowing to place more than 5 jobs in a
queue. This functionality is applicable to all Industry Clouds that use
managed packages. See Apex Flex Queue.
flowApiName string API name of an active flow process that must be executed by the Batch
Management job.
You can either specify the flow API name in the
executionProcessApiName field or in the flowApiName
field.
flowInputVariable string Input variable of associated flow that is used by the batch job to uniquely
identify records.
masterLabel string Required. Name of the Batch Management job, up to 80 characters.
processGroup string Required. Name of the group for which the Batch Management job
processes records.
retryCount integer Required. Number of times this Batch Management job must be rerun
in case it fails. The maximum retry count is 3. Valid values are 1–3.

Rebate Management Batch Management
Field Name Field Type Description
retryInterval integer Required. Number of milliseconds after which the Batch Management
job must be rerun in case it fails. Valid values are 1,000–10,000.
status string Indicates the status of the Batch Management job. Valid values are
Active and Inactive.
type string (enumeration The type of process that the Batch Management job must execute. This
of type string) field is available in API version 55.0 and later. Valid values are:
• Flow
• Loyalty Program Process
BatchDataSource
Represents the source of information whose records must be processed by the Batch Management job.
Fields
Field Name Field Type Description
condition string Required. Criteria defined to filter the records.
criteria string Type of filter criteria that’s used to filter records for processing.
dataSourceType string Type of data source that's used to create the batch job definition. Valid values
are:
• SingleSobject
• MultiSobject
Available in API version 64.0 and later.
filters BatchDataSrcFilterCriteria Filter criterion that decides which records must be processed by the Batch
on page 313[] Management job.
orderFields BatchDataSourceOrderField Fields that are used to order the records before the records are added to a
on page 314 batch in a job.
sourceObject string Required. API name of an object whose records must be processed by the
batch job.
If the batch job type is Loyalty Program Process, the source object must be:
• TransactionJournal if the batch job is used to process transaction journals
by applying the applicable loyalty program process.
• An object that stores the details of loyalty program members whose tier
must be assessed by the loyalty program process specified in the
executionProcessApiName field.

Rebate Management Batch Management
Field Name Field Type Description
sourceObjectField string API name of the source object field that uniquely identifies records for which
the batch job is executed. This field is available in API version 57.0 and later.
This field is only applicable when the batch job’s type is Loyalty Program Process
and a TierProcess type active loyalty program process is specified in the
executionProcessApiName field. Specify the API name of a field that
is a lookup to the LoyaltyProgramMember object and uniquely identifies the
members whose tier must be assessed.
BatchDataSrcFilterCriteria
Represents the filter conditions that decide which records must be processed by the Batch Management job.
Fields
Field Name Field Type Description
domainObjectName string Name of the object the field is associated with. Available in API version 64.0
and later.
dynamicValueType string Data type of the input variable used as a filter.
fieldName string Required. Name of the field that must be used to filter records.
fieldPath string Stores the path to a field in the object. Available in API version 64.0 and later.
fieldValue string Required. Value of the field that must be filtered. Specify the field if
isDynamicValue is set to False.
isDynamicValue boolean Required. Indicates whether the filter criteria is dynamic.
operator string (enumeration Required. Operator that is specified in the filter criteria. Valid values are:
of type string)
• equals
• excludes
• greaterThan
• greaterThanOrEqualTo
• in
• includes
• lessThan
• LessThanOrEqualTo
• GreaterOrEqual
• like
• notEquals
• notIn
sequenceNo integer Required. Sequence number used to refer the criteria in a filter.

Rebate Management Batch Management
BatchDataSourceOrderField
Represents the fields that are used to group data.
Fields
Field Name Field Type Description
domainObjectName string Required. Name of the object the field is associated with. Available in API version
64.0 and later.
fieldName string Required. Name of the field that must be used to filter records. Available in API
fieldPath string Required. Stores the path to a field in the object. Available in API version 64.0
and later.
Declarative Metadata Sample Definition
The following is an example of a BatchProcessJobDefinition component.
<?xml version="1.0" encoding="UTF-8"?>
<BatchProcessJobDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
<batchSize>10</batchSize>
<dataSource>
<condition>1</condition>
<criteria>all</criteria>
<filters>
<dynamicValue>false</dynamicValue>
<dynamicValueType>string</dynamicValueType>
<fieldName>Name</fieldName>
<fieldValue>abcd</fieldValue>
<operator>equals</operator>
<sequenceNo>1</sequenceNo>
</filters>
<sourceObject>Account</sourceObject>
</dataSource>
<flowApiName>Flow1</flowApiName>
<flowInputVariable>recordId</flowInputVariable>
<masterLabel>BatchJob1</masterLabel>
<processGroup>Loyalty</processGroup>
<retryCount>2</retryCount>
<retryInterval>1000</retryInterval>
<status>Inactive</status>
<description>test</description>
<type>Flow</type>
<executionProcessApiName>testFlow</executionProcessApiName>
</BatchProcessJobDefinition>
The following is an example of a Flow object used in Metadata API.
<?xml version="1.0" encoding="UTF-8"?>

Rebate Management Batch Management
<!--
~ Copyright 2020 Salesforce, Inc.
~ All Rights Reserved
~ Company Confidential
-->
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
<apiVersion>51.0</apiVersion>
<interviewLabel>Flow1 {!$Flow.CurrentDateTime}</interviewLabel>
<label>Flow1</label>
<processMetadataValues>
<name>BuilderType</name>
<value>
<stringValue>LightningFlowBuilder</stringValue>
</value>
</processMetadataValues>
<processMetadataValues>
<name>OriginBuilderType</name>
<value>
<stringValue>LightningFlowBuilder</stringValue>
</value>
</processMetadataValues>
<processType>AutoLaunchedFlow</processType>
<recordLookups>
<name>getAcc</name>
<label>getAcc</label>
<locationX>614</locationX>
<locationY>465</locationY>
<assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
<filterLogic>and</filterLogic>
<filters>
<field>Id</field>
<operator>EqualTo</operator>
<value>
<elementReference>recordId</elementReference>
</value>
</filters>
<getFirstRecordOnly>true</getFirstRecordOnly>
<object>Account</object>
<storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>
<start>
<locationX>73</locationX>
<locationY>213</locationY>
<connector>
<targetReference>getAcc</targetReference>
</connector>
</start>
<status>Draft</status>
<variables>
<name>recordId</name>
<dataType>String</dataType>
<isCollection>false</isCollection>
<isInput>true</isInput>
<isOutput>false</isOutput>

Rebate Management Batch Management
</variables>
</Flow>
The following is an example package.xml that references the previous definition.
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
<types>
<members>*</members>
<name>BatchProcessJobDefinition</name>
</types>
<types>
<members>Flow1</members>
<name>Flow</name>
</types>
<version>51.0</version>
</Package>
Wildcard Support in the Manifest File
This metadata type supports the wildcard character * (asterisk) in the package.xml manifest file. For information about using the
manifest file, see Deploying and Retrieving Metadata with the Zip File.
Batch Management Invocable Actions
Run an active Batch Management job definition. For more information on custom invocable actions, see REST API Developer Guide
and Actions Developer Guide.
Batch Job Actions
Run an active Batch Management job definition. This action executes a defined Batch Management job asynchronously.
Submit Failed Records Batch Job
Run to resubmit an existing batch job with failed records for processing. This action executes the batch job asynchronously.
Batch Job Actions
Run an active Batch Management job definition. This action executes a defined Batch Management job asynchronously.
A Batch Management job processes a flow in manageable parts. For more information about running an active Batch Management jobs,
see Schedule a Batch Job in Salesforce Help.
This object is available in API version 51.0 and later.
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/custom/batchJobAction
Formats
JSON
HTTP Methods
GET, POST

Rebate Management Batch Management
Authentication
Authorization: Bearer token
Inputs
The batch job action uses the batch job definition ID and input variables to execute the job and generate a batch job ID. The input values
vary according to the input variables in that flow.
Outputs
Output Details
batchJobId
Type
string
Description
ID of the batch job generated after the request is successful. This batch job ID is used to track
the progress of the batch job in Monitor Workflow Services.
Usage
A request body is always required. The input values vary according to the input variables in that flow. If your batch job doesn't require
any input variables, you still must send an empty JSON body.
{
"inputs": [{}]
}
JSON Sample Request
{
"noOfEmployees" : 900,
"accountIndustry" : "Technology"
}
JSON Sample Response
{
"batchJobId": "0lMxx0000A000001EAA"
"accepted": "true"
}
Submit Failed Records Batch Job
Run to resubmit an existing batch job with failed records for processing. This action executes the batch job asynchronously.
This object is available in API version 52.0 and later.
Supported REST HTTP Methods
URI
/services/data/vXX.X/actions/standard/submitFailedRecordsBatchJob

Rebate Management Batch Management
Formats
JSON
HTTP Methods
GET, POST
Authentication
Authorization: Bearer token
Inputs
Input Details
failedRecordIds
Type
array
Description
The IDs of failed records in a batch job.
parentBatchJobId
Type
string
Description
Required. The ID of a batch job with failed records.
Outputs
Output Details
batchJobId
Type
string
Description
The ID of a batch job generated after the request is successful. This batch job ID is used to track
the progress of the batch job in Monitor Workflow Services in the org.
status
Type
string
Description
Indicates whether a batch job succeeded or failed.
Usage
JSON Sample Request
{
"inputs": [{
"parentBatchJobId": "0mdRM0000004DXrYAM",
"failedRecordIds": [

Rebate Management Monitor Workflow Services
"001RM000005AG0bYAG", "001RM000005AERZYA4", "001RM000005AG0WYAW"
]
}]
}
JSON Sample Response
[ {
"actionName" : "submitFailedRecordsBatchJob",
"errors" : null,
"isSuccess" : true,
"outputValues" : {
"batchJobId" : "0mdRM0000004DZ9YAM"
}
} ]
Monitor Workflow Services
The Montior Workflow Services standard objects can be used to track the run of Data Processing
EDITIONS
Engine definitons and Batch Management jobs. During a run, you can view details about each part
that the run is broken down into. After the run is complete, you can view its status and the records
Available in: Lightning
which weren't processed during the run.
Experience
The objects of Monitor Workflow Services aren't available in Object Manager of your Salesforce org.
Available in: Monitor
Workflow Services is
BatchJob available with Enterprise,
Represents an instance of a batch job that is either running and has been run. This object is Unlimited, and Performance
Editions where Data
available in API version 51.0 and later.
Processing Engine or Batch
BatchJobPart
Management is avaiable
Represents one part of a batch job. This object is available in API version 51.0 and later.
BatchJobPartFailedRecord
Represents records that a batch job part couldn't successfully process. This object is available in API version 51.0 and later.
BatchJob
Represents an instance of a batch job that is either running and has been run. This object is available in API version 51.0 and later.
Supported Calls
delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(), retrieve(),
search(), undelete()
Fields
Field Details
AdditionalInformation
Type
textarea

Rebate Management Monitor Workflow Services
Field Details
Properties
Create, Nillable, Update
Description
A JSON that contains additional context about the batch jon.
BatchJobDefinitionId
Type
reference
Properties
Filter, Group, Sort
Description
The unique identifier of the associated batch job definition.
This is a relationship field.
Relationship Name
BatchJobDefinition
Relationship Type
Lookup
Refers To
BatchJobDefinition
BatchJobDefinitionName
Type
string
Properties
Filter, Group, Sort
Description
The developer name of the associated batch job definition.
EndTime
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the batch job run was completed.
ErrorDescription
Type
string
Properties
Filter, Nillable, Sort
Description
The error message in case the batch job run failed.

Rebate Management Monitor Workflow Services
Field Details
ExecutionStage
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort, Update
Description
Specifies the stage at which the batch job's run failed. This field is available in API version
66.0 and later.
Possible values are:
• Datasync
• Execution
• Preprocessing
• Writeback
ExternalReference
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The unique identifier of the process that's running or has run the batch job.
IsDebugOn
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether debug mode was turned on (true) or not (false) when a definition was
run.
The default value is false.
IsDebugRecipeDeleted
Type
boolean
Properties
Create, Defaulted on create, Filter, Group, Sort, Update
Description
Indicates whether debug recipes and datasets were deleted (true) or not (false).
When the IsDebugOn is set to True, and the definition is run, after 7 days
IsDebugRecipeDeleted is automatically set to True, and debug recipes and datasets are
deleted.
The default value is false.

Rebate Management Monitor Workflow Services
Field Details
LastReferencedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp for when the current user last viewed the batch job.
LastViewedDate
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp for when the current user last viewed this item.
Name
Type
string
Properties
Filter, Group, idLookup, Sort
Description
The name of the batch job.
OwnerId
Type
reference
Properties
Filter, Group, Sort
Description
Unique identifier of the user who initiated the batch job run.
This is a polymorphic relationship field.
Relationship Name
Owner
Relationship Type
Lookup
Refers To
Group, User
ProcessGroup
Type
string
Properties
Filter, Group, Sort
Description
The group or team for which the batch job is run.

Rebate Management Monitor Workflow Services
Field Details
RetryCount
Type
int
Properties
Filter, Group, Nillable, Sort
Description
The number of times the batch job run is automatically rerun in case it fails.
RuntimeParameter
Type
textarea
Properties
Nillable
Description
The values of the input variables that are used as filter criteria in a Batch Management job.
StartTime
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the batch job run was started.
Status
Type
picklist
Properties
Filter, Group, Restricted picklist, Sort
Description
The status of the batch job run.
Possible values are:
• Canceled
• Completed
• CompletedWithFailures
• Failed
• InProgress
• Queued
• QueueingInProgress
• Submitted
TotalInputRecordCount
Type
int

Rebate Management Monitor Workflow Services
Field Details
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The total number of records that were provided as input to the batch job. This field is available
in API version 66.0 and later.
TotalProcessedRecordCount
Type
int
Properties
Filter, Group, Nillable, Sort
Description
The total number of records that were processed by all the batch job parts associated with
the batch job. This field is available in API version 66.0 and later.
Type
Type
picklist
Properties
Defaulted on create, Filter, Group, Restricted picklist, Sort
Description
The type of batch job that is run.
Possible values are:
• Calc—Data Processing Engine
• DecisionTableRefresh
• Flow
• DeepCloneSalesAgreement
• ManagerProvisioning
The process types available to you vary depending on the licenses available in your org.
UtilisedExecutionLimit
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The CRM Analytics or Data 360 execution capacity utilized by Data Processing Engine batch
jobs before the current run started. This field is available in API version 66.0 and later.
UtilisedWritebackLimit
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update

Rebate Management Monitor Workflow Services
Field Details
Description
The CRM Analytics or Data 360 writeback capacity utilized by Data Processing Engine batch
jobs before the current run started. This field is available in API version 66.0 and later.
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
BatchJobFeed
Feed tracking is available for the object.
BatchJobHistory
History is available for tracked fields of the object.
BatchJobPart
Represents one part of a batch job. This object is available in API version 51.0 and later.
When a batch job is run, it is divided in to multiple parts. Each part is used to process a specific number of records.
Supported Calls
describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(), retrieve()
Fields
Field Details
BatchJobId
Type
reference
Properties
Filter, Group, Sort
Description
The unique identifier of the associated batch job.
This is a relationship field.
Relationship Name
BatchJob
Relationship Type
Lookup
Refers To
BatchJob
EndTime
Type
dateTime

Rebate Management Monitor Workflow Services
Field Details
Properties
Filter, Nillable, Sort
Description
The timestamp when the batch job part was processed.
ErrorDescription
Type
string
Properties
Filter, Nillable, Sort
Description
The error message in case the batch job part failed.
FailedRecFileBody
Type
base64
Properties
Nillable
Description
Contains the details of the records that the batch job part failed to process.
FailedRecFileContentType
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
Shows the type of data that the batch job part failed to process. For example,
application/html or text/csv.
FailedRecFileLength
Type
int
Properties
Filter, Group, Nillable, Sort
Description
The character length of the failed record file.
FailedRecFileName
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The name of the file that contains the details of the failed records.

Rebate Management Monitor Workflow Services
Field Details
FailedRecordCount
Type
int
Properties
Filter, Group, Nillable, Sort
Description
The number of records that the batch job part couldn't process.
FailedRowCount
Type
long
Properties
Filter, Group, Nillable, Sort
Description
The number of records that were processed but the batch job part failed to write back for a
Data Processing Engine definition run. This field is available in API version 66.0 and later.
InputRecordCount
Type
int
Properties
Filter, Group, Nillable, Sort
Description
The number of records that the batch job part must process.
InputRowCount
Type
long
Properties
Filter, Group, Nillable, Sort
Description
The number of records that were submitted to the batch job part for a Data Processing
Engine definition run. This field is available in API version 66.0 and later.
Name
Type
string
Properties
Filter, Group, idLookup, Sort
Description
The name of the batch job part.
OutputRecordCount
Type
int
Properties
Filter, Group, Nillable, Sort

Rebate Management Monitor Workflow Services
Field Details
Description
The number of records the batch job part has processed.
OutputRowCount
Type
long
Properties
Filter, Group, Nillable, Sort
Description
The number of records that were processed by the batch job part for a Data Processing
Engine definition run. This field is available in API version 66.0 and later.
ParentBatchJobPartId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
The unique identifier of the part batch job part associated with the batch job part.
This is a relationship field.
Relationship Name
ParentBatchJobPart
Relationship Type
Lookup
Refers To
BatchJobPart
RecordFileBody
Type
base64
Properties
Nillable
Description
Contains the details of the records that the batch job part processed.
RecordFileContentType
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
Shows the type of data that the batch job part processed. For example,
application/html or text/csv.

Rebate Management Monitor Workflow Services
Field Details
RecordFileLength
Type
int
Properties
Filter, Group, Nillable, Sort
Description
The character length of the file that contains the records that the batch job part processed.
RecordFileName
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The name of the file that contains the details of the records that the batch job part processed.
RetryCount
Type
int
Properties
Filter, Group, Nillable, Sort
Description
The number of times the batch job part is automatically rerun in case it fails.
StartTime
Type
dateTime
Properties
Filter, Nillable, Sort
Description
The timestamp when the batch job part's run was started.
Status
Type
picklist
Properties
Defaulted on create, Filter, Group, Restricted picklist, Sort
Description
The status of the batch job part.
Possible values are:
• Canceled
• Completed
• Failed
• InProgress
• New

Rebate Management Monitor Workflow Services
Field Details
• Waiting
Type
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
The type of node in case the associated batch job is of the type Calc (Data Processing Engine).
Possible values are:
• Aggregate
• Analysis
• Append
• AtomicWriteback
• Compute
• CsvIngestion
• Custom
• Datasync
• Execution
• Filter
• Forecast
• Hierarchy
• Join
• OutputRecordsNode
• Register
• Slice
• Source
• Summary
• Transform
• Writeback
UserReference
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The ID of the user who is assigned as the writeback user in the Writeback Object node of the
Data Processign Engine definition for which the batch job part has written back results. This
field is available in API version 66.0 and later.

Rebate Management Monitor Workflow Services
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
BatchJobPartFeed
Feed tracking is available for the object.
BatchJobPartHistory
History is available for tracked fields of the object.
BatchJobPartFailedRecord
Represents records that a batch job part couldn't successfully process. This object is available in API version 51.0 and later.
Supported Calls
describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(), retrieve()
Fields
Field Details
BatchJobId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
The unique identifier of the associated batch job.
This is a relationship field.
Relationship Name
BatchJob
Relationship Type
Lookup
Refers To
BatchJob
BatchJobPartId
Type
reference
Properties
Filter, Group, Sort
Description
The unique identifier of the associated batch job part.
This is a relationship field.
Relationship Name
BatchJobPart

Rebate Management Monitor Workflow Services
Field Details
Relationship Type
Lookup
Refers To
BatchJobPart
ErrorDescription
Type
string
Properties
Filter, Nillable, Sort
Description
The error message that indicates why the batch job part couldn't process the records.
Name
Type
string
Properties
Filter, Group, idLookup, Sort
Description
The name of the batch job part failed record.
Record
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The unique identifier of the batch record that processed the failed records.
RecordName
Type
string
Properties
Filter, Group, Nillable, Sort
Description
The name of the record that's associated with the batch job part failed record.
ResubmittedBatchJobId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
The batch job used to submit failed records. This field is available in API version 52.0 and
later.
This is a relationship field.

Rebate Management Monitor Workflow Services
Field Details
Relationship Name
ResubmittedBatchJob
Relationship Type
Lookup
Refers To
BatchJob
Status
Type
picklist
Properties
Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort
Description
Specifies the status of the failed records. This field is available in API version 52.0 and later.
Possible values are:
• Failed
• Resubmitted
The default value is 'Failed'.
Associated Objects
This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.
BatchJobPartFailedRecordFeed
Feed tracking is available for the object.
BatchJobPartFailedRecordHistory
History is available for tracked fields of the object.

STOCK ROTATION
Manage structured product returns and inventory replacement programs. Automate the end-to-end lifecycle of stock rotation, from
partner submission and validation to claim creation and budget tracking.
Stock Rotation Business APIs
You can access Stock Rotation Business APIs using REST endpoints. These REST APIs follow similar conventions as Connect REST APIs.
Stock Rotation Business APIs
You can access Stock Rotation Business APIs using REST endpoints. These REST APIs follow similar conventions as Connect REST APIs.
To understand the architecture, authentication, rate limits, and how the requests and responses work, see Connect REST API Developer
Guide.
Resources
Learn more about the available Stock Rotation API resources.
Request Bodies
Learn more about the available request bodies of Stock Rotation APIs.
Response Bodies
Learn more about the available response bodies of Stock Rotation APIs.
Resources
Learn more about the available Stock Rotation API resources.
Stock Rotation Execution (POST)
Performs a stock rotation action for the specified line items and filters.
Stock Rotation Execution (POST)
Performs a stock rotation action for the specified line items and filters.
Resource
/connect/stock-rotation-execution
Resource example
https://yourInstance.salesforce.com/services/data/v66.0/connect/stock-rotation-execution
Available version
66.0
HTTP methods
POST

Stock Rotation Resources
Request body for POST
JSON example
{
"actionType": "GenerateClaim",
"stockRotationExecutionId": "1Ft1234567890abcdef",
"sourceObjectIds": [
"obj-1",
"obj-2",
"obj-3"
],
"filterCriteria": {
"fieldCriteria": [
{
"fieldApiName": "AccepedQuantity",
"operator": "GreaterThan",
"filterValues": [
"100"
]
},
{
"fieldApiName": "Status",
"operator": "In",
"filterValues": [
"ReadyForClaim"
]
}
]
}
}
Properties
Name Type Description Required or Available
Optional Version
actionType String The action to perform on the stock Required 66.0
rotation execution. Valid values are:
• GenerateClaim — Generate
claims for scrapped items and
returns.
• CalculateClaimAmount —
Calculate the claim amount for the
stock rotation line items that are
filtered.
filterCriteria Stock Rotation The filter criteria for selecting stock Optional. Either 66.0
Filter Criteria Input rotation line items. sourceObjectIds
or
filterCriteria
must be provided.

Stock Rotation Request Bodies
Name Type Description Required or Available
Optional Version
sourceObjectIds String[] The IDs of stock rotation line items to Optional. Either 66.0
include in the action. sourceObjectIds
or
filterCriteria
must be provided.
stockRotationExecutionId String The ID of the stock rotation execution to Required. 66.0
run the action on.
Response body for POST
Stock Rotation Execution on page 338
Request Bodies
Learn more about the available request bodies of Stock Rotation APIs.
Stock Rotation Execution Input
Input representation for performing an action on a stock rotation execution.
Stock Rotation Field Criteria Input
Individual filter criteria for stock rotation operations
Stock Rotation Execution Input
Input representation for performing an action on a stock rotation execution.
JSON example
{
"actionType": "GenerateClaim",
"stockRotationExecutionId": "1Ft1234567890abcdef",
"sourceObjectIds": [
"obj-1",
"obj-2",
"obj-3"
],
"filterCriteria": {
"fieldCriteria": [
{
"fieldApiName": "AccepedQuantity",
"operator": "GreaterThan",
"filterValues": [
"100"
]
},
{
"fieldApiName": "Status",
"operator": "In",

Stock Rotation Request Bodies
"filterValues": [
"ReadyForClaim"
]
}
]
}
}
Properties
Name Type Description Required or Available
Optional Version
actionType String The action to perform on the stock rotation Required 66.0
execution. Valid values are:
• GenerateClaim — Generate
claims for scrapped items and returns.
• CalculateClaimAmount —
Calculate the claim amount for the
stock rotation line items that are
filtered.
filterCriteria Stock Rotation Filter The filter criteria for selecting stock rotation Optional. Either 66.0
Criteria Input line items. sourceObjectIds
or
filterCriteria
must be provided.
sourceObjectIds String[] The IDs of stock rotation line items to Optional. Either 66.0
include in the action. sourceObjectIds
or
filterCriteria
must be provided.
stockRotationExecutionId String The ID of the stock rotation execution to Required. 66.0
run the action on.
Stock Rotation Field Criteria Input
Individual filter criteria for stock rotation operations
JSON example
{
"filterCriteria": [
{
"fieldApiName": "Industry__c",
"operator": "Equals",
"filterValues": [
"Healthcare"
]
}

Stock Rotation Response Bodies
]
}
Properties
Name Type Description Required or Available
Optional Version
fieldApiName String The API name of the field to filter on. Required 66.0
filterValues Array of String The values used to filter line items based Required 66.0
on the field and operator.
operator String The comparison operator applied to the Required 66.0
field. Valid values are:
• Contains
• Equals
• GreaterThan
• GreaterThanOrEqual
• In
• LessThan
• LessThanOrEqual
• NotEquals
• NotIn
Response Bodies
Learn more about the available response bodies of Stock Rotation APIs.
Stock Rotation Execution
Output representation for a stock rotation action request.
Stock Rotation Output Error
Represents an error returned by a stock rotation action, including the error code and a message explaining the failure.
Stock Rotation Execution
Output representation for a stock rotation action request.
JSON example
{
"stockRotationExecutionId": "1Ft1234567890abcdef",
"isSuccess": true,
"errorDetails": null
}

Stock Rotation Response Bodies
Property Name Type Description Filter Group and Available Version
Version
errorDetails Stock Rotation Details of errors if the operation was Big, 66.0 66.0
Output Error[] unsuccessful.
isSuccess Boolean Indicates whether the operation was Big, 66.0 66.0
successful (true) or not (false).
stockRotationExecutionId String The stock rotation execution ID that was Big, 66.0 66.0
processed.
Stock Rotation Output Error
Represents an error returned by a stock rotation action, including the error code and a message explaining the failure.
JSON example
{
"errorDetails": [
{
"code": "VALIDATION_ERROR",
"message": "Action type is required"
}
]
}
Property Name Type Description Filter Group and Available Version
Version
code String The error code for the failure. Big, 66.0 66.0
message String The error message for the failure. Big, 66.0 66.0

SHIP AND DEBIT PROCESS MANAGEMENT
Use Ship and Debit Process Management to create ship and debit programs and set up special prices and discounts that partners receive
for different products.
Ship and Debit Process Management Standard Objects
Ship and Debit Process Management data model provides objects and fields to create and manage end-to-end ship and debit
programs. Use these objects to define special pricing and discounts, enabling manufacturers to compensate partners for competitively
priced products and protect partner margins.
Ship and Debit Process Management Standard Objects
Ship and Debit Process Management data model provides objects and fields to create and manage
EDITIONS
end-to-end ship and debit programs. Use these objects to define special pricing and discounts,
enabling manufacturers to compensate partners for competitively priced products and protect
Available in: Lightning
partner margins.
Experience
Available in: Enterprise,
Channel Partner Inventory Tracking Object in Ship and Debit Process Management
Professional, and
Channel Partner Inventory Tracking provides access to a standard object that you can use in Unlimited, Editions
Ship and Debit Process Management to monitor the deduction details and link credit and debit
transactions.
Rebate Management Objects in Ship and Debit Process Management
Rebate Management provides access to standard objects that you can use in Ship and Debit Process Management to create and
manage end-to-end ship and debit programs.
Channel Partner Inventory Tracking Object in Ship and Debit Process
Management
Channel Partner Inventory Tracking provides access to a standard object that you can use in Ship and Debit Process Management to
monitor the deduction details and link credit and debit transactions.
For more information about the Channel Partner Inventory Tracking object, refer to this resource.
• PartnerUnsoldInvLedger on page 9
Rebate Management Objects in Ship and Debit Process Management
Rebate Management provides access to standard objects that you can use in Ship and Debit Process Management to create and manage
end-to-end ship and debit programs.
For more information about the Rebate Management objects, refer to these resources.
• RebateClaim on page 169
• RebateClaimAdjustment on page 177

Ship and Debit Process Management Rebate Management Objects in Ship and Debit Process
Management
• RebateMemberClaimAggregrate on page 180
• RebatePartnerSpecialPrcTrm on page 190
• RebateProgram on page 196
• RebateProgramMember on page 199
• RebatePtnrSpclPrcTrmBnft on page 205

CHANNEL REVENUE MANAGEMENT ASSOCIATED OBJECTS
This section provides a list of objects associated to Channel Revenue Management standard objects with their standard fields.
Some fields may not be listed for some objects. To see the system fields for each object, see System Fields in the Object Reference for
Salesforce and Lightning Platform.
To verify the complete list of fields for an object, use a describe call from the API or inspect with an appropriate tool. For example, inspect
the WSDL or use a schema viewer.
StandardObjectName Feed Feed
StandardObjectNameFeed is the model for all feed objects associated with standard objects. These objects represent the
posts and feed-tracked changes of a standard object.
StandardObjectName History History
StandardObjectNameHistory is the model for all history objects associated with standard objects. These objects represent the
history of changes to the values in the fields of a standard object.
StandardObjectName OwnerSharingRule OwnerSharingRule
StandardObjectNameOwnerSharingRule is the model for all owner sharing rule objects associated with standard objects.
These objects represent a rule for sharing a standard object with users other than the owner.
StandardObjectName Share Share
StandardObjectNameShare is the model for all share objects associated with standard objects. These objects represent a
sharing entry on the standard object.
StandardObjectName Feed Feed
StandardObjectNameFeed is the model for all feed objects associated with standard objects. These objects represent the posts
and feed-tracked changes of a standard object.
The object name is variable and uses StandardObjectNameFeed syntax. For example, AccountFeed represents the posts and
feed-tracked changes on an account record. We list the available associated feed objects at the end of this topic. For specific version
information, see the documentation for the standard object.
Supported Calls
delete(), describeSObjects(), getDeleted(), getUpdated(), query(), retrieve()
Special Access Rules
In the internal org, users can delete all feed items they created. This rule varies in Experience Cloud sites where threaded discussions
and delete-blocking are enabled. Site members can delete all feed items they created, provided the feed items don’t have content nested
under them—like a comment, answer, or reply. Where the feed item has nested content, only feed moderators and users with the
Modify All Data permission can delete threads.
To delete feed items they didn’t create, users must have one of these permissions:
• Modify All Data

Channel Revenue Management Associated Objects StandardObjectName Feed Feed
• Modify All Records on the parent object, like Account for AccountFeed
• Moderate Chatter
Note: Users with the Moderate Chatter permission can delete only the feed items and comments they can see.
Only users with this permission can delete items in unlisted groups.
For more special access rules, if any, see the documentation for the standard object. For example, for AccountFeed, see the special access
rules for Account.
Fields
Field Details
BestCommentId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
The ID of the comment marked as best answer on a question post.
Body
Type
textarea
Properties
Nillable, Sort
Description
The body of the post. Required when Type is TextPost. Optional when Type is
ContentPost or LinkPost.
CommentCount
Type
int
Properties
Filter, Group, Sort
Description
The number of comments associated with this feed item.
ConnectionId
Type
reference
Properties
Filter, Group, Nillable, Sort
Description
When a PartnerNetworkConnection modifies a record that is tracked, the CreatedBy field
contains the ID of the system administrator. The ConnectionId contains the ID of the
PartnerNetworkConnection. Available if Salesforce to Salesforce is enabled for your
organization.

Channel Revenue Management Associated Objects StandardObjectName Feed Feed
Field Details
InsertedById
Type
reference
Properties
Group, Nillable, Sort
Description
ID of the user who added this item to the feed. For example, if an application migrates posts
and comments from another application into a feed, the InsertedBy value is set to the
ID of the context user.
isRichText
Type
boolean
Properties
Defaulted on create, Filter, Group, Sort
Description
Indicates whether the feed item Body contains rich text. If you post a rich text feed comment
using SOAP API, set IsRichText to true and escape HTML entities from the body.
Otherwise, the post is rendered as plain text.
Rich text supports the following HTML tags:
• <p>
Tip: Though the <br> tag isn’t supported, you can use <p>&nbsp;</p> to
create lines.
• <a>
• <b>
• <code>
• <i>
• <u>
• <s>
• <ul>
• <ol>
• <li>
• <img>
The <img> tag is accessible only through the API and must reference files in Salesforce
similar to this example: <img src="sfdc://069B0000000omjh"></img>
Note: In API version 35.0 and later, the system replaces special characters in rich text
with escaped HTML. In API version 34.0 and prior, all rich text appears as a plain-text
representation.
LikeCount
Type
int

Channel Revenue Management Associated Objects StandardObjectName Feed Feed
Field Details
Properties
Filter, Group, Sort
Description
The number of likes associated with this feed item.
LinkUrl
Type
url
Properties
Nillable, Sort
Description
The URL of a LinkPost.
NetworkScope
Type
picklist
Properties
Group, Nillable, Restricted picklist, Sort
Description
Specifies whether this feed item is available in the default Experience Cloud site, a specific
Experience Cloud site, or all sites. This field is available in API version 26.0 and later, if digital
experiences is enabled for your org.
NetworkScope can have the following values:
• NetworkId—The ID of the Experience Cloud site in which the FeedItem is available.
If left empty, the feed item is only available in the default Experience Cloud site.
• AllNetworks—The feed item is available in all Experience Cloud sites.
Note the following exceptions for NetworkScope:
• Only feed items with a Group or User parent can set a NetworkId or a null value for
NetworkScope.
• For feed items with a record parent, users can set NetworkScope only to
AllNetworks.
• You can’t filter a feed item on the NetworkScope field.
ParentId
Type
reference
Properties
Filter, Group, Sort
Description
ID of the record that is tracked in the feed. The detail page for the record displays the feed.
RelatedRecordId
Type
reference

Channel Revenue Management Associated Objects StandardObjectName Feed Feed
Field Details
Properties
Group, Nillable, Sort
Description
ID of the ContentVersion record associated with a ContentPost. This field is null for all
posts except ContentPost.
Title
Type
string
Properties
Group, Nillable, Sort
Description
The title of the feed item. When the Type is LinkPost, the LinkUrl is the URL and
this field is the link name.
Type
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
The type of feed item. Values are:
• ActivityEvent—indirectly generated event when a user or the API adds a Task
associated with a feed-enabled parent record (excluding email tasks on cases). Also
occurs when a user or the API adds or updates a Task or Event associated with a case
record (excluding email and call logging).
For a recurring Task with CaseFeed disabled, one event is generated for the series only.
For a recurring Task with CaseFeed enabled, events are generated for the series and each
occurrence.
• AdvancedTextPost—created when a user posts a group announcement and, in
Lightning Experience as of API version 39.0 and later, when a user shares a post.
• AnnouncementPost—Not used.
• ApprovalPost—generated when a user submits an approval.
• BasicTemplateFeedItem—Not used.
• CanvasPost—a post made by a canvas app posted on a feed.
• CollaborationGroupCreated—generated when a user creates a public group.
• CollaborationGroupUnarchived—Not used.
• ContentPost—a post with an attached file.
• CreatedRecordEvent—generated when a user creates a record from the publisher.
• DashboardComponentAlert—generated when a dashboard metric or gauge
exceeds a user-defined threshold.
• DashboardComponentSnapshot—created when a user posts a dashboard
snapshot on a feed.

Channel Revenue Management Associated Objects StandardObjectName Feed Feed
Field Details
• LinkPost—a post with an attached URL.
• PollPost—a poll posted on a feed.
• ProfileSkillPost—generated when a skill is added to a user’s Chatter profile.
• QuestionPost—generated when a user posts a question.
• ReplyPost—generated when Chatter Answers posts a reply.
• RypplePost—generated when a user creates a Thanks badge in WDC.
• TextPost—a direct text entry on a feed.
• TrackedChange—a change or group of changes to a tracked field.
• UserStatus—automatically generated when a user adds a post. Deprecated.
Visibility
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
Specifies whether this feed item is available to all users or internal users only. This field is
available if dgitial experiences is enabled for your org.
Visibility can have the following values:
• AllUsers—The feed item is available to all users who have permission to see the
feed item.
• InternalUsers—The feed item is available to internal users only.
Note the following exceptions for Visibility:
• For record posts, Visibility is set to InternalUsers for all internal users by
default.
• External users can set Visibility only to AllUsers.
• On user and group posts, only internal users can set Visibility to
InternalUsers.
Usage
A feed for an object is automatically created when a user enables feed tracking for the object. Use feeds to track changes to records. For
example, AccountFeed tracks changes to an account record. Use feed objects to retrieve the content of feed fields, such as type of feed
or feed ID.
Note the following SOQL restrictions. No SOQL limit if logged-in user has the View All Data permission. If not, specify a LIMIT clause
of 1,000 records or fewer. SOQL ORDER BY on fields using relationships is not available. Use ORDER BY on fields on the root object
in the SOQL query.
Object That Follows This Model
This object follows the standard pattern for associated feed objects.

Channel Revenue Management Associated Objects StandardObjectName History History
• BatchJob
• BatchJobPart
• BatchJobPartFailedRecord
StandardObjectName History History
StandardObjectNameHistory is the model for all history objects associated with standard objects. These objects represent the
history of changes to the values in the fields of a standard object.
The object name is variable and uses StandardObjectNameHistory syntax. For example, AccountHistory represents the history of
changes to the values of an account record’s fields. We list the available associated history objects at the end of this topic. For specific
version information, see the documentation for the standard object.
Supported Calls
describeSObjects(), getDeleted(), getUpdated(), query(), retrieve()
Special Access Rules
For specific special access rules, if any, see the documentation for the standard object. For example, for AccountHistory, see the special
access rules for Account.
Fields
Field Name Details
StandardObjectNameId
Type
reference
Properties
Filter, Group, Sort
Description
ID of the standard object.
DataType
Type
picklist
Properties
Filter, Group, Nillable, Restricted picklist, Sort
Description
Data type of the field that was changed.
Field
Type
picklist
Properties
Filter, Group, Restricted picklist, Sort

Channel Revenue Management Associated Objects StandardObjectName OwnerSharingRule OwnerSharingRule
Field Name Details
Description
Name of the field that was changed.
NewValue
Type
anyType
Properties
Nillable, Sort
Description
New value of the field that was changed.
OldValue
Type
anyType
Properties
Nillable, Sort
Description
Old value of the field that was changed.
Objects That Follow This Model
These objects follow the standard pattern for associated history objects.
• AccountLeadTime
• BatchJob
• BatchJobPart
• BatchJobPartFailedRecord
• PartnerStagedData
• PartnerUnsoldInventory
• PartnerUnsoldInvLedger
• PtnrInvItmRecon
• PtnrInvItmReconTrace
StandardObjectName OwnerSharingRule OwnerSharingRule
StandardObjectNameOwnerSharingRule is the model for all owner sharing rule objects associated with standard objects. These
objects represent a rule for sharing a standard object with users other than the owner.
The object name is variable and uses StandardObjectNameOwnerSharingRule syntax. For example,
ChannelProgramOwnerSharingRule is a rule for sharing a channel program with users other than the channel program owner. We list
the available associated owner sharing rule objects at the end of this topic. For specific version information, see the standard object
documentation.

Channel Revenue Management Associated Objects StandardObjectName OwnerSharingRule OwnerSharingRule
Note: To enable access to this object for your org, contact Salesforce customer support. However, we recommend that you
instead use Metadata API to programmatically update owner sharing rules because it triggers automatic sharing rule recalculation.
The SharingRules Metadata API type is enabled for all orgs.
Supported Calls
create(), delete(), describeSObjects(), getDeleted(), getUpdated(), query(), retrieve(), update(),
upsert()
Special Access Rules
For specific special access rules, if any, see the documentation for the standard object. For example, for ChannelProgramOwnerSharingRule,
see the special access rules for ChannelProgram.
Fields
Field Name Details
AccessLevel
Type
picklist
Properties
Create, Filter, Group, Restricted picklist, Sort, Update
Description
Determines the level of access users have to records. Values are:
• Read (read only)
• Edit (read/write)
Description
Type
textarea
Properties
Create, Filter, Nillable, Sort, Update
Description
Description of the sharing rule. Maximum length is 1000 characters.
DeveloperName
Type
string
Properties
Create, Filter, Group, Nillable, Sort, Update
Description
The unique name of the object in the API. This name can contain only underscores
and alphanumeric characters, and must be unique in your org. It must begin with
a letter, not include spaces, not end with an underscore, and not contain two
consecutive underscores. In managed packages, this field prevents naming
conflicts on package installations. With this field, a developer can change the

Channel Revenue Management Associated Objects StandardObjectName Share Share
Field Name Details
object’s name in a managed package and the changes are reflected in a
subscriber’s organization.
When creating large sets of data, always specify a unique DeveloperName
for each record. If no DeveloperName is specified, performance slows down
while Salesforce generates one for each record.
GroupId
Type
reference
Properties
Create, Filter, Group, Sort
Description
ID of the source group. Records that are owned by users in the source group
trigger the rule to give access.
Name
Type
string
Properties
Create, Filter, Group, idLookup, Sort, Update
Description
Label of the sharing rule as it appears in the UI. Maximum length is 80 characters.
UserOrGroupId
Type
reference
Properties
Create, Filter, Group, Sort
Description
ID of the user or group that you are granting access to.
Objects That Follow This Model
These objects follow the standard pattern for associated owner sharing rule objects.
• AccountLeadTime
• PartnerStagedData
• PartnerUnsoldInventory
StandardObjectName Share Share
StandardObjectNameShare is the model for all share objects associated with standard objects. These objects represent a sharing
entry on the standard object.

Channel Revenue Management Associated Objects StandardObjectName Share Share
The object name is variable and uses StandardObjectNameShare syntax. For example, AccountBrandShare is a sharing entry on
an account brand. We list the available associated share objects at the end of this topic. For specific version information, see the standard
object documentation.
Supported Calls
create(), delete(), describeSObjects(), query(), retrieve(), update(), upsert()
Special Access Rules
For specific special access rules, if any, see the documentation for the standard object. For example, for AccountBrandShare, see the
special access rules for AccountBrand.
Fields
Field Name Details
AccessLevel
Type
picklist
Properties
Create, Filter, Group, Restricted picklist, Sort, Update
Description
The level of access allowed. Values are:
• All (owner)
• Edit (read/write)
• Read (read only)
ParentId
Type
reference
Properties
Create, Filter, Group, Sort
Description
ID of the parent record.
RowCause
Type
picklist
Properties
Create, Filter, Group, Nillable, Restricted picklist, Sort
Description
Reason that the sharing entry exists.
UserOrGroupId
Type
reference

Channel Revenue Management Associated Objects StandardObjectName Share Share
Field Name Details
Properties
Create, Filter, Group, Sort
Description
ID of the user or group that has been given access to the object.
Object That Follows This Model
This object follows the standard pattern for associated share objects.
• AccountLeadTime
• TransitTime
• PartnerStagedData
• PartnerUnsoldInventory