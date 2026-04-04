# LLM Anti-Patterns — Multi-Language and Translation

## Anti-Pattern 1: Using Picklist Translated Label in Apex or SOQL

**What the LLM generates:** Apex or SOQL that compares a picklist field against the translated label instead of the API value.

**Why it happens:** LLMs use the most natural language form of the value they see in documentation or examples.

**Correct pattern:**
```apex
// WRONG: Spanish translation label in condition
if (opp.StageName == 'Calificación') { } // translated label

// CORRECT: API value always
if (opp.StageName == 'Qualification') { } // API value
```

**Detection hint:** Any picklist comparison using a non-English string where the org default language is English.

---

## Anti-Pattern 2: Hardcoding User-Facing Strings in Validation Rules

**What the LLM generates:** Validation rule error message as a string literal: `"This field is required"`.

**Why it happens:** String literals are the simplest approach and work in single-language orgs.

**Correct pattern:**
Use `$Label.Validation_Message_Name` in the error message field of the validation rule. The label provides translations automatically based on user language.

**Detection hint:** Any validation rule error message that is a plain quoted string rather than a `$Label.*` reference.

---

## Anti-Pattern 3: Translating Experience Cloud via Language-Conditional Rich Text

**What the LLM generates:** A workaround using multiple Rich Text components with conditional visibility based on user locale to show translated content.

**Why it happens:** LLMs find the most obvious conditional visibility workaround without knowing about native Experience Cloud language support.

**Correct pattern:** Use the native Experience Cloud language support: Translation Workbench + Language Switcher component. For content management, use the site's built-in language variant system.

**Detection hint:** Any Experience Cloud page design with multiple components showing/hiding based on `$User.LanguageLocaleKey`.

---

## Anti-Pattern 4: Using System.Label.* in Apex Test Classes Without Language Setup

**What the LLM generates:** Apex test classes that assert on `System.Label.My_Label` expecting the Spanish translation without setting up the test user's language.

**Why it happens:** LLMs do not consider that test methods run as the running user (typically English) unless explicitly configured.

**Correct pattern:**
To test translations in Apex, create a test user with the target language and run the assertion as that user:
```apex
@isTest static void testSpanishLabel() {
    User spanishUser = [SELECT Id FROM User WHERE LanguageLocaleKey = 'es' LIMIT 1];
    System.runAs(spanishUser) {
        System.assertEquals('Valor en español', System.Label.My_Label);
    }
}
```

**Detection hint:** Any Apex test asserting on a Custom Label value without a `System.runAs()` block with a specific language user.

---

## Anti-Pattern 5: Disabling Translation Workbench to Reset Translations

**What the LLM generates:** Advice to disable Translation Workbench as a troubleshooting step or to "reset" the translation state.

**Why it happens:** LLMs suggest disable/enable as a generic troubleshooting pattern without knowing that disabling removes all translations immediately.

**Correct pattern:** Never disable Translation Workbench in production. To remove translations for a specific language, remove that language from the Supported Languages list. To reset individual translations, re-import a corrected translation file.

**Detection hint:** Any recommendation to "disable Translation Workbench" in a production context.
