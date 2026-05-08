# Examples — Mobile Publisher

## Example 1: Branded partner-portal app for a wholesale distributor

**Context:** A wholesale distributor runs a partner Experience Cloud site where ~3,000 dealers place orders, look up inventory, and submit warranty claims. They want a branded mobile app — own logo, own brand on the App Store — so dealers don't see "Salesforce" branding and the app feels like a first-party tool. Login uses SSO to the dealer's existing account on the company's IdP.

**Problem:** They cannot use the standard Salesforce Mobile App because that would expose Salesforce branding on the dealer's home screen and is not searchable under the customer's brand on the App Store.

**Solution:**

1. Procure Mobile Publisher (Experience Cloud) license tied to the partner site.
2. Asset bundle: app icon (1024×1024 iOS no-alpha, 512×512 Android, 432×432 adaptive layers), splash variants, primary/accent hex colors matching brand guidelines.
3. Push: customer's Apple Developer team generates an APN Auth Key (`.p8`) — Key ID + Team ID + bundle ID `com.distributor.dealer` configured in Mobile Publisher Settings. FCM service account JSON for Android.
4. Identity: SSO via Experience Cloud Login flow + the customer's IdP. App Store reviewer credentials = a sandbox dealer account with a 6-digit code that bypasses the IdP MFA challenge for the duration of review.
5. Account-deletion path added to Experience Cloud as a Lightning page — surfaces "Delete my account" with a 30-day soft-delete and confirmation email.
6. TestFlight + Play Internal Testing distribution to 5 inhouse testers + 5 dealer testers. Push and deep-link verified end-to-end.
7. Production submission. Store listing emphasizes dealer-portal capability without using "Salesforce" in the listing copy.

**Why it works:** The brand is the customer's, the underlying experience is the existing partner site (no rebuild), push and deep links work because they were tested before submission, and the App Store review passes because the reviewer can complete the login flow and the account-deletion path satisfies the policy requirement.

---

## Example 2: Field Service technician app with custom branding

**Context:** A national HVAC service company runs Field Service Lightning for 1,200 technicians. They want the FSL Mobile experience but with their company brand instead of "Salesforce Field Service." The technicians use the app for offline scheduling, asset photos, and work-order completion.

**Problem:** Standard FSL Mobile carries Salesforce branding. The company wants a recruiting and culture story that includes "use our company-branded app on the job," and the standard app conflicts with that.

**Solution:**

1. Procure Mobile Publisher (Field Service) license — distinct from Experience Cloud Mobile Publisher SKU.
2. Confirm all required FSL features (offline data, photo upload, scheduled work order assignment) are enabled in the underlying FSL configuration *before* engaging Mobile Publisher. Mobile Publisher inherits feature flags; disabling something in FSL disables it in the branded app too.
3. Asset bundle and store listing as Example 1.
4. Distribution model: enterprise distribution via Apple Developer Enterprise Program. Reasoning: the app is for employees only, not the public, so Apple's enterprise program (private to the company) avoids the App Store review process entirely.
5. MDM rollout: app pushed to managed iPads via Intune. No app-store search; no public store listing.
6. Push: APN Auth Key + FCM as Example 1, but signed under the Enterprise certificate.

**Why it works:** Field Service Mobile Publisher is the right SKU because the source experience is FSL Mobile, not Experience Cloud. Enterprise distribution avoids the App Store review process that's irrelevant for an employee-only app. The branding satisfies the recruiting / culture goal without rebuilding the FSL flow.

---

## Example 3: When the standard Salesforce Mobile App is the right answer

**Context:** A 250-seat sales-only Salesforce org wants their reps to "have a Salesforce app on their phone." There is no external user audience; only internal sales reps and managers will use it.

**Problem:** Reaching for Mobile Publisher here is over-spec. The standard Salesforce Mobile App is free, fully customizable through Lightning App Builder + mobile navigation menus, and reps already have it via the App Store with their employee credentials.

**Solution:**

- Use the standard Salesforce Mobile App. Customize through Lightning App Builder, mobile navigation, and quick actions.
- For branding inside the app, use App Manager to set the app brand color and logo on the loading screen.
- Skip Mobile Publisher entirely; the SKU cost and operational burden (resubmission cadence, push certificates, store listings) is not justified for an internal-only audience.

**Why it works:** The mobile-app surface area for internal reps is identical to standard Salesforce Mobile. Mobile Publisher's value is *external-facing branding and store presence*, neither of which applies here.

---

## Anti-Pattern: Treating Mobile Publisher as a generic mobile-app builder

**What practitioners do:** A team buys Mobile Publisher with the expectation that they can build "any" mobile app — embedded screens with custom React Native, custom Apex-driven logic outside Experience Cloud, third-party SDK integration unrelated to Salesforce.

**What goes wrong:** Mobile Publisher requires the source to be an Experience Cloud site or Field Service mobile flow. Custom screens outside that scope are not supported. Plugin / native-module additions are limited to what the Mobile Publisher template ships with; there is no general "add my own native code" path. Teams discover the constraint after procurement and end up either rebuilding the experience inside Experience Cloud (slow) or going custom-native (Mobile Publisher SKU now sunk cost).

**Correct approach:** Confirm the source experience and the capability set *before* procurement. If the requirement is "fully custom mobile app with native modules," Mobile Publisher is the wrong tool and a custom-native build (or hybrid framework like Capacitor) is the right answer.
