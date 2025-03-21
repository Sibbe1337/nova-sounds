# Firebase Authentication Setup

This guide will help you set up Firebase Authentication with Google Sign-In for the YouTube Shorts Machine application.

## Prerequisites

1. A Google account
2. A Firebase project (you can create one at [Firebase Console](https://console.firebase.google.com/))

## Steps to Set Up Firebase Authentication

### 1. Create a Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Enter a project name (e.g., "YouTube Shorts Machine")
4. Choose whether to enable Google Analytics (recommended)
5. Follow the prompts to create your project

### 2. Register Your Web App

1. From the Firebase Console, select your project
2. Click on the web icon (</>) to add a web app
3. Provide a nickname for your app (e.g., "YouTube Shorts Machine Web")
4. Optionally, check "Also set up Firebase Hosting"
5. Click "Register app"
6. Copy the Firebase configuration (apiKey, authDomain, etc.)

### 3. Update Firebase Configuration in the Application

1. Open the file `static/js/firebase-config.js`
2. Replace the placeholder values with your Firebase configuration:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID",
  measurementId: "YOUR_MEASUREMENT_ID"
};
```

### 4. Enable Google Authentication Provider

1. In the Firebase Console, go to "Authentication" > "Sign-in method"
2. Click on "Google" and enable it
3. Configure the OAuth consent screen by providing your app information
4. Add your domain to the "Authorized domains" list
5. Save your changes

### 5. Set Up Service Account for Server-Side Verification

1. In the Firebase Console, go to "Project settings" > "Service accounts"
2. Click "Generate new private key"
3. Download the JSON file
4. Rename the file to `firebase-credentials.json` and place it in your project root directory
5. Ensure the file is listed in .gitignore to keep it secure

### 6. Install Required Packages

Make sure you have the required packages installed:

```bash
pip install -r requirements.txt
```

### 7. Configure Environment Variables

Add the following to your .env file:

```
FIREBASE_CREDENTIALS=firebase-credentials.json
```

## Testing Authentication

1. Start your application
2. Navigate to the signup page
3. Click "Sign in with Google"
4. You should be prompted to sign in with your Google account
5. After successful sign-in, you'll be redirected to the homepage

## Troubleshooting

- **Firebase initialization error**: Check that your Firebase configuration is correct
- **Google sign-in popup doesn't appear**: Ensure your domain is added to the authorized domains in Firebase
- **Server-side verification fails**: Verify that your service account file is correctly placed and properly formatted
- **CORS errors**: If testing locally, ensure you're using a supported browser and check Firebase console for any restrictions

## Security Considerations

- Never expose your Firebase configuration in public repositories
- Always verify tokens on the server side
- Set up proper Firebase Security Rules to control access to your data
- Use environment variables for sensitive information 