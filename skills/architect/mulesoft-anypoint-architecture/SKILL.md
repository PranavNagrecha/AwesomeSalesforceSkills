---
name: mulesoft-anypoint-architecture
description: "Use when designing or evaluating MuleSoft Anypoint Platform deployment topology, runtime model selection, API governance with API Manager, or Anypoint Exchange strategy. Trigger keywords: CloudHub, Runtime Fabric, Anypoint Platform, API Manager, Anypoint Exchange, MuleSoft runtime model, private space, Anypoint Security. NOT for Salesforce-native integration patterns (use integration/api-led-connectivity), NOT for Salesforce Connector configuration in MuleSoft (use integration/mulesoft-salesforce-connector), NOT for MuleSoft flow implementation or DataWeave scripting."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
  - Performance
triggers:
  - "Which MuleSoft runtime model should we deploy to — CloudHub or Runtime Fabric?"
  - "How do I enforce API policies across all integrations in Anypoint Platform?"
  - "What is the difference between CloudHub 1.0, CloudHub 2.0, and Runtime Fabric for our org?"
  - "We need to share reusable APIs and assets across teams using MuleSoft — where do they live?"
  - "API Manager policies are configured but not being enforced at runtime"
tags:
  - mulesoft
  - anypoint-platform
  - cloudhub
  - runtime-fabric
  - api-manager
  - api-governance
  - integration-architecture
inputs:
  - "Deployment requirements: data residency, private network access, Kubernetes infrastructure ownership"
  - "API governance requirements: authentication policies, rate limiting, threat protection"
  - "Team structure: number of integration teams, asset-sharing requirements"
  - "Scale and reliability requirements: expected throughput, SLA targets"
outputs:
  - "Runtime model selection recommendation with rationale"
  - "API Manager policy configuration plan"
  - "Anypoint Exchange asset organization strategy"
  - "Deployment topology diagram notes"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# MuleSoft Anypoint Architecture

Use this skill when selecting a MuleSoft Anypoint Platform runtime model, designing API governance with API Manager, or structuring assets in Anypoint Exchange. This skill covers platform-level topology decisions — it does not cover Salesforce-specific connector configuration or DataWeave scripting.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the organization requires private network access, customer-managed Kubernetes, or is comfortable with a fully-managed SaaS runtime
- Determine whether data residency or compliance requirements constrain which CloudHub regions are available
- Check the current Anypoint Platform subscription tier — Anypoint Security features (Tokenization, Edge) are not available on all runtime models
- Identify whether APIs have been deployed to API Manager yet — policies cannot be enforced until an API Instance is registered and in Active status

---

## Core Concepts

### The Four Runtime Models

MuleSoft Anypoint Platform offers four runtime deployment models. Selecting the wrong one is the most common architectural mistake:

