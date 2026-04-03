# Salesforce Automotive Cloud Developer Guide
Source: https://developer.salesforce.com/docs/
Downloaded: 2026-04-03

> **Version:** 66.0, Spring '26 — Last updated: April 3, 2026
>
> **Scope of this extract:** This document covers pages 1–24 of the Automotive Cloud Developer Guide. It includes the introduction and the beginning of Chapter 2 (Automotive Cloud Standard Objects). The 24 pages capture complete field documentation for: AccountAccountRelation, ActionableEventOrchestration, ActionableEventSubtype, ActionableEventType, and the start of ActionableEventTypeDef. The full guide covers 100+ domain objects including Vehicle, VehicleDefinition, FinancialAccount, Appraisal, Claim, WarrantyTerm, and many more.

---

Introduction to Automotive Cloud Developer Guide

This guide provides information on the objects and APIs used by
Automotive Cloud. You can also find developer resources for
features that can be used to extend Automotive Cloud.


> **Editions:**

The Automotive Cloud data model provides a set of objects and
fields that you can use to store and manage information about
vehicles, parts, and accessories. You can track and manage all
stakeholders involved in the lifecycle of a vehicle, and you can use
features such as Action Plans, Records Alerts, Timeline, or Interest Tags to access and share additional
information.

> Available in: Enterprise,
Unlimited, and Developer
Editions.

Extend Automotive Cloud with other standard objects such as BusinessBrand, BusinessMilestone, LifeEvent,
GeoCode, and UnitOfMeasure.

Use the Engagement data model and Identity Verification to work with Service Console for Automotive.

If you’re using sales agreements, advanced account forecasting, program-based business, and account
manager targets, refer to Manufacturing Cloud Developer Guide.

Automotive Cloud integration assets are available in MuleSoft Direct for customers to deploy to their
MuleSoft instance. The integration APIs give the customers the flexibility to extend or customize the
integrations as required. See the Automotive Cloud Integrations API guide for more information and
details about the Automotive Cloud integration assets.


## CHAPTER 2 Automotive Cloud Standard Objects

Automotive Cloud data model provides objects and fields to
manage vehicles, customers, stakeholders, and financial
relationships for your automotive company. Both dealer groups
and original equipment manufacturers (OEMs) can use Automotive
Cloud for varied requirements. Use the Automotive Cloud objects
to manage vehicle definitions and vehicles, track stakeholders,
manage leads, and report sales of vehicles and parts. Automotive
Cloud is available in Lightning Experience.


> **Editions:**

> Available in: Enterprise,
Unlimited, and Developer
Editions.

SEE ALSO:

Salesforce Help: Automotive Cloud Data Model

In this chapter ...

- AccountAccountRelation

- ActionableEventOrchestration

- ActionableEventSubtype

- ActionableEventType

- ActionableEventTypeDef

- ActionableOrchResponseEvent

- ActionableOrchSourceEvent

- Appraisal

- AppraisalAdjustment

- AppraisalItem

- AppraisalItemAddOn

- AppraisalItemProviderVal

- AssessmentIndicatorDefinition

- AssetAccountParticipant

- AssetContactParticipant

- AssetMilestone

- AssetTitle

- AssetTitleParty

- AssetWarranty

- Claim

- ClaimCoverage

- ClaimCoveragePaymentDetail

- ClaimItem

- ClaimParticipant

- Codeset

- CodesetRelationship

- ContactContactRelation

- DealerVehDefSearchableField

- 

- 

- 

- 

FinancialAccount

FinancialAccountAddress

FinancialAccountBalance

FinancialAccountFee


Automotive Cloud Standard Objects

- 

- 

- 

- 

- 

- 

- 

- 

FinancialAccountMilestone

FinancialAccountParty

FinancialAccountStatement

FinancialAccountTransaction

FinclAcctPtyFinclAsset

Fleet

FleetAsset

FleetParticipant

- GenericVisitTask

- GenericVisitTaskContext

- GnrcVstKeyPerformanceInd

- GnrcVstTaskContextRelation

- Holiday

- 

- 

LeadLineItem

LeadPreferredSeller

- OpportunityPreferredSeller

- PartyCreditPrflFinclAcct

- PartyCreditProfileAlert

- PartyCreditProfileInquiry

- PartyFinancialAsset

- PartyFinclAssetAddlOwner

- PartyRelationshipGroup

