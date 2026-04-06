# LLM Anti-Patterns — VS Code Salesforce Extensions

Common mistakes AI coding assistants make when generating or advising on VS Code Salesforce Extensions configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending JDK 8 for Apex Language Server

**What the LLM generates:** Instructions to install JDK 8 or set `JAVA_HOME` to a JDK 8 installation for the Salesforce extensions.

**Why it happens:** Older training data references JDK 8 as the Salesforce standard. The Apex Language Server dropped JDK 8 support and now requires JDK 11, 17, or 21 (21 recommended).

**Correct pattern:**

```json
{
  "salesforcedx-vscode-apex.java.home": "/usr/local/opt/openjdk@21"
}
```

**Detection hint:** Any mention of `jdk-8`, `jdk1.8`, `java-8`, or `openjdk@8` in a VS Code Salesforce setup context.

---

## Anti-Pattern 2: Telling Users to Set JAVA_HOME Instead of the Extension Setting

**What the LLM generates:** "Set your `JAVA_HOME` environment variable to point to your JDK installation" without mentioning `salesforcedx-vscode-apex.java.home`.

**Why it happens:** `JAVA_HOME` is the generic Java convention. LLMs default to general Java guidance rather than the extension-specific setting.

**Correct pattern:**

```json
{
  "salesforcedx-vscode-apex.java.home": "/path/to/jdk-21"
}
```

The extension-specific setting in `.vscode/settings.json` takes precedence over `JAVA_HOME` and is more reliable because it is committed to the repo and shared across the team. `JAVA_HOME` should be the fallback, not the primary recommendation.

**Detection hint:** Advice that mentions only `JAVA_HOME` or `export JAVA_HOME` without also mentioning `salesforcedx-vscode-apex.java.home`.

---

## Anti-Pattern 3: Recommending Deploy-on-Save Without Checking Org Type

**What the LLM generates:** "Enable deploy-on-save for faster development" as a universal recommendation without qualifying the org type.

**Why it happens:** Deploy-on-save is a popular productivity tip. LLMs surface it without the critical caveat that it behaves differently (and dangerously) on non-source-tracked orgs.

**Correct pattern:**

```text
Enable deploy-on-save ONLY for source-tracked orgs (scratch orgs, source-tracked sandboxes).
For non-tracked orgs (production, Developer Edition, non-tracked sandboxes),
deploy manually to avoid silently overwriting server changes.
```

**Detection hint:** Any recommendation to enable `push-or-deploy-on-save` that does not include a qualifier about org type or source tracking.

---

## Anti-Pattern 4: Suggesting sfdx Commands Instead of sf Commands

**What the LLM generates:** `sfdx force:source:push`, `sfdx force:source:deploy`, `sfdx force:auth:web:login` and other legacy `sfdx` namespace commands.

**Why it happens:** Training data is dominated by the older `sfdx` CLI. The Salesforce CLI has been unified under the `sf` namespace since 2023. While `sfdx` commands may still work as aliases, official documentation and the extensions now use `sf` commands.

**Correct pattern:**

```bash
# Correct
sf project deploy start
sf org login web
sf apex run test

# Incorrect / legacy
sfdx force:source:deploy
sfdx auth:web:login
sfdx force:apex:test:run
```

**Detection hint:** Any command starting with `sfdx force:` or `sfdx auth:`.

---

## Anti-Pattern 5: Conflating Interactive and Replay Debugger Requirements

**What the LLM generates:** "To debug Apex in VS Code, set breakpoints and press F5" without distinguishing between the two debugger types or their prerequisites.

**Why it happens:** LLMs treat Apex debugging as a single feature. In reality, the Interactive Debugger requires a paid license and locks the org, while the Replay Debugger is free but requires a debug log file.

**Correct pattern:**

```text
Two Apex debugger options exist:

1. Interactive Debugger — requires the Apex Interactive Debugger license.
   Sets real-time breakpoints. Locks the entire org during the session.
   Use only on personal scratch orgs.

2. Replay Debugger — no license required.
   Replays a captured debug log. Does not lock the org.
   Use on shared sandboxes and when no debugger license is available.
```

**Detection hint:** Debugging instructions that do not mention "Interactive" vs "Replay" or do not mention the license requirement.

---

## Anti-Pattern 6: Hallucinating Extension Settings Names

**What the LLM generates:** Settings like `salesforcedx.deploy.onSave`, `sfdx.pushOnSave`, `apex.java.home`, or other invented setting keys that do not exist in the extension.

**Why it happens:** LLMs interpolate plausible VS Code setting names from partial patterns in training data rather than looking up the actual setting identifiers.

**Correct pattern:**

```json
{
  "salesforcedx-vscode-core.push-or-deploy-on-save.enabled": true,
  "salesforcedx-vscode-apex.java.home": "/path/to/jdk"
}
```

**Detection hint:** Any `salesforcedx` or `sfdx` settings key that does not match the documented extension settings. Common hallucinations include missing hyphens, wrong nesting, or shortened prefixes.
