# LLM Anti-Patterns — MuleSoft Anypoint Architecture

Common mistakes AI coding assistants make when generating or advising on MuleSoft Anypoint Platform architecture.

---

## Anti-Pattern 1: Recommending Runtime Fabric for Generic Cloud Deployments

**What the LLM generates:** An architecture recommendation that selects Runtime Fabric because "it is the most enterprise-grade and cloud-native option for production MuleSoft deployments," without evaluating whether the organization operates Kubernetes.

**Why it happens:** LLMs associate "Kubernetes" and "container-native" with enterprise best practice without modeling that RTF requires the customer to provision and operate Kubernetes clusters. RTF appears as the most capable runtime and gets selected as the default.

**Correct pattern:** Runtime Fabric is appropriate only when the organization must own the runtime infrastructure and already has Kubernetes operations capability. For cloud deployments requiring private isolation without Kubernetes ownership, CloudHub 2.0 private spaces are the correct choice.

**Detection hint:** If a runtime model recommendation does not evaluate Kubernetes operations capability and data residency constraints explicitly, the selection may be wrong.

---

## Anti-Pattern 2: Treating API Manager Policies as Automatically Enforced After Configuration

**What the LLM generates:** Instructions to configure OAuth 2.0 policy in API Manager, then mark the API as secured — without mentioning that the API Instance must be Active and the Mule application must have Autodiscovery configured.

**Why it happens:** LLMs model policy configuration as the final step and do not model the two-part enforcement mechanism (Active status + Autodiscovery binding). Policy configuration in the UI appears complete, so the LLM treats it as complete.

**Correct pattern:** API Manager policies are enforced only when: (1) the API Instance is Active, and (2) the Mule application has `api-gateway:autodiscovery` configured with the correct API Instance ID. Both conditions must be met. Post-deployment, validate enforcement by calling the API without credentials and confirming a policy rejection.

**Detection hint:** If an API governance plan configures policies in API Manager but does not mention Active status or Autodiscovery configuration, enforcement is not confirmed.

---

## Anti-Pattern 3: Conflating CloudHub 2.0 with Runtime Fabric

**What the LLM generates:** Architecture documentation or a selection recommendation that describes CloudHub 2.0 as "customer-managed containers" or describes Runtime Fabric as "a newer version of CloudHub 2.0."

**Why it happens:** Both involve containers and are newer than CloudHub 1.0. LLMs conflate them because they appear adjacent in the runtime model list and both involve containerization.

**Correct pattern:** CloudHub 2.0 = MuleSoft-managed containers (customer does not touch the infrastructure). Runtime Fabric = customer-managed Kubernetes cluster with MuleSoft cloud control plane. These are fundamentally different operational models with different responsibility boundaries.

**Detection hint:** If architecture documentation describes CloudHub 2.0 as "customer-managed" or Runtime Fabric as "like CloudHub 2.0 but with more control," the model is wrong.

---

## Anti-Pattern 4: Recommending Runtime Fabric When Anypoint Security Edge Is Required

**What the LLM generates:** An architecture that selects Runtime Fabric for compliance reasons and also specifies Anypoint Security Edge (tokenization proxy) as a security control.

**Why it happens:** LLMs do not model that Edge and Tokenization are feature-limited to CloudHub runtimes. RTF appears to be the more secure and controlled runtime, so it gets selected alongside security features without checking feature compatibility.

**Correct pattern:** Anypoint Security Edge and Tokenization are only available on CloudHub 1.0 and CloudHub 2.0. If either feature is required, the runtime model must be CloudHub. Verify all required Anypoint Security features before finalizing runtime model selection.

**Detection hint:** If a design specifies both Runtime Fabric and Anypoint Security Edge or Tokenization, this combination is not supported.

---

## Anti-Pattern 5: Omitting Anypoint Exchange from Multi-Team Integration Architecture

**What the LLM generates:** A multi-team MuleSoft integration architecture where each team builds and maintains its own connectors, RAML specs, and DataWeave libraries in isolation, with no shared asset repository.

**Why it happens:** LLMs generate self-contained integration designs without modeling the organizational asset-sharing mechanism. Exchange is not mentioned because it appears optional rather than foundational to API-led connectivity at scale.

**Correct pattern:** Anypoint Exchange is the platform-native asset marketplace for the organization. REST API specs, connectors, templates, and DataWeave libraries should be published to Exchange so that integration teams can discover and reuse them. Omitting Exchange from multi-team architectures creates duplicated work, inconsistent implementations, and no governance over which API versions are in use.

**Detection hint:** If a multi-team MuleSoft architecture does not mention Anypoint Exchange or an equivalent asset sharing mechanism, teams will build redundant integration assets.
