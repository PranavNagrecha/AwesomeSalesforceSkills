# MuleSoft Anypoint Architecture — Work Template

Use this template when designing or evaluating a MuleSoft Anypoint Platform deployment.

## Project Context

- Organization: ___________
- Project scope: ___________
- Data residency requirements: ___________
- Compliance requirements (PCI, HIPAA, etc.): ___________

---

## Runtime Model Selection

| Requirement | Value | Notes |
|---|---|---|
| Must own Kubernetes infrastructure | Yes / No | |
| Private VPC-level isolation required | Yes / No | |
| Anypoint Security Edge required | Yes / No | |
| Anypoint Tokenization required | Yes / No | |
| Organization has Kubernetes ops capability | Yes / No | |
| Target cloud region(s) | | |

**Selected runtime model:** [ ] CloudHub 1.0  [ ] CloudHub 2.0  [ ] Runtime Fabric  [ ] Hybrid Standalone

**Rationale:** ___________

---

## API Manager Governance Plan

| API Name | API Instance ID | Status | Policies Applied | Autodiscovery Configured |
|---|---|---|---|---|
| | | Active / Inactive | | Yes / No |
| | | Active / Inactive | | Yes / No |
| | | Active / Inactive | | Yes / No |

**Autodiscovery config snippet (per Mule app):**

```xml
<api-gateway:autodiscovery apiId="${api.id}" flowRef="main"/>
```

**Application property (`api.id`):** Set to the API Instance ID from API Manager.

---

## Anypoint Exchange Asset Inventory

| Asset Name | Type | Version | Owner Team | Published |
|---|---|---|---|---|
| | REST API / Connector / Template | | | Yes / No |
| | REST API / Connector / Template | | | Yes / No |

---

## Anypoint Security Validation

- [ ] Anypoint Security Edge requirement checked against selected runtime model
- [ ] Anypoint Tokenization requirement checked against selected runtime model
- [ ] If RTF selected: Edge and Tokenization confirmed NOT required, OR runtime model revised to CloudHub

---

## Post-Deployment API Governance Validation

```bash
# Call a governed API without credentials — expect 401 (policy enforcement active)
curl -i https://<api-endpoint>/<resource>
# Expected: HTTP 401 Unauthorized
# If HTTP 200: API Instance may be Inactive or Autodiscovery misconfigured

# Call with valid client credentials — expect 200
curl -i -H "client_id: <id>" -H "client_secret: <secret>" https://<api-endpoint>/<resource>
# Expected: HTTP 200 OK
```

---

## Deployment Checklist

- [ ] Runtime model selected with documented rationale
- [ ] CloudHub 2.0 private space configured (if private isolation required)
- [ ] All API Instances registered in API Manager and set to Active
- [ ] All Mule applications have Autodiscovery configured with correct Instance IDs
- [ ] Anypoint Security features verified against selected runtime model
- [ ] Exchange assets published with correct naming and versioning
- [ ] Post-deployment policy enforcement test passed (unauthenticated request rejected)

---

## Notes

_Capture runtime model rationale, Kubernetes capability assessment, and open Anypoint Security questions._
