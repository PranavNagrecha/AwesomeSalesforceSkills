# Examples — Long-Running Process Orchestration

## Example 1: Order Fulfillment Pipeline With Bounded Queueable Chain

**Context:** An e-commerce integration must run four sequential steps when an order is placed: (1) validate inventory with an external API, (2) reserve stock via DML, (3) trigger fulfillment via a second external API, (4) send a confirmation Platform Event for downstream billing. Each step is a distinct callout or DML operation. The process must recover if step 2 or 3 fails.

**Problem:** Without bounded chaining and a Finalizer, a failure in step 3 leaves inventory reserved (step 2 committed) with no compensating action and no operations visibility. An unguarded recursive chain also risks flooding the async queue if a bug causes infinite re-enqueueing.

**Solution:**

```apex
// Shared state object — serializable, carries only IDs and small scalars
public class OrderState {
    public Id orderId;
    public Integer currentStep;
    public Integer retryCount;
    public OrderState(Id orderId) {
        this.orderId = orderId;
        this.currentStep = 1;
        this.retryCount = 0;
    }
}

// Step 1: Validate inventory
public class ValidateInventoryQueueable implements Queueable, Database.AllowsCallouts {
    private final OrderState state;

    public ValidateInventoryQueueable(OrderState state) {
        this.state = state;
    }

    public void execute(QueueableContext ctx) {
        System.attachFinalizer(new OrderStepFinalizer(state, 1));

        // Callout to inventory API
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:InventoryAPI/validate');
        req.setMethod('POST');
        HttpResponse res = new Http().send(req);

        if (res.getStatusCode() != 200) {
            throw new CalloutException('Inventory validation failed: ' + res.getBody());
        }

        // Update checkpoint
        updateCheckpoint(state.orderId, 'ValidateInventory', 'Complete', null);

        // Chain step 2
        state.currentStep = 2;
        AsyncOptions opts = new AsyncOptions();
        opts.MaximumQueueableStackDepth = 5;
        System.enqueueJob(new ReserveStockQueueable(state), opts);
    }

    private void updateCheckpoint(Id orderId, String step, String status, String error) {
        Order__c rec = new Order__c(
            Id = orderId,
            CurrentStep__c = step,
            StepStatus__c = status,
            LastError__c = error,
            StepUpdatedAt__c = System.now()
        );
        update rec;
    }
}

// Finalizer: handles failure for any step
public class OrderStepFinalizer implements System.Finalizer {
    private final OrderState state;
    private final Integer failedStep;
    private static final Integer MAX_RETRIES = 3;

    public OrderStepFinalizer(OrderState state, Integer failedStep) {
        this.state = state;
        this.failedStep = failedStep;
    }

    public void execute(FinalizerContext ctx) {
        if (ctx.getResult() == ParentJobResult.SUCCESS) {
            return; // Normal completion — next step was already enqueued in execute()
        }

        Exception ex = ctx.getException();
        state.retryCount++;

        if (state.retryCount <= MAX_RETRIES) {
            // Re-enqueue the same step
            state.currentStep = failedStep;
            AsyncOptions opts = new AsyncOptions();
            opts.MaximumQueueableStackDepth = 5;
            System.enqueueJob(getJobForStep(failedStep, state), opts);
        } else {
            // Exhausted retries — mark failed and run compensation
            markProcessFailed(state.orderId, failedStep, ex.getMessage());
            System.enqueueJob(new CompensateOrderQueueable(state));
        }
    }

    private Queueable getJobForStep(Integer step, OrderState s) {
        if (step == 1) return new ValidateInventoryQueueable(s);
        if (step == 2) return new ReserveStockQueueable(s);
        if (step == 3) return new TriggerFulfillmentQueueable(s);
        return new NotifyBillingQueueable(s);
    }

    private void markProcessFailed(Id orderId, Integer step, String msg) {
        update new Order__c(
            Id = orderId,
            ProcessStatus__c = 'Failed',
            CurrentStep__c = String.valueOf(step),
            LastError__c = msg
        );
    }
}
```

**Why it works:** Each step runs in its own transaction with a full governor limit allocation. The Finalizer guarantees recovery even when the parent job is terminated by a system-level exception that `try/catch` cannot intercept. `MaximumQueueableStackDepth = 5` caps the chain so a bug cannot produce an infinite loop. State travels through constructor fields — no static variables that would be cleared between transactions.

---

## Example 2: Document Processing Pipeline Using Platform Event State Machine

**Context:** A legal firm uses Salesforce to manage document review workflows. When a new Case Document is uploaded, the system must: (1) extract metadata via an external NLP service (up to 30 seconds), (2) assign reviewers based on extracted categories, (3) notify reviewers via email, and (4) update the case status. Steps 2–4 cannot start until step 1 returns, but step 1's response may arrive minutes later via a callback.

**Problem:** A simple Queueable chain cannot wait for an external callback. Holding a Queueable open is not possible — once `execute()` returns, the transaction ends. A Platform Event state machine handles the asynchronous callback naturally.

**Solution:**

