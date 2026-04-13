# LLM Anti-Patterns — Experience Cloud Deployment Admin

Common mistakes AI coding assistants make when generating or advising on Experience Cloud site deployment.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Advising Deployment of ExperienceBundle Without First Verifying Network and CustomSite Exist in Target

**What the LLM generates:** "Deploy ExperienceBundle to production using the following CLI command: `sf project deploy start --manifest package.xml --target-org production`" — with a `package.xml` that includes only `ExperienceBundle`, or includes both `Network` and `ExperienceBundle` in a single manifest without sequencing.

**Why it happens:** LLMs treat Experience Cloud deployment like any other metadata deployment where a single manifest covers all components. They are not trained to recognize that ExperienceBundle has a hard runtime dependency on an existing Network record in the target org and will fail if that record is absent.

**Correct pattern:**

```
Step 1: Confirm Network record exists in target org
  sf data query \
    --query "SELECT Id, Name, Status FROM Network WHERE Name = 'YourSiteName'" \
    --target-org production

Step 2: If Network is absent, deploy Network and CustomSite first
  sf project deploy start --manifest package-deps.xml --target-org production --wait 30

Step 3: Only after Step 2 succeeds, deploy ExperienceBundle
  sf project deploy start --manifest package-site.xml --target-org production --wait 30
```

**Detection hint:** Flag any response that includes `ExperienceBundle` in a deploy command or manifest without an explicit prior step verifying or deploying `Network` and `CustomSite`. Also flag single-manifest deploys that list both `Network` and `ExperienceBundle` as members without a sequencing note.

---

## Anti-Pattern 2: Including SiteDotCom in the Deployment Package

**What the LLM generates:** A `package.xml` or change set recommendation that includes `SiteDotCom` as a component alongside `ExperienceBundle`, often copied verbatim from a retrieved package output.

**Why it happens:** When an LLM sees a retrieved metadata folder or package.xml containing `SiteDotCom`, it assumes the retrieved output is deployment-ready and includes all components as-is. LLMs do not know that SiteDotCom is automatically included in retrieval output but must be excluded from deployment.

**Correct pattern:**

```xml
<!-- WRONG — do not include SiteDotCom with ExperienceBundle -->
<types>
    <members>CustomerPortal</members>
    <name>SiteDotCom</name>
</types>
<types>
    <members>CustomerPortal</members>
    <name>ExperienceBundle</name>
</types>

<!-- CORRECT — remove SiteDotCom entirely from the deployment manifest -->
<types>
    <members>CustomerPortal</members>
    <name>ExperienceBundle</name>
</types>
```

**Detection hint:** Flag any deployment manifest or change set recommendation that contains both `SiteDotCom` and `ExperienceBundle` as members. Also flag any response that does not mention removing SiteDotCom when describing Experience Cloud site retrieval and redeployment.

---

## Anti-Pattern 3: Treating Deployment Success as Equivalent to Site Being Live

**What the LLM generates:** "Once the deployment completes successfully, your Experience Cloud site will be available to users at https://yourdomain.my.site.com/sitename." or "After the change set deploys, the site will be live."

**Why it happens:** LLMs generalize from standard metadata deployments where deploying a component makes it immediately active. They are not aware of the Experience Cloud-specific requirement that ExperienceBundle deployments always land in Draft status and require an explicit Publish action before end users can access the site.

**Correct pattern:**

```
After deployment completes:
1. Log in to the target org
2. Navigate to Setup > Digital Experiences > All Sites
3. Click Builder next to the deployed site
4. In Experience Builder, click Publish

OR via Connect REST API:
POST /services/data/v63.0/connect/communities/{communityId}/publish
Authorization: Bearer {accessToken}
```

**Detection hint:** Flag any response that claims the site will be "live," "available," or "accessible" immediately after deployment without including an explicit Publish step. Also flag responses that do not mention Draft status after ExperienceBundle deployment.

---

## Anti-Pattern 4: Advising That Enable Experience Bundle Metadata API Is a One-Time Global Setting

