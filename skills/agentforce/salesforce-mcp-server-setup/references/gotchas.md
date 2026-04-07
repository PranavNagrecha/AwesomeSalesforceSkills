# Gotchas — Salesforce MCP Server Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Connected App Propagation Delay

**What happens:** After enabling the OAuth 2.0 Client Credentials Flow on a Connected App (or changing the run-as user), the change is not immediately visible to all Salesforce authorization servers. The proxy returns HTTP 401 with "invalid_client" during this window even though the configuration looks correct in Setup.

**When it occurs:** Immediately after creating or modifying a Connected App. The delay can be up to 10 minutes.

**How to avoid:** Wait at least 10 minutes after any Connected App change before testing the proxy. Do not assume a 401 immediately after setup is a credentials error — it may just be propagation lag.

---

## Gotcha 2: Apex Stateless Execution — No Cross-Request State

**What happens:** The `McpServer` instance and all registered tool objects are constructed fresh on every HTTP POST. Any data written to instance variables or static variables in the tool class during one request will not be present in the next request.

**When it occurs:** Any time a practitioner tries to implement a "session" or "context accumulation" pattern across multiple MCP tool calls.

**How to avoid:** Design tools to be fully stateless. Pass all required context in the tool's `params` map. Store conversation state in Salesforce records (e.g., a custom object) or in the MCP client's context — not in Apex variables.

---

## Gotcha 3: Sharing Context of the Run-As User

**What happens:** SOQL queries inside Apex tool classes run in the sharing context of the Connected App's run-as user. If the run-as user is a restricted service account, SOQL may return empty result sets even though records exist. There is no Apex exception — the query silently returns zero rows.

**When it occurs:** When the run-as user's profile or sharing rules restrict record visibility.

**How to avoid:** Either grant the run-as user appropriate sharing access for the records the tools need, or explicitly annotate the tool class with `without sharing` if business requirements allow it. Document the sharing decision in code comments.

---

## Gotcha 4: `--endpoint` Must Match the Apex `urlMapping` Exactly

**What happens:** The npm proxy constructs the full URL as `{instance-url}/services/apexrest{endpoint}`. If the `--endpoint` value does not match the Apex `@RestResource(urlMapping=...)` value exactly (including leading slash, case sensitivity), the proxy gets a 404 and no tools are registered in the MCP client.

**When it occurs:** When the endpoint path is configured as `/mcp/v1` in the Apex class but `/services/apexrest/mcp/v1` is passed as the `--endpoint` flag (doubling the prefix), or vice versa.

**How to avoid:** Always use only the path after `/services/apexrest` as the `--endpoint` value. Example: if the class has `urlMapping='/mcp/v1'`, set `--endpoint /services/apexrest/mcp/v1`. The proxy prepends `/services/apexrest` automatically — do NOT include it again.

---

## Gotcha 5: `npx` Caches Old Package Versions

**What happens:** `npx salesforce-mcp-lib` uses a cached version of the package if one exists in the npm cache. After a new version is released that fixes a bug or adds new MCP protocol methods, the proxy continues running the old version until the cache is cleared.

**When it occurs:** When `npx` was previously used to run the package and the cache has not expired.

**How to avoid:** Use `npx -y --prefer-online salesforce-mcp-lib` in the MCP client config, or pin to a specific version with `npx salesforce-mcp-lib@x.y.z`. After a package update, run `npx --yes salesforce-mcp-lib@latest` once to force a cache refresh.
