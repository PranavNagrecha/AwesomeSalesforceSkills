# LLM Anti-Patterns — Loyalty Management Setup

## Anti-Pattern 1: Using Non-Qualifying Points for Tier Assessment

**What the LLM generates:** Loyalty program setup with a single "Points" currency configured as both the tier measurement and the redemption currency.

**Why it happens:** A single universal "points" currency is the intuitive model for loyalty programs. LLMs apply this pattern without knowing Salesforce Loyalty Management's two-currency architectural requirement.

**Correct pattern:** Create separate currencies: a qualifying currency (for tier measurement, associated with the Tier Group) and a non-qualifying currency (for redemption). Tier groups read only from their associated qualifying currency — non-qualifying currency is invisible to tier assessment.

**Detection hint:** Program designs with a single currency serving both tier advancement and redemption are using the wrong architecture.

---

## Anti-Pattern 2: Assuming DPE Jobs Run Automatically After Program Setup

**What the LLM generates:** "After setting up the Loyalty Program, tier advancement will work automatically as members accumulate points."

**Why it happens:** Platform automation is often assumed to be self-starting. LLMs don't model the DPE activation requirement as a separate mandatory step.

**Correct pattern:** DPE jobs (Reset Qualifying Points, Aggregate/Expire Fixed Non-Qualifying Points) must be explicitly activated in Setup > Data Processing Engine after program creation. Without activation, no tier processing ever runs.

**Detection hint:** Any setup guide that describes loyalty program configuration without mentioning DPE job activation is incomplete.

---

## Anti-Pattern 3: Associating Multiple Qualifying Currencies with One Tier Group

**What the LLM generates:** A program design where multiple qualifying currencies (spend-based and engagement-based) are both associated with the same tier group for a combined tier score.

**Why it happens:** Combined multi-dimensional scoring for tier advancement seems natural. The platform constraint (one qualifying currency per tier group) is not intuitive.

**Correct pattern:** Each tier group supports exactly one associated qualifying currency. For multi-dimensional tier programs, create separate tier groups with separate qualifying currencies and track membership in each independently.

**Detection hint:** Designs that associate multiple qualifying currencies with a single tier group violate the platform's one-currency-per-tier-group constraint.

---

## Anti-Pattern 4: Activating Only One Partner Loyalty DPE Definition

**What the LLM generates:** Instructions to activate the "Create Partner Ledgers" DPE definition for partner loyalty setup, without mentioning the "Update Partner Balance" definition.

**Why it happens:** One visible DPE definition is found and activated. The second is missed because it's a separate DPE record.

**Correct pattern:** Partner loyalty requires two DPE definitions: "Create Partner Ledgers" AND "Update Partner Balance". Both must be activated. Omitting one results in partner transactions being recorded without balance updates.

**Detection hint:** Partner loyalty setup instructions that mention only one DPE definition are incomplete.

---

## Anti-Pattern 5: Multiple Loyalty Programs on One Experience Cloud Site

**What the LLM generates:** "Configure the Loyalty Member Portal Experience Cloud site and associate it with all your loyalty programs."

**Why it happens:** LLMs model Experience Cloud sites as flexible multi-purpose portals without knowing the one-program-per-site constraint.

**Correct pattern:** A Loyalty Member Portal Experience Cloud site can be associated with exactly one loyalty program. For multiple programs, create separate Experience Cloud sites. If a unified multi-program portal is required, it must be built with custom LWC components, not the standard Loyalty Member Portal template.

**Detection hint:** Any instruction to associate multiple loyalty programs with a single Experience Cloud site is incorrect.