- PartyRoleRelation

- ProductFaultCode

- ProductLaborCode

- ProductWarrantyTerm

- PtyCrPrflFinclAcctActvty

- RebateClaim

- 

- 

- 

- 

- 

- 

- 

- 

- 

- 

- 

- 

- 

- 

SellerProduct

ServiceAppointment

ServiceResourceSkill

ServiceTerritory

ServiceTerritoryMember

Skill

SkillRequirement

TelemetryActionDefinition

TelemetryActionDefStep

TelemetryActionRelatedProcess

TelemetryActnDefStepAttr

TelemetryDefinition

TelemetryDefinitionVersion

TimeSlot


Automotive Cloud Standard Objects

- 

TransactionJournal

- Vehicle

- VehicleDefinition

- VehDefSearchableField

- VehicleSearchableField

- Visit

- WarrantyTerm

- WarrantyTermCoverage

- WorkType

- WorkTypeGroup

- WorkTypeGroupMember


Automotive Cloud Standard Objects

AccountAccountRelation

AccountAccountRelation

Represents a relationship between accounts, such as a relationship between a dealer account and a household account. This object is
available in API version 58.0 and later.

Supported Calls

create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(),  search(),  undelete(),  update(),  upsert()

Special Access Rules

Automotive and Group Membership must be enabled.

Fields

Field

AccountId

EndDate

Details

Type

reference

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


Automotive Cloud Standard Objects

AccountAccountRelation

Field

Details

Description

Specifies the hierarchy between accounts that are related.

Possible values are:

- Child

- Parent

- Peer

The default value is  Parent.

IsActive

Type

boolean

Properties

Create, Defaulted on create, Filter, Group, Sort, Update

Description

Indicates whether the account is actively involved with the related account (true) or not
(false).

The default value is  false.

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


Automotive Cloud Standard Objects

AccountAccountRelation

Field

Details

Properties

Create, Defaulted on create, Filter, Group, Sort, Update

Description

ID of the owner of this object.

This field is a polymorphic relationship field.

PartyRoleRelationId

RelatedAccountId

Relationship Name

Owner

Relationship Type

Lookup

Refers To

Group, User

Type

reference

Properties

Create, Filter, Group, Sort, Update

Description

The relationship between two accounts.

This field is a relationship field.

Relationship Name
PartyRoleRelation

Relationship Type

Lookup

Refers To

PartyRoleRelation

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


Automotive Cloud Standard Objects

AccountAccountRelation

Field

RelatedInverseRecordId

Details

Type

reference

Properties

Create, Filter, Group, Nillable, Sort, Update

Description

The record that specifies the inverse relationship between the accounts.

StartDate

This field is a relationship field.

Relationship Name

RelatedInverseRecord

Relationship Type

Lookup

Refers To

AccountAccountRelation

Type

date

Properties

Create, Filter, Group, Nillable, Sort, Update

Description

The date when the relationship starts.

Associated Objects

This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.

AccountAccountRelationChangeEvent

Change events are available for the object.

AccountAccountRelationFeed

Feed tracking is available for the object.

AccountAccountRelationHistory

History is available for tracked fields of the object.

AccountAccountRelationOwnerSharingRule
Sharing rules are available for the object.

AccountAccountRelationShare

Sharing is available for the object.


Automotive Cloud Standard Objects

ActionableEventOrchestration

ActionableEventOrchestration

Represents the details of an actionable event and specifies how to orchestrate the processes. The record stores details such as the event
type, subtype, and category, and the expression set and the context mappings related to an orchestration. This object is available in API
version 63.0 and later.

Supported Calls

create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(),  search(),  update(),  upsert()

Fields

Field

ApiName

Details

Type

string

Properties

ContextDefinitionId

Create, Filter, Group, idLookup, Sort

Description

The API name of an actionable event orchestration record.

Type

reference

Properties

Create, Filter, Group, Nillable, Sort, Update

Description

The context definition related to the expression set that processes an actionable event.

This field is a relationship field.

ContextDefinitionName

Relationship Name
ContextDefinition

Refers To

ContextDefinition

Type

string

Properties

Create, Filter, Group, Nillable, Sort, Update

Description

The name of a context definition that's associated with the actionable event orchestration.

ContextMappingId

Type

reference


Automotive Cloud Standard Objects

ActionableEventOrchestration

Field

