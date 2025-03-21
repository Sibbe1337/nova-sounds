# Google Cloud Platform Setup Guide

This guide explains how to set up Google Cloud Platform (GCP) for the YouTube Shorts Machine application.

## 1. Create a Google Cloud Platform Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "YouTube Shorts Machine")
5. Click "Create"

## 2. Enable Required APIs

1. In the GCP console, go to "APIs & Services" > "Library"
2. Search for and enable the following APIs:
   - Google Cloud Storage API
   - Cloud Firestore API (if using Firestore)
   - YouTube Data API v3 (for YouTube uploads)

## 3. Create a Service Account

1. In the GCP console, go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Enter a service account name (e.g., "youtube-shorts-machine")
4. Add a description (optional)
5. Click "Create and Continue"
6. Add the following roles:
   - Storage Admin
   - Firestore Admin (if using Firestore)
7. Click "Continue" and then "Done"

## 4. Create a Service Account Key

1. Find your service account in the list
2. Click the three dots (menu) at the end of the row
3. Select "Manage keys"
4. Click "Add Key" > "Create new key"
5. Choose "JSON" as the key type
6. Click "Create"
7. The key file will be downloaded to your computer
8. Move this file to your project directory and rename it to `service-account-key.json`

## 5. Update Environment Variables

Make sure your `.env` file has the following entries:

```
GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
GCS_BUCKET_NAME=youtube-shorts-music
GCS_VIDEO_BUCKET=youtube-shorts-output
DEV_MODE=false
```

## 6. Create Buckets and Upload Sample Music

Run the setup script:

```bash
python setup_gcs.py
```

This will:
1. Create the necessary GCS buckets
2. Upload any MP3 files from the `sample_music` directory to the music bucket

## 7. (Optional) Set Up YouTube API

If you want to upload videos to YouTube, you'll need to:

1. Set up OAuth consent screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" and click "Create"
   - Fill in the required information

2. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URIs (e.g., `http://localhost:8000/auth/callback`)
   - Download the JSON file and save it as `client_secret.json` in your project directory

3. Update environment variables:
   ```
   CLIENT_SECRETS_FILE=client_secret.json
   ``` 