- **CloudHub 1.0** — Fully MuleSoft-managed SaaS. Mule runtimes run in MuleSoft-owned AWS infrastructure. Simplest to operate. Does not support private spaces (all traffic routes through MuleSoft's public infrastructure unless VPN is configured). 12+ available regions. Use when simplicity and managed operations are the priority and private network isolation is not required.
- **CloudHub 2.0** — Containerized iPaaS. Mule runtimes run in MuleSoft-managed containers with a private space option for VPC-level isolation. Supports 12+ regions. Use when a managed runtime is preferred but private network isolation or a specific region is required. CloudHub 2.0 is NOT customer-managed Kubernetes.
- **Runtime Fabric (RTF)** — Customer-managed Kubernetes cluster with MuleSoft's cloud-based control plane. The organization owns and operates the Kubernetes infrastructure; MuleSoft manages the Anypoint control plane. Use when the organization must own the runtime infrastructure (compliance, on-premises, hybrid cloud). Requires Kubernetes operations capability.
- **Hybrid Standalone** — Mule runtime installed on customer-owned VMs or bare-metal servers, registered to Anypoint Platform's Runtime Manager. Least automated, maximum customer control. Use for legacy on-premises deployments with existing VM infrastructure.

**Key constraint:** Anypoint Security Edge (tokenization proxy) and some Anypoint Security Tokenization features are NOT supported on Runtime Fabric. Verify feature support before selecting RTF for security-sensitive deployments.

### API Manager as Governance Layer

API Manager is the governance and policy enforcement layer for Anypoint Platform. Critical behaviors:

- API Manager stores policy configuration. Policy enforcement happens at the Mule runtime (not in Anypoint Platform cloud).
- An API must be registered as an **API Instance** in API Manager and set to **Active** status before policies are enforced. Inactive API Instances have policies configured but not applied — policies silently do not run.
- The Mule runtime must have the **API Autodiscovery** element configured with the correct API Instance ID. Without this binding, the runtime does not contact API Manager and runs with no governance.
- Rate limiting, OAuth 2.0 token enforcement, IP allowlisting, and threat protection are all API Manager policies applied at the gateway layer.

### Anypoint Exchange as Asset Repository

Anypoint Exchange is the internal and external asset marketplace for the organization:

- REST APIs (RAML or OAS specs), connectors, templates, examples, and DataWeave libraries are published to Exchange
- Assets are versioned independently of deployments
- Exchange enables self-service discovery for integration teams — this is the primary mechanism for enforcing API-led connectivity asset reuse
- Exchange is scoped to an Anypoint Organization (the top-level account boundary)

---

## Common Patterns

### Runtime Model Selection

**When to use:** Every new MuleSoft deployment project.

**How it works:**
1. Determine if customer must own Kubernetes infrastructure → Runtime Fabric
2. Determine if private VPC-level isolation is required without owning Kubernetes → CloudHub 2.0 private space
3. Determine if fully managed with public routing is acceptable → CloudHub 1.0 or CloudHub 2.0
4. Determine if existing VM/on-premises infrastructure → Hybrid Standalone

**Why not to default to Runtime Fabric:** RTF requires the customer to provision, upgrade, and operate Kubernetes clusters. Teams without Kubernetes operations capability will struggle with RTF despite it appearing like a "more enterprise" choice.

### API Manager Policy Enforcement Setup

**When to use:** When deploying a new API and needing to enforce authentication, rate limiting, or threat protection.

**How it works:**
1. Register the API in API Manager → creates an API Instance with an Instance ID
2. Set the API Instance to **Active** status
3. Apply policies to the API Instance (e.g., OAuth 2.0, Client ID Enforcement, Rate Limiting)
4. Add `<api-gateway:autodiscovery apiId="${api.id}" flowRef="main"/>` to the Mule application
5. Set `api.id` in application properties to the API Instance ID
6. Deploy the Mule application — runtime now contacts API Manager and enforces policies

**Why Active status matters:** Inactive API Instances have policies configured in API Manager but the runtime receives no policy instructions. The application runs without enforcement and generates no error.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Fully managed cloud runtime, no compliance/data residency constraints | CloudHub 1.0 or CloudHub 2.0 | Least operational overhead; MuleSoft manages infrastructure |
| Need private network isolation without owning Kubernetes | CloudHub 2.0 with private space | Managed containers + VPC-level isolation; simpler than RTF |
| Must own runtime infrastructure (compliance, on-premises hybrid) | Runtime Fabric on customer Kubernetes | Customer-managed K8s + MuleSoft control plane |
| Anypoint Security Edge / Tokenization required | CloudHub 1.0 or CloudHub 2.0 | Edge/Tokenization not supported on Runtime Fabric |
| API not enforcing policies despite configuration | Verify API Instance is Active + Autodiscovery is configured | Inactive status or missing Autodiscovery means no enforcement |
| Teams need to share and discover reusable integration assets | Publish to Anypoint Exchange | Exchange is the platform-native asset marketplace |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Gather requirements** — Determine data residency, compliance requirements, private network access needs, Kubernetes ownership capability, and Anypoint Security feature requirements (Edge, Tokenization)
2. **Select runtime model** — Apply the decision table above. Confirm CloudHub vs RTF vs Hybrid. If RTF, confirm the organization has Kubernetes operations capability
3. **Design API Manager governance** — Identify which APIs require policies, register API Instances, confirm Active status, define policy sets (OAuth, rate limiting, threat protection), document Autodiscovery configuration
4. **Plan Anypoint Exchange structure** — Define asset naming conventions, versioning strategy, and which teams publish vs. consume assets
5. **Validate Anypoint Security feature compatibility** — If Edge or Tokenization is required, confirm the selected runtime model supports it before committing to RTF
6. **Document the topology** — Produce a deployment topology diagram covering runtime model, API Manager governance points, Exchange asset registry, and private space or VPC configuration
7. **Review against Well-Architected pillars** — Confirm security policies are enforced (not just configured), reliability SLAs are compatible with the selected runtime, and operational runbooks exist for the runtime model

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Runtime model selected and rationale documented (CloudHub 1.0 / 2.0 / RTF / Hybrid)
- [ ] API Manager API Instances are in Active status for all governed APIs
- [ ] Mule applications have Autodiscovery configured with correct API Instance IDs
- [ ] Anypoint Security feature requirements (Edge/Tokenization) validated against selected runtime model
- [ ] Anypoint Exchange asset structure and naming conventions defined
- [ ] Private space or VPC configuration documented if private network isolation is required
- [ ] Kubernetes operations capability confirmed before recommending Runtime Fabric

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **API Manager policies configured but not enforced** — An API Instance in Inactive status has all policies configured in API Manager, but the Mule runtime does not receive policy instructions. APIs run unprotected with no error message and no log entry indicating enforcement is disabled.
2. **CloudHub 2.0 is not Runtime Fabric** — CloudHub 2.0 uses MuleSoft-managed containers. Runtime Fabric uses customer-managed Kubernetes. Recommending RTF for a "cloud-native" deployment without confirming Kubernetes operations capability creates a significant operational burden the team is not prepared for.
3. **Anypoint Security Edge not supported on Runtime Fabric** — Tokenization and Edge policies are only available on CloudHub 1.0 and CloudHub 2.0. Selecting Runtime Fabric for compliance reasons and then discovering Edge is unavailable requires a full runtime model migration.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Runtime model selection document | Rationale for CloudHub / RTF / Hybrid with requirements mapped to features |
| API Manager governance plan | API Instance list, policy assignments, Active status checklist, Autodiscovery config |
| Anypoint Exchange asset inventory | Asset names, versions, owning teams, consumer teams |
| Deployment topology notes | Runtime model, region, private space/VPC config, API gateway enforcement points |

---

## Related Skills

- `integration/api-led-connectivity` — For designing the Experience/Process/System API layer pattern within MuleSoft
- `integration/mulesoft-salesforce-connector` — For configuring the Salesforce connector within a Mule application
- `integration/hybrid-integration-architecture` — For decisions about when MuleSoft vs. Salesforce-native integration is appropriate
