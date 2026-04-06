# Examples — Lead Data Import and Dedup

## Example 1: Trade Show CSV Import With Pre-Normalization

**Context:** A marketing team imports a 3,000-record CSV from a trade show badge-scan vendor. The file has inconsistent email casing, company names with varying abbreviations, and approximately 15% of records with no email address. The org uses Data Import Wizard with Email as the dedup field.

**Problem:** Without normalization, email case mismatches cause the wizard to insert records it should update. Records with no email are always inserted as new, creating instant duplicates for any returning attendee who did not provide email. After a prior import, the org accumulated ~400 duplicates in two days.

**Solution:**

Pre-import normalization script (Python, runs locally before upload):

```python
import csv
import re

def normalize_phone(raw):
    """Strip all non-digit characters from a phone number."""
    digits = re.sub(r'\D', '', str(raw))
    return digits if digits else ''

def normalize_email(raw):
    """Lowercase and strip whitespace from email."""
    return str(raw).strip().lower()

def normalize_company(raw):
    """Remove common suffixes for consistent matching."""
    raw = str(raw).strip()
    for suffix in [', Inc.', ' Inc.', ', LLC', ' LLC', ', Ltd', ' Ltd', ', Ltd.']:
        if raw.endswith(suffix):
            raw = raw[:-len(suffix)].strip()
    return raw

input_file = 'tradeshow_raw.csv'
output_file = 'tradeshow_normalized.csv'

with open(input_file, newline='', encoding='utf-8') as infile, \
     open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    seen_emails = set()
    for row in reader:
        row['Email'] = normalize_email(row.get('Email', ''))
        row['Phone'] = normalize_phone(row.get('Phone', ''))
        row['Company'] = normalize_company(row.get('Company', ''))
        # Remove exact-email duplicates within the file itself
        if row['Email'] and row['Email'] in seen_emails:
            continue
        if row['Email']:
            seen_emails.add(row['Email'])
        writer.writerow(row)
```

After normalization, upload `tradeshow_normalized.csv` using Data Import Wizard:
- Object: Leads
- Action: Add new and update existing records
- Match by: Email
- Map standard fields (First Name, Last Name, Email, Phone, Company, Lead Source = Trade Show)

**Why it works:** Lowercasing email removes case-mismatch false negatives. Deduplicating within the file before upload eliminates duplicate rows that the wizard would insert because it only matches against existing Salesforce records, not against other rows in the same file. Records with no email are still inserted (no fix for this in the wizard — route them to a manual review queue via Assignment Rule after import).

---

## Example 2: Web-to-Lead Duplicate Detection With After-Insert Apex Trigger

**Context:** A B2B company runs a content download form via Web-to-Lead. Prospects frequently submit the form multiple times. The marketing team enabled a Lead Duplicate Rule set to "Block" but discovered it was not preventing duplicates — leads were still being created for repeat submitters.

**Problem:** Web-to-Lead POST requests bypass the Duplicate Rule blocking action. Every form submission creates a new Lead record regardless of the rule. The Duplicate Record Set is created, but the lead insert is not prevented. The sales team was receiving multiple assignment notifications for the same prospect.

**Solution:**

After-insert Apex trigger that calls `findDuplicates()` and flags records for routing:

```apex
trigger LeadWebDuplicateCheck on Lead (after insert) {
    // Only process leads with an email (required for reliable matching)
    List<Lead> leadsWithEmail = new List<Lead>();
    for (Lead l : Trigger.new) {
        if (String.isNotBlank(l.Email)) {
            leadsWithEmail.add(l);
        }
    }
    if (leadsWithEmail.isEmpty()) return;

    Datacloud.FindDuplicatesResult[] results =
        Datacloud.DuplicateRule.findDuplicates(leadsWithEmail);

    List<Lead> toUpdate = new List<Lead>();
    for (Integer i = 0; i < results.size(); i++) {
        Boolean isDuplicate = false;
        for (Datacloud.DuplicateResult dr : results[i].getDuplicateResults()) {
            if (!dr.getMatchResults().isEmpty()) {
                isDuplicate = true;
                break;
            }
        }
        if (isDuplicate) {
            Lead l = new Lead(Id = leadsWithEmail[i].Id);
            l.Duplicate_Status__c = 'Potential Duplicate';
            l.OwnerId = Label.Dedup_Queue_Id; // custom label holding queue ID
            toUpdate.add(l);
        }
    }
    if (!toUpdate.isEmpty()) {
        update toUpdate;
    }
}
```

Assignment Rule routes non-duplicate leads to the standard territory queue. Duplicate-flagged leads go to a data steward queue for review and merge.

**Why it works:** The after-insert trigger fires regardless of the insert pathway (Web-to-Lead, API, UI), giving uniform coverage. `findDuplicates()` evaluates all active Duplicate Rules on Lead. Routing to a separate queue prevents duplicate leads from being worked by two different reps simultaneously while the dedup decision is pending.

---

## Anti-Pattern: Relying on Duplicate Rule "Block" for API or Web-to-Lead Channels

**What practitioners do:** Configure a Lead Duplicate Rule with action "Block" and assume all duplicate leads are prevented from entering the org across all channels.

**What goes wrong:** Web-to-Lead submissions, REST API inserts, and Apex `Database.insert()` calls do not honor the blocking action unless the calling code explicitly handles the duplicate rule result. The lead is created, a `DuplicateRecordSet` is created, and no error is surfaced to the calling system. Admins reviewing the Duplicate Rule configuration believe it is working because the rule is "active" and Alert records are being created — but so are the duplicate leads.

**Correct approach:** Use "Alert" mode as the rule action (captures Duplicate Record Sets for all channels) and implement a complementary after-insert Apex trigger or Flow to detect and route duplicates that arrive via non-UI channels. Reserve "Block" mode only for UI-based data entry workflows where its behavior is reliable.
