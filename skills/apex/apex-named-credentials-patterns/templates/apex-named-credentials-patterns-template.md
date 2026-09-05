# Apex Named Credentials Patterns — Work Template

Copy this into your working notes at the start of a Named Credential task. Fill it in as you
go; the finished form is the handover artefact for whoever reviews or deploys the change.

**Skill:** `apex-named-credentials-patterns`

**Request summary:** _(what the requester asked for, in their words)_

---

## 1. Context — answers to the Questions to Ask table

| Question | Answer |
|---|---|
| Named Credential API name | |
| Does that name exist in every target org (scratch / sandbox / prod)? | |
| Model — `Legacy` or `SecuredEndpoint`? | |
| External Credential name (`SecuredEndpoint` only) | |
| `authenticationProtocol` | |
| Principal type — `NamedPrincipal` or `PerUserPrincipal`? | |
| Principal `parameterName` | |
| Permission set granting the principal | |
| User the callout runs as (and is that user assigned the set?) | |
| Who owns the `Authorization` header — platform or Apex? | |
| Merge fields needed? Which, and in header or body? | |
| Transaction type — sync / Queueable / Batch / Continuation | |
| Endpoint host, and is a Remote Site Setting still present for it? | |

Evidence for the model question:

```bash
sf data query --query "SELECT DeveloperName, Endpoint, PrincipalType, CalloutOptionsGenerateAuthorizationHeader, CalloutOptionsAllowMergeFieldsInHeader, CalloutOptionsAllowMergeFieldsInBody FROM NamedCredential"
```

A populated `Endpoint` or `PrincipalType` means the credential is legacy — both fields are
legacy-only and deprecated at API 56.0.

---

## 2. Approach

**Pattern chosen from SKILL.md § Common Patterns:**

- [ ] Environment-portable callout through a `SecuredEndpoint` credential
- [ ] Endpoint that needs the credential in a non-standard header
- [ ] Replacing a Remote Site Setting plus a hardcoded secret
- [ ] Other — describe below

**Why this one, and what was rejected:**

**Decision-guidance row that settled it:**

---

## 3. Artefacts to produce

| # | Artefact | Path | Done |
|---|---|---|---|
| 1 | `ExternalCredential` XML | `force-app/main/default/externalCredentials/` | |
| 2 | `NamedCredential` XML | `force-app/main/default/namedCredentials/` | |
| 3 | `PermissionSet` grant | `force-app/main/default/permissionsets/` | |
| 4 | Apex client + `-meta.xml` | `force-app/main/default/classes/` | |
| 5 | Apex test class | `force-app/main/default/classes/` | |
| 6 | `package.xml` | `manifest/` | |

Shapes for 1–6 are in `references/code-examples.md`.

---

## 4. Checklist

Copied from SKILL.md § Review Checklist — tick as you verify each one, and note where.

- [ ] All callout endpoints use the `callout:<NCApiName>` prefix — no literal base URLs.
- [ ] Every `callout:` name resolves to a Named Credential that exists in the target org.
- [ ] `generateAuthorizationHeader` is deployed explicitly, and exactly one side sets `Authorization`.
- [ ] Any `{!$Credential.*}` merge field is paired with the matching `allowMergeFields*` flag in the same change.
- [ ] `HTMLENCODE` appears only around body merge fields, never header ones.
- [ ] The External Credential declares a principal, and a permission set grants it.
- [ ] The permission set is assigned to the user the callout actually runs as, including in async contexts.
- [ ] `req.setTimeout()` is set explicitly.
- [ ] Tests use `HttpCalloutMock` (or `Test.setContinuationResponse`) and cover 401.
- [ ] No secret remains in a Custom Label, Custom Setting, or Custom Metadata record after migration.
- [ ] Checker is clean.

```bash
python3 skills/apex/apex-named-credentials-patterns/scripts/check_apex_named_credentials_patterns.py \
    --manifest-dir force-app --strict
sf apex run test --tests <YourTestClass> --result-format human --wait 10
```

---

## 5. Deploy log

| Step | Command or action | Result |
|---|---|---|
| 1 | `sf project deploy start --metadata ExternalCredential:<name>` | |
| 2 | `sf project deploy start --metadata NamedCredential:<name>` | |
| 3 | `sf project deploy start --metadata PermissionSet:<name>` | |
| 4 | Human enters credential values against the principal in Setup | |
| 5 | `sf project deploy start --manifest manifest/package.xml --test-level RunSpecifiedTests --tests <TestClass>` | |
| 6 | `sf org assign permset --name <name>` | |
| 7 | Smoke callout as a granted user | |

---

## 6. Notes

**Deviations from the standard pattern, and why:**

**Anything marked UNVERIFIED in the skill that this change depends on — and how it was
confirmed against the org:**

**Cleanup still outstanding (Remote Site Setting removed? old secret rotated?):**
