# Examples — NPSP API and Integration

## Example 1: BDI Gift Integration from a Peer-to-Peer Fundraising Platform

**Context:** A nonprofit uses a peer-to-peer fundraising platform (e.g., Classy) that pushes gift data to Salesforce via REST API. The existing integration inserts Opportunity and OppPayment records directly, bypassing NPSP.

**Problem:** GAU allocations, soft credits, and household rollup totals are not updated. Major donor households show incorrect giving totals because the integration-created Opportunities bypass NPSP's TDTM trigger handlers.

**Solution:**

```apex
// Route gifts through DataImport__c instead of direct Opportunity insert
public class ClassyGiftProcessor {
    public static void processGifts(List<ClassyDonation> donations) {
        List<npsp__DataImport__c> imports = new List<npsp__DataImport__c>();
        
        for (ClassyDonation d : donations) {
            imports.add(new npsp__DataImport__c(
                npsp__Contact1_Firstname__c     = d.firstName,
                npsp__Contact1_Lastname__c      = d.lastName,
                npsp__Contact1_Email__c         = d.email,
                npsp__Donation_Amount__c        = d.amount,
                npsp__Donation_Date__c          = d.donationDate,
                npsp__Donation_Stage__c         = 'Closed Won',
                npsp__Payment_Method__c         = d.paymentMethod,
                npsp__Donation_Campaign_Name__c = d.campaignName,
                // Fund allocation
                npsp__GAU_Allocation_1_General_Accounting_Unit__c = d.gauId,
                npsp__GAU_Allocation_1_Amount__c = d.amount
            ));
        }
        
        insert imports;
        
        // Process synchronously for batch sizes < 200
        npsp.BDI_DataImport_API.processDataImportRecords(
            new npsp.BDI_DataImport_API.BDIImportSettings(),
            imports,
            false
        );
        
        // Check for failures
        for (npsp__DataImport__c di : [
            SELECT npsp__Status__c, npsp__FailureInformation__c, 
                   npsp__DonationImported__c
            FROM npsp__DataImport__c WHERE Id IN :imports
        ]) {
            if (di.npsp__Status__c == 'Failed') {
                // Log failure for remediation
                System.debug('BDI failure: ' + di.npsp__FailureInformation__c);
            }
        }
    }
}
```

**Why it works:** Routing gifts through `npsp__DataImport__c` and `BDI_DataImport_API` ensures all NPSP processing fires: GAU allocations are created, soft credits are processed, household account rollups are updated, and Elevate payment IDs are linked if applicable.

---

## Example 2: Using ERD APIs to Display Projected Payment Schedule

**Context:** A nonprofit wants to add a donor portal feature showing recurring donors their upcoming scheduled payments for the next 12 months.

**Problem:** The developer queries `npe03__Recurring_Donation__c` child Opportunities to show upcoming payments, but finds only 12 future installment Opportunities exist at any time. Donors with annual giving schedules see only 1 upcoming payment instead of the multi-year view the portal requires.

**Solution:**

```apex
// Use RD2 Installments API for projected schedule (NOT Opportunity query)
public class RecurringDonationPortalService {
    
    @AuraEnabled
    public static List<ProjectedInstallment> getProjectedSchedule(Id rdId) {
        // Get 24 projected installments (API returns calculated projections)
        List<npsp.RD2_ApiService.Installment> installments = 
            npsp.RD2_ApiService.getInstallments(rdId, 24);
        
        List<ProjectedInstallment> result = new List<ProjectedInstallment>();
        for (npsp.RD2_ApiService.Installment inst : installments) {
            result.add(new ProjectedInstallment(
                inst.installmentDate,
                inst.amount,
                inst.paymentMethod
            ));
        }
        return result;
    }
    
    public class ProjectedInstallment {
        @AuraEnabled public Date paymentDate;
        @AuraEnabled public Decimal amount;
        @AuraEnabled public String paymentMethod;
        public ProjectedInstallment(Date d, Decimal a, String pm) {
            this.paymentDate = d; this.amount = a; this.paymentMethod = pm;
        }
    }
}
```

**Why it works:** `RD2_ApiService.getInstallments()` calculates the projected schedule based on the recurring donation configuration — it is not limited by how many future Opportunity records have been created by the batch job. This provides an accurate multi-period view for the donor portal.

---

## Anti-Pattern: Checking for Projected Installment Opportunities Immediately After getInstallments()

**What practitioners do:** After calling `RD2_ApiService.getInstallments()`, developers query Opportunity records to confirm they were created, expecting the API call to persist the installments.

**What goes wrong:** `getInstallments()` returns calculated projections — it does NOT create Opportunity records. Future installment Opportunities are created by NPSP's scheduled `RD2_OpportunityEvaluation_BATCH` Apex job. Querying for the installment Opportunities immediately after the API call returns zero results.

**Correct approach:** Use `getInstallments()` for display-only projected schedule data. For actual payment processing or giving history, query the persisted Opportunity records (which are created by the scheduled batch). Never use the Installments API to verify that Opportunities have been created.
