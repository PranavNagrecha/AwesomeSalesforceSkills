# Examples — Agent Rate Limit Strategy

## Example 1: Budget service sketch

**Context:** 100 Service reps use agent summarization; one rep loops a bad input 500x.

**Problem:** Single rep consumes tenant daily budget; all other reps get 503.

**Solution:**

```apex
public with sharing class BudgetService {
    public static Boolean consume(Id userId, Integer estTokens) {
        Agent_Rate_Limit__mdt p = [SELECT Hourly_Tokens__c FROM Agent_Rate_Limit__mdt
                                    WHERE Persona__c='ServiceRep' LIMIT 1];
        Decimal used = [SELECT SUM(Tokens__c) t FROM User_Token_Ledger__c
                         WHERE UserId__c=:userId AND HourBucket__c=:currentHour()][0].get('t');
        if ((used ?? 0) + estTokens > p.Hourly_Tokens__c) return false;
        EventBus.publish(new Agent_Token_Consumed__e(UserId__c=userId, Tokens__c=estTokens));
        return true;
    }
}
```

**Why it works:** Per-user cap stops the bad-rep scenario without affecting others.


---

## Example 2: Graceful fallback

**Context:** Budget exhausted mid-conversation.

**Problem:** Dropping the user mid-turn is worse than a slow response.

**Solution:**

Render: 'I'm handing you to a person — your conversation is preserved.' Create Case with `Agent_Transcript__c` populated, assign to the queue.

**Why it works:** Preserves context, recovers trust, and creates a repair signal for SRE.