Details

Properties

Create, Filter, Group, Nillable, Sort, Update

Description

The context mapping that processes an actionable event.

This field is a relationship field.

ContextMappingName

DefinitionId

EventCategory

EventSubtypeId

Relationship Name
ContextMapping

Refers To

ContextMapping

Type

string

Properties

Create, Filter, Group, Nillable, Sort, Update

Description

The name of a context mapping in the context definition that's associated with the actionable
event orchestration.

Type

reference

Properties

Filter, Group, Nillable, Sort, Update

Description

The unique identifier of the actionable event orchestration's definition.

This field is a relationship field.

Relationship Name

Definition

Refers To

ActionableEventOrchDef

Type

picklist

Properties

Create, Filter, Group, Nillable, Sort, Update

Description

The category of an actionable event.

Type

reference

Properties

Create, Filter, Group, Nillable, Sort, Update


Automotive Cloud Standard Objects

ActionableEventOrchestration

Field

EventTypeId

ExecutionProcedureId

Details

Description

The subtype of an actionable event.

This field is a relationship field.

Relationship Name
EventSubtype

Refers To

ActionableEventSubtype

Type

reference

Properties

Create, Filter, Group, Sort, Update

Description

The type of an actionable event.

This field is a relationship field.

Relationship Name
EventType

Refers To

ActionableEventType

Type

reference

Properties

Create, Filter, Group, Sort, Update

Description

The expression set or flow definition that executes the orchestration.

This field is a relationship field.

Relationship Name

ExecutionProcedure

Refers To

ExpressionSet

ExecutionProcedureName

Type

string

Properties

Create, Filter, Group, Nillable, Sort, Update

Description

The name of the flow definition or the expression set template that executes the orchestration.

ExecutionProcedureType

Type

picklist


Automotive Cloud Standard Objects

ActionableEventOrchestration

Field

Details

Properties

Create, Filter, Group, Restricted picklist, Sort, Update

Description

Specifies the type of automated procedure that executes the orchestration.

IsActive

Possible values are:

- Expression Set-Based

- Flow-Based

Type

boolean

Properties

Create, Defaulted on create, Filter, Group, Sort, Update

Description

Specifies if an actionable event orchestration record is active (true) or not (false).

The default value is  false.

IsInstalledTemplate

Type

boolean

Properties

Defaulted on create, Filter, Group, Sort

Description

Indicates whether the actionable event orchestration is an installed template that can't be
modified (true) or not (false).

The default value is  false.

IsTemplate

Type

boolean

Properties

Defaulted on create, Filter, Group, Sort

Description

Indicates whether the actionable event orchestration is a template (true) or not (false).

The default value is  false.

LastReferencedDate

Type

dateTime

Properties

Filter, Nillable, Sort

Description

The date the associated location was last modified.


Automotive Cloud Standard Objects

ActionableEventOrchestration

Field

LastViewedDate

Details

Type

dateTime

Properties

Filter, Nillable, Sort

Description

Name

OwnerId

UsageType

The date the associated location was last viewed.

Type

string

Properties

Create, Filter, Group, idLookup, Sort, Update

Description

The name of an actionable event orchestration record.

Type

reference

Properties

Create, Defaulted on create, Filter, Group, Sort, Update

Description

The owner ID of an actionable event orchestration record.

This field is a polymorphic relationship field.

Relationship Name

Owner

Refers To

Group, User

Type

picklist

Properties

Create, Filter, Group, Restricted picklist, Sort, Update

Description

The usage type of the event orchestration.

Possible values are:

- Automotive

- Standard

Associated Objects

This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.


Automotive Cloud Standard Objects

ActionableEventSubtype

ActionableEventOrchestrationChangeEvent
Change events are available for the object.

ActionableEventOrchestrationFeed

Feed tracking is available for the object.

ActionableEventOrchestrationHistory

History is available for tracked fields of the object.

ActionableEventOrchestrationOwnerSharingRule

Sharing rules are available for the object.

ActionableEventOrchestrationShare
Sharing is available for the object.

ActionableEventSubtype

Represents the subtype of an external or internal event that's processed by the Actionable Event Orchestration framework to trigger
different types of actions. This object is available in API version 62.0 and later.

Supported Calls

create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(),  search(),  undelete(),  update(),  upsert()

Fields

Field

ActionableEventTypeId

Details

Type

reference

