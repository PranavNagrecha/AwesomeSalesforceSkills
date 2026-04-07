# Examples — Self-Service Design

## Example 1: Help Center Redesign Reducing Ticket Volume for a SaaS Company

**Context:** A B2C SaaS company runs a Salesforce Experience Cloud portal. Monthly case volume is 4,200 cases. The top three contact reasons are: password reset (18%), billing inquiry (14%), and API error codes (11%). The existing portal has a case submission form as the landing page with a link to a knowledge base in the navigation bar. Article coverage exists for all three top contact reasons but uses internal terminology in article titles (e.g., "SSO Token Expiry" instead of "Can't log in").

**Problem:** Customers bypass the knowledge base entirely because the case form is the most prominent UI element. Article titles do not match the language customers use in search queries, so search returns poor results even when relevant articles exist. The deflection rate as measured by the Case Deflection component is 4% — far below the 25% target.

**Solution:**

The redesign makes three targeted changes without rebuilding the portal:

1. Replace the case form landing page with a Help Center search page. Move the case submission link to the search results page (visible after a search interaction) and to a "Contact Support" link in the global navigation.

2. Retitle the 15 highest-traffic articles using customer-facing language. "SSO Token Expiry" becomes "I can't log in or my password isn't working." "Billing Cycle FAQ" becomes "When will I be charged and what's on my invoice?" This change alone improves Knowledge search recall for the top contact reasons.

3. Enable the Case Creation component's article suggestion feature on the case submission page. Configure it to surface suggestions after the customer enters a case subject.

**Why it works:** Article search recall improves because titles now match the vocabulary customers use. Moving the search bar to the landing page intercepts customers before they reach the case form. Pre-deflection article surfacing during case creation provides a second deflection opportunity for customers who reached the form despite the search landing page. The three changes are independent and each contributes incrementally to the deflection rate improvement — the redesign does not depend on all three succeeding simultaneously.

Measured outcome (90 days post-launch): deflection rate increased from 4% to 23%. Monthly case volume for the top three contact reasons dropped by 18%.

---

## Example 2: Pre-Submission Search Prompt Driving Article Deflection for a Partner Portal

**Context:** A manufacturing company runs an Experience Cloud Partner Community for authorized resellers. Dealers submit 1,100 warranty claim cases per month. Analysis shows 340 of those cases (31%) result in resolution notes that copy text verbatim from the existing Warranty Claims Knowledge article — meaning the dealer had the article available but submitted a case anyway without reading it.

**Problem:** The case submission form is a single-page form with no pre-deflection mechanism. Dealers have been trained to submit cases first and ask questions later. There is no friction in the current flow, and there is no mechanism to surface the relevant article before submission.

**Solution:**

Implement a mandatory search prompt using a custom Lightning Web Component (LWC) on the case submission page:

1. The case submission page loads showing only a search field and the prompt: "Search for an answer before opening a case."
2. The LWC calls a Search API query against the Knowledge base when the dealer types 3+ characters.
3. If matching articles are returned, they are displayed with title, summary excerpt, and a "This answered my question" button.
4. After the dealer either clicks "This answered my question" (records a deflection event) or clicks "I still need to submit a case" (dismisses the prompt), the full case form renders.
5. The LWC fires a platform event on deflection to support reporting in CRM Analytics.

The case form is not accessible without completing the search prompt step. However, the "I still need to submit a case" button is always visible — there is no loop that traps dealers.

**Why it works:** The mandatory search step catches the cohort of cases submitted out of habit rather than genuine need. The article is surfaced in context, at the moment the dealer has articulated their query. The "This answered my question" button gives dealers a low-effort way to exit without submitting, and records a measured deflection event. The always-visible "I still need to submit" escape hatch prevents frustration for dealers with complex, article-free issues.

Measured outcome (60 days post-launch): warranty claim cases dropped from 1,100 to 780 per month. The 340 habitually-submitted cases were reduced by approximately 290, with the remainder representing genuine warranty issues not covered by the article.

---

## Anti-Pattern: Launching Community Q&A Without Seeded Content

**What practitioners do:** Enable the Experience Cloud Questions component on the portal and announce the community in a customer newsletter. Expect peer support to organically generate content and deflection within the first month.

**What goes wrong:** The portal launches with zero answered questions. Early visitors see no content, post no questions (social proof is absent), and leave. The "ghost town" perception sets in within the first two weeks. Community posting rates drop to near zero and do not recover. The component is disabled or ignored within 60 days. The deflection contribution is zero throughout.

**Correct approach:** Before launch, seed the community with 20–50 realistic Q&A pairs created from existing support content: convert the top 20 support macro responses into community question-and-answer posts, use real customer-phrased question titles from historical case subjects, and mark best answers. Assign two or three internal advocates to monitor the community for the first 30 days and respond to unanswered questions within 24 hours. Peer contributions emerge after the community demonstrates that questions get answered — not before.
