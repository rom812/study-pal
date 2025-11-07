# Google Calendar Integration Setup Guide

## Overview

Study Pal can sync your study schedules directly to Google Calendar using a Model Context Protocol (MCP) server. This guide walks you through setting up the integration.

## Prerequisites

- Google account with Calendar access
- Node.js installed (for running the MCP server)
- Google Cloud Project with Calendar API enabled

## Setup Steps

### 1. Install Google Calendar MCP Server

The Google Calendar MCP server runs locally and provides a bridge between Study Pal and your Google Calendar.

```bash
# Install the Google Calendar MCP server
npm install -g @modelcontextprotocol/google-calendar
```

Or if you prefer to run it from a local directory:

```bash
# Clone or install in a specific directory
mkdir mcp-servers
cd mcp-servers
npm install @modelcontextprotocol/google-calendar
```

### 2. Set Up Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:8080/oauth2callback`
   - Download the credentials JSON file

5. Extract the following from your credentials:
   - Client ID
   - Client Secret
   - Project ID

### 3. Configure Environment Variables

Update your `.env` file with the Google Calendar MCP configuration:

```bash
# Google Calendar MCP Server Configuration
GOOGLE_CALENDAR_MCP_URL=http://localhost:3000
# No auth token required for local MCP server

# Google OAuth Credentials
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_PROJECT_ID=your-project-id
GOOGLE_OAUTH_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GOOGLE_OAUTH_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8080/oauth2callback
```

### 4. Start the MCP Server

Before using the calendar sync feature, start the Google Calendar MCP server:

```bash
# If installed globally
google-calendar-mcp --port 3000

# Or if installed locally
cd mcp-servers
npx @modelcontextprotocol/google-calendar --port 3000
```

The server should start on port 3000 (or the port you specified).

### 5. Authenticate with Google

On first use, the MCP server will prompt you to authenticate:

1. The server will provide an authentication URL
2. Open the URL in your browser
3. Sign in with your Google account
4. Grant permission to access your Google Calendar
5. You'll be redirected back with a success message

The authentication tokens are stored locally and will be reused for future sessions.

## Using Calendar Sync in Study Pal

Once the MCP server is running and authenticated, you can sync schedules from the chatbot:

1. Start the chatbot:
   ```bash
   python main.py --chat
   ```

2. Complete a study session and analyze it:
   ```
   💭 You: /finish
   ```

3. Create a schedule based on your weak points:
   ```
   💭 You: /schedule
   ```

4. Enter your availability:
   ```
   Start time (HH:MM, 24-hour format): 14:00
   End time (HH:MM, 24-hour format): 16:00
   ```

5. When prompted, choose to sync to calendar:
   ```
   📆 Sync this schedule to your calendar? (yes/no): yes
   ✅ Schedule synced to calendar!
   ```

6. Check your Google Calendar - you should see study sessions created!

## Troubleshooting

### Calendar sync says "✅ Synced" but no events appear

**Possible causes:**

1. **MCP server not running**
   - Make sure the Google Calendar MCP server is running on port 3000
   - Check the server logs for errors

2. **Authentication issues**
   - The MCP server may need re-authentication
   - Restart the MCP server and re-authenticate

3. **Environment variables missing**
   - Verify all `GOOGLE_OAUTH_*` variables are set in `.env`
   - Check that `GOOGLE_CALENDAR_MCP_URL` points to the correct server

4. **Wrong calendar**
   - Events are created in your "primary" calendar
   - Check that you're looking at the correct Google account

5. **Timezone issues**
   - The default timezone is set to "Asia/Jerusalem"
   - Update `scheduler_agent.py:126` if you need a different timezone:
     ```python
     "timeZone": "America/New_York",  # Change as needed
     ```

6. **Date issues**
   - The scheduler creates events for "today" by default
   - Check if events were created for today's date
   - Future enhancement: Allow specifying the date

### Connection refused errors

```
RuntimeError: Google Calendar MCP interaction failed: Connection refused
```

**Solution:**
- The MCP server is not running
- Start the server: `google-calendar-mcp --port 3000`

### OAuth errors

```
RuntimeError: Google Calendar MCP reported an error: Invalid OAuth token
```

**Solution:**
- Re-authenticate with the MCP server
- Delete stored tokens (usually in `~/.google-calendar-mcp/`)
- Restart the MCP server and authenticate again

### API not enabled

```
Error: Google Calendar API has not been used in project...
```

**Solution:**
- Go to Google Cloud Console
- Enable the Google Calendar API for your project

## Advanced Configuration

### Custom MCP Server Port

If port 3000 is already in use, you can run the server on a different port:

1. Start the server on a custom port:
   ```bash
   google-calendar-mcp --port 3001
   ```

2. Update your `.env`:
   ```bash
   GOOGLE_CALENDAR_MCP_URL=http://localhost:3001
   ```

### Custom Tool Name

If the MCP server uses a different tool name for creating events:

```bash
GOOGLE_CALENDAR_MCP_CREATE_TOOL=custom-create-event-tool-name
```

### Adding Authentication Token

For remote MCP servers that require authentication:

```bash
GOOGLE_CALENDAR_MCP_TOKEN=your-bearer-token
```

## How It Works

1. **Schedule Creation**: When you use `/schedule`, Study Pal creates a Pomodoro-based study schedule prioritizing your weak points
2. **Event Formatting**: Each study session is converted to a calendar event with:
   - Title: "Study: [topic]"
   - Description: "Pomodoro study session for [topic]"
   - Start/End times based on your schedule
   - Timezone setting
3. **MCP Communication**: The `CalendarConnector` sends events to the MCP server via HTTP
4. **Google Calendar API**: The MCP server uses Google Calendar API to create events
5. **Confirmation**: You see "✅ Synced" when all events are successfully created

## Event Format

Study sessions appear in your calendar as:

```
Title: Study: derivatives
Time: 14:00 - 14:25
Description: Pomodoro study session for derivatives
```

Breaks are NOT added to the calendar (only study blocks).

## Security Notes

- OAuth tokens are stored locally by the MCP server
- Never commit your `.env` file to version control
- Keep your Client Secret confidential
- The MCP server only has access to your Google Calendar (not other Google services)

## Support

If you encounter issues:
1. Check the MCP server logs
2. Verify all environment variables are set correctly
3. Ensure the Google Calendar API is enabled in your project
4. Try re-authenticating with Google
5. Check this guide's troubleshooting section

For MCP server issues, refer to the [@modelcontextprotocol/google-calendar](https://github.com/modelcontextprotocol/servers) documentation.
