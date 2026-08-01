# LLM Anti-Patterns — Agent Rate Limit Strategy

Scope: the client-side budget gate that sits in front of a high-traffic agent, and the
Apex governor exposure that gate itself creates. Throttling inbound REST consumers is a
different problem and belongs to `integration/api-governance-and-rate-limits`.

**Read this first.** Salesforce does not publish a single universal per-org Agentforce
request or token ceiling in the developer documentation; entitlement varies by edition,
licence and add-on. So the first rule of this skill is that any number you use as a
threshold must be read from your own org's usage page or from your contract — never
hard-coded from memory, and never copied from a blog. Everything below follows from
that.

## Anti-Pattern 1: Asserting a token or request limit the docs do not publish

The most damaging thing an assistant does here is answer confidently. Asked "what is the
Agentforce rate limit", it produces a specific number of requests per minute or tokens
per day, the team builds thresholds around it, and the alerting is wrong from day one —
usually silent, because a threshold set too high never fires.

❌ "Agentforce allows N requests per minute, so alert at 0.8 × N."
✅ Read the entitlement your org actually has from the Agentforce and Einstein usage
pages in Setup, record where the number came from and when it was read, and store it in
custom metadata so it can be corrected without a deploy. If a number cannot be sourced,
the correct output is "see your org's Einstein usage page", not an estimate.

## Anti-Pattern 2: Estimating tokens from character count and never reconciling

`chars / 4` is a reasonable pre-call estimate for the user's message and a badly wrong
one for the whole request, because grounding is what actually fills the context window.
A turn estimated at 500 tokens can be an order of magnitude larger once retrieved
records are rendered in. Budgets built on the estimate alone drift permanently
optimistic.

❌ Charge the ledger `message.length() / 4` and move on.
✅ Charge an estimate that includes the grounded payload length, then reconcile against
observed consumption on a schedule and carry the correction forward. Track the ratio of
estimated to actual as its own metric — when it moves, the grounding configuration
changed.

## Anti-Pattern 3: A per-turn aggregate query and a per-turn DML write

The obvious ledger design does a `SUM()` query and an insert on every turn. Inside a
single Apex transaction that pattern is bounded by hard, documented limits: 100 SOQL
queries and 150 DML statements synchronously. It survives a demo and fails the moment
anything batches turns together.

**Wrong** — one aggregate query and one insert per turn, inside the request path:

```apex
public static Boolean consume(Id userId, Integer estTokens) {
    AggregateResult ar = [SELECT SUM(Tokens__c) t FROM User_Token_Ledger__c
                          WHERE UserId__c = :userId AND HourBucket__c = :currentHour()];
    Decimal used = (Decimal) ar.get('t');
    if ((used == null ? 0 : used) + estTokens > limitFor(userId)) return false;
    insert new User_Token_Ledger__c(UserId__c = userId, Tokens__c = estTokens);
    return true;
}
```

**Right** — read a pre-aggregated counter, publish the consumption event, aggregate the
ledger asynchronously:

```apex
public with sharing class BudgetService {
    public static Boolean consume(Id userId, Integer estTokens) {
        // Custom metadata reads are exempt from the SOQL query limit, so the policy
        // lookup is free no matter how many times it happens in the transaction.
        Agent_Rate_Limit__mdt policy = Agent_Rate_Limit__mdt.getInstance('ServiceRep');
        Decimal used = BudgetCache.usedThisHour(userId);   // one rolled-up counter row
        if (used + estTokens > policy.Hourly_Tokens__c) return false;
        EventBus.publish(new Agent_Token_Consumed__e(
            UserId__c = userId, Tokens__c = estTokens));
        return true;
    }
}
```

The custom-metadata exemption is documented explicitly: "This limit doesn't apply to
custom metadata types. In a single Apex transaction, custom metadata records can have
unlimited SOQL queries." That is why the policy belongs in CMDT and the counter does
not.

Source: Apex Governor Limits —
https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm

## Anti-Pattern 4: Hard-coding the threshold in Apex

A literal in a class means every traffic shift is a deployment, and no support engineer
can respond to an incident at 02:00. Assistants reach for a constant because it is the
shortest correct-looking code.

❌ `private static final Integer HOURLY_TOKENS = 50000;`
✅ `Agent_Rate_Limit__mdt` per persona, read with `getInstance()`. Custom metadata is
deployable, packageable and queryable without consuming the SOQL limit — and the value
can be corrected in production without a release.

## Anti-Pattern 5: Retrying into the wall

When the platform refuses a call, the generated handler retries immediately, often in a
loop. That converts one refusal into many and, if the refusal was a concurrency limit
rather than a daily one, guarantees it stays exceeded. The platform's own long-running
request behaviour makes this concrete: exceeding the concurrent long-running request
allocation returns `REQUEST_LIMIT_EXCEEDED`, and adding more concurrent requests is
exactly the wrong response.

❌ `catch (Exception e) { return callAgent(input); }`
✅ Classify first, then act: a concurrency or throttling refusal gets exponential backoff
with jitter and a bounded retry count; a budget refusal gets no retry at all and goes
straight to the fallback path, because retrying a spent budget cannot succeed.

Source: Salesforce Platform API limits — concurrent long-running request allocation and
`REQUEST_LIMIT_EXCEEDED` —
https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm

## Anti-Pattern 6: A fallback that drops the conversation

"Please try again later" discards everything the user has typed, and they either repeat
themselves — consuming more budget — or leave. The failure mode of a budget gate should
cost less than the thing it is protecting against.

❌ Return a generic error string and end the turn.
✅ Hand off with state preserved: create the Case with the transcript attached, route it
to the queue that owns the topic, and tell the user what happens next and when. Approve
that copy with the same people who approve the agent's other responses.

## Anti-Pattern 7: Measuring exhaustion only when a user complains

Without a per-persona view, the first signal is a support ticket, by which point the
budget has been spent by whoever spent it. Assistants generate the gate and skip the
telemetry because the gate is the part that was asked for.

❌ The gate exists; nothing reports on it.
✅ Emit p50 and p95 tokens per turn per persona, the count of refusals per hour, and the
estimate-to-actual ratio. Alert on refusal rate rather than on absolute consumption —
consumption rising is normal growth, refusals rising is a defect or an abuser.
