# LLM Anti-Patterns — Government Cloud Compliance

Common mistakes AI coding assistants make when generating or advising on Salesforce Government Cloud compliance.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Commercial Cloud Features Are Available in GovCloud

**What the LLM generates:** Advice or solution designs that reference Einstein GPT, Agentforce agents, the latest Lightning components, or newly announced Salesforce features without confirming GovCloud authorization status. Example: "Enable Einstein Case Classification in your GovCloud org to automatically route incoming cases." Or: "Use Agentforce to automate the intake workflow in your GovCloud Plus deployment."

**Why it happens:** LLMs are trained on Salesforce documentation and community content that predominantly covers the commercial cloud. GovCloud feature availability documentation is sparse in training data. The model defaults to recommending features it knows exist on the platform without distinguishing between commercial and government availability.

**Correct pattern:** Before recommending any feature in a GovCloud context, explicitly caveat: "Confirm this feature is available in your GovCloud or GovCloud Plus environment via the Salesforce Government Cloud Feature Availability Guide, as features may lag commercial availability by one or more release cycles." For generative AI features specifically, always flag that FedRAMP authorization for AI features requires additional review cycles and may not be current.

**Detection hint:** Any recommendation that mentions Einstein AI, Agentforce, agent builder, Einstein GPT, or a feature released in the last two Salesforce releases without a GovCloud availability caveat is likely this anti-pattern.

---

## Anti-Pattern 2: Treating FedRAMP Moderate and FedRAMP High as Interchangeable

**What the LLM generates:** Advice that uses "FedRAMP" as a blanket term without distinguishing between Moderate and High, or that maps FedRAMP Moderate guidance to a system that requires FedRAMP High. Example: "Salesforce Government Cloud is FedRAMP authorized, so you can deploy your agency's system there." Or: "GovCloud meets FedRAMP requirements" without specifying whether the system needs Moderate or High.

**Why it happens:** "FedRAMP" is commonly used as shorthand in training data without the Moderate/High distinction. The difference between the two baselines is significant (approximately 100 additional controls, stricter personnel security, stricter encryption requirements), but it is underrepresented in general Salesforce content.

**Correct pattern:** Always qualify FedRAMP authorization with the impact level: "Salesforce Government Cloud holds FedRAMP Moderate authorization. Salesforce Government Cloud Plus holds FedRAMP High authorization. Confirm which impact level your system requires before selecting the offering." For DoD systems, further qualify with the IL level: IL4 requires FedRAMP High (GovCloud Plus minimum); IL5 requires Hyperforce GovCloud with additional controls.

**Detection hint:** Any statement about "FedRAMP authorized" without specifying Moderate or High, or any advice to use "GovCloud" without qualifying whether it means GovCloud (Moderate) or GovCloud Plus (High).

---

## Anti-Pattern 3: Ignoring the ATO Inheritance Boundary and Telling the Customer They Are Automatically Compliant

**What the LLM generates:** Statements like "Salesforce Government Cloud is FedRAMP authorized, so your deployment is FedRAMP compliant" or "Since Salesforce holds the ATO, your agency doesn't need to do additional compliance work." This conflates the Cloud Service Provider's ATO with the customer agency's system ATO.

**Why it happens:** The FedRAMP inherited authorization model is nuanced. Salesforce holds the ATO for the infrastructure and platform layer. The customer agency must obtain their own ATO for their system — the application and data layer — which inherits the Salesforce authorization for the infrastructure controls but requires the agency to implement and document approximately 241 customer-owned and shared controls.

**Correct pattern:** "Salesforce Government Cloud holds its own FedRAMP authorization covering the infrastructure and platform layer. Your agency's system must obtain a separate ATO through the RMF process. Your SSP will inherit the infrastructure controls from Salesforce's authorization package, but you must document and implement the customer-owned controls (application configuration, access management, incident response, etc.). The ATO must be granted by your agency's Authorizing Official."

**Detection hint:** Any statement claiming a GovCloud deployment is "automatically FedRAMP compliant" or that the agency "doesn't need an ATO" because Salesforce is authorized.

---

