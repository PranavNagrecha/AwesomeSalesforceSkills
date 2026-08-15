# Examples — Screen Flow Accessibility

Worked examples grounded in what a Screen element can actually express. Every
example names the Flow metadata that carries the semantics, because the recurring
failure in this domain is a team doing accessibility work in CSS and prose when
the platform had a property for it.

**The standard to target:** Salesforce states that "Lightning Experience follows
the internationally recognized best practices in Section 508 of the
Rehabilitation Act and the Web Content Accessibility Guidelines (WCAG) 2.2 Level
AA to the extent possible." Audit against 2.2 AA, not 2.1. The practical delta
for Screen Flows is six criteria that did not exist in 2.1:

| New in WCAG 2.2 | Level | Where it bites in a Screen Flow |
|---|---|---|
| 2.4.11 Focus Not Obscured (Minimum) | AA | A sticky flow footer or a Lightning modal covering the focused field on a small viewport |
| 2.5.7 Dragging Movements | AA | Any custom LWC on a screen using drag-and-drop reordering with no click alternative |
| 2.5.8 Target Size (Minimum) — 24×24 CSS px | AA | Custom icon buttons in a screen component |
| 3.2.6 Consistent Help | A | A multi-screen flow whose help text or support link moves position between screens |
| 3.3.7 Redundant Entry | A | A multi-screen flow that asks for the same value twice instead of carrying it forward in a variable |
| 3.3.8 Accessible Authentication (Minimum) | AA | A flow step that requires a cognitive puzzle to proceed |

WCAG 2.2 also removed 4.1.1 Parsing, which is why an old audit report flagging
duplicate IDs may no longer describe a conformance failure.

---

## Example 1: Help Text Is a Tooltip, Not a Description

**Context:** A "Reason for Refund" text input carries important guidance in the
screen component's Help Text: "Enter the RMA number if one was issued."

**Problem:** `helpText` on a screen field renders as a help icon the user has to
hover or activate. It is discoverable to a sighted mouse user scanning the form,
and it is discoverable to nobody who is not looking for it. Guidance that is
required in order to complete the field correctly is not optional information,
and putting it behind an interaction is a design decision most authors do not
realize they made.

**Solution:** Split the content by whether it is required to complete the field.

```xml
<screens>
    <name>Refund_Details</name>
    <label>Refund Details</label>
    <allowBack>true</allowBack>
    <allowFinish>false</allowFinish>
    <allowPause>true</allowPause>
    <showFooter>true</showFooter>
    <showHeader>true</showHeader>

    <fields>
        <name>Refund_Instructions</name>
        <fieldText>&lt;p&gt;Enter the RMA number if one was issued. If the customer returned the item without an RMA, enter NONE.&lt;/p&gt;</fieldText>
        <fieldType>DisplayText</fieldType>
    </fields>

    <fields>
        <name>Refund_Reason</name>
        <dataType>String</dataType>
        <fieldText>Reason for refund</fieldText>
        <fieldType>InputField</fieldType>
        <helpText>Free-text notes for the finance team. Optional.</helpText>
        <isRequired>true</isRequired>
    </fields>
</screens>
```

**Why it works:** The instruction a user needs in order to answer correctly is a
Display Text field immediately before the input, in the reading order, available
to everyone. The Help Text keeps only genuinely supplementary content — the kind
where missing it costs nothing.

**The test to apply:** if a user who never opens the help icon can still complete
the field correctly, the content belongs in Help Text. If they cannot, it belongs
in the screen.

---

## Example 2: Wrong vs Right — Required Fields

**Wrong:**

```xml
<fields>
    <name>Postal_Code</name>
    <dataType>String</dataType>
    <fieldText>Postal code *</fieldText>
    <fieldType>InputField</fieldType>
    <isRequired>false</isRequired>
</fields>
```

The asterisk in the label is a visual convention with no semantics behind it. A
screen reader announces "Postal code star, edit text." The field is not
programmatically required, so no assistive technology announces it as required,
no browser validation fires, and the flow's own enforcement — if any — lives in a
Decision several elements later where the error is disconnected from the field.

**Right:**

```xml
<fields>
    <name>Postal_Code</name>
    <dataType>String</dataType>
    <fieldText>Postal code</fieldText>
    <fieldType>InputField</fieldType>
    <isRequired>true</isRequired>
    <validationRule>
        <errorMessage>&lt;p&gt;Enter a postal code in the format A1A 1A1.&lt;/p&gt;</errorMessage>
        <formulaExpression>REGEX({!Postal_Code}, "[A-Za-z][0-9][A-Za-z] ?[0-9][A-Za-z][0-9]")</formulaExpression>
    </validationRule>
</fields>
```

