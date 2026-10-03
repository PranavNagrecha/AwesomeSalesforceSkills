# Examples — Slack Salesforce Integration Setup

## Example 1: First-Time Org Connection in One Session

**Context:** A company wants Salesforce channels and the Salesforce app in Slack for its production org.

**Problem:** The Salesforce admin looked for a "connect to Slack" button in Setup and found only a page with nothing pending. The Slack side had never requested the connection.

**Solution:** Book one session with the Slack Owner (or a person with the Salesforce Admin system role in Slack) and the Salesforce System Admin, then follow the three documented steps:

```text
Step 1  Slack   Workspace name > Tools & settings > Manage Salesforce Organizations
                > Connect Salesforce Org; enter the org URL; Account mapping field = Email;
                Automatic account mapping = on; Request Connection
Step 2  Salesforce  Setup > Platform tools > Slack > Manage Slack Connection;
                select the user mapping field; accept the terms; Approve
Step 3  Slack   Manage Salesforce Organizations > select the pending connection > Activate
                (Owner or Salesforce Admin system role)
Then    Salesforce  Assign the permission set with Connect Salesforce with Slack to every
                Slack user; members with mapped accounts get the Salesforce app in Slack
```

**Why it works:** The approval page in Salesforce shows a request only after Slack has sent one, and activation needs a Slack role the Salesforce admin may not hold. Doing the steps in order with both role holders present finishes the connection in one sitting.

---

## Example 2: Governing What Record Links Reveal

**Context:** A financial services firm found that Opportunity links posted in a broad channel showed deal amounts to junior staff who cannot see that field in Salesforce.

**Problem:** Link unfurling was set to "Data Viewable by User Sharing the Link", so the channel saw the poster's view of the record, rendered with the object's compact layout because no Slack Record Layout existed.

**Solution:**

1. In Setup > Initial Slack Setup > Verify Data Sharing Options, change the unfurling option to Name, Type, and Preview Button. The channel now sees the name and type; the preview window opens with each viewer's own permissions.
2. For objects where a data preview is still wanted, create a URL Unfurling Slack Record Layout (Object Manager > object > Slack Record Layouts > New > URL Unfurling Layout) with only non-sensitive fields, and assign it to the relevant profiles.
3. For Sales Cloud for Slack notifications, set record detail security to Show object type only.
4. Publish a channel policy covering public channels, private channels, and Slack Connect channels.

**Why it works:** What a channel sees is the configured unfurling option plus the layout it uses, so changing those two settings changes the exposure for every future link.

---

## Anti-Pattern: Attempting a Government Cloud Connection

**What practitioners do:** Start the connection for a Government Cloud org because the customer asked for Slack features.

**What goes wrong:** Slack cannot connect to Government Cloud Salesforce orgs, and the Salesforce for Slack apps are not supported in Government Cloud or Government Cloud Plus.

**Correct approach:** State the restriction early and propose an alternative pattern, such as a custom Slack app or middleware.

See [`metadata-examples.md`](metadata-examples.md) for the connection plan file the checker validates and the permission set to deploy.
