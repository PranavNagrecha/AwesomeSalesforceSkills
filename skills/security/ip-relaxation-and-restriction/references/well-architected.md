# Well-Architected Notes — IP Relaxation and Restriction

## Relevant Pillars

- **Security** — Primary pillar. IP restriction is a *network* assumption applied to
  an *identity* problem, and its value scales with how genuinely static the source
  address is. For an integration user calling from a partner's provisioned NAT it is
  a strong, cheap control that makes a leaked credential unusable. For a human
  population it is a weak control with an expensive failure mode, because humans
  move and networks change. The most consequential design decision in this domain is
  which population gets which control — and the most common failure is applying the
  *soft* control (Trusted IP Ranges) while believing it is the hard one.

- **Operational Excellence** — Every IP range is a dependency on somebody else's
  network, with an expiry date nobody in Salesforce controls and no alert when it
  passes. The control degrades silently: a partner rotates a NAT address, the
  nightly job starts failing at 02:00, and the failure looks like a credential
  problem. The operational artifacts that make this survivable are a `description`
  on every range naming its owner and renewal date, a dual-range overlap procedure
  for rotations, and a monitored alert on login failures for integration identities.

- **Reliability** — A hard IP block has an asymmetric failure mode. When it works,
  nothing is observable; when it fails, the affected identity is completely locked
  out with no self-service recovery. On a System Administrator profile that can mean
  a Salesforce Support case measured in days during which nobody can change anything
  in the org. Reliability here means keeping an unrestricted, MFA-protected,
  monitored break-glass path and never letting the control's blast radius include
  its own remedy.

- **Performance** — Narrow but real: IP-restricting a Site guest user's profile
  forces static resources to private caching, and reverting has a documented tail of
  up to 45 days before caches clear.

## Architectural Trade-offs

**Profile Login IP Ranges vs MFA.** These are not alternatives at the same layer.
IP is an assumption about the network; MFA is an assumption about the person. MFA
scales across travel, home working, ISP changes, and partner rotations, and
Salesforce requires it for all logins regardless. IP restriction adds a second,
independent factor that an attacker with valid credentials cannot satisfy remotely —
but only where the address is genuinely fixed. The correct reading is: MFA
everywhere, IP restriction additionally on integration identities.

**Login-time vs per-request enforcement.** The default checks IP at login only,
which leaves an established session portable — the property that makes session
replay work. **Enforce login IP ranges on every request** closes that, and is the
only version of the control that helps during an incident. Its cost is org-wide
scope: the setting activates every Login IP Range on every profile simultaneously,
and users whose address changes mid-session (mobile handoff, VPN reconnect, carrier
NAT rotation) are interrupted. Enabling it is a project — inventory, prune, rehearse
— not a checkbox.

**Per-profile vs per-connected-app scope.** A profile restriction covers every
authentication path for the identities holding it. A connected app's `ipRelaxation`
scopes the decision to one integration, which is useful when one profile serves both
a stable middleware platform and travelling humans. The cost is that the control is
now split across two Setup screens owned by two teams, and an app set to `BYPASS`
silently cancels the profile design. Whichever way you split it, audit both together
or you are auditing neither.

**`ENFORCE_RELAXREFRESH` as the honest middle.** For a long-running background job
that obtained its refresh token from an allowed address but now refreshes from a
rotating egress, this value keeps the initial authorisation IP-gated while letting
refresh happen anywhere. It is a genuine engineering trade rather than a
capitulation, and it is materially narrower than `BYPASS`. Record it as a documented
hole, with the reason, so a future reviewer does not have to reconstruct the
argument.

**Static egress as a contractual term.** Whether IP restriction is available at all
for a partner integration is decided during contracting, not during build. Partners
on cloud platforms can provision static egress if asked early; they usually cannot
retrofit it the week before go-live. Treating "supply a static egress address, IPv4
and IPv6" as a requirement alongside the data contract is the difference between
having this control and pretending to.

## Anti-Patterns

1. **Recording Trusted IP Ranges as an access restriction.** They suppress the
   device-activation challenge; they refuse nothing. An org with Network Access
   ranges and no profile ranges has no IP-based access control at all, whatever the
   security document says.

2. **Hard-locking the System Administrator profile.** No self-service recovery, and
   the lockout can include the only person able to undo it. Use MFA, short sessions,
   and login alerting instead, and keep a monitored break-glass admin.

3. **Designing profile IP ranges without auditing connected app `ipRelaxation`.**
   One `BYPASS` cancels the whole design, and the two settings live on screens owned
   by different teams.

4. **Allow-listing a cloud provider's published range.** It admits everyone with an
   account at that provider. Worse than no control, because it stops the search for
   a real one.

5. **Assuming a removed range closes access.** It prevents the next login. Existing
   sessions and OAuth tokens survive unless per-request enforcement is on, so
   incident response must terminate sessions and revoke tokens explicitly.

6. **Ranges with no `description`.** An undescribed range can never be safely
   removed, because nobody can prove it is dead. The list only grows, and each entry
   is a permanent widening.

7. **IPv4-only ranges for a dual-stack partner.** The integration works until the
   partner's network team enables IPv6, then fails intermittently depending on which
   family each connection picks.

8. **IP-restricting a public Site's guest profile.** If only known addresses should
   reach it, it should not be public — and the change forces private static-resource
   caching with a 45-day tail on reversal.

## Official Sources Used

- Salesforce Security Guide — Restrict Login IP Ranges in the Enhanced Profile User Interface (Setup path, start/end address rule, IPv4-mapped IPv6 range constraint, Partner User five-address cap, edition-dependent location, required permissions, the guest-user static-resource caching note) — https://help.salesforce.com/s/articleView?id=platform.users_profiles_login_ip_ranges.htm&type=5
- Salesforce Security Guide — Session Settings, "Enforce login IP ranges on every request" and its org-wide scope — https://help.salesforce.com/s/articleView?id=platform.admin_sessions.htm&type=5
- Salesforce Security Guide — Device Activation (identity challenge on unrecognised device or address outside a trusted range) — https://help.salesforce.com/s/articleView?id=platform.security_activations.htm&type=5
- Salesforce Security Guide — Set Trusted IP Ranges for Your Organization — https://help.salesforce.com/s/articleView?id=platform.security_networkaccess.htm&type=5
- Salesforce Security Guide — Monitor Login History (Source IP vs Forwarded for IP, and the note that Forwarded for IP is not populated for OAuth and SSO logins) — https://help.salesforce.com/s/articleView?id=platform.security_login_history.htm&type=5
- Salesforce Security Guide — Salesforce Security Basics, "Salesforce requires that all logins use multi-factor authentication (MFA)" — https://help.salesforce.com/s/articleView?id=platform.security_overview.htm&type=5
- Metadata API Developer Guide — ConnectedApp, `ipRelaxation` and its four values — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_connectedapp.htm
- Metadata API Developer Guide — Profile, `loginIpRanges` (`ProfileLoginIpRange[]`, API 17.0 and later) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_profile.htm
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

<!-- UNVERIFIED: the claim that Login IP Ranges are evaluated at login only (and
     therefore that an established session survives an IP change unless "Enforce
     login IP ranges on every request" is enabled) is the necessary reading of
     the documented purpose of that setting, but no Salesforce source consulted
     in this pass states the default session behaviour explicitly. Treat the
     mechanism as documented and the default-session detail as inference. -->
<!-- UNVERIFIED: "Setup → Session Management" as the exact navigation for
     terminating active sessions was not re-verified in this pass. The
     capability exists (the Security Guide references User Sessions and User
     Session Types); confirm the current menu label before putting it in a
     runbook. -->