**Why it works:** `isRequired` produces the platform's own required semantics —
the marker and the announcement come from the component, consistently, in every
language the org is translated into. `validationRule` on the field attaches the
error to the field it belongs to, so the message is announced in context rather
than appearing as free-floating text elsewhere on the page.

**The `errorMessage` is a string you write, so write it as an instruction.**
"Invalid" tells a screen reader user nothing they can act on. "Enter a postal code
in the format A1A 1A1" tells them exactly what to do, and reads equally well
whether it is announced or seen.

---

## Example 3: Conditional Visibility Moves Content Under the User

**Context:** A "Do you have a promo code?" checkbox reveals a promo code input
below it via a component visibility rule.

**Problem:** Revealing a field changes the DOM after the page has been read. A
screen reader user who has already navigated past that point does not
automatically learn that something appeared; a magnification user may have the
new content outside their viewport entirely. The interaction feels obvious when
you can see the whole form and is invisible when you cannot.

**Solution:**

```xml
<fields>
    <name>Has_Promo_Code</name>
    <dataType>Boolean</dataType>
    <fieldText>I have a promo code</fieldText>
    <fieldType>InputField</fieldType>
    <isRequired>false</isRequired>
</fields>

<fields>
    <name>Promo_Code</name>
    <dataType>String</dataType>
    <fieldText>Promo code</fieldText>
    <fieldType>InputField</fieldType>
    <isRequired>false</isRequired>
    <visibilityRule>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>Has_Promo_Code</leftValueReference>
            <operator>EqualTo</operator>
            <rightValue>
                <booleanValue>true</booleanValue>
            </rightValue>
        </conditions>
    </visibilityRule>
</fields>
```

Three design rules make this usable:

1. **The revealed field is immediately after its trigger in the field order.** If
   the trigger is at the top of the screen and the revealed field is at the
   bottom, sequential navigation reaches it far from the interaction that caused
   it.
2. **The label of the trigger states what will happen.** "I have a promo code" is
   better than "Promo code?" because it describes an outcome.
3. **Nothing revealed is required unless its trigger makes it so.** A field that
   appears and is simultaneously required creates a validation failure the user
   may never see the cause of.

**Why it works:** It keeps the reveal adjacent in the reading order, which is the
only part of the problem the flow author controls. The announcement behaviour of
the reveal itself belongs to the component and to the platform.

**Where this breaks down:** a reveal that moves *existing* content — pushing the
Next button below the fold on a small viewport — can put the focused element
under a sticky footer, which is WCAG 2.2's 2.4.11 Focus Not Obscured. Test
conditional reveals at a narrow viewport, not just at desktop width.

---

## Example 4: Multi-Column Sections and the Reading Order

**Context:** A screen uses a two-column section to place "First name" and "Last
name" side by side, and below them "Address line 1" spanning both columns.

**Problem:** Multi-column layouts in a Screen Flow are built from
`RegionContainer` and `Region` fields, and the DOM order is the order the regions
and their children appear in the metadata — not the visual grid position. Reorder
the fields for a nicer visual balance and the tab order can start going right,
then left, then down, then back up.

**Solution:** Author the metadata in reading order and let the layout follow.

```xml
<fields>
    <name>Name_Section</name>
    <fieldType>RegionContainer</fieldType>
    <fields>
        <name>Name_Column_1</name>
        <fieldType>Region</fieldType>
        <fields>
            <name>First_Name</name>
            <dataType>String</dataType>
            <fieldText>First name</fieldText>
            <fieldType>InputField</fieldType>
            <isRequired>true</isRequired>
        </fields>
    </fields>
    <fields>
        <name>Name_Column_2</name>
        <fieldType>Region</fieldType>
        <fields>
            <name>Last_Name</name>
            <dataType>String</dataType>
            <fieldText>Last name</fieldText>
            <fieldType>InputField</fieldType>
            <isRequired>true</isRequired>
        </fields>
    </fields>
</fields>
```

**Why it works:** first column then second column, matching left-to-right reading
for an LTR locale, with no reliance on CSS ordering.

**The verification step, which takes 30 seconds:** open the screen and press Tab
repeatedly without touching the mouse. Write down the order you land in. If it
does not match the order you would read the screen aloud, the layout is wrong —
and no amount of labelling fixes it.

**The locale caveat:** an org with RTL languages enabled gets a mirrored visual
layout from the same DOM order, which is correct. Do not "fix" the metadata order
to compensate for what RTL rendering does.

---

## Example 5: A Keyboard-Only Audit Script You Can Hand to QA

**Context:** A five-screen onboarding flow needs an accessibility sign-off and
the team has no dedicated accessibility tester.

**Problem:** Automated checkers catch a minority of real failures — they are good
at missing alt text and colour contrast and blind to focus order, announcement
quality, and whether an error is reachable. A manual script that anyone can run
catches more, provided it is specific enough to produce the same result twice.

