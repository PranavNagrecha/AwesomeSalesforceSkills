# IP Relaxation / Restriction — Gotchas

## 1. Trusted IPs Are Not A Block

Trusted IPs relax the device challenge; they do not block outside
logins. If you want a block, use Profile Login IP Ranges.

## 2. Admin Self-Lockout

Too-tight Profile Login IP Ranges on admin profiles lock admins out
during travel, IP changes, or WFH days. Recovery requires support.

## 3. Dynamic IPs From Cloud Providers

Integration partners on AWS/GCP/Azure may not have a static IP unless
explicitly provisioned (NAT Gateway / Cloud NAT). A dynamic IP range
must either be allow-listed broadly (bad) or the partner must provision
static egress (right).

## 4. Mobile Apps Bypass Expectations

Some mobile login paths can surprise IP checks due to NAT / carrier
proxying. Test mobile explicitly before enforcing.

## 5. Apex Callouts From Salesforce Have Their Own Egress

If an external system IP-restricts Salesforce callouts, use Salesforce's
published IP ranges or configure Named Credential through an egress
proxy.

## 6. IPv6 Handling

Profile Login IP Ranges support IPv6, but integration partners may
present an IPv6 address for some traffic and IPv4 for others. Cover both.

## 7. Login Flows Ignore IP Restrictions In Some Modes

Some login flow contexts (e.g., certain SSO setups) evaluate IP rules
differently. Test the specific login path before declaring safe.

## 8. Changes Take Effect Immediately And Silently

Tighten a range and in-flight users are not kicked, but next login
fails. This is normal — notify users beforehand.
