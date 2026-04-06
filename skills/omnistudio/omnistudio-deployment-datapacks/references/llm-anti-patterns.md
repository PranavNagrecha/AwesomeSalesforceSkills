# LLM Anti-Patterns — OmniStudio Deployment DataPacks

Common mistakes AI coding assistants make when generating or advising on OmniStudio DataPack deployment.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Standard Metadata API Deployment for OmniStudio Components

**What the LLM generates:** "Deploy OmniScripts using sf project deploy start" when OmniStudio components historically required DataPacks (vlocity CLI) for deployment, not standard Metadata API.

**Why it happens:** Standard SFDX deployment is the default Salesforce CI/CD pattern. LLMs apply it universally without noting that OmniStudio components have their own deployment mechanism. Note: recent Salesforce releases are adding Metadata API support for some OmniStudio components, but DataPacks remain the primary method for many.

**Correct pattern:**

```text
OmniStudio deployment options:

DataPacks (vlocity CLI / OmniStudio CLI):
- Primary deployment method for OmniStudio components
- Exports/imports as JSON files in source control
- Handles OmniStudio-specific dependencies and references
- Command: vlocity packDeploy / vlocity packExport

Metadata API (emerging support):
- Some OmniStudio components now support Metadata API deployment
- Check Salesforce release notes for current coverage
- OmniProcess, FlexCard metadata types may be deployable
- Not all components are supported yet

Recommendation:
- Use DataPacks for comprehensive OmniStudio deployment
- Use Metadata API only for components confirmed to support it
- Do not mix deployment methods for the same component
```

**Detection hint:** Flag standard `sf project deploy` commands for OmniStudio components without verifying Metadata API support. Check for missing DataPack deployment consideration.

---

## Anti-Pattern 2: Not Handling Environment-Specific Record IDs in DataPacks

**What the LLM generates:** "Export DataPacks from sandbox and import to production" without addressing that DataPack JSON files may contain environment-specific Salesforce record IDs that do not exist in the target org.

**Why it happens:** DataPack export captures the full JSON representation including internal record references. LLMs treat the export as portable without noting the ID portability issue.

**Correct pattern:**

```text
Environment-specific references in DataPacks:

Problem: DataPack JSON may contain:
- Record IDs from the source org (do not exist in target)
- Named Credential references (may differ per environment)
- User IDs (source org users may not exist in target)
- Custom Metadata record names (usually portable)

Mitigation:
1. Use vlocity CLI's match key system to resolve references
   by name instead of ID
2. Review exported JSON for hardcoded 15/18-character IDs
3. Use environment-specific configuration for Named Credentials
   and endpoints
4. Test DataPack import in a staging environment before production
5. Configure org-specific values post-import
```

**Detection hint:** Flag DataPack deployment instructions that do not mention ID portability or match key resolution. Search exported JSON for `"Id": "00[0-9A-Za-z]{12,15}"` patterns.

---

## Anti-Pattern 3: Importing DataPacks Without Checking Dependency Order

**What the LLM generates:** "Import all DataPacks at once" without noting that OmniStudio components have dependencies (OmniScript references Integration Procedures, which reference DataRaptors) and must be imported in dependency order.

**Why it happens:** LLMs treat DataPack import as a single operation. The dependency chain (DataRaptors before Integration Procedures before OmniScripts before FlexCards) must be respected.

**Correct pattern:**

```text
DataPack import dependency order:

1. DataRaptors (no dependencies on other OmniStudio components)
2. Calculation Procedures and Calculation Matrices
3. Integration Procedures (may reference DataRaptors)
4. OmniScripts (reference Integration Procedures and DataRaptors)
5. FlexCards (may reference OmniScripts and Integration Procedures)

vlocity CLI handles this automatically when using packDeploy
with proper configuration, but manual imports via the UI must
follow this order.

If import fails with "missing dependency":
1. Check which component is referenced but not yet imported
2. Import the dependency first, then retry
3. Use vlocity CLI's dependency resolution for automated ordering
```

**Detection hint:** Flag manual DataPack import instructions that do not specify dependency order. Check for OmniScript imports before their referenced Integration Procedures.

---

## Anti-Pattern 4: Not Activating Components After DataPack Import

**What the LLM generates:** "Import the DataPack and the OmniScript will be available to users" without noting that imported OmniStudio components are inactive by default and must be explicitly activated.

**Why it happens:** Some deployment methods auto-activate. DataPack imports typically import components in an inactive state, requiring manual activation. LLMs assume deployment equals activation.

**Correct pattern:**

```text
Post-import activation checklist:

After DataPack import, activate in order:
1. DataRaptors: activate each imported DataRaptor
2. Integration Procedures: activate the correct version
3. Calculation Procedures: activate and verify matrix versions
4. OmniScripts: activate the imported version
5. FlexCards: activate and publish

Activation verification:
- Check that the expected version is active (not a previous version)
- Test each activated component before declaring deployment complete
- If multiple versions exist, ensure only the intended version is active

CI/CD automation:
- vlocity CLI can activate components as part of packDeploy
- Configure activation settings in the deployment job definition
- Add post-deploy smoke tests to verify activation
```

**Detection hint:** Flag DataPack deployment instructions that do not include activation steps. Check for missing post-import verification.

---

## Anti-Pattern 5: Committing DataPack JSON Files Without Review

**What the LLM generates:** "Export DataPacks and commit to Git" without reviewing the exported JSON for sensitive data, oversized payloads, or unwanted configuration from the source org.

**Why it happens:** LLMs treat DataPack export as a clean, version-controllable artifact. In practice, exported JSON can include debug settings, test data references, org-specific URLs, and large embedded resources that should not be committed.

**Correct pattern:**

```text
DataPack Git commit best practices:

1. Review before commit:
   - Check for hardcoded org-specific URLs or IDs
   - Remove debug/test configurations not intended for other environments
   - Verify that Named Credential references use portable names

2. .gitignore for DataPack artifacts:
   - Ignore backup files created by vlocity CLI
   - Ignore local cache directories
   - Keep only the canonical DataPack JSON files

3. JSON formatting:
   - Pretty-print JSON for readable diffs
   - Use consistent formatting (vlocity CLI default is fine)
   - Large embedded resources (images, documents) should be
     externalized, not embedded in JSON

4. Code review: treat DataPack changes like code changes
   - Review field mappings in DataRaptor definitions
   - Review step configurations in OmniScript/IP definitions
   - Verify version numbers match the release plan
```

**Detection hint:** Flag DataPack commits that include large JSON files (>1 MB) without review notes. Check for org-specific IDs or URLs in committed DataPack JSON.
