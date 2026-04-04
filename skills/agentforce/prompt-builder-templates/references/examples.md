# Examples — Prompt Builder Templates

---

## Example 1: Field Generation Template to Auto-Populate a Case Resolution Summary

**Scenario:** A support team wants to use generative AI to draft a resolution summary on Case records after an agent marks the case resolved. The summary should incorporate the case subject, description, the account name, and the most recently added internal comment.

**Problem:** Without grounding, the LLM produces generic filler text ("The issue was resolved successfully") that has no relationship to the actual case. Copying data manually into the prompt at invocation time is error-prone and not scalable across hundreds of agents.

**Solution:**

1. Create a Template-Triggered Prompt Flow named `CaseResolutionGrounding`. In the flow, use a Get Records element to retrieve the most recent `CaseComment` for the case (ordered by `CreatedDate DESC`, limit 1). Use the Add Prompt Instructions element to output the comment body as a string.
2. In Prompt Builder, create a new **Field Generation** template. Set the object to `Case` and the target field to `Resolution_Summary__c` (a Long Text Area field).
3. Write the prompt body:
   ```
   You are a Salesforce support assistant. Write a concise, professional resolution summary for the following support case. The summary will be visible to customers.

   Case Subject: {!$Record.Subject}
   Case Description: {!$Record.Description}
   Account Name: {!$Record.Account.Name}
   Internal Resolution Notes: {!Flow:CaseResolutionGrounding.prompt}

   Write the summary in 3–5 sentences. Focus on what was done to resolve the issue.
   ```
4. Save and preview against a real resolved case. Verify the Resolved Prompt shows actual case data before activating.
5. Activate the template. In App Builder on the Case record page, bind the Einstein button on `Resolution_Summary__c` to this template.

**Why it works:** Record merge fields pull subject, description, and account name directly from the context record at zero latency. The Flow grounds the most recent internal comment — data that requires a SOQL query and cannot be expressed as a simple merge field. The explicit instruction format ("you are a support assistant... 3–5 sentences") constrains the LLM output to the desired length and tone, reducing hallucination. All data passes through the Einstein Trust Layer before reaching the LLM.

---

## Example 2: Flex Template for Agent Action — Personalized Renewal Outreach

**Scenario:** An Agentforce sales agent needs to generate personalized renewal outreach text for an Account. The agent action should accept the Account ID as input, retrieve contract end date and contract value from a custom object, and produce a tailored paragraph for the sales rep to review before sending.

**Problem:** A Field Generation or Sales Email template cannot be assigned to an agent action — only Flex templates support the flexible input model required by Agentforce actions. Using a static email template produces generic text that does not reflect the customer's specific contract terms.

**Solution:**

1. Create an Apex class with an `@InvocableMethod` assigned capability type `FlexTemplate://Renewal_Outreach`:

```apex
public class RenewalGroundingProvider {
    public class Request {
        @InvocableVariable(required=true)
        public String accountId;
    }

    public class Response {
        @InvocableVariable
        public String prompt;
    }

    @InvocableMethod(
        label='Get Renewal Contract Data'
        capabilityType='FlexTemplate://Renewal_Outreach'
    )
    public static List<Response> getContractData(List<Request> requests) {
        List<Response> responses = new List<Response>();
        for (Request req : requests) {
            Contract__c c = [
                SELECT End_Date__c, Annual_Value__c, Product_Family__c
                FROM Contract__c
                WHERE Account__c = :req.accountId
                ORDER BY End_Date__c DESC
                LIMIT 1
            ];
            Response r = new Response();
            r.prompt = 'Contract End Date: ' + String.valueOf(c.End_Date__c)
                + '\nAnnual Value: $' + String.valueOf(c.Annual_Value__c)
                + '\nProduct Family: ' + c.Product_Family__c;
            responses.add(r);
        }
        return responses;
    }
}
```

2. In Prompt Builder, create a new **Flex** template named `Renewal_Outreach`. Add one input: `AccountId` (type: Text).
3. Write the prompt body:
   ```
   You are a senior enterprise sales assistant. Generate a warm, professional renewal outreach paragraph for a sales rep to send to the account below. Reference the contract end date and the value of the renewal to convey urgency and personalization.

   Account ID: {!$Input:AccountId}
   Contract Details: {!$Apex:RenewalGroundingProvider.getContractData}

   Write one paragraph of 4–6 sentences. Do not include a subject line or greeting — only the body paragraph.
   ```
4. Save and preview by supplying a real Account ID in the preview inputs. Verify the Resolved Prompt shows the contract data injected by Apex.
5. Activate the template. In the Agentforce agent action configuration, select this Flex template and map the `AccountId` input to the agent's current record context.

**Why it works:** The Flex type is the only template type compatible with agent actions. Apex grounding is chosen over Flow because the contract data requires a SOQL query on a custom object with ordering logic — a pattern suited to Apex's richer query control. The capability type string in the `@InvocableMethod` annotation exactly matches the Flex template's API name (`Renewal_Outreach`), which is required for the platform to route the Apex method to the correct template.

---

## Anti-Pattern: Using a Sales Email Template Where a Flex Template Is Needed

**What practitioners do:** A developer needs to generate outreach text from an Agentforce agent action and reaches for the Sales Email template type because the output is email-related.

**What goes wrong:** Sales Email templates cannot be assigned to agent actions. The agent action configuration panel does not show Sales Email templates in its template picker. The developer wastes time debugging the missing template, often concluding there is a permission issue when the root cause is a type mismatch.

**Correct approach:** Use a **Flex** template for any output surfaced through an agent action, regardless of whether the content is email-like. Sales Email is specifically scoped to the activity composer in the CRM UI and is not a general-purpose email generation template.

---

## Anti-Pattern: Activating a Template Without Preview Against Real Data

**What practitioners do:** Build the prompt with merge fields in the editor, review it visually, and activate immediately to save time.

**What goes wrong:** Merge fields that reference related objects (e.g., `{!$Record.Opportunity.Account.Name}`) may resolve to empty string if the relationship is null on the preview record or if the path is wrong. The template activates, users click the Einstein button, and receive blank output. There is no error — just an empty field.

**Correct approach:** Always use Save & Preview with a real record that has populated values for every merge field in the template. Inspect the **Resolved Prompt** panel (not just the Generated Response) to confirm every token has resolved to actual data before activating.
