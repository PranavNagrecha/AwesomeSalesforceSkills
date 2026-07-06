# LLM Anti-Patterns — Data Cloud Code Extensions

Common mistakes AI coding assistants make when generating or advising on Data Cloud Code
Extensions. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Reaching for Apex when the ask is "custom logic in Data Cloud"

**What the LLM generates:** an Apex batch class or trigger and instructions to "deploy it to
Data Cloud," or a claim that Apex runs inside Data 360 transform pipelines.

**Why it happens:** "custom code on Salesforce" overwhelmingly means Apex in training data;
Code Extension is new and Python-based, so the model pattern-matches to the wrong runtime.

**Correct pattern:** custom in-platform logic for Data 360 is a **Python** code extension —
a custom script (batch data transform) or a custom function (search-index chunking) — built
with the Salesforce CLI Code Extension plugin and the `salesforce-data-customcode` SDK.
Python is the only supported language today.

**Detection hint:** any `Database.Batchable`, trigger, or `@InvocableMethod` proposed as the
implementation of a Data Cloud transform or chunking requirement.

---

## Anti-Pattern 2: Inventing CLI subcommands and SDK APIs

**What the LLM generates:** plausible-looking commands like `sf data transform deploy` or
`sf datacloud code push`, and `entrypoint.py` code importing fabricated SDK classes with
invented method names.

**Why it happens:** the model has seen thousands of `sf` commands and Python SDKs and
interpolates a surface that "should" exist; the real plugin is too new and sparsely
documented in training data.

**Correct pattern:** name only the documented toolchain — Salesforce CLI **2.130.9+**, Code
Extension plugin **0.1.5+**, `salesforce-data-customcode` SDK, `sf org login web` /
`sf org display --target-org` for auth (`sf org login` alone is a command topic, not a
runnable command; the setup guide lists the environment-specific flags) — and direct the
user to the plugin-generated
scaffold and its `examples/` folder for exact SDK usage instead of writing it from memory.

**Detection hint:** any `sf` subcommand or SDK class/method name that can't be traced to the
Code Extension developer guide or the generated scaffold.

---

## Anti-Pattern 3: Treating a chunking function as a general data job

**What the LLM generates:** a "chunking function" that queries DLOs/DMOs at runtime to
enrich chunks, writes results to other objects, or caches state between invocations.

**Why it happens:** the model generalizes from data-pipeline patterns where a processing
step can freely read stores and keep state.

**Correct pattern:** the function is a targeted chunking extension: it receives parsed
`SearchIndexChunkingV1DocElement` objects in a `SearchIndexChunkingV1Request`, returns
chunks in a `SearchIndexChunkingV1Response`, does **not** read DLOs/DMOs during runtime,
and must process each request independently because Data 360 can invoke it multiple times
depending on batching.

**Detection hint:** any DLO/DMO read, external lookup, or cross-invocation state inside
chunking-function logic.

---

## Anti-Pattern 4: Crossing object types in a script design

**What the LLM generates:** a batch-transform script that reads a DLO and writes a DMO
"to save a step," or writes to a standard DMO from a DMO-to-DMO transform.

**Why it happens:** generic ETL framing treats sources and targets as interchangeable
tables; the model doesn't surface Data 360's parity rule.

**Correct pattern:** scripts must read from and write to the same object type — **DLOs to
DLOs and DMOs to DMOs** — and DMO-to-DMO transforms can only write to **transform-type
DMOs**. Cross-type movement belongs in standard mappings outside the script.

**Detection hint:** a proposed script whose source is a `__dll` object and whose target is a
DMO (or vice versa), or a DMO target that isn't transform-type.

---

## Anti-Pattern 5: Recommending change sets or packages for promotion

**What the LLM generates:** "add the code extension to an outbound change set" or a
`package.xml` / unlocked-package plan to move the transform to production.

**Why it happens:** change sets and Metadata API manifests are the default promotion story
for nearly every other Salesforce artifact.

**Correct pattern:** the documented promotion mechanism is a **DevOps Data Kit**: the batch
data transform's code extension is auto-included, referenced DLOs/DMOs are added
**manually**, and deployment follows the fixed order DLOs/DMOs → code extensions → batch
data transforms, stopping on the first failed component. A change-set or package plan for
the code extension itself isn't grounded in the Code Extension developer guide.

**Detection hint:** `package.xml`, "change set," or package-install steps proposed as the
promotion vehicle for the code extension or its batch transform.

---

## Anti-Pattern 6: Overstating maturity, languages, or org support

**What the LLM generates:** "Code Extension is GA," "also supports Java/Node," "works in
any edition," or silence about BYOK, Feature Manager, and the permission gate.

**Why it happens:** models fill in maturity labels and availability from the shape of
similar features rather than the actual docs.

**Correct pattern:** the Code Extension developer guide attaches **no GA/Beta/Pilot label** — don't assert one. State
the real gates: Developer/Enterprise/Performance/Unlimited editions, Feature Manager
enablement, **not supported with BYOK**, Data Cloud Architect permission set to run/monitor/
migrate, Python-only today with more languages and Data 360 surfaces planned but not shipped.

**Detection hint:** "generally available," "beta," a non-Python language, or an availability
claim with no accompanying BYOK/edition/permission caveat.

---

## Anti-Pattern 7: Editing the Dockerfile or loosening the version pins

**What the LLM generates:** Dockerfile tweaks ("bump the base image," "add an apt package")
or advice that "any Python 3.x works."

**Why it happens:** customizing Dockerfiles is normal in generic container workflows, and
version pins look like suggestions.

**Correct pattern:** the scaffold's `Dockerfile` is used for containerized builds and
deployments — **don't modify it**. Add runtime pip dependencies to `requirements.txt`
(dev-only ones to `requirements-dev.txt`), and develop on **Python 3.11** specifically with
Azul Zulu OpenJDK 17.x and Docker Desktop.

**Detection hint:** any diff touching `Dockerfile`, or setup instructions naming a Python
version other than 3.11.