Properties

Create, Filter, Group, Sort

Description

The parent event type related to an actionable event subtype.

This field is a relationship field.

Relationship Name

ActionableEventType

Relationship Type
Master-detail

Refers To

ActionableEventType (the master object)

Type

string

Properties

Create, Filter, Group, Sort


ApiName


Automotive Cloud Standard Objects

ActionableEventType

Field

Details

Description

The API name of an actionable event sub type.

LastReferencedDate

LastViewedDate

Type

dateTime

Properties

Filter, Nillable, Sort

Description

The date the associated location was last modified.

Type

dateTime

Properties

Filter, Nillable, Sort

Description

The date the associated location was last viewed.

Name

Type

string

Properties

Create, Filter, Group, idLookup, Sort, Update

Description

The name of an event subtype that represents a specific external or internal actionable event.

Associated Objects

This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.

ActionableEventSubtypeFeed

Feed tracking is available for the object.

ActionableEventSubtypeHistory

History is available for tracked fields of the object.

ActionableEventType

Represents the type of an external or internal event that's processed by the Actionable Event Orchestration framework to trigger different
types of actions. This object is available in API version 62.0 and later.


Automotive Cloud Standard Objects

ActionableEventType

Supported Calls

create(), delete(), describeLayout(), describeSObjects(), getDeleted(), getUpdated(), query(),
retrieve(),  search(),  update(),  upsert()

Fields

Field

ApiName

Details

Type

string

Properties

Create, Filter, Group, idLookup, Sort

Description

The API name of an actionable event type.

DefinitionId

Type

reference

Properties

LastReferencedDate

LastViewedDate

Filter, Group, Nillable, Sort, Update

Description

The unique identifier of the actionable event type's definition.

This field is a relationship field.

Relationship Name

Definition

Refers To

ActionableEventTypeDef

Type

dateTime

Properties

Filter, Nillable, Sort

Description

The date the associated location was last modified.

Type

dateTime

Properties

Filter, Nillable, Sort

Description

The date the associated location was last viewed.


Automotive Cloud Standard Objects

ActionableEventTypeDef

Field

Name

OwnerId

Details

Type

string

Properties

Create, Filter, Group, idLookup, Sort, Update

Description

The name of an event type that represents a specific external or internal actionable event
type.

Type

reference

Properties

Create, Defaulted on create, Filter, Group, Sort, Update

Description

The owner ID of an event type that represents a specific external or internal actionable event
type.

This field is a polymorphic relationship field.

Relationship Name

Owner

Refers To

Group, User

Associated Objects

This object has the following associated objects. If the API version isn’t specified, they’re available in the same API versions as this object.
Otherwise, they’re available in the specified API version and later.

ActionableEventTypeChangeEvent

Change events are available for the object.

ActionableEventTypeFeed

Feed tracking is available for the object.

ActionableEventTypeHistory

History is available for tracked fields of the object.

ActionableEventTypeOwnerSharingRule
Sharing rules are available for the object.

ActionableEventTypeShare

Sharing is available for the object.

ActionableEventTypeDef

Represents the definition of an actionable event type so that the records can be migrated from one org to another. This object is available
in API version 62.0 and later.


Automotive Cloud Standard Objects

ActionableEventTypeDef

Supported Calls

create(),  delete(),  describeSObjects(),  query(),  retrieve(),  update(),  upsert()

Fields

Field

DeveloperName

FullName

Details

Type

string

Properties

Create, Filter, Group, Sort, Update

Description

The developer name of the actionable event type definition.

Type

string

Properties

Group, Nillable

Description

The name of the actionable event type definition.

Query this field only if the query result contains no more than one record. Otherwise, an error
is returned. If more than one record exists, use multiple queries to retrieve the records. This
limit protects performance.

Language

Type

picklist

Properties

Create, Defaulted on create, Filter, Group, Nillable, Restricted picklist, Sort, Update

Description

The language in which this actionable event type definition is created.

Possible values are:

- af—Afrikaans

- am—Amharic

- ar—Arabic

- ar_AE—Arabic (United Arab Emirates)

- ar_BH—Arabic (Bahrain)

- ar_DZ—Arabic (Algeria)

- ar_EG—Arabic (Egypt)

- ar_IQ—Arabic (Iraq)

- ar_JO—Arabic (Jordan)

- ar_KW—Arabic (Kuwait)