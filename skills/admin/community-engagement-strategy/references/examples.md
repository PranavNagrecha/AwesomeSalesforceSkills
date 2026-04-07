# Examples — Community Engagement Strategy

## Example 1: 10-Tier Reputation System for a Technology Support Community

**Context:** A software company launches a customer community for peer support. The goal is deflecting 20% of support case volume within six months. Members help each other by answering questions.

**Problem:** The initial deployment used generic tier names ("Level 1" through "Level 5") with equal point weights for all actions. Members farmed points by posting short, low-quality replies. The leaderboard did not reflect actual expertise. Trusted advisors — who wrote thorough answers — were outranked by members posting volume.

**Solution:**

```
Reputation Configuration — Tech Support Community

Tier | Name                   | Min Points | Max Points
-----|------------------------|------------|------------
1    | Newcomer               | 0          | 99
2    | Explorer               | 100        | 299
3    | Contributor            | 300        | 699
4    | Helper                 | 700        | 1,499
5    | Advisor                | 1,500      | 2,999
6    | Expert                 | 3,000      | 5,999
7    | Trusted Expert         | 6,000      | 9,999
8    | Community Champion     | 10,000     | 19,999
9    | Master                 | 20,000     | 49,999
10   | Legend                 | 50,000     | (no cap)

Point weights per action:
- Post a question:          1 pt
- Write a comment/answer:   2 pts
- Receive a like:           3 pts
- Best answer marked:       10 pts
```

Steps taken:
1. Navigate to Setup > Digital Experiences > All Sites > [Site Name] > Reputation.
2. Enable Reputation for the site.
3. Add 10 tiers. Enter the tier name and minimum point threshold for each level.
4. Edit point weights: set "Receive a like" to 3 and "Best answer" to 10.
5. Save and confirm tier names appear on member profile cards in a test member session.

**Why it works:** Weighting best-answer actions at 10x the base action forces the leaderboard to reflect quality contribution. Role-meaningful tier names ("Trusted Expert", "Legend") signal community standing to other members without requiring them to calculate point totals.

---

## Example 2: Product Ideation Portal with Defined Status Workflow

**Context:** A SaaS company wants to collect structured product feedback through their customer community. Previously, feature requests came in via support tickets with no visibility to other customers on whether ideas were considered.

**Problem:** Ideation was enabled but with no status workflow defined and no assigned owners. Ideas sat at "New" status for months. Customers stopped voting because feedback appeared to disappear into a black hole. Engagement on the ideation section dropped to near zero within 60 days of launch.

**Solution:**

```
Ideation Setup — Product Feedback Portal

Step 1: Enable Ideas
  Setup > Digital Experiences > All Sites > [Site] > Ideas Settings
  Toggle: Enable Ideas = ON

Step 2: Add Ideas Tab to Navigation
  Experience Builder > Navigation > Add Tab > Ideas

Step 3: Create IdeaThemes
  Theme 1: "Mobile App Improvements" — Owner: Sara Chen, Product Manager (Mobile)
  Theme 2: "API & Integration Requests" — Owner: Dev Partnerships Team
  Theme 3: "Reporting & Analytics"     — Owner: Analytics PM

Step 4: Define Status Workflow (per theme)
  Statuses configured:
  - New             (default on submission)
  - Under Review    (PM has read and is evaluating)
  - Planned         (added to roadmap)
  - Implemented     (shipped)
  - Closed — Not Planned (will not pursue; comment required explaining why)

Step 5: Assign Owners and Review Cadence
  Each theme owner reviews and updates statuses on a 30-day cycle.
  Status change must include a comment visible to voters.
```

**Why it works:** The status workflow makes the idea lifecycle visible to members. A monthly cadence for status updates maintains responsiveness signals. The "Closed — Not Planned" status with a required explanation comment preserves trust even when ideas are declined — members see that the team read and considered their input. The Ideas tab in navigation is mandatory; without it the feature is invisible regardless of backend settings.

---

## Anti-Pattern: Launching with No Seed Content and No Onboarding Path

**What practitioners do:** Enable the Experience Cloud site and open it to members without creating any baseline content, without writing a "Start Here" article, and without defining a member onboarding journey.

**What goes wrong:** The first member to arrive sees an empty community. No questions to answer, no articles to read, no ideas to vote on. The empty-state experience communicates that the community is inactive. Activation rates (members who take a first action) remain low in the first 30 days. Once members form the habit of not engaging, reversing the pattern is difficult.

**Correct approach:** Before go-live, seed the community with at minimum:
1. A pinned "Welcome / Start Here" article explaining the community's purpose.
2. 10–15 seeded questions or discussion posts (can be based on FAQ content from support).
3. At least one IdeaTheme with one seed idea already posted by an internal account.
4. A clearly described first-action path for new members: "Introduce yourself in the Welcome thread."

This baseline content gives the first cohort of members something to interact with and signals that the community is active.
