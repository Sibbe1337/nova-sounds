# YouTube Shorts Machine

YouTube Shorts Machine is an AI-powered automation tool that generates and uploads YouTube Shorts using music stored in Google Cloud Storage.

## Features

- AI-powered video creation with auto-generated beat synchronization
- Google Cloud Storage integration for music selection
- YouTube API upload for direct posting
- Task queue for asynchronous video processing
- Simple web UI for video creation and status monitoring
- Cross-platform publishing to TikTok, Instagram, and Facebook (fully implemented)
- Thumbnail optimization with A/B testing capability
- Content scheduling and batch processing
- AI-driven analytics and performance predictions
- Optimal publishing time recommendations
- Intelligent music recommendations based on video content
- Advanced content analysis with image classification (new)

All features listed above are fully implemented and available in the current version.

## Project Structure

```
youtube-shorts-machine/
├── src/
│   ├── app/           # Core application code
│   │   ├── api/       # FastAPI endpoints
│   │   ├── core/      # Core business logic
│   │   ├── models/    # Data models
│   │   ├── services/  # Service integrations
│   │   │   ├── ai/    # AI services (optimization, predictions)
│   │   │   ├── gcs/   # Google Cloud Storage
│   │   │   ├── social/# Social media integrations
│   │   │   ├── video/ # Video processing
│   │   │   ├── music/ # Music analysis and recommendations
│   │   │   └── youtube/# YouTube API integration
│   │   └── tasks/     # Celery tasks
│   ├── tests/         # Unit/integration tests
│   └── ui/            # Web UI
├── templates/         # HTML templates
├── static/            # Static files
│   └── css/           # CSS styles
├── .env.example       # Example environment variables
├── docker-compose.yml # Docker Compose configuration
├── Dockerfile         # Docker configuration
└── requirements.txt   # Python dependencies
```

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose (for containerized deployment)
- Google Cloud account with Storage and YouTube API access
- FFmpeg installation
- Social media developer accounts (for cross-platform publishing)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/youtube-shorts-machine.git
cd youtube-shorts-machine
```

2. Set up the environment:

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your credentials
```

4. Set up Google Cloud Platform:

```bash
# Follow the instructions in SETUP_GCP.md to:
# 1. Create a GCP project
# 2. Enable necessary APIs
# 3. Create a service account
# 4. Download service account key
# 5. Upload sample music files
```

5. Run the application:

```bash
# Using Docker Compose
docker-compose up -d

# OR run services individually
uvicorn src.app.api.main:app --host 0.0.0.0 --port 8000 --reload
uvicorn src.ui.main:app --host 0.0.0.0 --port 8001 --reload
celery -A src.app.tasks.config worker --loglevel=info
```

## Usage

1. Open your browser and navigate to http://localhost:8001
2. Authenticate with YouTube (click on "Authenticate" in the navigation)
3. Select a music track and upload images
4. Click "Create Short" to start the process
5. Track the status of your video on the status page

### New Features

#### Cross-Platform Publishing

The application now supports publishing videos to multiple platforms beyond YouTube:

1. Configure your social media credentials in the settings
2. Create a video using the standard workflow
3. Select target platforms during the publishing step
4. The video will be automatically formatted and published to all selected platforms
5. View consolidated analytics across all platforms

#### Thumbnail Optimization

Improve your video's click-through rate with A/B testing:

1. Upload a base image for your thumbnail
2. The system generates multiple variants with different styles
3. Test variants are automatically measured for performance
4. Get recommendations for the best-performing thumbnail
5. Apply AI-powered optimizations based on analysis

#### Content Scheduling and Batch Processing

Efficiently manage large-scale content creation:

1. Create a batch of videos with different parameters
2. Schedule publishing at optimal times for each platform
3. View the status and analytics of all scheduled content
4. Get recommendations for the best publishing times based on platform data
5. Automate entire content calendars with a few clicks

#### Intelligent Music Recommendations

Get perfect music matches for your videos with AI-powered recommendations:

1. Upload a video or select an existing one in your library
2. The system analyzes the video content for pacing, mood, and energy
3. Receive recommendations for music tracks that match your video's characteristics
4. Browse similar tracks to fine-tune your selection
5. Preview music with your video before finalizing
6. Use batch processing to get recommendations for multiple videos at once

## Testing

All features in YouTube Shorts Machine have been thoroughly tested to ensure reliability and correct functionality.

### Available Tests

- **API Endpoint Tests**: Verify all API endpoints respond correctly
- **Feature Tests**: Test individual feature implementations
- **Integration Tests**: Test full workflows from video creation to publishing
- **Social Media Integration Tests**: Verify cross-platform publishing capabilities

### Running Tests

To run the full test suite:

```bash
python run_tests.py
```

This will generate comprehensive test reports in the `test-output` directory.

For more detailed information about testing, please refer to [TESTING.md](TESTING.md).

## Configuration

### Google Cloud Storage Integration

The application can use either mock data (development mode) or real Google Cloud Storage buckets (production mode). To use real GCS:

1. Create a service account with Storage Admin permissions
2. Download the JSON key file and save it as `service-account-key.json` in the project root
3. Create two GCS buckets:
   - One for music tracks (default: `youtube-shorts-music`)
   - One for generated videos (default: `youtube-shorts-output`)
4. Set `DEV_MODE=false` in your `.env` file

To use the setup script:

```bash
# Create sample music directory with MP3 files
mkdir -p sample_music
# Add your MP3 files to sample_music/

# Run the setup script
python setup_gcs.py
```

### YouTube API

Set up YouTube API credentials:

1. Create a project in the Google Cloud Console
2. Enable the YouTube Data API v3
3. Create OAuth 2.0 credentials
4. Download the credentials as `client_secret.json`
5. Place this file in the project root or set the path in your `.env` file

### Social Media Integration

To enable cross-platform publishing, configure the following:

1. TikTok: Set up a TikTok Developer account and obtain API credentials
2. Instagram: Use the Facebook Graph API with Instagram permissions
3. Facebook: Set up a Facebook Developer account and obtain API credentials
4. Configure all credentials in the `.env` file or through the UI settings

## Development Mode

The application can run in development mode without real external services. To enable development mode:

```
# In .env file
DEV_MODE=true
```

In development mode:
- Mock music tracks are used instead of GCS
- Video processing is simulated
- YouTube uploads are mocked
- In-memory storage is used instead of Firestore
- Social media publishing is simulated
- Scheduling runs locally without external dependencies

## UI Components

The application includes a comprehensive UI component library designed for consistency, accessibility, and performance.

### CSS Structure

- **Variables**: Global CSS variables for theming (`variables.css`)
- **Component Styles**: Individual component-specific CSS files
- **Responsive Utilities**: Utility classes for responsive layouts (`responsive-utils.css`)
- **Accessibility**: Enhanced accessibility support (`a11y.css`)

### JavaScript Utilities

- **API Client**: Standardized API communication (`api-client.js`)
- **Form Validation**: Client-side validation with consistent UI feedback (`form-validator.js`)
- **UI Utilities**: Common UI interaction handlers (`ui-utils.js`)
- **Theme Management**: Light/dark theme support (`theme-switcher.js`)
- **Application Core**: Global app state and initialization (`app.js`)

### Documentation

The UI components are documented in the `/ui-docs` section of the application (only available in development mode):

```bash
# Start the app in development mode to access UI docs
DEV_MODE=true python -m uvicorn src.app.api.main:app --host 127.0.0.1 --port 8000
```

Then visit `http://localhost:8000/ui-docs` to explore the component library.

## License

This project is licensed under the MIT License - see the LICENSE file for details. # tuben