```apex
// Process instance Custom Object: DocumentReview__c
// Fields: Status__c, CurrentStep__c, RetryCount__c, LastError__c, StepAdvancedAt__c

// Platform Event: DocReviewStep__e
// Fields: ReviewId__c (External ID), Step__c (text), Payload__c (JSON text)

// Launch: called from a trigger or flow when document is uploaded
public class DocumentReviewOrchestrator {
    public static void launch(Id caseDocumentId) {
        DocumentReview__c run = new DocumentReview__c(
            Status__c = 'Running',
            CurrentStep__c = 'ExtractMetadata',
            CaseDocument__c = caseDocumentId
        );
        insert run;

        EventBus.publish(new DocReviewStep__e(
            ReviewId__c = run.Id,
            Step__c = 'ExtractMetadata',
            Payload__c = JSON.serialize(new Map<String, Object>{ 'docId' => caseDocumentId })
        ));
    }
}

// Platform event trigger: thin dispatcher
trigger DocReviewStepTrigger on DocReviewStep__e (after insert) {
    for (DocReviewStep__e evt : Trigger.new) {
        switch on evt.Step__c {
            when 'ExtractMetadata' {
                System.enqueueJob(new ExtractMetadataWorker(evt.ReviewId__c, evt.Payload__c));
            }
            when 'AssignReviewers' {
                System.enqueueJob(new AssignReviewersWorker(evt.ReviewId__c, evt.Payload__c));
            }
            when 'NotifyReviewers' {
                System.enqueueJob(new NotifyReviewersWorker(evt.ReviewId__c, evt.Payload__c));
            }
            when 'CloseCase' {
                System.enqueueJob(new CloseCaseWorker(evt.ReviewId__c, evt.Payload__c));
            }
        }
    }
}

// Example worker: AssignReviewers step
public class AssignReviewersWorker implements Queueable {
    private final Id reviewId;
    private final String payloadJson;

    public AssignReviewersWorker(Id reviewId, String payloadJson) {
        this.reviewId = reviewId;
        this.payloadJson = payloadJson;
    }

    public void execute(QueueableContext ctx) {
        System.attachFinalizer(new DocReviewFinalizer(reviewId, 'AssignReviewers'));

        Map<String, Object> payload = (Map<String, Object>) JSON.deserializeUntyped(payloadJson);
        String category = (String) payload.get('category');

        // Business logic: assign based on extracted category
        List<User> reviewers = [SELECT Id FROM User WHERE ReviewCategory__c = :category LIMIT 5];
        List<CaseReviewer__c> assignments = new List<CaseReviewer__c>();
        for (User u : reviewers) {
            assignments.add(new CaseReviewer__c(
                DocumentReview__c = reviewId,
                Reviewer__c = u.Id
            ));
        }
        insert assignments;

        // Update checkpoint
        update new DocumentReview__c(Id = reviewId, CurrentStep__c = 'NotifyReviewers');

        // Advance to next step via Platform Event
        payload.put('reviewerCount', reviewers.size());
        Database.SaveResult result = EventBus.publish(new DocReviewStep__e(
            ReviewId__c = reviewId,
            Step__c = 'NotifyReviewers',
            Payload__c = JSON.serialize(payload)
        ));

        if (!result.isSuccess()) {
            throw new EventBusException('Failed to publish NotifyReviewers event: '
                + result.getErrors()[0].getMessage());
        }
    }
}
```

**Why it works:** The Platform Event decouples step timing from transaction execution. The external NLP callback (not shown) publishes a `DocReviewStep__e` with `Step__c = 'AssignReviewers'` when extraction completes, which is exactly what the trigger listens for. The process can resume hours later without holding any Salesforce resources. Each worker is independently retryable via the Finalizer. The `DocumentReview__c` record provides operational visibility at all times.

---

## Anti-Pattern: Embedding All Steps In A Single Queueable With Loop

**What practitioners do:** To avoid managing multiple Queueable classes, developers place all steps in a single class with a `while` loop or a `switch` statement, incrementing a counter until all steps are done:

```apex
// WRONG — do not use
public class AllStepsQueueable implements Queueable, Database.AllowsCallouts {
    private Integer step;

    public void execute(QueueableContext ctx) {
        while (step <= 5) {
            if (step == 1) doStep1();
            else if (step == 2) doStep2(); // callout
            else if (step == 3) doStep3(); // heavy DML
            // ... etc.
            step++;
        }
    }
}
```

**What goes wrong:** All five steps consume from the same transaction's governor limit bucket. Step 3's heavy DML combined with step 2's callout may push the transaction past the DML or CPU limit, failing the entire job and requiring recovery from step 1. There is no safe checkpoint between steps. A single `System.attachFinalizer()` cannot distinguish which step failed, making targeted retry impossible. Callouts after DML in the same transaction require `Database.AllowsCallouts` on the whole class, which is often omitted for the non-callout steps.

**Correct approach:** Each step is a separate Queueable class with its own transaction, its own Finalizer, and an explicit step identifier in the state object. The state object's `currentStep` field allows the Finalizer to re-enqueue precisely the failed step without replaying prior steps.
