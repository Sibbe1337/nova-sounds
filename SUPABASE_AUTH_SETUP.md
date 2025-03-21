# Supabase Authentication Setup

This guide will help you set up Supabase Authentication with Google Sign-In for the YouTube Shorts Machine application.

## Prerequisites

1. A Google account
2. A Supabase project (already set up at https://gsyiemgxyvxlqhwgwscd.supabase.co)

## Supabase Configuration Overview

The application is already configured with the following Supabase details:

- **Supabase URL**: `https://gsyiemgxyvxlqhwgwscd.supabase.co`
- **Supabase Anon Key**: The anonymous key is already configured in the application

## Setting Up Google Authentication in Supabase

To enable Google authentication in your Supabase project, follow these steps:

1. Go to the [Supabase Dashboard](https://app.supabase.com/)
2. Select your project
3. In the left sidebar, navigate to "Authentication" > "Providers"
4. Find "Google" in the list of providers and click on it
5. Enable the provider by toggling the switch to "Enabled"
6. You'll need to provide:
   - **Client ID**: Get this from the Google Cloud Console
   - **Client Secret**: Get this from the Google Cloud Console

## Creating Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Set the Application type to "Web application"
6. Add your Supabase authentication callback URL to the Authorized redirect URIs:
   ```
   https://gsyiemgxyvxlqhwgwscd.supabase.co/auth/v1/callback
   ```
7. Copy the Client ID and Client Secret
8. Paste these values in the Supabase Google provider settings

## Adding Your Application's Domain

For security reasons, you need to add your application's domain to Supabase:

1. In the Supabase Dashboard, go to "Authentication" > "URL Configuration"
2. Add your site URL to the "Site URL" field
3. Add any additional redirect URLs your application might use

## Environment Variables

The application expects the following environment variables:

```
SUPABASE_URL=https://gsyiemgxyvxlqhwgwscd.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

These are already configured in the application code, but if you need to change them, update them in the following files:

- `src/app/api/auth.py`
- `static/js/supabase-auth.js`
- `templates/auth.html` (for the inline script)

## How Authentication Works

1. User clicks "Sign in with Google" on the application
2. They are redirected to the Google OAuth consent screen
3. After granting permission, Google redirects back to the Supabase callback URL
4. Supabase processes the authentication and redirects to your application's callback route
5. The application processes the authentication token and establishes a session

## Testing Authentication

1. Start your application
2. Navigate to the signup page
3. Click "Sign in with Google"
4. You should be prompted to sign in with your Google account
5. After successful sign-in, you'll be redirected to the homepage

## Troubleshooting

- **Authentication fails**: Ensure your Google OAuth credentials are correctly configured in Supabase
- **Redirect errors**: Check that all redirect URLs are properly configured in both Google Cloud Console and Supabase
- **CORS errors**: If testing locally, make sure your local domain is added to the allowed site URLs in Supabase

## Additional Resources

- [Supabase Authentication Documentation](https://supabase.io/docs/guides/auth)
- [Google OAuth Setup Guide](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Supabase JavaScript Client](https://supabase.io/docs/reference/javascript/) 