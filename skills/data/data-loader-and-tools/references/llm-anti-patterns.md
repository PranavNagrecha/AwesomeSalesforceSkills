# LLM Anti-Patterns: Data Loader and Tools

Common mistakes AI assistants make when advising on Salesforce data load tools.

---

## 1. Defaulting to Data Loader for All Imports (Ignoring Data Import Wizard)

**The mistake**: Recommending Data Loader as the default tool for any data load task, regardless of record count or object type.

**Why it is wrong**: For loads under 50,000 records on supported objects (Accounts, Contacts, Leads, Cases, Campaign Members, Solutions, Person Accounts), the Data Import Wizard is the preferred tool. It is browser-based, requires no installation, provides guided field mapping, and has a lower operational surface. Data Loader introduces unnecessary setup overhead (desktop install, credential configuration, batch tuning) for use cases the Import Wizard handles well.

**Correct behavior**: Check record count and object type first. Route to Data Import Wizard for <50K supported-object loads. Only recommend Data Loader when the load exceeds 50K records, targets an unsupported object, or requires automation.

---

## 2. Treating Workbench as a Maintained Official Tool

**The mistake**: Recommending Workbench (workbench.developerforce.com) as a go-to tool for SOQL, REST exploration, or data operations without noting its sunset trajectory.

**Why it is wrong**: Salesforce has announced that Workbench is on a sunset path. Building workflows or documentation that depend on Workbench for production tasks creates operational continuity risk. Salesforce's official replacements are VS Code with Salesforce Extensions, Salesforce CLI (`sf data query`), and Code Builder.

**Correct behavior**: Mention Workbench only for ad-hoc, exploratory, non-production tasks — and always note that it is being sunset. Recommend VS Code Extensions or Salesforce CLI for any workflow that needs to survive long-term.

---

## 3. Treating Salesforce Inspector as an Official Salesforce Product

**The mistake**: Recommending "Salesforce Inspector" as if it is an official Salesforce tool, including it alongside Data Loader and the Import Wizard without qualification.

**Why it is wrong**: Salesforce Inspector and its community fork Inspector Reloaded are open-source Chrome browser extensions. They are not developed or supported by Salesforce. They are not appropriate for production data changes, bulk operations, or environments subject to security review (ISV packaging, regulated industries, orgs with strict extension policies). Presenting them as official tools misleads users about support expectations and security posture.

**Correct behavior**: Always identify Salesforce Inspector/Inspector Reloaded as open-source, community-maintained Chrome extensions. Scope their recommendation to quick, read-mostly, developer-context tasks. Explicitly state they are not official Salesforce products.

---

## 4. Not Mentioning the BulkApiHardDelete Permission for Hard Delete Operations

**The mistake**: Advising a user to perform a hard delete operation in Data Loader without noting the required permission.

**Why it is wrong**: Hard delete in Salesforce (bypassing the Recycle Bin) requires the **"Bulk API Hard Delete"** permission, which is separate from standard admin capabilities and not included in the System Administrator profile by default. Running a hard delete without this permission will fail silently or with a confusing error. More importantly, granting this permission without awareness can introduce data loss risk — hard deletes are irreversible.

**Correct behavior**: When hard delete is the requested operation, explicitly state that the Bulk API Hard Delete permission must be granted to the running user's profile or permission set before proceeding. Recommend verifying least-privilege and confirming with the data owner.

---

## 5. Recommending SOAP Batch Size Tuning for Bulk API 2.0 Jobs

**The mistake**: Advising users to tune the batch size setting in Data Loader when using Bulk API 2.0 mode.

**Why it is wrong**: Bulk API 2.0 manages batching automatically — there is no manual batch size to configure. The batch size setting in Data Loader applies only to SOAP mode (max 200 records per batch) and Bulk API v1 (up to 10,000 per batch). Telling a user to "increase your batch size" when they are in Bulk API 2.0 mode gives incorrect, inapplicable advice and may cause confusion when the setting has no effect.

**Correct behavior**: Distinguish clearly between API modes. For Bulk API 2.0 (the default for large loads in modern Data Loader versions), state that batching is automatic and no manual size configuration is needed. Reserve batch-size tuning advice for SOAP or Bulk API v1 contexts only.

---

## 6. Recommending Plaintext Credentials in process-conf.xml

**The mistake**: Providing Data Loader headless configuration examples that include plaintext usernames and passwords in `process-conf.xml` without flagging this as a security risk.

**Why it is wrong**: `process-conf.xml` files are frequently committed to version control, shared across teams, or stored on shared file systems. Plaintext credentials in these files represent a direct security and compliance failure. Data Loader provides an encryption utility (`encrypt.bat`/`encrypt.sh`) specifically to address this, and OAuth 2.0 JWT flow is the preferred approach for headless automation.

**Correct behavior**: Never show plaintext passwords in `process-conf.xml` examples. Always demonstrate the encrypted password approach or OAuth JWT configuration. Flag the security risk explicitly when discussing headless Data Loader setup.

---

## 7. Ignoring the Workbench Replacement Guidance When Recommending REST API Exploration

**The mistake**: Pointing users to Workbench as the first suggestion for exploring REST API calls or running ad-hoc SOQL without offering CLI alternatives.

**Why it is wrong**: Since Workbench is sunset-bound, new workflows built around it will need to be migrated. Salesforce CLI provides `sf data query` for ad-hoc SOQL and `sf org open` with REST Explorer equivalents. VS Code Extensions provide an integrated SOQL editor. These are the tools Salesforce is directing users toward.

**Correct behavior**: For REST exploration and ad-hoc SOQL, lead with Salesforce CLI or VS Code Extensions. Mention Workbench only as a current option with an explicit sunset caveat.
