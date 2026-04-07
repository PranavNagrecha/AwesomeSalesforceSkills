# LLM Anti-Patterns — Salesforce MCP Server Setup

Common mistakes AI coding assistants make when generating or advising on Salesforce MCP Server Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Salesforce Hosted MCP with salesforce-mcp-lib

**What the LLM generates:** Instructions to enable a Salesforce platform feature in Setup > Agents > MCP Servers, as if salesforce-mcp-lib is a native Salesforce product.

**Why it happens:** LLMs conflate the open-source community library (salesforce-mcp-lib, MIT) with the separate Salesforce Hosted MCP Server beta feature (a first-party Salesforce product for specific clouds). Both use "Salesforce" and "MCP" in their names and were introduced around the same time period.

**Correct pattern:**

```
salesforce-mcp-lib is a developer-installed open-source package.
Setup steps:
1. sf package install --package 04tdL000000So9xQAC --target-org YOUR_ORG
2. Write an Apex REST endpoint class
3. Run the npm proxy: npx salesforce-mcp-lib --instance-url ... --client-id ... --client-secret ... --endpoint ...
There is no Salesforce Setup UI wizard for this library.
```

**Detection hint:** Look for references to "Setup > Agents" or "Salesforce Setup wizard" in the MCP setup instructions. salesforce-mcp-lib has no Setup UI.

---

## Anti-Pattern 2: Passing the Full REST Path as `--endpoint`

**What the LLM generates:** `--endpoint /services/apexrest/mcp/v1` when the Apex class has `urlMapping='/mcp/v1'`.

**Why it happens:** LLMs see the full Salesforce REST URL pattern (`/services/apexrest/...`) in documentation and assume the `--endpoint` flag should match the full URL path. But the npm proxy prepends `/services/apexrest` automatically.

**Correct pattern:**

```bash
# Apex class: @RestResource(urlMapping='/mcp/v1')
# Correct proxy flag:
--endpoint /services/apexrest/mcp/v1

# This produces the full URL:
# https://your-org.my.salesforce.com/services/apexrest/mcp/v1
```

Wait — the proxy does NOT prepend `/services/apexrest`. The `--endpoint` value is appended directly to the instance URL. So the correct value IS `/services/apexrest/mcp/v1`. The anti-pattern is passing just `/mcp/v1` and expecting the proxy to fill in the rest.

**Detection hint:** If `--endpoint` does not start with `/services/apexrest/`, the proxy will construct a URL that returns 404.

---

## Anti-Pattern 3: Treating Apex Static Variables as Session State

**What the LLM generates:** Tool implementations that store state between calls using `static Map<String, Object> sessionState = new Map<String, Object>();` or similar patterns.

**Why it happens:** LLMs trained on server-side frameworks assume that a running server process maintains state between requests. In Salesforce Apex REST, each HTTP request is a fresh Apex execution context. Static variables are NOT shared across requests.

**Correct pattern:**

```apex
global class MyTool extends McpToolDefinition {
    // WRONG: static state does not persist across MCP calls
    // private static Map<String, Object> cache = new Map<String, Object>();

    global override Object execute(Map<String, Object> params) {
        // All context must come from params or be queried fresh each time
        String recordId = (String) params.get('recordId');
        return [SELECT Id, Name FROM Account WHERE Id = :recordId LIMIT 1];
    }
}
```

**Detection hint:** Any `static` field in an `McpToolDefinition` subclass that is written to in `execute()` is almost certainly an error.

---

## Anti-Pattern 4: Using Named User Authentication Instead of Client Credentials

**What the LLM generates:** Instructions to use the OAuth 2.0 Username-Password Flow or JWT Bearer Flow to authenticate the npm proxy, including username and password fields in the configuration.

**Why it happens:** Username-Password flow is the most commonly documented "headless" Salesforce OAuth pattern in training data. LLMs default to it when they see "no browser login."

**Correct pattern:**

```
salesforce-mcp-lib uses OAuth 2.0 Client Credentials Flow exclusively.
Required Connected App settings:
- Enable OAuth Settings: true
- Enable Client Credentials Flow: true
- Run As: a named service account user
Required proxy flags: --client-id and --client-secret only.
No username, no password, no certificate.
```

**Detection hint:** Any mention of `username`, `password`, `security_token`, or `grant_type=password` in the proxy configuration is the wrong OAuth flow.

---

## Anti-Pattern 5: Omitting Global Access Modifier on Tool Classes

**What the LLM generates:** `public class MyTool extends McpToolDefinition` instead of `global class MyTool extends McpToolDefinition`.

**Why it happens:** LLMs default to `public` for Apex classes because it is the correct modifier for most org code. But salesforce-mcp-lib is a 2GP managed package; extending its abstract classes from subscriber org code requires `global` access modifier when the extended class needs to be callable by the package.

**Correct pattern:**

```apex
// WRONG
public class MyRecordLookupTool extends McpToolDefinition { ... }

// CORRECT
global class MyRecordLookupTool extends McpToolDefinition {
    global override Map<String, Object> inputSchema() { ... }
    global override String validate(Map<String, Object> params) { ... }
    global override Object execute(Map<String, Object> params) { ... }
}
```

**Detection hint:** If the Apex class or its overriding methods use `public` instead of `global`, the code will fail to compile when the parent is from a managed package that exposes `global` abstract methods.

---

## Anti-Pattern 6: Installing the Package into Production Before Sandbox Testing

**What the LLM generates:** `sf package install --package 04tdL000000So9xQAC --target-org production` as the first install command.

**Why it happens:** Instructions are sometimes simplified to show production as the target. LLMs reproduce this without the sandbox-first caveat.

**Correct pattern:**

```
Always install to a sandbox first:
sf package install --package 04tdL000000So9xQAC --target-org my-sandbox --wait 10
Test fully in sandbox, then promote to production using your standard deployment pipeline.
Package ID 04tdL000000So9xQAC is the Apex component. Verify the ID against
the GitHub release page (https://github.com/Damecek/salesforce-mcp-lib/releases)
before any production install — package IDs are version-specific.
```

**Detection hint:** Any instructions that go directly to production package installation without a sandbox step should be flagged.
