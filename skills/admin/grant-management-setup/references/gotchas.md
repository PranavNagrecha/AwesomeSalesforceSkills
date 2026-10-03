# Gotchas: Grant Management Setup

Non-obvious behaviours that cause grant tracking to fail or mislead. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "Grantmaking Guide" means Grantmaking (Spring '26, https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/grantmaking.pdf); "NPC Guide" means the Nonprofit Cloud Developer Guide, Version 67.0 (https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/nonprofit_cloud.pdf), Grantmaking chapter; "OFM source" means the Outbound Funds Module package source published by Salesforce.org at https://github.com/SalesforceFoundation/OutboundFundsModule.

## Gotcha 1: Outbound Funds, Grants Management, And Grantmaking Are Three Different Things, And Grantmaking Cannot Be Turned Off

**What happens:** Guidance, automation, and data models built for one grants product fail on another. The Outbound Funds Module is a managed package with namespace `outfunds` (`Funding_Program__c`, `Funding_Request__c`, `Disbursement__c`, `Requirement__c`, `Review__c`, `Funding_Request_Role__c`). Grantmaking is a platform feature with standard objects (`FundingAward`, `FundingDisbursement`, `FundingAwardRequirement`, `FundingOpportunity`, and others). The Grants Management managed package is a third product with its own documentation. "After you turn on Grantmaking, you can't disable it," and Salesforce recommends not turning it on in an org with the Grants Management managed package installed.

**When it occurs:** When Trailhead or documentation for one product is applied to an org on another, and when someone enables Grantmaking in production "to have a look."

**How to avoid:** Confirm the installed namespaces and whether Grantmaking Settings is on before writing any query, flow, or Apex. Try Grantmaking in a sandbox or trial org first. Never mix `outfunds__` names with Grantmaking objects in one automation.

**Source:** Grantmaking Guide, Introduction to Grantmaking (Important note on the Grants Management managed package) and Turn On Grantmaking (Setup path and "can't disable" note). OFM source, `cumulusci.yml` (namespace `outfunds`) and `force-app/main/default/objects`.

---

## Gotcha 2: Grantmaking Objects Need The Licence, The Feature Switch, And A System Permission

**What happens:** An org on Nonprofit Cloud cannot see `FundingAward`, `FundingDisbursement`, or `FundingAwardRequirement`. Each is "available only if the Grantmaking license is enabled, Grantmaking is enabled, and the Manage Funding Awards system permission is assigned to users." The Grantmaking Manager permission set (CRM users) and Grantmaking for Experience Cloud permission set include the object access and "auto-assigns the Grantmaking permission set license." UNVERIFIED (2026-10-03): the earlier statement that a refreshed sandbox may lack the licence even when production has it was not confirmed.

**When it occurs:** Orgs that bought Nonprofit Cloud for fundraising or programs without Grantmaking, and users given object permissions by hand without the system permission.

**How to avoid:** Check the permission set licences in the org before design (`SELECT MasterLabel, Status, TotalLicenses, UsedLicenses FROM PermissionSetLicense`), turn on Grantmaking, and assign Grantmaking Manager. For custom fields, add a custom permission set and combine them in a permission set group rather than cloning the standard set. Do not rebuild `FundingAward` as a custom object.

**Source:** NPC Guide, Special Access Rules on FundingAward, FundingDisbursement, and FundingAwardRequirement. Grantmaking Guide, Grantmaking Editions and Permissions (permission sets, licence auto-assignment, Customizing Permissions). Object Reference, Version 67.0, PermissionSetLicense fields.

---

## Gotcha 3: A Requirement Has Two Status Fields, And Rejected Is A Standard Value

**What happens:** The earlier version of this skill described a fixed "Open, Submitted, Approved" lifecycle with no Rejected state. The documented model is different. `FundingAwardRequirement.Status` has the values Approved, Delayed, In Progress, Open, Rejected, and Submitted. A separate `ApprovalStatus` has New, In Review, Approved, and Rejected, and `IsSubmitted` and `SubmittedDate` record submission. `Type` values are Combined Report, Contract, Financial Report, and Narrative Report, not "Progress Report, Final Report, Site Visit." Teams that update only one status field produce reports that disagree.

**When it occurs:** When reviewers record decisions on `ApprovalStatus` while grantees and automation move `Status`, or when custom picklist values are added to imitate values that already exist.

**How to avoid:** Decide which field carries which meaning (for example, `Status` for the grantee-facing state and `ApprovalStatus` for the review decision) and write it into the setup document. Keep standard values before adding custom ones. Use `IsSubmitted` and `SubmittedDate` as the submission facts in reports.

**Source:** NPC Guide, FundingAwardRequirement fields (`Status`, `ApprovalStatus`, `IsSubmitted`, `SubmittedDate`, `Type`, `DueDate`, `AssignedContactId`, `AssignedUserId`).

---

## Gotcha 4: A Disbursement Is A Scheduled Or Made Payment With Its Own Status Set, And There Is No "Draft"

**What happens:** Grants staff treat `FundingDisbursement` as a ledger entry created after payment, losing the forward schedule. Others build automation around a "Draft" status that does not exist. The object "Represents a payment that has been made or scheduled to be made," with `ScheduledDate` and `DisbursementDate`, `Amount`, `IsApproved`, `PaymentMethodType` (Cash, Check, EFT, Wire), and `Status` values Approved, Cancelled, Paid, Pending Approval, Processing, Returned, and Scheduled.

**When it occurs:** When accounting habits ("disbursement means money left the bank") meet the data model, and when examples written against invented field names (`DisbursementAmount`) are copied.

**How to avoid:** Create every tranche at award setup with `Status` = Scheduled and a future `ScheduledDate`, then move it through Pending Approval, Approved, Processing, and Paid, setting `DisbursementDate` when paid. Use Returned and Cancelled rather than deleting records.

**Source:** NPC Guide, FundingDisbursement (description; fields `Amount`, `DisbursementDate`, `FundingAwardId` master-detail, `IsApproved`, `PaymentMethodType`, `PaymentNumber`, `ScheduledDate`, `Status`).

---

## Gotcha 5: Requirements Can Point At The Disbursement They Gate, But The Gate Is Yours To Build

**What happens:** `FundingAwardRequirement.FundingDisbursementId` links a requirement to a disbursement, described as "The funds are disbursed only after the requirements are fulfilled." Teams assume the platform blocks payment. UNVERIFIED (2026-10-03): no fetched source says the platform enforces this; treat the relationship as the hook for your own automation. A validation rule on the disbursement cannot see requirements that point at it, so a before-save flow or Apex is needed for the cross-record check.

**When it occurs:** Funders whose policy is "no second tranche until the interim report is approved."

**How to avoid:** Link each gating requirement to its disbursement with `FundingDisbursementId`. Enforce same-record rules with validation rules (Example 3 in `references/examples.md`) and the cross-record rule with a record-triggered flow that looks up unapproved requirements for the disbursement.

**Source:** NPC Guide, FundingAwardRequirement (`FundingDisbursementId` description; `FundingAwardId` master-detail). Metadata API Developer Guide, Version 67.0, ValidationRule ("evaluates the data in one or more fields" of the record being saved).

---

## Gotcha 6: Outbound Funds Has Requirements And Disbursements, Has No Opportunity Lookup, And Is Community-Maintained

**What happens:** The earlier version of this skill said the Outbound Funds Module has no deliverable-tracking object, ties grants to the Opportunity through a lookup, and is now Salesforce-maintained. The package source shows `outfunds__Requirement__c` (with `Due_Date__c`, `Status__c`, `Type__c`, `Funding_Request__c`, and a `Disbursement__c` lookup), `outfunds__Disbursement__c` (with `Scheduled_Date__c`, `Disbursement_Date__c`, `Amount__c`, `Status__c`), and no Opportunity field on `Funding_Request__c`. The repository describes the app as "a community developed and maintained Open Source Commons project." The NPSP extension (namespace `outfundsnpspext`) links disbursements to NPSP General Accounting Units through `GAU_Expenditure__c`.

**When it occurs:** Platform comparisons that undersell Outbound Funds, and support planning that assumes a vendor support line.

**How to avoid:** Compare products on what each package contains. Record the support model: Salesforce for Grantmaking, the Open Source Commons community for Outbound Funds. When NPSP fund accounting matters, plan for the `outfundsnpspext` extension.

**Source:** OFM source: repository description; `force-app/main/default/objects/*/fields` for `Funding_Request__c`, `Disbursement__c`, `Requirement__c`, `Funding_Program__c`. OutboundFundsModuleNPSP source (https://github.com/SalesforceFoundation/OutboundFundsModuleNPSP): `cumulusci.yml` namespace `outfundsnpspext`; `GAU_Expenditure__c` fields.

---

## Gotcha 7: Applications Have Two Models Since Spring '26, And Grantmaking Fields Need An Application Record Type Config

**What happens:** A team configures `IndividualApplication` because older guidance says so. Spring '26 introduced a Grantmaking data model built on Application Form objects, and Individual Application "won't receive future platform enhancements." `FundingAward` carries both `IndividualApplicationId` and `ApplicationFormId` (API 66.0+). Teams on Individual Application also miss Grantmaking fields and layouts until an Application RecordType Config with Application Usage Type = Grantmaking points at their record type.

**When it occurs:** New builds started from pre-Spring '26 material, and orgs where the Individual Application record type was created but never registered.

**How to avoid:** Choose the application model in the design record. For Individual Application, create the record type and the Application RecordType Config (Setup > Quick Find "Application RecordType Config" > New; Application Usage Type = Grantmaking; Object Name = Individual Application). Populate the matching lookup on `FundingAward`.

**Source:** NPC Guide, Chapter 2 Grantmaking Data Model (Spring '26 Application Form model; Individual Application note); FundingAward fields (`IndividualApplicationId`, `ApplicationFormId`). Grantmaking Guide, Configure an Application Record Type for Grantmaking.

---

## Gotcha 8: One Grant Is One Award; Tranches And Requirements Are Master-Detail Children

**What happens:** Staff create one `FundingAward` per payment ("Q1 grant," "Q2 grant"), quadrupling committed totals and duplicating requirements. Both `FundingDisbursement` and `FundingAwardRequirement` reference `FundingAward` through master-detail relationships, so the model expects one parent per grant agreement; changes to terms belong on a `FundingAwardAmendment`. `FundingAward.Status` has three values: Active, Cancelled, Completed.

**When it occurs:** Multi-year and multi-tranche grants, and teams that track amendments by cloning awards.

**How to avoid:** Create one `FundingAward` per agreement with `Amount` as the total award, add tranches as `FundingDisbursement` children, add amendments as `FundingAwardAmendment` records, and set `Status` = Completed when the last tranche is paid. Note that editions are documented inconsistently: the Grantmaking Guide lists Enterprise, Unlimited, and Developer for Nonprofit Cloud for Grantmaking, while the NPC Guide's object reference lists Enterprise, Performance, and Unlimited; confirm with the account team.

**Source:** NPC Guide, FundingAward (`Amount` "The total award amount"; `Status` values; `AwardeeId`), FundingDisbursement and FundingAwardRequirement (`FundingAwardId` master-detail), FundingAwardAmendment ("a modification to the scope or finances of a previously approved award"), Grantmaking Object Reference edition box. Grantmaking Guide, Supported Editions for Grantmaking; Manage Funding Awards with Grantmaking (step 6, amendments).
