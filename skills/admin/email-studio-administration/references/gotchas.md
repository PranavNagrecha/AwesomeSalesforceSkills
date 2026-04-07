# Gotchas — Email Studio Administration

Non-obvious Salesforce Marketing Cloud platform behaviors that cause real production problems in this domain.

## Gotcha 1: Triggered Send Definition Must Be Activated Before It Can Fire

**What happens:** A Triggered Send Definition created in Email Studio starts in "Building" status. While in "Building" status, any API call or automation trigger that references the definition is silently dropped — no error is returned to the calling system, no error appears in the send logs, and the email simply does not deliver.

**When it occurs:** Any time a new Triggered Send Definition is built for a transactional or event-driven email. Teams typically discover this after production deployment when the operations team reports that order confirmations or password resets are not sending. The definition appears configured correctly in the UI.

**How to avoid:** After completing the definition build, explicitly click the "Activate" button in the Triggered Send Definitions list. The status must change from "Building" to "Active." Include activation as a named step in deployment runbooks. Test the API trigger with a test subscriber before any production traffic is routed.

---

## Gotcha 2: Global Unsubscribe From a Transactional Send Overwrites Commercial Opt-In If Classification Is Wrong

**What happens:** If a Triggered Send Definition carrying genuinely transactional content (e.g., a shipping notification) is assigned a Commercial Send Classification instead of a Transactional one, and the subscriber clicks "Unsubscribe" in the footer, the system records a global commercial unsubscribe. This removes the subscriber from all future commercial sends — including newsletters and promotional emails they explicitly opted into.

**When it occurs:** Most commonly when the default Business Unit Send Classification (usually Commercial) is left on a triggered send without review. Also occurs when teams build new transactional sends by cloning an existing commercial email template that already carries the commercial classification.

**How to avoid:** Create a named Transactional Send Classification in each Business Unit at setup time. Require all Triggered Send Definitions to explicitly declare their classification before activation. Audit existing Triggered Send Definitions quarterly to confirm classification accuracy.

---

## Gotcha 3: Dynamic Content Rule Order Determines Evaluation Priority — Not Specificity

**What happens:** Dynamic content rules in a Content Builder block are evaluated strictly top-to-bottom. The first rule that evaluates to true wins, regardless of how specific or restrictive the rule is. A broad generic rule placed above a specific rule will match before the specific rule ever evaluates.

**When it occurs:** Most frequently when rules are added incrementally over time. A developer adds a specific Gold-tier rule after an existing "has any loyalty number" generic rule, expecting specificity to take precedence. Instead, every loyalty subscriber matches the generic rule and never sees the Gold-tier content.

**How to avoid:** Order rules from most specific (most restrictive conditions) to least specific (broadest conditions), with an unconditional default variation at the bottom. After any rule change, preview the email using test subscribers from each rule segment to confirm the correct variation renders.

---

## Gotcha 4: A/B Test Winner Does Not Fire Automatically If the Evaluation Window Produces No Clear Winner

**What happens:** If both test variants perform identically within the evaluation window (identical open rates, or the difference is within rounding), the auto-winner logic may not fire. The holdout audience receives no email. Depending on Business Unit settings, the send may expire silently without a winner being declared.

**When it occurs:** Most frequently on small test lists (fewer than 5,000 per test arm) where open events are too sparse to differentiate within the evaluation window. Also occurs if the evaluation window ends during off-peak hours when subscribers have not yet opened either version.

**How to avoid:** Size test groups to generate at least 300–500 open events within the evaluation window (use historical open rates to calculate required audience size). For small sends, consider disabling auto-send and using manual winner selection instead. Always monitor the test after the evaluation window closes to confirm winner deployment.

---

## Gotcha 5: Adding an Address to the Global Suppression List After a Send Job Has Started Does Not Exclude It From That Job

**What happens:** The Global Suppression List is evaluated at the time a send job's subscriber list is compiled, not continuously throughout delivery. If an address is added to the GSL after the job has started executing, that address may already be in the send queue and will receive the email.

**When it occurs:** When a legal or compliance team requests emergency suppression of an address during an active send window — for example, following a customer complaint received while a large batch send is running.

**How to avoid:** For emergency suppressions during active sends, pause the send job first (if the send size and timing allow), add the address to the GSL, then resume. For post-send suppression, add the address to the GSL immediately and document that the address received the send in question. For large sends, build a pre-send suppression verification step into the approval workflow before the job is activated.

---

## Gotcha 6: Content Detective Does Not Guarantee Inbox Delivery — It Scans for Known Trigger Words Only

**What happens:** Content Detective scans the email body and subject line for known spam trigger phrases and reports a score. Teams treat a passing Content Detective score as a deliverability guarantee. In reality, Content Detective is a static word-list scanner. It does not assess sender reputation, IP warming status, domain authentication (SPF/DKIM/DMARC), engagement history, or ISP-specific filtering rules — all of which are primary drivers of inbox placement.

**When it occurs:** New teams building their first Email Studio send often run Content Detective and treat it as the only pre-send validation step. Spam complaint rates or inbox placement issues emerge post-send despite the email "passing" Content Detective.

**How to avoid:** Use Content Detective as one of several validation steps, not as the sole deliverability check. Complement it with Inbox Preview (Litmus) for rendering, a seed list send to real ISP inboxes for inbox/spam folder placement testing, and an ongoing review of sender reputation metrics in the Intelligence Reports dashboard.