**Solution:**

```text
SCREEN FLOW KEYBOARD AUDIT — <Flow API Name>, version <N>
Run in: Lightning Experience AND Experience Cloud (if the flow is embedded there)
Viewport: run once at 1280px, once at 400px wide

For each screen:
 [ ] Tab from the top. Record the order of every stop.
     PASS if it matches the order you would read the screen aloud.
 [ ] At every stop, the focus indicator is visible and not covered by the
     flow footer, a modal, or a sticky header.      (WCAG 2.2 - 2.4.11)
 [ ] Every interactive control is reachable by Tab / Shift-Tab.
     Any control reachable only by mouse is a FAIL, no exceptions.
 [ ] Radio groups: arrow keys move within the group, Tab exits it.
 [ ] Every input announces a label, and required inputs announce as required.
     PASS only if the requiredness comes from the component, not from an
     asterisk in the label text.
 [ ] Submit the screen with a deliberately invalid value.
     - The error is announced, not only shown.
     - The error text says what to do, not that something is wrong.
     - Focus lands somewhere from which the error is reachable.
 [ ] Any content revealed by a conditional visibility rule appears immediately
     after the control that revealed it in tab order.
 [ ] No custom control smaller than 24x24 CSS pixels.  (WCAG 2.2 - 2.5.8)
 [ ] No interaction that requires dragging without a click alternative.
                                                       (WCAG 2.2 - 2.5.7)
 [ ] No value is asked for twice across screens that the flow already holds
     in a variable.                                    (WCAG 2.2 - 3.3.7)

Then, once, with a screen reader (NVDA + Firefox, or VoiceOver + Safari):
 [ ] Walk the entire flow. Log every stop where the announcement does not tell
     you what the control is, what state it is in, and what will happen.
```

**Why it works:** every line has a binary outcome and names the criterion behind
it, so two people running it agree and a failure maps to something specific
enough to fix. The "run it in both containers" line is not padding — see
`references/gotchas.md` on rendering differences between Lightning Experience and
Experience Cloud.

---

## Anti-Pattern: Placeholder Text as the Label

**What practitioners do:** Leave `fieldText` sparse and put the real guidance in
placeholder text, because the form looks cleaner.

**What goes wrong:** The placeholder disappears the moment the user types, so
anyone who is interrupted mid-form loses the only description of what the field
wanted. Placeholder contrast is deliberately low, which fails contrast
requirements for text that is doing a label's job. And a screen reader's
treatment of placeholder text is inconsistent across combinations, so some users
hear "edit text" and nothing else.

**Correct approach:** `fieldText` is the label and it is always visible. A
placeholder may carry an *example* of the expected format — never the name of the
field and never the instruction.

---

## Anti-Pattern: Colour as the Only Signal

**What practitioners do:** Style errors red, valid states green, and required
markers red, and consider the state communicated.

**What goes wrong:** It fails for colour-blind users, in high-contrast mode, on a
monochrome print, and for every screen reader user. WCAG 1.4.1 Use of Colour is
explicit that colour cannot be the sole visual means of conveying information.

**Correct approach:** state is carried by text, and colour reinforces it. Use
`isRequired` so the required semantics come from the component; use
`validationRule` with an `errorMessage` written as an instruction so the error is
text attached to its field. Then style it however you like — the styling is now
redundant rather than load-bearing.

---

## Anti-Pattern: Dropping in a Custom LWC and Assuming the Platform Covers It

**What practitioners do:** Add a `ComponentInstance` field pointing at a custom
LWC, and treat the screen's accessibility as unchanged because the rest of the
screen uses standard components.

**What goes wrong:** Standard screen components carry label association, required
semantics, and error announcement because Salesforce built them that way. A
custom component carries whatever its author implemented. Everything inside it —
labels, focus management, ARIA, keyboard interaction, target size — is now the
component's responsibility, and the flow author usually did not write it and
cannot see it.

**Correct approach:** treat every `ComponentInstance` on the screen as a separate
audit scope. `lwc/lwc-accessibility` owns the component's internals; this skill's
boundary is the screen. What belongs to the flow author is knowing which fields
on the screen are `ComponentInstance` and refusing to sign off a screen
containing an unaudited one.

---

## Anti-Pattern: Auditing Only in Lightning Experience

**What practitioners do:** Test the flow in Lightning Experience, pass it, and
ship it to an Experience Cloud site.

**What goes wrong:** The two containers apply different themes, different SLDS
versions, and different surrounding page structure. Contrast that passed against
the LEX background can fail against a site's brand colours; focus order can
change because the flow is now inside the site's page structure; and a sticky
site header can obscure the focused element in a way LEX never did.

**Correct approach:** audit in every container the flow is actually published to.
It is the same script, run twice, and it is where a meaningful share of real
failures live.
