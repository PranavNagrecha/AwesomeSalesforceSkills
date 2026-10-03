# Gotchas: Prompt Builder Templates

Non-obvious Prompt Builder behaviours that cause blank output, failed deployments, or untraceable changes. Each gotcha names its source. "GenAI Guide" means Quickstart Your Einstein Generative AI Solution, Spring '26 (generative_ai.pdf), Prompt Builder chapter. "Metadata API" means the Metadata API Developer Guide, Version 67.0.

## Gotcha 1: No Active Version Means No Template, and Activated Versions Are Immutable

**What happens:** Users stop seeing a template after someone deactivates its version to "pause" it, or an admin cannot edit a version that went live last month.

**When it occurs:** "Only one version of a template can be active at a time, and if no versions are active the template becomes unavailable to your users." "Activating a template version makes it immutable. Even if deactivated, any version that was ever active remains immutable." "When a new version of a prompt template is created, it doesn't automatically become active." In metadata, "Published prompt templates can't be edited with UI or Metadata API."

**How to avoid:** Never deactivate without activating a replacement. Make changes with Save As > Save as a New Version, preview, then activate the new version. Treat every activation as a release.

**Source:** GenAI Guide, Activate and Deactivate Prompt Templates; Use Multiple Versions of a Prompt Template. Metadata API, GenAiPromptTemplate (status: Published).

---

## Gotcha 2: Records Without a Usable Name Can't Be Previewed

**What happens:** The preview record picker is empty for an object, or the chosen record never appears.

**When it occurs:** "Prompt templates with encrypted or missing name fields can't be previewed. Their records are unavailable in the test record selector." The same applies to objects "with no Name field or objects whose Name field is encrypted."

**How to avoid:** Preview on an object with a plain Name field where possible, or plan a test path through the invoking feature (record page, flow, or action) for objects that cannot be previewed.

