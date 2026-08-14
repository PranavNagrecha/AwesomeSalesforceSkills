# LLM Anti-Patterns — Visualforce Security And Modernization

Common mistakes AI coding assistants make when generating or advising on Visualforce hardening and modernization. Avoid these in generated output.

---

## Anti-Pattern 1: Suggesting view state shrink without measuring first

**What the LLM generates:** "Your view state is too large; mark these 14 controller properties as `transient` and the page will work."

**Why it happens:** LLMs treat the 170 KB limit as a fixed input and `transient` as a one-size-fits-all fix. They skip the measurement step because they cannot run the View State Inspector.

**Correct pattern:**

```
1. Open the page in Developer Console with View State Inspector enabled.
2. Identify the actual top-N largest properties — the contribution is rarely
   what the developer expects (often it's a single SelectOption list or an
   unbounded SOQL result).
3. Mark only those `transient` (or remove from the controller entirely if
   the data is fetchable on demand).
4. Re-measure. If the page still hits the ceiling, the structural fix is
   moving to JS Remoting, not more `transient` keywords.
```

**Detection hint:** Generated suggestions that mark > 5 properties `transient` without referencing the View State Inspector or any measurement step.

---

## Anti-Pattern 2: Missing FLS enforcement on custom-controller getters that return sObjects

**What the LLM generates:**

```apex
public Employee__c getEmployee() {
    return [
        SELECT Id, Name, Salary__c
        FROM Employee__c
        WHERE Id = :empId
    ];
}
```

**Why it happens:** LLMs default to "the simplest SOQL that returns the record" and treat `with sharing` on the surrounding class as sufficient security. Training data contains many examples of pre-Summer-'23 code that did not have `WITH USER_MODE` available, and the syntax has not propagated.

**Correct pattern:**

```apex
public Employee__c getEmployee() {
    return [
        SELECT Id, Name, Salary__c
        FROM Employee__c
        WHERE Id = :empId
        WITH USER_MODE
        LIMIT 1
    ];
}
```

**Detection hint:** Any SOQL inside a Visualforce custom-controller class that lacks `WITH USER_MODE` or `WITH SECURITY_ENFORCED`. The bundled checker script regexes for this. Resolve the hit against the `apiVersion` in the class's `.cls-meta.xml` before calling it a leak: at 67.0+ (Summer '26) database operations default to user mode, so a *bare* query is already FLS-enforced and the finding is legibility, not exposure. A query carrying `WITH SYSTEM_MODE` is the opposite case — it opts out at every version, so it stays a real exposure finding. See [`agents/_shared/AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md) § *Apex security idiom by API version*.

---

## Anti-Pattern 3: Assuming `with sharing` covers FLS

**What the LLM generates:** "I added `with sharing` to the controller class, so the page is now FLS-secure."

**Why it happens:** LLMs conflate three distinct security layers — sharing (records), CRUD (objects), FLS (fields) — into one `with sharing` keyword. The semantic distinction is documented but rarely highlighted in training data; many tutorials over-state what `with sharing` does.

**Correct pattern:** Always pair `with sharing` with explicit FLS/CRUD enforcement. The cleanest way is `WITH USER_MODE` on every SOQL query and `Database.insert(records, AccessLevel.USER_MODE)` for DML. State the layered model in the explanation: "`with sharing` enforces record-level visibility; `WITH USER_MODE` enforces field- and object-level access."

**Detection hint:** Any explanation that says "FLS is enforced because the class is `with sharing`" — that is structurally wrong.

---

## Anti-Pattern 4: "Fixing" CSRF errors by disabling the protection

**What the LLM generates:**

```html
<apex:page csrfProtection="false" ...>
```

with the explanation "this fixes the CSRF token mismatch error."

**Why it happens:** The error messages are confusing ("CSRF token mismatch" sounds like the protection is broken), and disabling the attribute is the most direct path to making the symptom go away. LLMs optimize for "make the error stop."

**Correct pattern:** Diagnose why the legitimate request is not carrying a token. Almost always it is a third-party integration that should be using REST instead, or a flow that should load the form via GET first to acquire the token. The remediation is at the integration boundary, not the platform's CSRF setting. If you must keep the integration on Visualforce, document why and have a security architect review the disablement.

**Detection hint:** Any generated `<apex:page ... csrfProtection="false" ...>` that does not include a security-justification comment immediately above it. The bundled checker flags every `csrfProtection="false"` for review.

---

## Anti-Pattern 5: Recommending mass migration of all VF pages to LWC

**What the LLM generates:** "Visualforce is the legacy framework. Migrate all 80 of your pages to LWC for a modernization roadmap."

**Why it happens:** LLMs treat newer-is-better as a default and conflate "Visualforce is older than LWC" with "Visualforce is deprecated." Visualforce is supported and continues to receive platform fixes; there is no announced sunset.

**Correct pattern:** Per-page disposition based on real signals — security findings, LEX-broken UX, controller maintenance burden. Stable internal-only pages stay on VF. PDF generators stay on VF (LWC has no PDF rendering). External-facing pages with security gaps go first to LWC. The `rewrite-lwc` set should be a minority of the inventory, not the default.

**Detection hint:** Generated migration plans that propose rewriting more than ~30% of an inventory in one quarter, or that list every VF page as a rewrite candidate without per-page rationale.

---

## Anti-Pattern 6: Treating `<apex:outputText>` and `<apex:outputField>` as interchangeable

**What the LLM generates:**

```html
<apex:outputText value="{!account.Sensitive_Field__c}"/>
```

**Why it happens:** LLMs see both components used in similar positions in training data and treat them as equivalent display tags. The FLS distinction is documented but easy to miss.

**Correct pattern:**

```html
<apex:outputField value="{!account.Sensitive_Field__c}"/>
```

`<apex:outputField>` enforces FLS when bound to a standard-controller record or a USER_MODE-queried sObject; `<apex:outputText>` does not. Reserve `<apex:outputText>` for controller-computed display strings (calculated labels, formatted numbers from non-sObject sources) — never for sObject field values.

**Detection hint:** Any `<apex:outputText value="{!record.FieldName__c}"/>` where the value binding references an sObject field. Replace with `<apex:outputField>`.

---

## Anti-Pattern 7: Generating navigation code using `window.location` instead of `sforce.one`

**What the LLM generates:**

```html
<apex:commandButton onclick="window.location='/lightning/n/MyTab'; return false;"/>
```

**Why it happens:** `window.location` is the universal browser API; LLMs default to it and rarely know about the LEX-iframe origin issue. Salesforce documentation recommends `sforce.one` but it is less commonly seen in training data.

**Correct pattern:**

```html
<script>
    function openTab() {
        if (typeof sforce !== 'undefined' && sforce.one) {
            sforce.one.navigateToURL('/lightning/n/MyTab');
        } else {
            window.location = '/lightning/n/MyTab';
        }
    }
</script>
<apex:commandButton onclick="openTab(); return false;"/>
```

The `sforce.one` API survives the iframe-to-host transition in LEX; `window.location` does not. Always include the fallback for Classic and standalone VF page access.

**Detection hint:** Any generated VF page navigation code that uses `window.location` for paths starting with `/lightning/`. Flag and replace with the `sforce.one` pattern.
