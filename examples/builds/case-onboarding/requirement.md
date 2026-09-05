# Requirement — Acme Software case intake on Service Cloud

Requester: Acme Software, B2B support team. Today support runs from a shared mailbox.
We are moving to Service Cloud and need case intake set up end to end.

- Cases arrive by email to support@acme.example (roughly 400 a day) and from a form on our
  website (roughly 60 a day). Agents also log about 20 cases a day by hand. There is no phone
  channel. Finance queries arrive at billing@acme.example and should be worked by Finance.
- Within the first minute of a case being created it must have an owner, the customer must
  receive an acknowledgement with the case number, the SLA clock must be running on the right
  calendar, and priority must be set from what the form or email tells us.
- Teams: Tier 1 (12 agents across EMEA and the US, membership changes monthly), Tier 2
  (4 engineers), Billing (2 finance staff). Tier 1 should get work pushed to them when they
  are available; Billing and Tier 2 pick from a list.
- SLA: Premier accounts get a first response within 4 business hours, standard accounts within
  1 business day. Anything untouched for 8 business hours escalates to Tier 2. Clocks pause on
  weekends and regional holidays. EMEA works London 08:00–18:00, the US works New York
  08:00–20:00. Severity 1 outages are 24/7 and never pause.
- Replies to customers go from support@ for general cases and from billing@ for finance cases.
- We must be able to prove it works in a sandbox before customers see it.

Out of scope for this phase: phone/telephony, chat, knowledge base, customer portal.