**What the LLM generates:** "You only need to enable the Experience Bundle Metadata API checkbox once in your Dev Hub or production org. All sandboxes and scratch orgs will inherit this setting."

**Why it happens:** LLMs incorrectly generalize from other Salesforce org-level settings that do propagate during sandbox refresh or scratch org creation. They do not know that this specific checkbox is org-local and not automatically inherited.

**Correct pattern:**

```
The Enable Experience Bundle Metadata API checkbox must be enabled independently in:
- Every sandbox (including after each sandbox refresh)
- Every scratch org (cannot be set via scratch org definition JSON; must be set post-create)
- Production org (if deploying ExperienceBundle directly to production)

Navigation: Setup > Digital Experiences > Settings >
  Enable Experience Bundle Metadata API [checkbox]

Add this step to:
- Sandbox post-refresh runbook
- Scratch org post-create setup script
- Pre-deployment checklist for every target org
```

**Detection hint:** Flag any response that says this setting "inherits," "propagates," "syncs," or "is already enabled" in a target org without first verifying it. Also flag responses that omit this step from sandbox setup or scratch org provisioning instructions.

---

## Anti-Pattern 5: Omitting Guest User Profile from the Deployment Plan for Sites with Public/Unauthenticated Access

**What the LLM generates:** A deployment plan that includes `Network`, `CustomSite`, and `ExperienceBundle` but does not include the site's Guest User Profile — with no mention that guest user permissions must be separately retrieved and deployed.

**Why it happens:** LLMs treat ExperienceBundle as the complete representation of the site, not realizing that the Guest User Profile is a separate `Profile` metadata component that controls all unauthenticated visitor access. The Guest User Profile is not listed in Experience Builder's component view, so LLMs trained on UI-centric descriptions miss it entirely.

**Correct pattern:**

```
Guest User Profile must be explicitly included in the deployment plan:

1. Identify the Guest User Profile name:
   Format: "[SiteName] Profile" (e.g., "CustomerPortal Profile")

2. Retrieve it as a Profile metadata component:
   sf project retrieve start \
     --metadata "Profile:CustomerPortal Profile" \
     --target-org source-sandbox

3. Include it in the dependency deploy step (before or with Network/CustomSite):
   package-deps.xml:
   <types>
       <members>CustomerPortal Profile</members>
       <name>Profile</name>
   </types>

4. After deployment, manually verify in target org:
   Setup > Experience Cloud Sites > [Site] > Workspaces > Administration > Guest User Profile
   Check: Apex Class Access, Object Permissions, Field-Level Security
```

**Detection hint:** Flag any Experience Cloud deployment plan for a site with guest/unauthenticated access that does not include the Guest User Profile as a component. Also flag responses that say "ExperienceBundle includes all site configuration" without specifying that the Guest User Profile is a separate metadata component.

---

## Anti-Pattern 6: Recommending a Single Monolithic Manifest for First-Time Site Deployment

**What the LLM generates:** "Create one `package.xml` with all components — Apex classes, Network, CustomSite, and ExperienceBundle — and run a single deploy command. This is the simplest approach."

**Why it happens:** LLMs optimize for simplicity and minimal steps. A single manifest is conceptually simpler than multiple sequenced manifests, so LLMs default to it without accounting for the metadata ordering constraints specific to ExperienceBundle.

**Correct pattern:**

```
For first-time Experience Cloud site deployment:

Manifest 1 (package-deps.xml) — deploy first:
- ApexClass members
- CustomObject members
- CustomField members (via CustomObject)
- Profile members (including Guest User Profile)
- PermissionSet members
- Network member
- CustomSite member

Manifest 2 (package-site.xml) — deploy only after Manifest 1 succeeds:
- ExperienceBundle member

Rationale: ExperienceBundle requires Network to exist in target at deploy time.
A single manifest does not guarantee commit ordering within the deploy.
```

**Detection hint:** Flag any first-time Experience Cloud site deployment recommendation that uses a single manifest or single change set containing both `Network`/`CustomSite` and `ExperienceBundle` without an explicit sequencing note or confirmation that Network already exists in the target org.
