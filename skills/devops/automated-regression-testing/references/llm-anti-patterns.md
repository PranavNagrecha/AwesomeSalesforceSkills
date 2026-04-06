# LLM Anti-Patterns — Automated Regression Testing

Common mistakes AI coding assistants make when generating or advising on Automated Regression Testing.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Standard CSS Selectors Without Shadow DOM Awareness

**What the LLM generates:**

```java
driver.findElement(By.cssSelector("lightning-input[name='Amount'] input")).sendKeys("50000");
```

**Why it happens:** LLMs are trained heavily on standard web testing examples where `document.querySelector` traverses the full DOM. Salesforce LWC Shadow DOM boundaries are domain-specific knowledge that generic training data does not emphasize. The model defaults to standard Selenium patterns that work on non-Salesforce web apps.

**Correct pattern:**

```java
// Using UTAM page object that handles shadow traversal
RecordForm form = utam.load(RecordForm.class);
form.getField("Amount").setText("50000");

// Or using Selenium 4 getShadowRoot() explicitly
WebElement host = driver.findElement(By.cssSelector("lightning-input"));
SearchContext shadow = host.getShadowRoot();
WebElement input = shadow.findElement(By.cssSelector("input"));
input.sendKeys("50000");
```

**Detection hint:** Look for `By.cssSelector` or `By.xpath` targeting elements known to be inside LWC shadow roots (`lightning-input`, `lightning-button`, `lightning-combobox`, any `c-*` component). If there is no `getShadowRoot()` or UTAM page object usage, the selector will fail at runtime.

---

## Anti-Pattern 2: Suggesting `Thread.sleep()` Instead of Explicit Waits

**What the LLM generates:**

```java
driver.findElement(By.id("save-button")).click();
Thread.sleep(5000); // Wait for save to complete
driver.findElement(By.cssSelector(".toastMessage"));
```

**Why it happens:** LLMs generate `Thread.sleep` as a simple, universally applicable solution. It appears in many training examples and "works" locally. The model does not account for Salesforce Lightning's asynchronous rendering pipeline where load times vary by 2-15 seconds depending on org complexity, network latency, and component count.

**Correct pattern:**

```java
driver.findElement(By.id("save-button")).click();
WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(15));
wait.until(ExpectedConditions.visibilityOfElementLocated(
    By.cssSelector("div.toastMessage")
));
```

**Detection hint:** Search for `Thread.sleep`, `time.sleep`, or `setTimeout` used between UI actions. In Salesforce Lightning, fixed delays are always wrong — the same page can load in 1 second or 12 seconds depending on org state.

---

## Anti-Pattern 3: Generating XPath Locators for Lightning Components

**What the LLM generates:**

```java
driver.findElement(By.xpath("//div[@class='slds-form-element']//input[@name='Name']"));
```

**Why it happens:** XPath is heavily represented in Selenium training data and is the traditional "power user" locator strategy. LLMs default to it when CSS selectors seem insufficient. However, XPath cannot cross Shadow DOM boundaries at all — `//` traversal stops at each shadow root, making XPath fundamentally incompatible with LWC testing.

**Correct pattern:**

```java
// XPath does not work across shadow boundaries. Use UTAM or getShadowRoot():
RecordForm form = utam.load(RecordForm.class);
form.getField("Name").setText("Acme Corp");
```

**Detection hint:** Any `By.xpath()` targeting elements inside Lightning components. XPath works for Visualforce pages and for elements outside shadow roots (e.g., the Lightning app shell), but never for elements inside LWC or Aura component shadow trees.

---

## Anti-Pattern 4: Recommending Selenium IDE Record-and-Playback for Salesforce

**What the LLM generates:** "Use Selenium IDE to record your test scenario in the browser, then export it as a test script. This captures all the clicks and inputs automatically."

**Why it happens:** Selenium IDE is the most commonly referenced entry point for test automation in generic web testing content. LLMs recommend it as the simplest path. They do not account for Salesforce-specific problems: recorded selectors include auto-generated IDs that change between sessions, shadow DOM traversal is not captured, and Lightning's client-side routing means URL-based navigation recorded by the IDE may not reproduce.

**Correct pattern:**

"For Salesforce Lightning, do not use Selenium IDE recording. Instead:
1. Build UTAM page objects for each screen in your test flow.
2. Write test methods that call page object methods.
3. Use the UTAM compiler to generate typed Java/JS classes from JSON descriptors.
Recording-based approaches produce unmaintainable tests within one Salesforce release cycle."

**Detection hint:** Mentions of "Selenium IDE", "record and playback", "record your test", or "export recorded test" in the context of Salesforce Lightning testing.

---

## Anti-Pattern 5: Hard-Coding Org URLs and Instance Identifiers

**What the LLM generates:**

```yaml
env:
  SALESFORCE_URL: "https://mycompany--uat.sandbox.my.salesforce.com"
  LOGIN_URL: "https://test.salesforce.com"
```

**Why it happens:** Training data contains many examples of hard-coded base URLs for web testing. LLMs do not know that Salesforce sandbox instances can change after refresh (the `cs45` or `cs78` portion changes), that My Domain URLs can be modified by admins, and that pre-release sandboxes use different instance pools.

**Correct pattern:**

```yaml
env:
  SALESFORCE_ORG_ALIAS: "uat-sandbox"
# Resolve URL dynamically at runtime:
# sf org display --target-org $SALESFORCE_ORG_ALIAS --json | jq -r '.result.instanceUrl'
```

**Detection hint:** Look for hard-coded Salesforce URLs containing instance identifiers (`cs`, `na`, `eu` prefixes), `.sandbox.my.salesforce.com` domains, or `test.salesforce.com` in CI configuration. The org alias plus `sf org display` should be the URL source.

---

## Anti-Pattern 6: Ignoring Test Data Setup and Teardown

**What the LLM generates:**

```java
@Test
public void testOpportunityApproval() {
    // Navigate to an existing opportunity
    driver.get(baseUrl + "/lightning/r/Opportunity/006xxx.../view");
    // ... test the approval flow
}
```

**Why it happens:** LLMs generate tests that assume existing data because most training examples for UI testing navigate to known URLs or use hard-coded record IDs. The model does not account for Salesforce test data isolation requirements: sandboxes are refreshed, scratch orgs are ephemeral, and record IDs are org-specific.

**Correct pattern:**

```java
@BeforeEach
public void setupTestData() {
    // Create test data via API before UI test
    RestAssured.given()
        .header("Authorization", "Bearer " + accessToken)
        .body("{\"Name\": \"Test Opp\", \"StageName\": \"Prospecting\", ...}")
        .post(baseUrl + "/services/data/v60.0/sobjects/Opportunity");
    // Store the returned ID for navigation
}

@Test
public void testOpportunityApproval() {
    driver.get(baseUrl + "/lightning/r/Opportunity/" + testOppId + "/view");
    // ... test the approval flow
}

@AfterEach
public void teardown() {
    // Delete test records via API
}
```

**Detection hint:** Tests that navigate to hard-coded record IDs (`/006...`, `/001...`) or assume specific records exist. Also look for tests with no `@Before`/`@BeforeEach` data setup method.
