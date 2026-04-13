# Cross-Cloud Deployment Patterns — Work Template

Use this template when planning or executing a deployment that spans Sales Cloud, Service Cloud, and Experience Cloud. Fill in each section before starting the deployment.

## Scope

**Skill:** `cross-cloud-deployment-patterns`

**Release name / ticket:** (fill in)

**Request summary:** (describe what is being released across which clouds)

## Context Gathered

Answer the Before Starting questions from SKILL.md:

- **Metadata types in scope:** (list all types — classify each as foundation / network / experience)
- **Source org API version:** (e.g., 63.0)
- **Target org API version:** (e.g., 63.0) — must be >= source
- **SiteDotCom present in retrieved metadata?** YES / NO — if YES, exclude before packaging
- **Network record name(s):** (name of the Network/CustomSite to be deployed)
- **ExperienceBundle or DigitalExperienceBundle?** (confirm which type based on org API version)
- **Deployment tool:** sf CLI / Metadata API / DevOps Center / Change Sets

## Deployment Batches

### Batch 1 — Foundation Layer

**package.xml location:** `manifests/foundation-package.xml`

**Types included:**
- [ ] CustomObject
- [ ] CustomField
- [ ] ApexClass
- [ ] ApexTrigger
- [ ] LightningComponentBundle
- [ ] PermissionSet
- [ ] Profile
- [ ] (add others as needed)

**Deploy command:**
```bash
sf project deploy start \
  --manifest manifests/foundation-package.xml \
  --target-org <alias> \
  --wait 60
```

**Validation gate:** Deployment must show `Deploy Succeeded` before proceeding to Batch 2.

---

### Batch 2 — Network Layer

**package.xml location:** `manifests/network-package.xml`

**Types included:**
- [ ] Network — member: `<NetworkName>`
- [ ] CustomSite — member: `<SiteName>`

**Deploy command:**
```bash
sf project deploy start \
  --manifest manifests/network-package.xml \
  --target-org <alias> \
  --wait 30
```

**Verification query (run after deploy):**
```bash
sf data query \
  --query "SELECT Id, Name, Status FROM Network WHERE Name = '<NetworkName>'" \
  --target-org <alias>
```

**Validation gate:** Network record must be queryable before proceeding to Batch 3.

---

### Batch 3 — Experience Layer

**package.xml location:** `manifests/experience-package.xml`

**Types included:**
- [ ] ExperienceBundle OR DigitalExperienceBundle — member: `<SiteName>`
- [ ] SiteDotCom EXCLUDED (confirm)

**Deploy command:**
```bash
sf project deploy start \
  --manifest manifests/experience-package.xml \
  --target-org <alias> \
  --wait 30
```

**Validation gate:** Site must be accessible after deployment.

---

## Pre-Flight Checklist

- [ ] All metadata classified into foundation / network / experience layers
- [ ] SiteDotCom excluded from all package.xml files and .forceignore updated
- [ ] Target org API version confirmed >= source org API version
- [ ] Foundation batch package.xml built and reviewed
- [ ] Network batch package.xml built and reviewed
- [ ] Experience batch package.xml built and reviewed, no SiteDotCom entries

## Post-Deployment Checklist

- [ ] Foundation deploy succeeded with no errors
- [ ] Network deploy succeeded, Network record queryable
- [ ] Experience deploy succeeded, no 'no Network named X found' errors
- [ ] Experience Cloud site loads correctly in target org
- [ ] Permission sets grant expected access
- [ ] Automated smoke tests passed

## Notes

(Record any deviations from the standard pattern, reasons, and outcomes)
