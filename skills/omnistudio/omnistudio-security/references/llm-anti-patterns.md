# LLM Anti-Patterns — OmniStudio Security

Common mistakes AI coding assistants make when generating or advising on OmniStudio security.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming DataRaptors Enforce CRUD and FLS Automatically

**What the LLM generates:** "DataRaptors respect the running user's permissions" without noting that DataRaptors run in system mode by default and do NOT enforce CRUD/FLS checks unless explicitly configured.

**Why it happens:** LLMs assume Salesforce components respect user permissions by default (which is true for standard UI but not for OmniStudio DataRaptors). This is a critical security gap for guest-facing or portal-facing OmniScripts.

**Correct pattern:**

```text
DataRaptor security behavior:

DEFAULT: DataRaptors run in SYSTEM MODE
- All fields are accessible regardless of user FLS
- All objects are queryable regardless of user CRUD
- This is DANGEROUS for guest user and portal user contexts
- CURRENCY: Salesforce began enabling EnforceDMFLSAndDataEncryption
  by default in the week of 2 February 2026. Where it is on, Data
  Mappers run in user context instead. Read the org's current value;
  do not assume either state.

Enforcement options:
1. OmniStudio security settings (use the real names):
   - Per Data Mapper: select "Check Field Level Security" on the
     Data Mapper's Options tab
   - Org-wide: an Omni Interaction Configuration entry named
     EnforceDMFLSAndDataEncryption with value "true" - Salesforce
     enables this by default from the week of 2 February 2026, so
     read the current value before creating a new entry
   - There is no setting called "Respect User CRUD/FLS"; that name
     sends admins hunting for a checkbox that does not exist

2. Per-DataRaptor configuration:
   - Check "Run with Sharing" if available in your version
   - Note: availability varies by OmniStudio version

3. Integration Procedure level:
   - Use Apex Remote Actions with User Mode enforcement
   - Replace DataRaptors with custom Apex that enforces FLS

For guest-facing or external-facing OmniScripts:
ALWAYS verify that CRUD/FLS enforcement is active.
```

**What Summer '26 did not change:** the DataRaptor default above is OmniStudio runtime behaviour and is unaffected by the API 67.0 Apex change, where SOQL/SOSL/DML default to user mode and a class with no sharing keyword runs `with sharing`. That change is gated on the `apiVersion` in a class's `.cls-meta.xml`, and a DataRaptor has none — raising a helper class's `apiVersion` buys a DataRaptor nothing. Verify the OmniStudio setting itself. Canonical table: [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version*.

**Detection hint:** Flag OmniStudio implementations exposed to guest or external users without CRUD/FLS enforcement verification. Check for Data Mappers with "Check Field Level Security" left clear, and read the current value of `EnforceDMFLSAndDataEncryption` in Omni Interaction Configuration — since the week of 2 February 2026 Salesforce enables it by default, so a missing record is not evidence that enforcement is off.

---

## Anti-Pattern 2: Exposing Sensitive Data in OmniScript Data JSON

**What the LLM generates:** OmniScript designs that prefill sensitive data (SSN, credit card numbers, salary) into the OmniScript data JSON for display or processing, making it visible in the browser's developer console.

**Why it happens:** LLMs design for functionality — if a field is needed, it is loaded into the data JSON. The fact that the entire OmniScript data structure is accessible in the browser's JavaScript console is a security concern not commonly discussed.

**Correct pattern:**

```text
Sensitive data in OmniScript:

Problem: the OmniScript data JSON is accessible in the browser
via developer tools. Any field loaded into the OmniScript is
visible to the user, even if it is not displayed on the page.

Mitigation:
1. Do NOT prefill sensitive fields (SSN, credit card, passwords)
   into the OmniScript data JSON
2. For display: use masked values (***-**-1234) computed server-side
   in the Integration Procedure
3. For processing: keep sensitive data in the Integration Procedure
   (server-side) and never pass it to the OmniScript (client-side)
4. For input: collect sensitive data and immediately send to the
   server via an Integration Procedure — do not store in OmniScript state

Shield Platform Encryption does NOT help here — encrypted fields
are decrypted before reaching the OmniScript data JSON.
```

**Detection hint:** Flag OmniScript prefill configurations that load SSN, credit card, salary, or other PII fields into the client-side data structure. Check for sensitive field API names in DataRaptor Extract mappings connected to OmniScripts.

---

## Anti-Pattern 3: Not Securing HTTP Actions in Integration Procedures for Guest Users

**What the LLM generates:** Integration Procedures with HTTP Actions that call external APIs, used in guest-facing OmniScripts, without considering that a guest user could manipulate the request by modifying the OmniScript data JSON.

**Why it happens:** LLMs trust that the OmniScript UI controls the input. In reality, a technical user can modify the browser's JavaScript state to send arbitrary data to the Integration Procedure's HTTP Action.

**Correct pattern:**

```text
HTTP Action security for guest/external contexts:

Risk: guest users can manipulate OmniScript input data via
browser developer tools, potentially:
- Changing API request parameters
- Accessing data they should not see
- Triggering actions on unauthorized records

Mitigation:
1. NEVER use client-supplied record IDs for data access
   in guest contexts — derive them server-side
2. Validate ALL input parameters in the Integration Procedure
   before using them in HTTP Actions or DataRaptor operations
3. Use Named Credentials with Named Principal (not Per User)
   for guest user callouts
4. Apply rate limiting or throttling for guest-accessible IPs
5. Log all guest-initiated Integration Procedure executions
6. Never expose internal API keys or endpoints in OmniScript data
```

**Detection hint:** Flag guest-facing OmniScripts that pass client-supplied record IDs to Integration Procedures without server-side validation. Check for HTTP Actions in guest-accessible IPs.

