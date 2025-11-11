# Login Feature Documentation

## Overview
A simple user ID-based login system has been added to Study Pal. Users only need to enter their user ID (no password required) to access their personalized study materials and sessions.

## Features

### 1. Login Screen
- Appears when the app first loads
- Simple user ID input field
- Validates that the user exists before granting access
- Shows error message for non-existent users

### 2. Main Application Access
- Hidden until user successfully logs in
- All tabs (Profile, Upload, Chat, Analysis, Schedule, Motivation) are protected
- User ID is automatically populated from the logged-in session

### 3. User Info Bar
- Shows the logged-in user's ID at the top of the main app
- Read-only display (can't be changed without logging out)
- Includes logout button and status button

### 4. Logout Functionality
- Clears the session
- Returns to login screen
- Clears all user-specific data from the UI

## How It Works

### User Flow
```
1. User visits app → Login screen appears
2. User enters their user_id (e.g., "default_user", "alice")
3. System checks if data/profiles/{user_id}.json exists
4. If exists → Login successful, show main app
5. If not exists → Show error message, keep on login screen
6. User can logout anytime → Returns to login screen
```

### Technical Implementation

#### Authentication Functions
- `validate_user_exists(user_id)` - Checks if user profile exists
- `login_user(user_id, session_state)` - Validates and sets session
- `logout_user(session_state)` - Clears session
- `handle_login()` - Manages UI visibility on login
- `handle_logout()` - Manages UI visibility on logout

#### Session Management
- Uses Gradio's `gr.State()` for session tracking
- Session stores: `{"logged_in": bool, "user_id": str}`
- Session persists throughout the user's browser session

#### UI Components
- **Login Screen** (`login_screen`): Visible by default
  - User ID input field
  - Login button
  - Status message area

- **Main App** (`main_app`): Hidden by default
  - User info bar with logged-in user display
  - Logout button
  - All main functionality tabs

## Existing Users
The system already has several existing users you can test with:
- `default_user`
- `example_user`
- `rom_test`
- `sheynis`

## Security Considerations

### Current Implementation
- **No password protection** - Only validates user ID exists
- **File-based validation** - Checks for profile JSON file
- **No encryption** - Profile data stored as plain JSON
- **No session timeout** - Session lasts until browser close or logout

### Suitable For
- Single-user deployments
- Trusted environments
- Development/testing
- Personal use applications

### Not Suitable For
- Multi-tenant production systems
- Public-facing applications
- Scenarios requiring strong authentication
- Systems with sensitive data

## Future Enhancements (Optional)
If you need stronger security in the future, consider:
1. Adding password authentication with bcrypt hashing
2. Implementing session timeouts
3. Adding email verification for new users
4. Rate limiting login attempts
5. Adding 2FA (two-factor authentication)
6. Encrypting user profile data

## Testing

### Manual Testing
1. Start the app: `python gradio_app.py`
2. Visit http://localhost:7860
3. Enter an existing user ID (e.g., "default_user")
4. Verify main app appears
5. Click logout
6. Verify return to login screen
7. Try a non-existent user ID
8. Verify error message appears

### Automated Testing
Run the test suite:
```bash
python test_login.py
```

This tests:
- User validation with existing users
- User validation with non-existing users
- Empty user ID handling
- Login flow
- Logout flow

## Files Modified
- [gradio_app.py](gradio_app.py) - Main UI file with login implementation

## Files Created
- [test_login.py](test_login.py) - Automated tests for login functionality
- [LOGIN_FEATURE.md](LOGIN_FEATURE.md) - This documentation file
