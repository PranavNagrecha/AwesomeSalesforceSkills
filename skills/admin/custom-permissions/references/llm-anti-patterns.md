# LLM Anti-Patterns — Custom Permissions

Common mistakes AI coding assistants make when generating or advising on Salesforce Custom Permissions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Routing a custom permission grant through a profile

**What the LLM generates:** "Add the custom permission to the Sales User profile so all sales reps get access." (Or, just as often, the over-correction: "custom permissions cannot be assigned to profiles at all.")

**Why it happens:** LLMs repeat the widely-copied claim that profiles cannot carry custom permissions. Both the claim and its opposite are wrong as stated. `Profile.customPermissions` is a real Metadata API field of type `ProfileCustomPermissions[]`, available in API version 31.0 and later -- the same version and the same `enabled` + `name` shape as `PermissionSet.customPermissions`. A profile grant deploys. It is still the wrong design, because the grant then rides the profile's implicit permission set and never appears in the permission's Permission Sets related list.

**Correct pattern:**

```
Grant through a Permission Set:
1. Create or edit a Permission Set.
2. Custom Permissions → Edit → move from Available to Enabled.
3. Assign the Permission Set to the users who need the capability.

Why not a Profile:
- The grant is invisible in Setup > Custom Permissions > Permission Sets.
- It cannot be revoked without editing the profile every user shares.
- It cannot be time-limited via permission set expiration.
- It surfaces only as PermissionSet.IsOwnedByProfile = true in a
  SetupEntityAccess query.

Do NOT say "profiles do not have custom permissions" — the metadata
element exists and deploys. Say "do not grant through profiles."
```

**Detection hint:** Flag both directions. Search for `custom permission` near `profile`: an output that assigns one to a profile is a design error; an output that claims the platform forbids it is a factual error. Correct output recommends a permission set *and* explains that a profile grant is possible but hidden.

---

## Anti-Pattern 2: Using the wrong syntax for checking custom permissions in formulas

**What the LLM generates:** "Use `$Permission.My_Custom_Permission` in your validation rule to check if the user has the permission."

**Why it happens:** LLMs get close but hallucinate the exact syntax, in two directions. First, they append `__c` as if the permission were a custom field: the correct reference is `$Permission.Enable_Discount_Override`, with no suffix. A custom permission's `DeveloperName` cannot even contain two consecutive underscores, so `__c` is not a legal part of the name. Second, and more damaging because it fails silently, they reuse the formula spelling in a Lightning page component-visibility filter or an In-App Guidance `uiFormulaRule`, where the required grammar carries an extra segment: `{!$Permission.CustomPermission.Enable_Discount_Override}`.

**Correct pattern:**

```
Checking custom permissions by context:

Validation Rule / Formula Field:
  $Permission.Enable_Discount_Override
  (No __c suffix — use the API name exactly as defined)

Apex:
  FeatureManagement.checkPermission('Enable_Discount_Override')

Flow:
  Create a Formula resource, Return Type Boolean, value
  $Permission.Enable_Discount_Override
  then reference that resource in the Decision element.
  ($Permission is not valid directly in a condition row.)

Visualforce:
  {!$Permission.Enable_Discount_Override}

LWC:
  import hasPerm from
    '@salesforce/customPermission/Enable_Discount_Override';
  (Resolves to true or undefined — never false.)

Lightning page component visibility / In-App Guidance:
  {!$Permission.CustomPermission.Enable_Discount_Override}
  (Note the extra CustomPermission. segment. App, Home,
   and record pages only.)
```

**Detection hint:** Two regexes. `\$Permission\.\w+__c` catches the bogus `__c` suffix. `leftValue>\{!\$Permission\.(?!CustomPermission\.|StandardPermission\.)` catches the formula spelling used inside a component-visibility or `uiFormulaRule` criterion, where it will evaluate to nothing rather than error.

---

## Anti-Pattern 3: Confusing custom permissions with permission set permissions (CRUD/FLS)

**What the LLM generates:** "Create a custom permission to give users read access to the Invoice object."

**Why it happens:** LLMs conflate custom permissions with CRUD/FLS permissions. Custom permissions are boolean feature gates -- they control access to a named capability (e.g., "can use the discount override button"), not object or field access. Object and field access is controlled by CRUD and FLS settings on profiles and permission sets.

**Correct pattern:**

```
Custom permissions vs CRUD/FLS:
- CRUD/FLS (on profiles/permission sets): controls which objects and
  fields a user can Create, Read, Update, Delete.
- Custom permissions: boolean flag that gates a feature or capability.
  Checked in validation rules, formulas, Apex, and Flow.

Use custom permissions for:
- Feature toggles ("Show Beta Feature")
- Business rule exceptions ("Allow Discount Override")
- UI visibility gates ("Show Advanced Reporting Tab")

Do NOT use custom permissions for object or field access control.
```

**Detection hint:** If the output creates a custom permission to control object or field access, it is using the wrong mechanism. Search for `read access`, `edit access`, or `CRUD` combined with `custom permission`.

---

## Anti-Pattern 4: Not considering the API name immutability before creation

**What the LLM generates:** "Create a custom permission named 'Test Permission' and we can rename it later."

**Why it happens:** LLMs treat custom permission creation as low-stakes. The API name of a custom permission cannot be changed after creation. Every reference in validation rules, formulas, Apex, and Flow uses the API name. Renaming requires creating a new custom permission, updating all references, and deleting the old one.

**Correct pattern:**

```
Before creating a custom permission:
1. Choose the API name carefully — it is permanent.
2. Follow a naming convention:
   - Enable_[Feature_Name] for feature gates.
   - Allow_[Action_Name] for business rule exceptions.
   - Show_[UI_Element] for UI visibility controls.
3. Document all locations that will reference the permission:
   - Validation rules, formula fields, Apex classes, Flow decisions.
4. Do NOT use generic names like "Test" or "Temp" — they become permanent.
```

**Detection hint:** If the output creates a custom permission with a vague or temporary name without warning about immutability, the naming risk is unaddressed. Search for `rename` or temporary-sounding names like `Test`, `Temp`, `Debug`.

---

## Anti-Pattern 5: Forgetting to check the custom permission in all relevant enforcement points

**What the LLM generates:** "Create a custom permission for the discount override and check it in the validation rule."

**Why it happens:** LLMs implement the check in one place but forget other enforcement points. If a custom permission gates a feature, it may need to be checked in the validation rule, the page layout visibility (Dynamic Forms), the Flow decision, the Apex controller, and the LWC conditional rendering. Missing an enforcement point creates a bypass.

**Correct pattern:**

```
Check custom permissions at ALL enforcement points:
1. Validation Rule: prevent data saves that violate the gate.
   NOT($Permission.Enable_Discount_Override) && Discount__c > 0.2
2. Dynamic Forms: hide the field entirely from non-permitted users.
   Visibility filter: $Permission.Enable_Discount_Override = true.
3. Flow: Decision element gating the branch that performs the action.
4. Apex: FeatureManagement.checkPermission('Enable_Discount_Override')
   before executing privileged logic.
5. LWC: wire an Apex method that checks the permission and conditionally
   render the UI component.

Missing any layer means the feature gate has a hole.
```

**Detection hint:** If the output checks the custom permission in only one location (e.g., only the validation rule) without mentioning other enforcement points, the gate may be bypassable. Count the number of enforcement points mentioned.
