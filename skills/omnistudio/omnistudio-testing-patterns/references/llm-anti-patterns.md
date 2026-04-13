# LLM Anti-Patterns — OmniStudio Testing Patterns

Common mistakes AI coding assistants make when generating or advising on OmniStudio testing.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Preview as Final Validation

**What the LLM generates:** "Run OmniScript Preview in the designer and verify all steps render correctly. If Preview passes, the OmniScript is ready for deployment."

**Why it happens:** LLMs draw on generic UI testing advice where a UI preview accurately reflects end-user behavior. OmniStudio Preview's fundamental limitation (admin context, no Navigation Actions) is not prominent in Salesforce's marketing documentation.

**Correct pattern:**

```
1. Run OmniScript Preview as a structural check (rendering, conditional logic, step flow).
2. ALSO deploy to a sandbox and test as the actual target user profile.
3. Explicitly test all Navigation Action steps in the deployed runtime.
4. For Experience Cloud deployments, test as a guest user or restricted community profile.
Preview is a first gate, not a sign-off gate.
```

**Detection hint:** Any response that says "Preview passes = ready for production" or omits mention of user-context testing.

---

## Anti-Pattern 2: Treating vlcStatus `warning` as Acceptable in IP Testing

**What the LLM generates:** "The Integration Procedure step returned a warning status. This is expected for non-critical steps and execution will continue normally."

**Why it happens:** LLMs pattern-match on general HTTP status code semantics (2xx = success, warnings are informational). OmniStudio's `vlcStatus: "warning"` does not guarantee correct output data — it means execution continued with potentially degraded output.

**Correct pattern:**

```
During IP testing:
- vlcStatus "success" = step completed with expected output. Verify output JSON.
- vlcStatus "warning" = step completed but output may be partial or empty. 
  Investigate errorMessage and downstream step inputs before proceeding.
- vlcStatus "error" = step failed. Stop and fix before testing downstream steps.
Never treat "warning" as a green light during testing.
```

**Detection hint:** Any response that calls `vlcStatus: "warning"` acceptable or equivalent to success during a testing context.

---

## Anti-Pattern 3: Suggesting Selenium/WebDriver Without Mentioning UTAM or Runtime Context

**What the LLM generates:** "Use Selenium WebDriver to automate OmniScript testing. Locate elements by CSS class or XPath."

**Why it happens:** Selenium/WebDriver is the most widely documented browser automation approach. LLMs apply generic web automation patterns without knowing OmniStudio's managed-package vs. standard-runtime HTML structure differences.

**Correct pattern:**

```
For OmniStudio end-to-end automation:
1. Use UTAM (UI Test Automation Model) — Salesforce's official page-object framework 
   for Lightning and OmniStudio components.
2. Confirm org runtime (Package Runtime vs. Standard/Core Runtime) before selecting 
   UTAM page objects — they differ between runtimes.
3. If raw Selenium/XPath selectors are used, document that they will break across 
   managed-package upgrades and runtime migrations.
```

**Detection hint:** Any mention of Selenium, WebDriver, XPath, or CSS selectors for OmniScript testing without mentioning UTAM or runtime type.

---

## Anti-Pattern 4: Recommending CSP or Named Credential Fixes Without Testing in IP Designer

**What the LLM generates:** "Add the external endpoint to CSP Trusted Sites and test your Integration Procedure from the OmniScript."

**Why it happens:** LLMs conflate browser-side CSP (which governs what Lightning components can load) with IP callout failures (which are server-side and governed by Named Credentials or Remote Site Settings). The correct first step is IP Test Execution, not browser-side configuration.

**Correct pattern:**

```
For Integration Procedure callout failures:
1. Open the IP designer and run the failing step in isolation using IP Test Execution.
2. Review vlcStatus and errorMessage — Named Credential issues will surface as 
   permission or authentication errors in the test response.
3. Remote Site Settings govern Apex callouts; Named Credentials govern IP callouts.
4. CSP Trusted Sites govern browser-side resource loading — NOT IP callouts.
```

**Detection hint:** Any suggestion to modify CSP Trusted Sites in response to an Integration Procedure callout error.

---

## Anti-Pattern 5: Mixing Package Runtime and Standard Runtime UTAM Page Objects

**What the LLM generates:** "Use the @salesforce/utam-jest-runner package and import the OmniScript page objects to test your scripts."

**Why it happens:** LLMs treat UTAM as a single unified library without knowing that OmniStudio Package Runtime and Standard/Core Runtime use different DOM structures requiring different page object libraries.

**Correct pattern:**

```
Before selecting UTAM page objects:
1. Check Setup > OmniStudio Settings to confirm the org runtime.
2. Package Runtime: Use the Vlocity/CMT namespace UTAM page objects 
   from the vlocity-build UTAM package.
3. Standard/Core Runtime: Use the Salesforce-native OmniStudio UTAM page objects
   from the @salesforce/utam-omnistudio-* npm packages.
4. Document the runtime type in the test suite README. Runtime migrations 
   invalidate previously working page objects without error — tests just fail to 
   locate elements.
```

**Detection hint:** Any UTAM recommendation that does not mention confirming the org runtime type before selecting the page object library.
