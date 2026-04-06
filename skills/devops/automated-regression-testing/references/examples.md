# Examples — Automated Regression Testing

## Example 1: UTAM Page Object for Custom LWC Record Form

**Context:** A team has a custom LWC component `c-opportunity-quick-create` used on their Sales Console. Every Salesforce release, manual testers spend two days clicking through this form. They want to automate regression.

**Problem:** Standard Selenium locators fail because the component renders inside Shadow DOM. The initial attempt used `By.cssSelector("input[name='Amount']")` which returned `NoSuchElementException` because the input lives inside multiple nested shadow roots (`one-record-home-flexipage` > `c-opportunity-quick-create` > `lightning-input`).

**Solution:**

```json
// utam/opportunityQuickCreate.utam.json
{
  "root": true,
  "selector": { "css": "c-opportunity-quick-create" },
  "shadow": {
    "elements": [
      {
        "name": "amountInput",
        "selector": { "css": "lightning-input[data-field='Amount']" },
        "type": "actionable"
      },
      {
        "name": "saveButton",
        "selector": { "css": "lightning-button[data-id='save']" },
        "type": "clickable"
      }
    ]
  }
}
```

```java
// Test using compiled UTAM page object
OpportunityQuickCreate form = utam.load(OpportunityQuickCreate.class);
form.getAmountInput().setText("50000");
form.getSaveButton().click();

// Assert toast message appears
ToastMessage toast = utam.load(ToastMessage.class);
assertThat(toast.getMessage()).contains("was created");
```

**Why it works:** UTAM compiles the JSON descriptor into a class that automatically traverses the shadow root chain. When Salesforce restructures the internal DOM in a future release, you update the JSON descriptor — not every test method. The 727+ pre-built Salesforce page objects handle standard components (`lightning-input`, `lightning-button`, etc.) out of the box.

---

## Example 2: Pre-Release Regression Pipeline with GitHub Actions

**Context:** A financial services company runs a Salesforce org with 200+ custom LWC components. They were caught off-guard by a Summer '25 release change that broke their approval flow UI. They need a systematic pre-release regression process.

**Problem:** Without a pre-release testing window, the team discovered the break on GA weekend when production upgraded. The fix required an emergency deployment on Monday morning, impacting 400 users.

**Solution:**

```yaml
# .github/workflows/prerelease-regression.yml
name: Pre-Release Regression Suite
on:
  schedule:
    # Run nightly during pre-release window (adjust dates per release)
    - cron: '0 2 * * *'  # 2 AM UTC
  workflow_dispatch:
    inputs:
      target_org:
        description: 'Pre-release sandbox alias'
        default: 'prerelease-sandbox'

jobs:
  regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Salesforce CLI
        run: npm install -g @salesforce/cli

      - name: Authenticate to pre-release sandbox
        run: |
          echo "${{ secrets.SFDX_AUTH_URL_PRERELEASE }}" > auth.txt
          sf org login sfdx-url --sfdx-url-file auth.txt --alias prerelease
          rm auth.txt

      - name: Install dependencies
        run: npm ci

      - name: Run UTAM regression suite
        run: |
          npx wdio run wdio.conf.js \
            --baseUrl $(sf org display --target-org prerelease --json | jq -r '.result.instanceUrl') \
            --reporters junit \
            --outputDir results/

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: regression-results-${{ github.run_id }}
          path: results/

      - name: Publish JUnit results
        if: always()
        uses: mikepenz/action-junit-report@v4
        with:
          report_paths: results/*.xml
          fail_on_failure: true
```

**Why it works:** The pipeline runs nightly during the pre-release window (typically 4-5 weeks before GA). Failures surface as GitHub Actions alerts, giving the team weeks to file Salesforce Known Issues, build workarounds, or adjust components before production upgrades. The `workflow_dispatch` trigger allows ad-hoc runs when Salesforce pushes mid-cycle patches to the pre-release instance.

---

## Anti-Pattern: Hard-Coding Shadow DOM Traversal Chains

**What practitioners do:** Instead of using UTAM or a proper page object layer, they write inline JavaScript to traverse shadow roots directly in test methods:

```java
// Anti-pattern: brittle inline shadow traversal
WebElement el = (WebElement) ((JavascriptExecutor) driver).executeScript(
    "return document.querySelector('one-app-nav-bar')" +
    ".shadowRoot.querySelector('one-app-nav-bar-item-root')" +
    ".shadowRoot.querySelector('a[data-id=\"Account\"]')"
);
el.click();
```

**What goes wrong:** This chain breaks whenever Salesforce adds, removes, or renames any intermediate shadow host in the component tree — which happens regularly during major releases. The same traversal path may work in Winter '26 but fail in Spring '26 because Salesforce inserted a new wrapper component. With 50+ tests using inline chains, each release requires a manual audit of every chain.

**Correct approach:** Wrap all shadow DOM traversal in page objects (UTAM JSON or custom POM classes). When a component structure changes, update one page object file instead of every test:

```java
// Correct: page object abstracts the traversal
AppNavBar navBar = utam.load(AppNavBar.class);
navBar.clickItem("Account");
```
