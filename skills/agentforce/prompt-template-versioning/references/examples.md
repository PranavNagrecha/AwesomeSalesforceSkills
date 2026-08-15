# Examples — Prompt Template Versioning

**Scope note.** This skill is about the *runtime promotion mechanics*: how the
live version changes, how fast, and what a rollback costs. The repository shape,
changelog convention, model pinning, and A/B design live in
`agentforce/agentforce-prompt-versioning`. The two skills meet at the version
number and diverge either side of it.

---

## The platform behaviour these examples are built on

Prompt Builder has **native versioning**. You can create and use multiple
versions of a prompt template to compare constructions and responses, and you
control which one users reach through activation and deactivation — with
**only one version active at a time**
([Use Multiple Versions of a Prompt
Template](https://help.salesforce.com/s/articleView?id=sf.prompt_builder_use_multiple_versions.htm&type=5),
[Activate and Deactivate Prompt
Templates](https://help.salesforce.com/s/articleView?id=sf.prompt_builder_activate_deactivate_templates.htm&type=5)).

The metadata reflects this directly. `GenAiPromptTemplate` (directory
`genAiPromptTemplates`, suffix `.genAiPromptTemplate`, minimum API version 60.0)
carries:

| Field | Type | What it does here |
|---|---|---|
| `activeVersionIdentifier` | string | Points at the version currently serving |
| `templateVersions` | `GenAiPromptTemplateVersion[]` | Every retained version, in one file |
| `masterLabel`, `type` | string | Required |
| `visibility` | enum | API or Global |

and each `GenAiPromptTemplateVersion` carries `content`, `versionNumber`,
`versionIdentifier`, `status` (`Published` or `Draft`), `primaryModel`, `inputs`,
`outputSchema`, `responseFormat` (HTML, JSON, or MarkDown), `isCitationEnabled`,
and `templateDataProviders`
([GenAiPromptTemplate](https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiprompttemplate.htm)).

**So the naive question — "how do I keep a history?" — is already answered by the
platform.** The real questions are the ones below: how do you promote without a
deploy, how do you run two variants at once when only one can be active, and how
do you make a rollback take seconds rather than a change window.

---

## Example 1 — WRONG vs RIGHT: what "promotion" costs

### WRONG — the assumption that there is no history, so version by name

```text
genAiPromptTemplates/
  SalesEmail_v3.genAiPromptTemplate-meta.xml
  SalesEmail_v4.genAiPromptTemplate-meta.xml    <- a whole new TEMPLATE per version
```

with Flow and Apex referencing `SalesEmail_v3` by developer name.

Three problems, and the first one is a factual mistake:

1. **The premise is wrong.** Prompt Builder retains versions natively; you do not
   need a new template per version to keep history.
2. **Every consumer is now coupled to the version number.** Promoting means
   editing every Flow and Apex class that names the template, then deploying
   them. That is a change window, an approval, and a test cycle for what is
   conceptually a one-field change.
3. **Rollback has the same cost as promotion**, which is the property you least
   want in an incident.

### RIGHT — versions inside one template, promotion by activation

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GenAiPromptTemplate xmlns="http://soap.sforce.com/2006/04/metadata">
    <masterLabel>Sales Email</masterLabel>
    <description>Drafts a follow-up email for an Opportunity.</description>
    <!-- `type` is required. Read the valid values for your org from an existing
         retrieved template (the metadata reference documents
         `einstein_gpt__fieldCompletion` as one example) rather than guessing —
         an invented type deploys nowhere. -->
    <type>REPLACE_WITH_A_RETRIEVED_TEMPLATE_TYPE</type>
    <visibility>Global</visibility>

    <!-- The promotion decision is THIS ONE FIELD. -->
    <activeVersionIdentifier>a1b2c3d4</activeVersionIdentifier>

    <templateVersions>
        <versionNumber>3</versionNumber>
        <versionIdentifier>a1b2c3d4</versionIdentifier>
        <status>Published</status>
        <content>...v3 prompt text...</content>
        <primaryModel>...</primaryModel>
    </templateVersions>

    <templateVersions>
        <versionNumber>4</versionNumber>
        <versionIdentifier>e5f6g7h8</versionIdentifier>
        <status>Published</status>
        <content>...v4 prompt text...</content>
        <primaryModel>...</primaryModel>
    </templateVersions>
</GenAiPromptTemplate>
```

Consumers reference the **template**, never a version. Promotion is a change to
`activeVersionIdentifier`; rollback is the inverse change. Both are metadata
deploys, both are diffable in git, and neither touches a Flow or an Apex class.

```bash
# Promote v4 (after editing activeVersionIdentifier in the file).
sf project deploy start \
  --source-dir force-app/main/default/genAiPromptTemplates \
  --target-org prod

# Roll back: revert the one-line change and deploy again.
git revert <sha> && sf project deploy start --source-dir force-app/main/default/genAiPromptTemplates --target-org prod
```

**What this still costs:** a metadata deploy, with whatever validation and
approval your pipeline attaches to one. For most teams that is minutes, and it
is the right answer. Example 2 is for the teams where it is not.

---

## Example 2 — When indirection earns its keep

### Context

A regulated org where every production metadata deploy requires a two-person
approval and a 30-minute window. The prompt for a customer-facing summary needs
to be revertible in under a minute during business hours.

### Problem

Activation is a metadata deploy. If your deploy path is slow, your rollback is
slow, and the constraint is organisational rather than technical — no amount of
prompt engineering fixes it.

### Solution — one layer of indirection, resolved at invocation

```text
Prompt_Binding__mdt
  DeveloperName            SalesEmail_Live
  Target_Slot__c           'SalesEmail'          <- what consumers ask for
  Template_Api_Name__c     'Sales_Email'         <- the template
  Version_Number__c        4                     <- the intended version
  Active__c                true
  Changed_By__c            Text
  Changed_On__c            DateTime
```

```apex
/**
 * PromptResolver — the only place a prompt template name is chosen.
 *
 * Consumers ask for a SLOT ('SalesEmail'), never a template or a version.
 * Swapping what a slot resolves to is a CMDT record edit, which is a
 * Setup change rather than a deploy.
 */
public with sharing class PromptResolver {

    public class Binding {
        public String templateApiName;
        public Integer versionNumber;
    }

    public static Binding forSlot(String slot) {
        // getAll() reads Custom Metadata without consuming a SOQL query.
        for (Prompt_Binding__mdt b : Prompt_Binding__mdt.getAll().values()) {
            if (b.Target_Slot__c == slot && b.Active__c) {
                Binding out = new Binding();
                out.templateApiName = b.Template_Api_Name__c;
                out.versionNumber = Integer.valueOf(b.Version_Number__c);
                return out;
            }
        }
        throw new PromptBindingException(
            'No active binding for slot ' + slot +
            '. Check Prompt_Binding__mdt — a missing binding is a config error, ' +
            'not a runtime condition to swallow.');
    }

    public class PromptBindingException extends Exception {}
}
```

### The honest tradeoff table

| | Direct activation | CMDT indirection |
|---|---|---|
| Promotion latency | One metadata deploy | One record edit |
| Rollback latency | One metadata deploy | One record edit |
| Auditability | Git history, reviewed | CMDT record + git if deployed as metadata |
| Moving parts | Zero extra | A resolver class, an object, a failure mode |
| Who can change it | Whoever can deploy | Whoever can edit CMDT — **wider** |

**Take indirection only when the deploy path is genuinely the constraint.** It
adds a component, a permission surface, and a new way to be wrong (a binding
pointing at a version that was retired). The most common mistake in this domain
is adopting the pattern because it sounds sophisticated rather than because a
measured deploy time made it necessary.

If you do adopt it, deploy the CMDT records as metadata so the binding change is
still reviewable in git. Editing CMDT directly in production buys speed at the
cost of the audit trail you built this to have.

---

## Example 3 — Canary: the reason indirection is sometimes unavoidable

### Context

A 400-seat sales org. v4 of the follow-up email prompt tests well on goldens,
but tone is the risk and goldens do not measure tone. The team wants 10% of reps
on v4 for a week.

### Problem

**Only one version of a prompt template can be active at a time.** There is no
platform-level traffic split. Serving two versions concurrently therefore
requires two templates and a resolver that chooses between them — the platform
gives you the versions, and you supply the routing.

### Solution — two templates, deterministic bucketing, an emitted variant tag

```apex
/**
 * Canary resolution. Deterministic on user id so a rep's experience is
 * stable across a session — a rep who sees v4 in the morning must not see
 * v3 in the afternoon, or the feedback is uninterpretable.
 */
public with sharing class PromptCanary {

    private static final Integer BUCKETS = 100;

    public static String resolveTemplate(String slot, Integer canaryPercent) {
        PromptResolver.Binding stable = PromptResolver.forSlot(slot);
        PromptResolver.Binding canary = PromptResolver.forSlot(slot + '__canary');

        if (canaryPercent <= 0) return stable.templateApiName;

        Integer bucket = Math.mod(
            Math.abs(UserInfo.getUserId().hashCode()), BUCKETS);
        Boolean inCanary = bucket < canaryPercent;

        // The variant tag is what makes the canary measurable. Without it,
        // you have two populations and no way to attribute anything.
        PromptVariantAssignment__e evt = new PromptVariantAssignment__e(
            Slot__c    = slot,
            Variant__c = inCanary ? 'canary' : 'stable',
            Template__c = inCanary ? canary.templateApiName : stable.templateApiName,
            User_Id__c = UserInfo.getUserId(),
            Assigned_At__c = System.now());
        EventBus.publish(evt);

        return inCanary ? canary.templateApiName : stable.templateApiName;
    }
}
```

### The ramp, and the two rules that make it mean something

```text
Day 0   canaryPercent = 10   Watch: edit rate, send rate, rep-reported issues
Day 3   canaryPercent = 25   Only if no metric moved adversely
Day 5   canaryPercent = 50
Day 7   canaryPercent = 100  Then promote v4 to activeVersionIdentifier and
                             delete the canary binding — the indirection is
                             temporary scaffolding, not permanent architecture.

RULE 1: never start a ramp on a Friday. Allow one full working day of
        observation with the people who can act on it present.
RULE 2: the kill switch is `canaryPercent = 0`, which must be settable
        without a deploy or it is not a kill switch.
```

**Emit the variant tag before you need it.** Retrofitting attribution onto a
running canary is not possible — you cannot recover which template served a
conversation that has already ended. The tag is the first thing to build and the
thing teams most often add after the canary has already run inconclusively.

---

## Example 4 — What actually breaks when you promote

A promotion is not only a text change. Three things in the version envelope can
differ between v3 and v4, and each has a distinct failure signature.

### Input contract

`GenAiPromptTemplateVersion.inputs` is a list of `GenAiPromptTemplateInput`, each
with `apiName`, `definition`, `description`, `masterLabel`, `referenceName`, and
`required`. If v4 adds a **required** input that v3 did not have, every consumer
must supply it *before* v4 is activated.

```text
FAILURE SIGNATURE: the prompt fails at invocation, not at deploy.
ORDERING RULE:     deploy consumers first, activate second. Always.
```

### Output contract

`responseFormat` is `HTML`, `JSON`, or `MarkDown`, and `outputSchema` constrains
JSON output. Changing either breaks any downstream parser.

```text
FAILURE SIGNATURE: consumer parses successfully and gets wrong values, or
                   throws on a shape it has never seen.
CHECK BEFORE PROMOTING: does any Apex, Flow, or LWC parse this output?
                        If yes, the format change is a coordinated release.
```

### Grounding contract

`templateDataProviders` and their parameters determine what data reaches the
prompt. A v4 that grounds on a new object needs that object accessible to the
running user, and needs its fields reviewed against the PII register — see
`agentforce/agentforce-pii-redaction`, since agents get no Trust Layer masking.

```text
FAILURE SIGNATURE: silently degraded output (grounding returns nothing), or a
                   disclosure incident (grounding returns more than intended).
```

### The pre-promotion diff that catches all three

```bash
# Structural diff of the version envelopes, ignoring prose changes to <content>.
git diff HEAD~1 -- force-app/main/default/genAiPromptTemplates/ \
  | grep -E '^[+-].*(<inputs>|<apiName>|<required>|responseFormat|outputSchema|templateDataProviders|primaryModel)'
```

Any hit means the promotion is a coordinated release rather than a one-field
flip. Any hit on `primaryModel` means the goldens must be re-run before
promotion, because the reasoning behind identical text has changed.

---

## Example 5 — Deployment ordering, which bites once and is remembered forever

### Context

A release deploys a new prompt template and a scorer definition that references
it. The deploy fails.

### The rule

The Metadata API deploys types in the order they appear in `package.xml`.
`GenAiPromptTemplate` must therefore appear **before** `AiAgentScorerDefinition`,
because the template must exist before a scorer referencing it can deploy.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- FIRST: the template. -->
    <types>
        <members>Sales_Email</members>
        <name>GenAiPromptTemplate</name>
    </types>

    <!-- THEN: anything that references it. -->
    <types>
        <members>Sales_Email_Tone_Scorer</members>
        <name>AiAgentScorerDefinition</name>
    </types>

    <version>67.0</version>
</Package>
```

### The generalisation worth carrying

Prompt templates are a **dependency of** agents, scorers, Flows, and Apex — never
the other way round. Put them early in the manifest, and put the consumer
deployment *after* them but the activation flip *after that*:

```text
1. Deploy the new template version (status Published, NOT active)
2. Deploy consumers that can handle both v3 and v4
3. Flip activeVersionIdentifier to v4
4. Observe
5. Retire v3 on a date, not on instinct
```

Step 2 is what makes step 3 reversible. If the consumers only handle v4, step 3
is one-way and you no longer have a rollback.