---

## Anti-Pattern 4: Granting OmniStudio Permissions Too Broadly

**What the LLM generates:** "Assign the OmniStudio Admin permission set to all users who need to use OmniScripts" when most users only need the OmniStudio User or Runtime permission set.

**Why it happens:** Admin permission sets resolve all access issues immediately. LLMs default to the broadest permission for simplicity.

**Correct pattern:**

```text
OmniStudio permission set assignment:

OmniStudio Admin:
- Full access: create, edit, delete, activate OmniStudio components
- Assign to: developers, admin configurators ONLY
- Never assign to: end users, guest users, portal users

OmniStudio User / Runtime:
- Read and execute OmniStudio components
- Cannot create, edit, or delete components
- Assign to: business users who interact with OmniScripts

Guest User:
- Minimal permissions: execute specific OmniScripts only
- Verify each permission individually
- Lock down Apex class access to only required classes

Principle of least privilege:
- Start with the minimum permission set
- Add permissions only as needed
- Review permission assignments quarterly
```

**What the permission sets do not cover:** on the standard runtime — that is, once **Managed Package Runtime** is disabled in Omnistudio Settings — assigning the right permission set is necessary but not sufficient. Field-level security must also be explicitly set for Omni Process Compilation (Read, Edit), Omni Data Transformation (Read), and Omniscript Saved Sessions (Read, Edit) on every profile that runs Omnistudio components. Missing them surfaces as a blank FlexCard, an Omniscript that will not load, or an LWC compilation error rather than an access error, so the model reaches for cache-clearing and component rewrites instead of field permissions. See `references/gotchas.md` §5.

**Detection hint:** Flag OmniStudio Admin permission set assignments to non-admin users. Check for guest users with OmniStudio Admin or User permissions. On standard-runtime orgs, check the three object grants above before accepting "the component is broken."

---

## Anti-Pattern 5: Not Reviewing Custom LWC Elements for Security in OmniScript Context

**What the LLM generates:** "Add a custom LWC element to the OmniScript for the file upload" without noting that custom LWC elements in OmniScripts must be reviewed for the same security concerns as standalone LWC components — XSS, CRUD/FLS enforcement, and input validation.

**Why it happens:** Custom LWC elements are treated as UI components. LLMs do not apply security review practices to OmniScript-embedded LWCs because they are seen as "inside" the OmniStudio framework.

**Correct pattern:**

```text
Custom LWC security review in OmniScript context:

1. @AuraEnabled methods called by the LWC:
   - Must enforce CRUD/FLS. Read the apiVersion in the class's
     .cls-meta.xml, not the org's release: at 67.0+ SOQL/SOSL/DML
     already default to user mode; at 66.0 and below they run in
     system mode until WITH USER_MODE (57.0+) says otherwise
   - On writes assembled from OmniScript input, prefer
     Security.stripInaccessible(AccessType.CREATABLE, records)
     on an insert - AccessType.UPDATABLE on an update - and DML
     the .getRecords() result; user mode throws and fails the
     whole DML instead
   - Must validate input parameters (not trust OmniScript data)
   - Must handle errors gracefully (not expose stack traces)

2. Client-side rendering:
   - Sanitize any data displayed from the OmniScript data JSON
   - Do not use innerHTML or lwc:dom="manual" with unsanitized data
   - Apply the same XSS prevention as any LWC

3. File uploads:
   - Validate file type and size server-side (not just client-side)
   - Scan for malware if accepting files from external users
   - Use ContentVersion with appropriate sharing settings

4. Data passed from OmniScript to LWC:
   - Treat as untrusted input (user can modify via browser console)
   - Validate in the LWC and in any Apex controller
```

**Detection hint:** Flag custom LWC elements in OmniScripts that call @AuraEnabled methods without CRUD/FLS enforcement. Check for innerHTML usage in OmniScript-embedded LWCs.

---

## Anti-Pattern 8: A `global without sharing` Callable as the OmniStudio DML helper

**What the LLM generates:** `global without sharing class QueryHelper implements Callable, omnistudio.VlocityOpenInterface` with `fetchRecords` concatenating a WHERE string from the IP map.

**Why it happens:** OmniStudio needs system-mode DML; Callable is the documented extension point.

**Correct pattern:** That class is invocable from **any** Integration Procedure, including ones a guest can reach via Aura. Do not ship a universal query helper onto a guest site. If system-mode DML is required, it is a **named, allowlisted** service with a fixed query shape — not a WHERE-string oracle — and tests must assert the guest cannot invoke it.

**Detection hint:** `implements Callable` or `VlocityOpenInterface` plus `without sharing` plus string-concatenated SOQL.

---

## Anti-Pattern 9: Trusting `%ContextId%` as the Subject

**What the LLM generates:** Remote Action Apex `Id target = (Id) input.get('ContextId');` then query that row.

**Why it happens:** Record pages pass ContextId; the designer merge field looks official.

**Correct pattern:** Resolve the subject from `UserInfo` or a server-minted session token. ContextId is a display hint. USER_MODE is not enough if the guest can already see the row.

**Detection hint:** `%ContextId%` / `{Params.contactId}` / query-string `contactId` used as an authorization key.

---

## Anti-Pattern 10: Guest Share All Active OmniProcesses, Unsigned

**What the LLM generates:** "Share OmniProcess Read to guest so the public script can run."

**Correct pattern:** Type/SubType allowlist. Enable IP signatures. FlexCard Name-share ignores IsActive. GenericInvoke is the gate.

**Detection hint:** Sharing rule `IsActive=true` on OmniProcess plus `isIntegProcdSignatureAvl=false`.
