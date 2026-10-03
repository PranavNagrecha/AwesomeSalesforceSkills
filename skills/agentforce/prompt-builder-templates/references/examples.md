# Examples — Prompt Builder Templates

---

## Example 1: Field Generation Template to Auto-Populate a Case Resolution Summary

**Scenario:** A support team wants to use generative AI to draft a resolution summary on Case records after an agent marks the case resolved. The summary should incorporate the case subject, description, the account name, and the most recently added internal comment.

**Problem:** Without grounding, the LLM produces generic filler text ("The issue was resolved successfully") that has no relationship to the actual case. Copying data manually into the prompt at invocation time is error-prone and not scalable across hundreds of agents.

**Solution:**

1. Create a Template-Triggered Prompt Flow named `CaseResolutionGrounding`. In the flow, use a Get Records element to retrieve the most recent `CaseComment` for the case (ordered by `CreatedDate DESC`, limit 1). Use a Create Prompt Instructions element to output the comment body as text. (Correction 2026-10-03: the element is Create Prompt Instructions; earlier versions said Add Prompt Instructions.)
2. In Prompt Builder, create a new **Field Generation** template. Set the object to `Case` and the target field to `Resolution_Summary__c` (a Long Text Area field).
3. Write the prompt body:
   ```
   You are a Salesforce support assistant. Write a concise, professional resolution summary for the following support case. The summary will be visible to customers.

   Case Subject: {!$Input:Case.Subject}
   Case Description: {!$Input:Case.Description}
   Account Name: {!$Input:Case.Account.Name}
   Internal Resolution Notes: {!$Flow:CaseResolutionGrounding.Prompt}

   Write the summary in 3–5 sentences. Focus on what was done to resolve the issue.
   ```
4. Save and preview against a real resolved case. Verify the resolution shows actual case data before activating.
5. Activate the template. In Lightning App Builder on the Case record page, add the template to the `Resolution_Summary__c` field.

Correction (2026-10-03): earlier versions of this example used `{!$Record.Subject}` and `{!Flow:CaseResolutionGrounding.prompt}`. Prompt Builder record merge fields take the form `{!$Input:Object.Field}`, and the Metadata API sample writes flow merge fields as `{!$Flow:FlowName.Prompt}`. Insert both from the Resource picker.

**Why it works:** Record merge fields pull subject, description, and account name directly from the context record at zero latency. The Flow grounds the most recent internal comment — data that requires a SOQL query and cannot be expressed as a simple merge field. The explicit instruction format ("you are a support assistant... 3–5 sentences") constrains the LLM output to the desired length and tone, reducing hallucination. All data passes through the Einstein Trust Layer before reaching the LLM.

---

## Example 2: Flex Template for Agent Action — Personalized Renewal Outreach

**Scenario:** An Agentforce sales agent needs to generate personalized renewal outreach text for an Account. The agent action should accept the Account ID as input, retrieve contract end date and contract value from a custom object, and produce a tailored paragraph for the sales rep to review before sending.

**Problem:** A static email template produces generic text that does not reflect the customer's specific contract terms. UNVERIFIED (2026-10-03): the earlier statement that only Flex templates can be assigned to agent actions was not found in a fetched source.

**Solution:**

1. Create an Apex class with an `@InvocableMethod`. Leave out `CapabilityType`: the Generative AI guide says the Flex capability "is no longer needed" and recommends removing `CapabilityType=FlexTemplate://*`. The Request variable name must match the template's input API name (`account`).

```apex
public class RenewalGroundingProvider {
    public class Request {
        @InvocableVariable(required=true)
        public Account account;
    }

    public class Response {
        @InvocableVariable
        public String prompt;
    }

    @InvocableMethod(label='Get Renewal Contract Data')
    public static List<Response> getContractData(List<Request> requests) {
        // Prompt Builder sends one request; only the first element has data.
        Id accountId = requests[0].account.Id;
        List<Contract__c> contracts = [
            SELECT End_Date__c, Annual_Value__c, Product_Family__c
            FROM Contract__c
            WHERE Account__c = :accountId
            WITH USER_MODE
            ORDER BY End_Date__c DESC
            LIMIT 1
        ];
        Response r = new Response();
        if (contracts.isEmpty()) {
            r.prompt = 'No contract on file.';
        } else {
            Contract__c c = contracts[0];
            r.prompt = 'Contract End Date: ' + String.valueOf(c.End_Date__c)
                + '\nAnnual Value: $' + String.valueOf(c.Annual_Value__c)
                + '\nProduct Family: ' + c.Product_Family__c;
        }
        return new List<Response>{ r };
    }
}
```

2. In Prompt Builder, create a new **Flex** template named `Renewal_Outreach`. In Define Resources, add one input named `account` with Object `Account`.
3. Write the prompt body:
   ```
   You are a senior enterprise sales assistant. Generate a warm, professional renewal outreach paragraph for a sales rep to send to the account below. Reference the contract end date and the value of the renewal to convey urgency and personalization.

   Account: {!$Input:account.Name}
   Contract Details: (insert from Resource > Apex > Get Renewal Contract Data)

   Write one paragraph of 4–6 sentences. Do not include a subject line or greeting — only the body paragraph.
   ```
4. Save and preview with a real Account. Verify the resolution shows the contract data returned by Apex; open the Developer Console first to see Apex debug output.
5. Activate the template, then reference it from the agent action and map the `account` input to the record in context.

**Why it works:** Flex lets the template define its own `account` input. Apex grounding is chosen because the contract data needs an ordered query on a custom object and a fallback when nothing is found. The Request variable `account` matches the template input API name, which the guide requires for String inputs and for object types used more than once, and the method returns one `Response` with a String `prompt`. Correction (2026-10-03): earlier versions said the CapabilityType string must match the template API name for the platform to route the method; the guide now recommends removing `FlexTemplate://` capability types.

---

## Anti-Pattern: Using a Sales Email Template Where a Flex Template Is Needed

**What practitioners do:** A developer needs to generate outreach text from an Agentforce agent action and reaches for the Sales Email template type because the output is email-related.

**What goes wrong:** Sales Email templates are built around Recipient, Sender, and Current Organization merge fields for Einstein Sales Emails. UNVERIFIED (2026-10-03): the earlier statement that the agent action picker never shows Sales Email templates was not found in a fetched source.

**Correct approach:** Use a **Flex** template for any output surfaced through an agent action, regardless of whether the content is email-like. Sales Email is specifically scoped to the activity composer in the CRM UI and is not a general-purpose email generation template.

---

## Anti-Pattern: Activating a Template Without Preview Against Real Data

**What practitioners do:** Build the prompt with merge fields in the editor, review it visually, and activate immediately to save time.

**What goes wrong:** Merge fields that reference related objects (e.g., `{!$Input:Opportunity.Account.Name}`) may resolve to nothing if the relationship is null on the preview record or if the path is wrong. The template activates, users click the Einstein button, and receive blank output. There is no error, just an empty field.

**Correct approach:** Always use Save & Preview with a real record that has populated values for every merge field in the template. Inspect the **Resolved Prompt** panel (not just the Generated Response) to confirm every token has resolved to actual data before activating.
