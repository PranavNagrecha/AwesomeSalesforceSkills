# Examples — Headless Experience Cloud

## Example 1: React App Fetching News Content from a Public SF CMS Channel

**Context:** A marketing team authors news articles in Salesforce CMS. The public-facing website is a React SPA hosted on a CDN, completely separate from any Salesforce Experience Cloud site. The React app needs to display the latest three news articles on the homepage.

**Problem:** Without guidance, practitioners either build a custom Apex REST resource (unnecessary overhead) or try to use the Experience Cloud Guest User API (wrong surface). They also frequently omit CORS setup, which results in the fetch silently failing in the browser.

**Solution:**

Step 1 — Retrieve the channel ID from Workbench:
```
GET /services/data/v62.0/connect/cms/delivery/channels
```
Response excerpt:
```json
{
  "channels": [
    {
      "channelId": "0apXx0000004C3KIAU",
      "channelName": "Public Site Channel",
      "channelType": "public",
      "domain": "https://yourorg.my.salesforce.com"
    }
  ]
}
```

Step 2 — Add `https://www.yoursite.com` to Setup > Security > CORS.

Step 3 — React fetch component:

```javascript
// src/api/cmsClient.js
const SF_INSTANCE = process.env.REACT_APP_SF_INSTANCE;
const CHANNEL_ID = process.env.REACT_APP_CMS_CHANNEL_ID;
const API_VERSION = 'v62.0';

export async function fetchLatestNews(count = 3) {
  const url = new URL(
    `${SF_INSTANCE}/services/data/${API_VERSION}/connect/cms/delivery/channels/${CHANNEL_ID}/contents`
  );
  url.searchParams.set('contentTypeName', 'sfdc_cms__news');
  url.searchParams.set('pageSize', String(count));
  url.searchParams.set('page', '1');

  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`CMS delivery API returned ${response.status}`);
  }
  const data = await response.json();
  return data.items ?? [];
}
```

```javascript
// src/components/NewsSection.jsx
import React, { useEffect, useState } from 'react';
import { fetchLatestNews } from '../api/cmsClient';

export function NewsSection() {
  const [articles, setArticles] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLatestNews(3)
      .then(setArticles)
      .catch(err => setError(err.message));
  }, []);

  if (error) return <p>Could not load news: {error}</p>;

  return (
    <section>
      {articles.map(article => (
        <article key={article.contentKey}>
          <h2>{article.title}</h2>
          <p>{article.excerpt}</p>
        </article>
      ))}
    </section>
  );
}
```

**Why it works:** The channel ID is externalized as an environment variable so sandbox and production use different values. CORS is configured before the first request. The `contentTypeName` filter keeps the payload small — only news items are returned, not the entire channel content catalogue.

---

## Example 2: Mobile App Consuming Authenticated CMS Banners via OAuth

**Context:** A member portal mobile app (React Native) needs to display promotional banners from Salesforce CMS. The banners are on an authenticated channel — only logged-in members should see them. The app authenticates users with Salesforce Identity via the OAuth web server flow.

**Problem:** Practitioners either try to use a public channel for member-only content (security gap) or embed a long-lived session ID in the app bundle (also a security risk). Token refresh is also commonly omitted, causing silent failures after the 2-hour access token window expires.

**Solution:**

Step 1 — Create a Connected App in Setup with:
- OAuth scopes: `api`, `refresh_token`, `offline_access`
- Callback URL matching the mobile app's deep-link scheme (e.g., `myapp://oauth/callback`)

Step 2 — Complete the OAuth web server flow to obtain `access_token` and `refresh_token`.

Step 3 — Fetch banners using the access token:

```javascript
// services/cmsService.js
const SF_INSTANCE = 'https://yourorg.my.salesforce.com';
const API_VERSION = 'v62.0';
const CHANNEL_ID = 'YOUR_AUTHENTICATED_CHANNEL_ID';

export async function fetchBanners(accessToken) {
  const url = `${SF_INSTANCE}/services/data/${API_VERSION}/connect/cms/delivery/channels/${CHANNEL_ID}/contents?contentTypeName=sfdc_cms__banner&pageSize=5`;

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
  });

  if (response.status === 401) {
    // Token expired — trigger refresh flow
    throw new TokenExpiredError('Access token expired');
  }

  if (!response.ok) {
    throw new Error(`Banner fetch failed: ${response.status}`);
  }

  const data = await response.json();
  return data.items ?? [];
}
```

Step 4 — Token refresh handler:

```javascript
// services/authService.js
const TOKEN_ENDPOINT = 'https://yourorg.my.salesforce.com/services/oauth2/token';

export async function refreshAccessToken(refreshToken, clientId) {
  const params = new URLSearchParams({
    grant_type: 'refresh_token',
    client_id: clientId,
    refresh_token: refreshToken,
  });

  const response = await fetch(TOKEN_ENDPOINT, {
    method: 'POST',
    body: params,
  });

  if (!response.ok) throw new Error('Token refresh failed');
  const { access_token } = await response.json();
  return access_token;
}
```

**Why it works:** The access token is user-scoped, so the delivery API can enforce channel visibility rules per user. The refresh token flow prevents the app from requiring re-authentication every two hours. The channel ID is stored in the app's configuration layer, not hardcoded in the fetch function.

---

## Anti-Pattern: Hardcoding the Channel ID in Source Code

**What practitioners do:** Copy the channel ID from a Workbench response during development and paste it directly into source code, often into a constant at the top of the file.

**What goes wrong:** The channel ID is an org-specific 18-character record ID. It differs between the developer sandbox, QA sandbox, UAT sandbox, and production. When the code is promoted, the hardcoded ID points to the wrong org or to a channel that does not exist in production. The delivery API returns a 404 with a non-descriptive error, and the root cause is obscure during incident response.

**Correct approach:** Store the channel ID as an environment variable (`REACT_APP_CMS_CHANNEL_ID`, `CMS_CHANNEL_ID`, etc.) that is injected at build time or runtime per environment. Document the per-environment values in a configuration manifest so they can be retrieved without Workbench access.
