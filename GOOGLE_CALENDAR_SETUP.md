# Google Calendar MCP Integration Setup

This guide explains how to set up and run the Google Calendar MCP server for Study Pal calendar integration.

## Current Status

✅ **Completed:**
- Cloned google-calendar-mcp repository to `/Users/romsheynis/Documents/GitHub/google-calendar-mcp`
- Installed npm dependencies
- Created OAuth credentials file (`gcp-oauth.keys.json`)
- Updated Study Pal `.env` with MCP server URL
- Wired `SchedulerAgent` to use `CalendarConnector`
- Updated `main.py` to initialize calendar integration

⚠️ **Pending:** OAuth authentication (requires manual completion due to Node.js file system timeout issues)

## Prerequisites

- Node.js installed
- Google Cloud Project with Calendar API enabled
- OAuth 2.0 credentials (Desktop app type)
- Redirect URIs configured in Google Cloud Console:
  - `http://localhost:3500/oauth2callback`
  - `http://localhost:8080/oauth2callback`

## Step 1: Complete OAuth Authentication

**Run this command in a new terminal window:**

```bash
cd /Users/romsheynis/Documents/GitHub/google-calendar-mcp
export GOOGLE_OAUTH_CREDENTIALS=/Users/romsheynis/Documents/GitHub/google-calendar-mcp/gcp-oauth.keys.json
npm run auth
```

**Then:**
1. The auth server will start on port 3500
2. A browser window should open automatically, or visit: http://localhost:3500
3. Sign in with your Google account
4. Grant calendar permissions
5. You'll be redirected back and the tokens will be saved to `~/.config/google-calendar-mcp/tokens.json`

**Troubleshooting:**
- If you see "ERR_CONNECTION_REFUSED", the auth server may have crashed due to file system issues
- Try running the command again in a fresh terminal session
- Make sure no other process is using port 3500: `lsof -i :3500`

## Step 2: Start the MCP Server

Once OAuth is complete, start the MCP server in HTTP mode:

```bash
cd /Users/romsheynis/Documents/GitHub/google-calendar-mcp
export GOOGLE_OAUTH_CREDENTIALS=/Users/romsheynis/Documents/GitHub/google-calendar-mcp/gcp-oauth.keys.json
npm run start:http
```

This will:
- Start the MCP server on http://localhost:3000
- Load your saved OAuth tokens
- Expose calendar management tools via MCP protocol

**Verify it's running:**
```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "healthy",
  "server": "google-calendar-mcp",
  "timestamp": "2025-11-02T..."
}
```

## Step 3: Run Study Pal

With the MCP server running, start Study Pal:

```bash
cd /Users/romsheynis/Documents/GitHub/study_pal
python main.py
```

Study Pal will now:
1. Generate a Pomodoro schedule based on user input
2. Automatically create Google Calendar events for each study block via the MCP server
3. Skip break periods (only study sessions are added to the calendar)

## How It Works

1. **SchedulerAgent** generates a schedule with study blocks and breaks
2. **sync_schedule()** method is called with the generated schedule
3. For each study session, it builds a calendar event payload:
   ```python
   {
       "summary": "Study: neural networks",
       "description": "Pomodoro study session for neural networks",
       "start": {
           "dateTime": "2025-11-02T18:00:00",
           "timeZone": "America/New_York"
       },
       "end": {
           "dateTime": "2025-11-02T18:25:00",
           "timeZone": "America/New_York"
       }
   }
   ```
4. **CalendarConnector** sends the payload to the MCP server at http://localhost:3000
5. The MCP server creates the event in your Google Calendar

## Configuration Files

**Study Pal `.env`:**
```env
GOOGLE_CALENDAR_MCP_URL=http://localhost:3000
# No token required for local MCP server
```

**OAuth Credentials (`gcp-oauth.keys.json`):**
Located at: `/Users/romsheynis/Documents/GitHub/google-calendar-mcp/gcp-oauth.keys.json`

**Saved Tokens (after auth):**
Location: `~/.config/google-calendar-mcp/tokens.json`

## Token Expiry

- **Test Mode:** Tokens expire after 7 days (you'll need to re-authenticate)
- **Production Mode:** Publish your app in Google Cloud Console to avoid weekly re-auth

To re-authenticate when tokens expire:
```bash
cd /Users/romsheynis/Documents/GitHub/google-calendar-mcp
export GOOGLE_OAUTH_CREDENTIALS=/Users/romsheynis/Documents/GitHub/google-calendar-mcp/gcp-oauth.keys.json
npm run auth
```

## Customization

### Change Timezone

Edit [agents/scheduler_agent.py:97](agents/scheduler_agent.py#L97):
```python
"timeZone": "Your/Timezone",  # e.g., "America/Los_Angeles"
```

### Modify Event Format

Edit the `_build_calendar_event_payload` method in [agents/scheduler_agent.py:76-103](agents/scheduler_agent.py#L76-L103)

### Disable Calendar Integration

Remove or comment out the `calendar_connector` parameter in [main.py:34](main.py#L34):
```python
scheduler = SchedulerAgent()  # Calendar integration disabled
```

## Known Issues

1. **Node.js File System Timeout:** On some macOS systems, Node.js may encounter `ETIMEDOUT` errors when reading files. This is a system-specific issue. If this happens:
   - Try running the auth command in a fresh terminal session
   - Check macOS security settings for file access permissions
   - Ensure the credentials file has proper permissions: `chmod 644 gcp-oauth.keys.json`

2. **Port Conflicts:** Ensure ports 3000 and 3500 are not in use by other applications

## Next Steps

- Test the integration by running `python main.py`
- Check your Google Calendar to see the created study events
- Adjust timezone settings as needed
- Consider publishing your Google Cloud app to production mode to avoid weekly token expiry

## Support

For MCP server issues, see:
- [google-calendar-mcp README](https://github.com/nspady/google-calendar-mcp)
- [google-calendar-mcp Issues](https://github.com/nspady/google-calendar-mcp/issues)

For Study Pal integration issues, check:
- [core/mcp_connectors.py](core/mcp_connectors.py) - CalendarConnector implementation
- [agents/scheduler_agent.py](agents/scheduler_agent.py) - Schedule sync logic
