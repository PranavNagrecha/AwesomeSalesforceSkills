# Examples — Agent Rate Limit Strategy

## Example 1: Budget service

**Context:** 100 Service reps use agent summarisation. One rep loops a malformed input
several hundred times in an afternoon.

**Problem:** with no per-user cap, one rep can consume the shared entitlement and every
other rep starts seeing refusals. The obvious ledger design makes this worse: an
aggregate query plus an insert on every turn puts the budget check itself inside the
per-transaction SOQL and DML budget.

**Solution:** policy in custom metadata (exempt from the SOQL limit), consumption
recorded through a platform event, aggregation done outside the request path.

```apex
public with sharing class BudgetService {

    public class Decision {
        public Boolean allowed;
        public String reasonCode;      // ALLOWED | OVER_HOURLY | OVER_DAILY
        public Integer retryAfterSec;
    }

    public static Decision consume(Id userId, String persona, Integer estTokens) {
        Decision d = new Decision();

        // getInstance() reads custom metadata; documented as exempt from the SOQL
        // query limit, so this is safe to call anywhere in the transaction.
        Agent_Rate_Limit__mdt policy = Agent_Rate_Limit__mdt.getInstance(persona);
        if (policy == null) {          // fail closed on an unconfigured persona
            d.allowed = false; d.reasonCode = 'OVER_HOURLY'; d.retryAfterSec = 3600;
            return d;
        }

        Agent_Budget_Counter__c c = BudgetCache.counterFor(userId);   // one row, not a SUM()
        Decimal hourUsed = c.Hour_Bucket__c == currentHourUtc() ? c.Hour_Tokens__c : 0;
        Decimal dayUsed  = c.Day_Bucket__c  == currentDayUtc()  ? c.Day_Tokens__c  : 0;

        if (hourUsed + estTokens > policy.Hourly_Tokens__c) {
            d.allowed = false; d.reasonCode = 'OVER_HOURLY';
            d.retryAfterSec = secondsToNextHourUtc();
            return d;
        }
        if (dayUsed + estTokens > policy.Daily_Tokens__c) {
            d.allowed = false; d.reasonCode = 'OVER_DAILY';
            d.retryAfterSec = secondsToNextDayUtc();
            return d;
        }

        // Record consumption out of band; the subscriber rolls it into the counter.
        EventBus.publish(new Agent_Token_Consumed__e(
            UserId__c = userId, Persona__c = persona,
            Estimated_Tokens__c = estTokens, Occurred_At__c = System.now()));

        d.allowed = true; d.reasonCode = 'ALLOWED';
        return d;
    }
}
```

**Why it works:** the per-user cap contains the misbehaving rep without touching anyone
else's throughput. The policy read costs nothing against the 100-query synchronous SOQL
limit because custom metadata is documented as exempt. Reading a single pre-rolled
counter row instead of an aggregate keeps the check O(1) as the ledger grows, and
returning a structured `Decision` — rather than a bare `Boolean` — is what lets the
caller distinguish "wait an hour" from "wait until tomorrow" in the fallback copy.

**Note on the thresholds themselves:** `Hourly_Tokens__c` and `Daily_Tokens__c` are
values you derive from your org's entitlement, read from the Agentforce and Einstein
usage pages in Setup. They are not platform constants, and this skill deliberately does
not supply a default — a wrong default alerts either never or constantly.

---

## Example 2: Graceful fallback with state preserved

**Context:** the budget is exhausted three turns into a conversation in which the
customer has already described their problem in detail.

**Problem:** a generic "please try again later" throws that context away. The customer
retypes it — spending more of tomorrow's budget — or abandons the channel. The failure
mode costs more than the overspend it prevents.

**Solution:** treat exhaustion as a routing decision, not an error.

In the LWC channel wrapper, the gate runs before the agent is dispatched:

```javascript
import consumeBudget from '@salesforce/apex/BudgetService.consume';
import handOff from '@salesforce/apex/AgentHandoffService.toQueue';

async function sendTurn(userText) {
    const estimate = estimateTokens(userText, this.groundedContextChars);
    const decision = await consumeBudget({
        userId: this.userId, persona: this.persona, estTokens: estimate
    });

    if (decision.allowed) {
        return this.dispatchToAgent(userText);
    }

    // Preserve the transcript, then tell the user precisely what happens next.
    const caseId = await handOff({
        transcript: this.transcript,
        reasonCode: decision.reasonCode
    });
    this.renderSystemMessage(
        decision.reasonCode === 'OVER_DAILY'
            ? `I've passed this to a specialist with everything you've told me. `
              + `Case ${caseId} — someone will reply today.`
            : `I've handed this to a colleague with the full conversation. `
              + `Case ${caseId} — you'll hear back shortly.`
    );
    this.emitMetric('agent_budget_refusal', decision.reasonCode);
}
```

**Why it works:** the transcript survives, so the customer never repeats themselves and
the human picking it up starts informed. Branching the copy on `reasonCode` means the
message is accurate rather than generic. The `emitMetric` call is the part teams skip and
then miss: refusal *rate* is the alertable signal, because consumption rising is ordinary
growth while refusals rising is either a defect or an abuser.
