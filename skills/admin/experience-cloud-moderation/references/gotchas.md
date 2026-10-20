# Gotchas — Experience Cloud Moderation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Cites are to the Winter '27 (264) `api_meta`, `object_reference` and `apexdev` guides.

UNVERIFIED (2026-10-20): Gotchas 2 (reputation not retroactive), 4 (partial-word keyword matching) and 5 (external licenses cannot hold the permissions) rest on Help-only behaviour; each is marked again where it is asserted.

## Gotcha 1: Review-Status Content Is Hidden from Everyone Except Its Author and Permitted Users

**What happens:** A member submits a post that matches a rule with the Review action. The feed item is created with status `PendingReview`: it is visible to its author and to users who see it and have View All Data or Can Approve Feed Post and Comment; the author and users with Can Approve Feed Post and Comment or Modify All Data can edit and delete it (object_reference 264 L136986-136990). For a held comment the same permissions apply, and the author can edit it if the parent feed item is published (L136371-136379). Comments, likes, bookmarks and shares on a pending-review item are blocked (L136995-136999). The earlier text that the author cannot edit a held post, and that Moderate Experiences Feeds is what reveals held content, is contradicted by these passages.

**When it occurs:** Any time a post or comment triggers a Review rule. This surprises community managers who expect to see all posts, and members who see their post "disappear" from the feed.

**How to avoid:** Communicate the Review workflow to moderators before launch. Confirm that the people who must see and act on held content hold Can Approve Feed Post and Comment; View All Data also reveals held items, and Modify All Data also edits, deletes and publishes held comments (L136986-136990, L136377-136379). SOQL on feed items ignores those permissions, so filter pending-review items out with an explicit clause (object_reference 264 L136992-136994). Customize the Block user message (`userMessage`, api_meta 264 L92283-92288) so members understand why content was refused. UNVERIFIED (2026-10-20): customizing a message shown for held content is not documented in the corpus.

---

## Gotcha 2: Reputation Points and Existing Members

**What happens:** UNVERIFIED (2026-10-20): that reputation levels and point rules configured after a community has been active award no points for historical actions, so long-standing members start at 0 points and Level 1 and may be caught by Member Criteria rules, is Help-only; no corpus line says either way. The levels are `ReputationLevel` entries with a Required `lowerThreshold` (api_meta 264 L94384-94387), and points accrue when a member acts (L94401).

**When it occurs:** When reputation is configured after site launch.

**How to avoid:** Test in a sandbox with an account that has prior activity before relying on reputation for any rule. If the behaviour is confirmed, audit current member activity and relax level-based rules until members have had time to earn points.

---

## Gotcha 3: Rule Precedence Is by Action, Not by Setup Order

**What happens:** Moderation rules are not evaluated top to bottom with the first match winning. Rules that block content run first, then rules to review and approve content, then rules that replace content, and last rules that flag; if two or more rules perform the same action the oldest rule runs first, by creation date (api_meta 264 L92226-92227). Replace rules do not run when the content also applies to a review rule, because community managers should review the original content (L92228-92229). The earlier text that a Block rule below a Flag rule never fires is contradicted by this passage.

**When it occurs:** When admins assume the Setup list order controls behaviour, or expect a replace rule to rewrite content that a review rule has already held.

**How to avoid:** Choose the action to express priority, not list position, and use the creation date as the tie-break for same-action rules. Test each rule combination with real posts.

---

## Gotcha 4: Keyword Matching Rules

**What happens:** Capitalization and trailing punctuation are ignored when keywords are matched, so a list entry of BadWord is matched when a member types BADWORD or badword (api_meta 264 L84926-84927). Wildcard characters are not supported (L84967), and a keyword can be up to 100 characters (L84965-84966). UNVERIFIED (2026-10-20): that a keyword also matches inside longer words, so "ban" would match "banner", "abandoned" and "band", is not stated in the corpus; treat it as a risk to test, not a fact.

**When it occurs:** When keyword lists are built quickly without testing. Short words, common root words and acronyms are the usual sources of false positives if substring matching applies.

**How to avoid:** Test every keyword list in a sandbox community before activating rules in production, use multi-word phrases where precision is needed, and review flagged content after go-live. Stay within the limits: 2,000 keywords per list, 30 keyword lists per org (L84924-84925).

---

## Gotcha 5: Moderate Experiences Feeds Is Not the Approval Permission

**What happens:** Admins assume the one "Moderate Experiences Feeds" permission lets a person see, approve and delete held content. It opens the Moderation feed of flagged items (apexdev 264 L25687-25688), the audit-trail reports (object_reference 264 L189821) and flag emails (L190716-190719). Editing and deleting pending-review feed items and comments, and changing a comment from PendingReview to Published, are tied to Can Approve Feed Post and Comment or Modify All Data (L136986-136990, L136373-136379); the corpus states the publish step for comments only.

**When it occurs:** When moderators are given only Moderate Experiences Feeds and then cannot publish held posts.

**How to avoid:** Assign both permissions deliberately and record who holds which. UNVERIFIED (2026-10-20): that external Customer Community or Partner Community license users cannot be granted these permissions, and the "community manager role" distinction, are Help-only; verify the license and permission pairing in a sandbox before designing an external moderation team.