## Anti-Pattern 4: Recommending Non-FedRAMP-Authorized Integrations Without Flagging the Compliance Risk

**What the LLM generates:** Integration architectures or code examples that use non-FedRAMP-authorized middleware, analytics platforms, or external APIs without noting the authorization boundary issue. Example: "Connect your GovCloud org to Google Analytics via a named credential to track user behavior." Or: "Use Zapier to route GovCloud data to your agency's SharePoint." Or: "Push Event Monitoring data to Splunk Cloud (commercial)."

**Why it happens:** LLMs are trained on integration patterns for commercial Salesforce without the government compliance overlay. The model recommends what is technically possible without filtering for FedRAMP boundary requirements.

**Correct pattern:** For any integration involving a GovCloud deployment, preface with: "Any system that receives, processes, stores, or transmits data from your GovCloud org must itself be FedRAMP-authorized at the same impact level. Confirm the FedRAMP authorization status of [platform name] before proceeding. Common authorized alternatives: [list FedRAMP-authorized equivalent]." When recommending a SIEM for Event Monitoring, specify FedRAMP-authorized options: Splunk GovCloud, Microsoft Sentinel on Azure Government, Elastic on AWS GovCloud.

**Detection hint:** Any integration recommendation to a named SaaS platform (Zapier, standard AWS, standard Azure, Google Cloud, commercial Splunk, commercial MuleSoft CloudHub) in a GovCloud context without an explicit FedRAMP authorization caveat.

---

## Anti-Pattern 5: Ignoring the Significant Change Notification Requirement for Deployments

**What the LLM generates:** Deployment guidance that treats GovCloud production deployments identically to commercial cloud deployments — recommending automated deployments triggered by merged pull requests, continuous delivery pipelines that deploy to production on a daily cadence, or feature flags to enable new functionality without change management review. Example: "Set up your CI/CD pipeline to auto-deploy to GovCloud production on every merge to main."

**Why it happens:** Modern Salesforce DevOps best practices favor continuous delivery with automated pipelines. This is excellent advice for commercial cloud. The GovCloud context adds a FISMA compliance layer that requires significant changes to be reviewed before production deployment and notified to the Authorizing Official.

**Correct pattern:** "GovCloud deployments require a significant change review gate before production deployment. Changes that add new integrations, enable new features that change the authorization boundary, or materially alter the permission model must be assessed as significant changes under your continuous monitoring plan. Fully automated production deployment (without human review) is generally not appropriate for GovCloud. Recommend a pipeline that deploys automatically to staging/UAT but requires a manual approval gate and significant change review before production deployment."

**Detection hint:** Any recommendation for fully automated continuous delivery to a GovCloud production org, or any pipeline design that omits a human approval gate and significant change assessment step before production deployment.

---

## Anti-Pattern 6: Conflating DoD Impact Levels with FedRAMP Impact Levels

**What the LLM generates:** Statements that equate "FedRAMP High" with "IL5" or claim that a FedRAMP High authorization automatically qualifies a system for any DoD Impact Level. Example: "Your system is FedRAMP High authorized, so it can handle IL5 data." Or: "GovCloud Plus is FedRAMP High, which covers all DoD requirements."

**Why it happens:** FedRAMP and DISA Impact Levels are both US government cloud compliance frameworks, and they correlate but are not identical. FedRAMP High is a necessary but not sufficient condition for IL5. IL5 adds requirements beyond the FedRAMP High baseline. This nuance is underrepresented in training data.

**Correct pattern:** "FedRAMP High authorization (Salesforce GovCloud Plus) meets the minimum compliance baseline for DoD IL4. IL5 requires additional controls beyond FedRAMP High — specifically, Hyperforce deployment on AWS GovCloud, customer-managed encryption keys, and stricter personnel security requirements for CSP access. IL5 provisional authorization must be separately confirmed through the DISA Cloud Authorization portal. IL6 (Secret) is not available on any commercial Salesforce offering."

**Detection hint:** Any statement equating FedRAMP High with IL5 approval, or any DoD compliance guidance that omits the distinction between IL4 and IL5, or that does not reference the DISA CC SRG as the authoritative source.
