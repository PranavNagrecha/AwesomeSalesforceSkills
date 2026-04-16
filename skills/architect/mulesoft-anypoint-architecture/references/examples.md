# Examples — MuleSoft Anypoint Architecture

Real-world scenarios where runtime model selection or API governance decisions have caused production issues.

---

## Example 1: API Policies Not Enforced Because API Instance Was Inactive

**Scenario:** A team deployed OAuth 2.0 Client ID Enforcement on a payment processing API through API Manager. In QA, the API accepted requests without a valid client ID. The team assumed the policy configuration was broken.

**Root cause:** The API Instance in API Manager was still in Inactive status. Inactive Instances have policies stored but do not instruct the Mule runtime to enforce them. The Mule runtime ran the application with no governance, and no error was logged.

**Resolution:** Set the API Instance to Active in API Manager. The Mule runtime immediately began receiving policy enforcement instructions from API Manager. Subsequent requests without a valid client ID were rejected.

**Lesson:** Always verify API Instance status is Active after configuring policies. Inactive status is a silent failure mode — there is no warning in API Manager and no error in the Mule application logs.

---

## Example 2: Runtime Fabric Recommended for Cloud Deployment Without Kubernetes Capability

**Scenario:** An architect designed a MuleSoft deployment architecture for a financial services firm. The design specified Runtime Fabric because the firm required "enterprise-grade, customer-controlled infrastructure." The firm's IT team did not operate Kubernetes clusters.

**Root cause:** Runtime Fabric was conflated with "more enterprise than CloudHub" without considering that RTF requires the customer to provision and operate Kubernetes. CloudHub 2.0 with a private space would have provided the required VPC-level network isolation and data residency without Kubernetes operational burden.

**Resolution:** Architecture was revised to use CloudHub 2.0 private spaces in the required region. The firm got private network isolation without Kubernetes management overhead.

**Lesson:** Runtime Fabric is appropriate when the organization already operates Kubernetes and must own the runtime infrastructure. For cloud deployments requiring private isolation without Kubernetes ownership, CloudHub 2.0 private spaces are the correct choice.

---

## Example 3: Anypoint Security Edge Blocked by Runtime Fabric Selection

**Scenario:** An organization selected Runtime Fabric for their MuleSoft deployment because compliance required on-premises-like infrastructure control. After deployment, the security team requested Anypoint Security Edge (tokenization proxy at the API gateway layer) for PCI compliance.

**Root cause:** Anypoint Security Edge is not supported on Runtime Fabric. The constraint was not identified during runtime model selection.

**Resolution:** The organization had to run a parallel CloudHub 2.0 deployment for APIs that required Edge tokenization, creating a split runtime environment.

**Lesson:** Verify Anypoint Security feature requirements (Edge, Tokenization) before finalizing runtime model selection. Edge and Tokenization are only available on CloudHub 1.0 and CloudHub 2.0.
