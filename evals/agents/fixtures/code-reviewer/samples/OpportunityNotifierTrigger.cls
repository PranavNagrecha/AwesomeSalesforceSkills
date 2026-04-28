/**
 * OpportunityNotifierTrigger — synthetic sample for code-reviewer eval.
 *
 * Carries the canonical anti-patterns the reviewer should catch:
 *   - Critical: SOQL inside a for-loop (governor-limit time bomb at bulk)
 *   - Critical: callout to a hard-coded HTTPS endpoint instead of a Named Credential
 *   - High:    DML inside a for-loop
 *   - High:    `without sharing` on a class that touches Opportunity / Contact
 *   - Medium:  no logging on the failure path; swallowed exception
 *   - Medium:  hardcoded record-type developer name
 */
public without sharing class OpportunityNotifier {
    public static void notify(List<Opportunity> opps) {
        for (Opportunity o : opps) {
            // SOQL in loop — Critical
            List<Contact> primaryContacts = [
                SELECT Id, Email, AccountId
                FROM Contact
                WHERE AccountId = :o.AccountId
            ];

            for (Contact c : primaryContacts) {
                // DML in loop — High
                Task t = new Task(
                    Subject = 'Follow up on ' + o.Name,
                    WhatId = o.Id,
                    WhoId = c.Id,
                    RecordTypeId = '0125g000000abcdAAA'  // hardcoded — Medium
                );
                insert t;

                // Hardcoded endpoint instead of Named Credential — Critical
                HttpRequest req = new HttpRequest();
                req.setEndpoint('https://hooks.example.com/notify?email=' + c.Email);
                req.setMethod('POST');
                try {
                    new Http().send(req);
                } catch (Exception e) {
                    // swallowed — Medium
                }
            }
        }
    }
}
