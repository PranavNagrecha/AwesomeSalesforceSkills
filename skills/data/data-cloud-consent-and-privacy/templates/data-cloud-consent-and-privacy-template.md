# Data Cloud Consent and Privacy — Work Template

Use this template when implementing consent management, data subject requests, or retention policies in Data Cloud.

## Scope

**Skill:** `data-cloud-consent-and-privacy`

**Request summary:** (fill in: consent enforcement, deletion request, or retention policy task)

## Consent Framework Assessment

- **ssot__ContactPointConsent__dlm populated?** [ ] Yes  [ ] No — populate before segment build
- **Data Use Purposes configured:** (list: e.g., "Marketing Email", "Marketing SMS")
- **Consent filter added to all marketing segments?** [ ] Yes  [ ] No — add OptIn filter

## Segment Consent Filter (required for every marketing segment)

```
Related Filter: ssot__ContactPointConsent__dlm
  DataUsePurpose = '<specific purpose>'
  AND Status = 'OptIn'
```

- [ ] Consent filter verified in Segment Builder for all active segments

## Deletion Request Workflow

- **Submission method:** [ ] Privacy Center  [ ] Data Deletion API
- **Identifier type:** [ ] Email  [ ] Phone  [ ] Other:
- **Processing SLA:** Up to 90 days
- **Downstream cascade deletion plan:**
  - [ ] Marketing Cloud
  - [ ] Ad platforms
  - [ ] External data warehouse
  - [ ] SFTP exports

## Retention Policy Configuration

| DLO Name | Retention (days) | Compliance Basis |
|---|---|---|
| (DLO name) | (days) | (GDPR/CCPA) |

- **Configured before ingestion begins?** [ ] Yes  [ ] No (retroactive requires Deletion API)

## Checklist

- [ ] Consent records in ssot__ContactPointConsent__dlm for applicable Data Use Purposes
- [ ] All marketing segments have explicit OptIn consent filter
- [ ] CCPA Do Not Sell mapped to custom Data Use Purpose (if applicable)
- [ ] Deletion workflow documented and tested
- [ ] Downstream cascade deletion strategy defined
- [ ] DLO retention policies configured per compliance requirement

## Notes

(Record consent model gaps, downstream cascade complexity, CCPA-specific configurations)
