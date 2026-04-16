# LLM Anti-Patterns — Data Storytelling Design

Common mistakes AI coding assistants make when generating or advising on data storytelling in Salesforce.

---

## Anti-Pattern 1: Designing Dashboards Without a Defined Call to Action

**What the LLM generates:** A dashboard design with multiple charts and no narrative text, organized by chart type rather than by the insight the audience needs.

**Why it happens:** LLMs default to "add relevant charts" without asking what decision the dashboard enables.

**The correct pattern:** Before placing any chart, define: "After viewing this, [audience] will [take this action]." The layout and text widgets must make this action obvious without requiring the viewer to synthesize across multiple charts.

**Detection hint:** If the proposed design has no text widget and no single primary message, the design is incomplete.

---

## Anti-Pattern 2: Recommending Smart Data Discovery Narrative as Auto-Embedded

**What the LLM generates:** "Enable Einstein Discovery and the narrative will appear in your CRM Analytics dashboard automatically."

**Why it happens:** LLMs conflate enabling Einstein Discovery stories with automatic narrative injection into dashboards.

**The correct pattern:** The Smart Data Discovery narrative API produces text that must be consumed by custom code (LWC, Visualforce). It does not auto-inject into CRM Analytics dashboards.

**Detection hint:** Any claim that enabling Einstein Discovery automatically adds narrative to existing dashboards is incorrect.

---

## Anti-Pattern 3: Using Multiple Dashboard Tabs Instead of Tableau Story Sheets for Sequential Narrative

**What the LLM generates:** "Create separate dashboard tabs for each step of the story — Introduction, Analysis, Recommendation."

**Why it happens:** LLMs suggest the most familiar Tableau/Salesforce pattern (tabs) without knowing the Story sheet exists.

**The correct pattern:** For sequential narrative, use Tableau Story sheets. They enforce guided sequence, support captions per view, and are designed for presentation mode. Multiple tabs require viewers to discover the sequence themselves.

**Detection hint:** If sequential narrative is the goal and the response suggests multiple dashboard tabs, suggest evaluating Tableau Story sheets instead.

---

## Anti-Pattern 4: Omitting Text Widgets from CRM Analytics Executive Dashboards

**What the LLM generates:** A CRM Analytics dashboard design with only metric tiles and charts, no text widgets.

**Why it happens:** LLMs list visualization elements without considering the narrative context layer.

**The correct pattern:** CRM Analytics executive dashboards must include text widgets with the primary message framed as a statement. Charts provide supporting evidence; text widgets deliver the conclusion.

**Detection hint:** Any CRM Analytics executive dashboard design without text widgets is missing the narrative layer.

---

## Anti-Pattern 5: Applying the Same Layout Pattern Regardless of Audience Role

**What the LLM generates:** A single dashboard template applied identically to executives, managers, and frontline users.

**Why it happens:** LLMs use a single dashboard template without accounting for role-specific information needs.

**The correct pattern:** Executive dashboards prioritize headline metrics (Z-pattern, 30-second readability). Manager dashboards include comparison and drill-down. Frontline dashboards prioritize action triggers and compact metric tiles with filter controls. Each role's design follows the Efficiency principle differently.

**Detection hint:** If audience-specific design is not addressed in the storytelling recommendations, the design is likely optimized for one role but not others.
