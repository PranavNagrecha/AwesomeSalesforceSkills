# Metadata Examples: A Flex Prompt Template That Uses a Retriever

The retriever itself is not deployable with the template ("the change sets don't include the retriever or search index metadata... This rule applies to change sets and Metadata API deployments"), so the release is two parts: recreate the retriever in the target org, then deploy the template. GenAiPromptTemplate element names follow the Metadata API Developer Guide, Version 67.0.

## Step 1 (target org): recreate the index and retriever

1. Deploy the search index configuration through a data kit (Data Cloud Guide, Add a Search Index Configuration to a Data Kit; Create a Search Index Configuration from a Data Kit).
2. In Einstein Studio, create the custom retriever `Policy_Passages` on that index with the same filters, output fields, and number of results as the source org, and activate it.

## Step 2: deploy the template

File: `force-app/main/default/genAiPromptTemplates/Case_Policy_Summary.genAiPromptTemplate-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiPromptTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Summarizes a case and cites matching policy passages from the Policy_Passages retriever.</description>
    <masterLabel>Case Policy Summary</masterLabel>
    <templateVersions>
        <content>You are a financial services case assistant.
Case number: {!$Input:Case.CaseNumber}
Subject: {!$Input:Case.Subject}
Description: {!$Input:Case.Description}

Policy passages:
{!$EinsteinSearch:Policy_Passages.results}

Instructions:
"""
Summarize the case in three sentences. Then list which policy passages above apply, quoting the passage title.
If no passage applies, say "No matching policy." Use only the passages provided.
"""</content>
        <inputs>
            <apiName>Case</apiName>
            <definition>SOBJECT://Case</definition>
            <referenceName>Input:Case</referenceName>
            <required>true</required>
        </inputs>
        <status>Draft</status>
        <templateDataProviders>
            <definition>einstein_search://Policy_Passages</definition>
            <label>Policy Passages</label>
            <referenceName>EinsteinSearch:Policy_Passages</referenceName>
        </templateDataProviders>
    </templateVersions>
    <type>einstein_gpt__flex</type>
    <visibility>Global</visibility>
</GenAiPromptTemplate>
```

UNVERIFIED (2026-10-03): the retriever's data provider `definition`, `referenceName`, and the merge field `{!$EinsteinSearch:Policy_Passages.results}` are placeholders shaped like the documented flow provider (`flow://Fetch_Products`, `{!$Flow:Fetch_Products.Prompt}`); no fetched source shows how a retriever is serialized. Build the template once in Prompt Builder, retrieve it, and replace these three values with the retrieved ones. The Prompt Builder limitations also say Flex template metadata can't be imported or exported with change sets, so prove the Metadata API path in a sandbox first.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case_Policy_Summary</members>
        <name>GenAiPromptTemplate</name>
    </types>
    <version>67.0</version>
</Package>
```

## Verify

1. `python3 skills/agentforce/rag-patterns-in-salesforce/scripts/check_rag_patterns_in_salesforce.py --manifest-dir force-app/main/default`.
2. Deploy as a user with Prompt Template Manager; prompt runners need the Data Cloud User permission set to run prompts with Einstein Search.
3. Preview with a real case, read the retriever JSON in the resolution, then activate.
