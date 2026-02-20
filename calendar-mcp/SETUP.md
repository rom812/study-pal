# Google Calendar MCP — OAuth Setup

## Prerequisites

- Google Cloud account
- A Google Cloud project

## Steps

### 1. Enable Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project (or create one)
3. Navigate to **APIs & Services > Library**
4. Search for "Google Calendar API" and **Enable** it

### 2. Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Choose **Desktop app** as the application type
4. Download the JSON file

### 3. Place Credentials

```bash
mkdir -p calendar-mcp/credentials
# Copy your downloaded JSON as:
cp ~/Downloads/client_secret_*.json calendar-mcp/credentials/gcp-oauth.keys.json
```

### 4. Add to `.env`

```env
GOOGLE_CALENDAR_MCP_ENABLED=1
```

### 5. First-Time Auth

On first run, the MCP server will open a browser window for Google OAuth consent.
After authorizing, tokens are stored in `calendar-mcp/credentials/` and auto-refresh.

### 6. Add Test User (if app is in test mode)

1. Go to **APIs & Services > OAuth consent screen > Audience**
2. Add your email as a test user
3. Wait 2-3 minutes for propagation

### Notes

- Tokens expire weekly in test mode; re-authenticate when needed
- For production, publish the OAuth consent screen