**Source:** GenAI Guide, Prompt Builder Limitations (Records Without a Name Don't Display in the Record Selector; Object Preview Limitations).

---

## Gotcha 3: Changing a Flow's or Apex Class's Inputs Breaks the Template

**What happens:** A developer adds an input to the grounding flow, and the template stops working and refuses to save new versions.

**When it occurs:** "If you change the inputs for a flow or Apex class that's used as a resource in a prompt template, the prompt template no longer works and you can't save new versions of the prompt template." For flows, "all inputs are considered required and must be present in the prompt template." Flow Builder's Debug option "isn't available for a Template-Triggered Prompt Flow."

**How to avoid:** Freeze the input contract of every grounding flow and Apex class. When the contract must change, create a new flow or class, point a new template version at it, and retire the old one. Test flows through Prompt Builder preview, and Apex with a test class plus Developer Console debug output during preview.

**Source:** GenAI Guide, Ground Prompt Templates with Salesforce Resources; Ground with Flow Merge Fields (note); Ground with Apex Merge Fields (note); Flow Changes After the Pilot.

---

## Gotcha 4: Template Changes Are Not in the Setup Audit Trail

**What happens:** A template's output changes overnight and nobody can tell who changed what.

**When it occurs:** "Creating or updating a prompt template isn't tracked in the Setup Audit Trail."

**How to avoid:** Keep GenAiPromptTemplate files in source control and deploy changes through a pipeline, or keep an external change log with the version number, author, date, and reason for each activation. The audit and feedback data in Data Cloud records `promptTemplateDevName__c` and `promptTemplateVersionNo__c` per request, which shows which version produced a given response.

**Source:** GenAI Guide, Prompt Builder Limitations (Audit Trail Isn't Supported); Data Model for Generative AI Audit and Feedback (GenAIGatewayRequest fields).

---

## Gotcha 5: Flex Template Metadata Has Import and Export Limits

**What happens:** A change set carrying a Flex template and its Apex class fails, or arrives incomplete.

**When it occurs:** "You can't import or export metadata from flex templates, including metadata related to flex templates," with examples "Apex classes that reference flex templates," "Flows that reference flex templates," and "Change sets to move flex-related artifacts between orgs." To delete a Flex template that uses flows or Apex, remove those resources from all versions, delete the referencing flows and classes, then delete the template. The Metadata API, meanwhile, lists `einstein_gpt__flex` as a valid GenAiPromptTemplate `type`.

**How to avoid:** Prove the deployment path for Flex templates in a sandbox before the release depends on it. Keep a manual rebuild runbook for Flex templates as the fallback.

**Source:** GenAI Guide, Prompt Builder Limitations (Limitations for Flex Templates). Metadata API, GenAiPromptTemplate (type values).

---

## Gotcha 6: Retrievers and Search Indexes Don't Deploy With the Template

**What happens:** A template that uses an Einstein Search retriever deploys, and fails in the target org because the retriever is missing.

**When it occurs:** "If a prompt uses an Einstein Search retriever, the change sets don't include the retriever or search index metadata. You must manually create the retriever in the destination org before deploying the retriever. This rule applies to change sets and Metadata API deployments." Data graphs must also already exist in the target org before a change set that references them.

**How to avoid:** Add "create search index and retriever in target" as a pre-deployment step, and confirm the retriever API name matches.

**Source:** GenAI Guide, Prompt Builder Limitations (Limitations for Einstein Search); Ground with Data Graphs (Considerations and Limitations).

---

## Gotcha 7: "Deploy Active Prompt Template Versions Only" Fails Templates With No Active Version

**What happens:** A deployment that worked last month now fails on a draft template.

**When it occurs:** EinsteinGptSettings `enableEinsteinGPTDeployPromptTemplatesAsActive` "Deploys only the active version of prompt templates to this org, and skips inactive versions. If a template doesn't have an active version, the deployment fails." Separately, GenAiPromptTemplate `activeVersion` and `versionNumber` "will not work in 64.0 and later"; use `activeVersionIdentifier` and `versionIdentifier`.

**How to avoid:** Know whether the target org has this setting on. Keep drafts out of release manifests, or give every deployed template an active version. Update old files that still carry `activeVersion` or `versionNumber`; the skill checker flags them (`PB-VER-01`).

**Source:** Metadata API, EinsteinGptSettings (enableEinsteinGPTDeployPromptTemplatesAsActive); GenAiPromptTemplate (activeVersion, versionNumber, versionIdentifier).

---

## Gotcha 8: Hard Limits on Size, Versions, and Resources

**What happens:** A template cannot take another related list, or an old template cannot save a new version.

**When it occurs:** Prompt templates have these limits: maximum template size 128,000 characters; 50 versions; 50 merge fields; 5 flow merge fields; 5 Apex merge fields; 5 related list merge fields; 5 inputs in a Flex template. Separately, "Customers have a default rate limit of 300 Large Language Model (LLM) generation requests per minute at their Salesforce Organization ID level."

**How to avoid:** Count resources during design. Move repeated lookups into one flow or Apex resource that returns a single block of text. Archive by cloning to a new template before hitting 50 versions. Size flows that call templates in bulk against the 300-per-minute limit.

**Source:** GenAI Guide, Prompt Builder Limits (Numerical Limits); Considerations for Einstein Generative AI (Rate Limits).

---

## Gotcha 9: The Apex CapabilityType Contract Changed

**What happens:** A team adds `CapabilityType='FlexTemplate://My_Template'` everywhere because older guidance said a mismatch drops the data silently, and the class can then serve only that one template type.

**When it occurs:** "The InvocableMethod annotation can specify a CapabilityType that matches the prompt template type," and a class that specifies one "can only be used by one prompt template type." For Flex, "the Flex capability is no longer needed. It's a good idea to migrate any Apex that uses CapabilityType=FlexTemplate://* so that it doesn't use the Flex template." Correction (2026-10-03): the earlier claim that a mismatch silently excludes Apex data was not found in the guide. Don't specify a CapabilityType for `einstein_gpt__caseEmailDraft`, and don't name its input `Case`.

**How to avoid:** For Flex, omit CapabilityType and match the Request variable API names to the template input API names (required for String inputs and for any object type used more than once). For Field Generation, define a `relatedEntity` Request variable of the template's object type. Return one `Response` with a String `Prompt`.

**Source:** GenAI Guide, Ground with Apex Merge Fields (CapabilityType table, Method Input, Method Output); Add Apex Merge Fields to a Flex Prompt Template.

---

## Gotcha 10: Related List Grounding Follows the User's Page Layout, Not Record Filters

**What happens:** Preview as an admin shows contacts in the prompt, while a sales rep's run sends none.

**When it occurs:** "The fields for the related list are based on the page layout of the parent object for the current user. Record-level filters aren't applied." "If a user doesn't have the related list on their parent object's page layout or Read permission on the associated object, no related list data is sent to the LLM." With custom record types, only related lists on the master record type's layout are available. Activities related lists aren't supported.

**How to avoid:** Preview as each persona. Put the related list on every persona's layout, or use a flow or Apex resource that selects exactly the records the prompt needs.

**Source:** GenAI Guide, Ground with Related List Merge Fields (Considerations, Guidelines, and Limitations).

---

## Gotcha 11: New Custom Objects and Fields Need a Fresh Session

**What happens:** A field created minutes ago does not appear in the Resource picker.

**When it occurs:** "When you create a custom object or custom field, it isn't available for use in Prompt Builder immediately. To use a new custom object or field immediately, log out and log back in."

**How to avoid:** Log out and back in after creating fields for a template, and add that step to build runbooks.

**Source:** GenAI Guide, Prompt Builder Limitations (New Custom Objects and Custom Fields Aren't Immediately Available After Creation).
