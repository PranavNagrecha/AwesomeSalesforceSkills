# LLM Anti-Patterns — Email Studio Administration

Common mistakes AI coding assistants make when generating or advising on Email Studio and Content Builder configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Multiple Email Versions for Multi-Segment Sends

**What the LLM generates:** Advice to create separate email records (e.g., "Email_Gold", "Email_Silver", "Email_Bronze") in Content Builder and send each to a segmented list, treating each version as an independent email.

**Why it happens:** LLMs trained on general email marketing content pattern-match to the "segmented list → segmented email" model common in legacy ESPs. Training data does not sufficiently emphasize that dynamic content blocks natively handle multi-segment personalization within a single email in Content Builder.

**Correct pattern:**

```
One email definition in Content Builder.
Each varying section → Dynamic Content block.
Rules ordered: most specific → least specific → Default variation.
One send job covers all segments.
```

**Detection hint:** If the output suggests creating more than one email record for what is described as "the same campaign with different content per segment," flag as this anti-pattern.

---

## Anti-Pattern 2: Recommending Transactional Classification for Marketing Emails to Remove the Footer

**What the LLM generates:** Advice to use a Transactional Send Classification for a newsletter, promotional offer, or any bulk marketing email, citing "removes the unsubscribe footer" or "cleaner email design" as the benefit.

**Why it happens:** LLMs conflate the platform-level classification field (which controls UI rendering of the footer) with legal compliance status. Training data includes content about how to configure the Transactional classification without sufficient coverage of the legal constraints on when it may be used.

**Correct pattern:**

```
Transactional Send Classification: ONLY for emails whose primary
  purpose is the facilitation of a completed commercial transaction
  (order confirmation, shipping notification, password reset,
  account security alert).

Commercial Send Classification: ALL marketing, promotional,
  newsletter, or awareness emails — regardless of audience size.
  CAN-SPAM footer required. Global unsubscribe enforced.
```

**Detection hint:** If the output recommends Transactional classification for any email described as a "newsletter," "promotion," "sale," "announcement," or "campaign," flag as this anti-pattern.

---

## Anti-Pattern 3: Assuming A/B Test Winner Auto-Sends Regardless of Audience Size

**What the LLM generates:** A/B test configuration advice that sets a short evaluation window (1–2 hours) and enables auto-send winner for a send list of 2,000 total subscribers, without noting that the test groups may be too small to reach statistical significance within the window.

**Why it happens:** LLMs describe the A/B test auto-winner feature based on its mechanical description (timer + criteria → auto-send) without accounting for minimum viable open event counts needed for reliable winner determination.

**Correct pattern:**

```
Test group sizing for reliable winner determination:
  - Target 300–500 open events per test arm within the evaluation window
  - Required audience per arm = target opens / historical open rate
  - Example: 25% open rate → need 1,200–2,000 subscribers per arm

For sends under 10,000 total subscribers:
  - Increase test arm percentage (25%/25%/50% instead of 10%/10%/80%)
  - OR use manual winner selection instead of auto-send
  - OR skip A/B test and send a single version with documented hypothesis
```

**Detection hint:** If the output sets test arms of 10% for a send audience under 20,000 without flagging audience size constraints, flag as this anti-pattern.

---

## Anti-Pattern 4: Omitting Triggered Send Definition Activation Step in Deployment Guidance

**What the LLM generates:** Deployment instructions for a Triggered Send Definition that describe building the definition, configuring the API call, and testing the integration — but do not include a step to explicitly Activate the definition from the Email Studio UI.

**Why it happens:** LLMs focus on the technical configuration steps (API setup, definition fields) and treat "activation" as an implicit consequence of completing the configuration. In Marketing Cloud, activation is a separate, explicit UI action — a built definition in "Building" status silently drops all triggers.

**Correct pattern:**

```
Triggered Send Definition deployment checklist:
  1. Build the definition (content, classification, list/DE)
  2. Save the definition
  3. Navigate to Triggered Send Definitions list
  4. Locate the definition and click "Activate"
  5. Confirm status changes from "Building" to "Active"
  6. Fire a test trigger via the API and confirm delivery
```

**Detection hint:** If deployment instructions for a Triggered Send do not include an explicit activation step referencing status change to "Active," flag as this anti-pattern.

---

## Anti-Pattern 5: Treating Content Detective as a Full Deliverability Check

**What the LLM generates:** Pre-send validation guidance that lists "run Content Detective and confirm no red flags" as the primary or sole deliverability validation step, without recommending seed list testing, Inbox Preview, or sender reputation review.

**Why it happens:** Content Detective is a named, visible feature in Email Studio and is easily surfaced in training data about "how to validate an email before sending." LLMs pattern-match to it as the validation step without understanding its narrow scope (static word-list scan only).

**Correct pattern:**

```
Pre-send validation pipeline (all steps required):
  1. Content Detective — scan for spam trigger words in body and subject
  2. Test send to seed list — confirm delivery, rendering, links, and
     dynamic content variations with real subscriber data
  3. Inbox Preview (Litmus) — confirm rendering across Gmail, Outlook,
     Apple Mail, and mobile clients
  4. Approval workflow — submit for manager sign-off if required
  5. Sender reputation check — review bounce rate and complaint rate
     from prior sends in Intelligence Reports before activating large sends
```

**Detection hint:** If pre-send validation guidance mentions only Content Detective or treats it as equivalent to "spam check" without mentioning seed sends or inbox rendering, flag as this anti-pattern.

---

## Anti-Pattern 6: Conflating Email Studio Dynamic Content With AMPscript Personalization Strings

**What the LLM generates:** Advice that mixes Dynamic Content block configuration with AMPscript `%%[IF]%%` conditional blocks, treating them as interchangeable tools for the same problem, or suggesting that dynamic content blocks should be built using AMPscript conditionals in the HTML layer.

**Why it happens:** Both Dynamic Content blocks and AMPscript conditionals produce subscriber-specific content, and LLMs merge the two mechanisms when generating generic "personalization" advice. Training data includes AMPscript documentation alongside Content Builder documentation without clearly delineating scope.

**Correct pattern:**

```
Dynamic Content blocks (UI-configured):
  - Use for: section-level swapping (hero image, offer copy, CTA)
    based on subscriber attributes or DE fields
  - Managed by: marketers in the Content Builder UI
  - No coding required

AMPscript conditionals (code-level):
  - Use for: inline text substitution, calculated values, complex
    multi-field logic that cannot be expressed in the UI rule builder
  - Managed by: developers in the HTML or text editor
  - Syntax: %%[IF @field == "value" THEN]%% ... %%[ENDIF]%%

Do not build section-level content swapping in AMPscript when
Dynamic Content blocks can handle it — AMPscript increases
technical debt and makes content edits harder for non-developers.
```

**Detection hint:** If the output recommends AMPscript `IF` blocks for a segmentation use case that could be handled by Dynamic Content UI rules, flag as this anti-pattern.
