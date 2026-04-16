# Gotchas — MuleSoft Anypoint Architecture

Non-obvious Anypoint Platform behaviors that cause real production problems.

---

## Gotcha 1: Inactive API Instance = Silent Policy Bypass

An API Instance in API Manager can have OAuth 2.0, rate limiting, and threat protection policies fully configured while in Inactive status. In that state, the Mule runtime receives no policy instructions and runs the application without enforcement. There is no error message, no warning log, and no API Manager alert. Traffic passes through as if no policies exist.

**Fix:** After configuring policies in API Manager, explicitly set the API Instance to Active. Build a post-deployment verification step that calls the API without credentials and confirms a policy rejection (401 or 429) is returned.

---

## Gotcha 2: Autodiscovery Missing = API Manager Governance Never Applied

API Manager policy enforcement requires the Mule application to have an `api-gateway:autodiscovery` element in its XML config, bound to the correct API Instance ID. If this element is missing or uses a wrong ID, the Mule runtime never contacts API Manager. The application runs with no governance and no log entry indicating governance is missing.

**Fix:** Add `<api-gateway:autodiscovery apiId="${api.id}" flowRef="main"/>` to every governed Mule application. Externalize `api.id` as an application property. Verify the ID matches the API Instance ID in API Manager.

---

## Gotcha 3: Anypoint Security Edge and Tokenization Are Not Supported on Runtime Fabric

Anypoint Security Edge (a tokenization proxy at the API gateway edge) and Anypoint Security Tokenization policies are only available on CloudHub 1.0 and CloudHub 2.0. Deploying on Runtime Fabric and then attempting to apply Edge policies fails — Edge is simply not available on that runtime model.

**Fix:** Identify Anypoint Security feature requirements before selecting a runtime model. If Edge or Tokenization is required, the deployment must run on CloudHub 1.0 or CloudHub 2.0.

---

## Gotcha 4: CloudHub 2.0 and Runtime Fabric Are Not the Same

CloudHub 2.0 uses MuleSoft-managed containers (the customer does not manage the underlying infrastructure). Runtime Fabric uses customer-managed Kubernetes clusters with MuleSoft's cloud control plane. Selecting Runtime Fabric for a "cloud-native" or "modern Kubernetes" deployment when the team has no Kubernetes operations experience creates immediate operational problems: cluster provisioning, upgrade management, node failure recovery, and certificate rotation all become customer responsibilities.

**Fix:** Default to CloudHub 2.0 for cloud deployments. Only select Runtime Fabric when the organization already operates Kubernetes and explicitly needs to own the runtime infrastructure for compliance or data residency reasons.

---

## Gotcha 5: API Manager Policies Are Per-API-Instance, Not Per-Environment Globally

Policies in API Manager are applied to individual API Instances. There is no global policy that automatically applies to all APIs in an environment. Each API Instance must have policies applied independently. Teams that add new APIs without registering them in API Manager and configuring policies have unprotected APIs in production with no enforcement.

**Fix:** Establish a mandatory API registration process: every new API must be registered in API Manager, set to Active, and have minimum policies (Client ID Enforcement or OAuth 2.0) applied before deployment to production. Enforce this through deployment pipeline gates.
