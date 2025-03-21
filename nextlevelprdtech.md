# YouTube Shorts Machine: Technical Product Requirements Document

## 1. System Architecture Overview

The YouTube Shorts Machine is built on a microservices architecture to ensure scalability, maintainability, and independent deployment of components. The system includes the following high-level architectural components:

### 1.1 Core Architecture Components

- **Frontend Application Layer**: React-based web application with responsive design
- **API Gateway Layer**: FastAPI-based RESTful API gateway
- **Service Layer**: Independent microservices for video processing, authentication, analytics, etc.
- **Storage Layer**: Google Cloud Storage, PostgreSQL, Redis
- **Machine Learning Layer**: AI services for video editing, trend analysis, and optimization
- **Integration Layer**: Connectors to external APIs (YouTube, TikTok, Instagram, etc.)
- **Background Processing Layer**: Celery workers for asynchronous task execution

### 1.2 System Context Diagram

```
┌─────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│                 │     │                   │     │                  │
│  Web Interface  │◄────┤   API Gateway     │◄────┤  Auth Service    │
│  (React)        │     │   (FastAPI)       │     │  (Firebase)      │
│                 │     │                   │     │                  │
└─────────────────┘     └───────────────────┘     └──────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│                 │     │                   │     │                  │
│ Video Processing│◄────┤   Storage Service │◄────┤  Analytics       │
│ Service         │     │   (GCS)           │     │  Service         │
│                 │     │                   │     │                  │
└─────────────────┘     └───────────────────┘     └──────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│                 │     │                   │     │                  │
│ Task Queue      │◄────┤   Social Media    │◄────┤  ML Inference    │
│ (Celery+Redis)  │     │   Integration     │     │  Service         │
│                 │     │                   │     │                  │
└─────────────────┘     └───────────────────┘     └──────────────────┘
```

### 1.3 Infrastructure Components

- **Kubernetes Cluster**: For container orchestration and service management
- **Containerization**: Docker for packaging and deployment
- **CI/CD Pipeline**: GitHub Actions for continuous integration and deployment
- **Monitoring**: Prometheus and Grafana for system monitoring
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana) for log management

## 2. Detailed Technical Components

### 2.1 Frontend Application

**Technology Stack**:
- React 18+ with TypeScript
- Redux for state management
- Material UI for component library
- Axios for API communication
- React Router for navigation
- Jest and React Testing Library for testing

**Key Frontend Components**:
- **AuthModule**: Handles user authentication, registration, and session management
- **DashboardModule**: Main user interface for video creation and management
- **VideoEditorModule**: Interactive interface for video customization
- **AnalyticsModule**: Displays performance metrics and insights
- **SettingsModule**: User preferences and account management
- **AdminModule**: Administrative functions for system management

**Frontend Architecture**:
- Component-based architecture with reusable UI elements
- State management using Redux for global state and React hooks for local state
- Responsive design supporting desktop and mobile interfaces
- Progressive Web App (PWA) capabilities for offline functionality

### 2.2 API Gateway Service

**Technology Stack**:
- FastAPI (Python 3.9+)
- Pydantic for data validation
- JWT for token-based authentication
- OpenAPI for API documentation
- Uvicorn as ASGI server

**Key API Endpoints**:

```
/api/v1/auth              # Authentication endpoints
/api/v1/videos            # Video management
/api/v1/music             # Music track management
/api/v1/uploads           # Platform upload management
/api/v1/analytics         # Analytics and reporting
/api/v1/trends            # Trend analysis and recommendations
/api/v1/users             # User management
/api/v1/subscriptions     # Subscription management
/api/v1/admin             # Administrative functions
```

**API Gateway Functions**:
- Request routing to appropriate microservices
- Authentication and authorization validation
- Rate limiting and throttling
- Request/response logging
- API versioning
- Cross-cutting concerns like CORS, compression

### 2.3 Video Processing Service

**Technology Stack**:
- Python 3.9+
- OpenCV for video manipulation
- FFMPEG for media processing
- PyTorch/TensorFlow for ML model integration
- Librosa for audio analysis

**Key Processing Components**:
- **BeatDetector**: Analyzes music tracks to extract beat information
- **VideoGenerator**: Creates videos based on templates and user inputs
- **TransitionEngine**: Applies intelligent transitions based on audio cues
- **CaptionGenerator**: Creates captions using OpenAI Whisper API
- **EffectsProcessor**: Applies visual effects synchronized to audio beats
- **VideoOptimizer**: Adjusts video parameters for specific platforms
- **ThumbnailGenerator**: Creates compelling thumbnails using AI

**Processing Pipeline**:
1. Music track analysis to extract beats, tempo, and waveform
2. Video template selection based on AI recommendations
3. Asset composition and timeline creation
4. Effects and transitions application
5. Text and caption overlay generation
6. Final render and optimization for target platforms
7. Upload to Google Cloud Storage

### 2.4 Storage Service

**Technology Stack**:
- Google Cloud Storage for media files
- PostgreSQL for relational data
- Redis for caching and session management
- Firebase Firestore for real-time data

**Data Storage Components**:
- **MediaBucket**: Google Cloud Storage bucket for raw and processed videos
- **MusicBucket**: Google Cloud Storage bucket for music tracks
- **MetadataDB**: PostgreSQL database for video metadata, user data, and analytics
- **CacheLayer**: Redis for frequently accessed data and session information
- **RealtimeDB**: Firebase Firestore for real-time collaboration features

### 2.5 Machine Learning Service

**Technology Stack**:
- Python 3.9+
- TensorFlow/PyTorch for model serving
- FastAPI for ML service API
- Redis for prediction caching
- Scikit-learn for feature extraction

**ML Models**:
- **VideoStylePredictor**: Recommends video styles based on content and trends
- **EngagementPredictor**: Predicts viewer engagement for A/B testing variants
- **TrendAnalyzer**: Identifies trending content patterns on YouTube
- **ThumbnailOptimizer**: Generates high-CTR thumbnails based on historical data
- **TimingRecommender**: Suggests optimal posting times based on audience data

### 2.6 Task Queue System

**Technology Stack**:
- Celery as task queue framework
- Redis as message broker
- Flower for task monitoring
- Supervisord for worker process management

**Queue Configuration**:
- Video processing queue with priority levels
- Upload queue for platform distribution
- Analytics processing queue
- ML inference queue
- Scheduled task queue for timed operations

## 3. APIs and Integrations

### 3.1 Google Cloud Storage API Integration

**Integration Requirements**:
- Authentication via service account credentials
- Bucket organization with prefix-based structure
- Signed URL generation for secure access
- Metadata management for assets
- Lifecycle policies for automatic cleanup

**Example Python Implementation**:

```python
from google.cloud import storage

def list_music_tracks(bucket_name, prefix=None):
    """
    Fetch available music tracks from Google Cloud Storage
    
    Args:
        bucket_name (str): Name of the GCS bucket
        prefix (str, optional): Filter by prefix (folder structure)
        
    Returns:
        list: List of track metadata
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    
    blobs = list(bucket.list_blobs(prefix=prefix))
    
    tracks = []
    for blob in blobs:
        if blob.content_type.startswith('audio/'):
            # Extract metadata
            metadata = blob.metadata or {}
            
            tracks.append({
                'name': blob.name,
                'url': blob.generate_signed_url(expiration=3600),
                'size': blob.size,
                'content_type': blob.content_type,
                'title': metadata.get('title', blob.name),
                'artist': metadata.get('artist', 'Unknown'),
                'duration': metadata.get('duration', 0),
                'license': metadata.get('license', 'unknown')
            })
    
    return tracks
```

### 3.2 YouTube API Integration

**Integration Requirements**:
- OAuth 2.0 authentication flow
- Permission scopes:
  - `https://www.googleapis.com/auth/youtube.upload`
  - `https://www.googleapis.com/auth/youtube`
  - `https://www.googleapis.com/auth/youtube.readonly`
- Video upload with metadata
- Scheduled publishing
- Analytics retrieval
- Comment moderation

**Example Python Implementation**:

```python
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_youtube(video_path, title, description, tags, credentials, privacy_status="public", publish_at=None):
    """
    Upload video to YouTube
    
    Args:
        video_path (str): Path to video file
        title (str): Video title
        description (str): Video description
        tags (list): List of tags
        credentials (google.oauth2.credentials.Credentials): OAuth credentials
        privacy_status (str): Privacy status (public, private, unlisted)
        publish_at (str, optional): ISO format datetime for scheduled publishing
        
    Returns:
        dict: Response from YouTube API with video ID and status
    """
    youtube = build('youtube', 'v3', credentials=credentials)
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '22'  # Entertainment category
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }
    
    # Add scheduled publishing if provided
    if publish_at:
        body['status']['publishAt'] = publish_at
    
    # Upload the video
    media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True)
    
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"Upload progress: {progress}%")
    
    return response
```

### 3.3 Other Social Media Platform Integrations

**1. TikTok API Integration**
- TikTok Creator API with authenticated sessions
- Video upload with music attribution
- Caption and hashtag optimization
- Scheduling capabilities

**2. Instagram Reels API Integration**
- Facebook Graph API for Instagram
- Content publishing API endpoints
- Caption and hashtag management
- Media upload with specific Reels parameters

**3. Facebook Reels API Integration**
- Facebook Graph API 
- Page access token authentication
- Video upload with specific aspect ratios
- Targeting and demographic options

### 3.4 OpenAI API Integration for Captions

**Requirements**:
- API key management
- Whisper API requests for transcription
- Language detection and translation
- Caption formatting and timing

**Example Python Implementation**:

```python
import openai
import json

def generate_captions(audio_file_path, api_key, language=None):
    """
    Generate captions for a video using OpenAI's Whisper API
    
    Args:
        audio_file_path (str): Path to audio file
        api_key (str): OpenAI API key
        language (str, optional): Target language code (e.g., "en")
        
    Returns:
        dict: Transcription with timestamps
    """
    openai.api_key = api_key
    
    with open(audio_file_path, "rb") as audio_file:
        options = {}
        if language:
            options["language"] = language
            
        response = openai.Audio.transcribe(
            "whisper-1", 
            audio_file,
            response_format="verbose_json",
            **options
        )
    
    # Format timestamps for video captions
    captions = []
    for segment in response.segments:
        captions.append({
            'start': segment['start'],
            'end': segment['end'],
            'text': segment['text']
        })
    
    return captions
```

## 4. Data Models

### 4.1 PostgreSQL Schema

**User Table**:
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    profile_picture_url TEXT,
    account_type VARCHAR(50) NOT NULL DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    preferences JSONB
);
```

**Video Projects Table**:
```sql
CREATE TABLE video_projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    video_style VARCHAR(100),
    music_track TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE,
    project_data JSONB,
    settings JSONB,
    analytics JSONB
);
```

**Platform Uploads Table**:
```sql
CREATE TABLE platform_uploads (
    upload_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES video_projects(project_id) ON DELETE CASCADE,
    platform_name VARCHAR(100) NOT NULL,
    platform_video_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    url TEXT,
    scheduled_for TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    engagement_metrics JSONB,
    platform_specific_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Subscriptions Table**:
```sql
CREATE TABLE subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    plan_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE,
    payment_provider VARCHAR(100),
    payment_provider_subscription_id VARCHAR(255),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    auto_renew BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Music Tracks Table**:
```sql
CREATE TABLE music_tracks (
    track_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    duration INTEGER NOT NULL, -- in seconds
    gcs_path TEXT NOT NULL,
    genre VARCHAR(100),
    bpm INTEGER,
    license_type VARCHAR(100),
    is_premium BOOLEAN DEFAULT FALSE,
    waveform_data JSONB,
    beat_markers JSONB,
    preview_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 Object Models

**Video Project Model**:
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class VideoProject(BaseModel):
    project_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str = "draft"
    video_style: Optional[str] = None
    music_track: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    
    # Project configuration
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    # Media assets
    media_assets: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timeline data
    timeline: Dict[str, Any] = Field(default_factory=dict)
    
    # Text overlays
    text_elements: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Effects
    effects: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Platform-specific settings
    platform_settings: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Generated video info
    output_video: Optional[Dict[str, Any]] = None
    
    # Analytics
    analytics: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        orm_mode = True
```

**User Model**:
```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class User(BaseModel):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    email: EmailStr
    password_hash: Optional[str] = None
    full_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    account_type: str = "free"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    is_verified: bool = False
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        orm_mode = True
```

## 5. Processing Workflows

### 5.1 Video Creation Workflow

1. **Initialization**:
   - User selects images/video clips and music track
   - User chooses video style and any additional options
   - System validates inputs and creates a new project

2. **Music Analysis**:
   - Extract tempo, beats, and waveform data
   - Identify key moments for transitions
   - Generate beat markers for synchronization

3. **Content Composition**:
   - Arrange media assets on timeline
   - Apply smart crop to ensure proper aspect ratios
   - Generate transitions based on beat markers
   - Apply selected style's effects and filters

4. **AI Enhancement**:
   - Apply AI-suggested effects at key moments
   - Generate captions if requested
   - Create text animations synchronized to music
   - Apply dynamic color grading based on mood

5. **Rendering**:
   - Generate draft preview at lower resolution
   - Process final video at target resolution
   - Optimize encoding for each target platform
   - Generate platform-specific variants

6. **Distribution**:
   - Upload to Google Cloud Storage
   - Create platform-specific metadata
   - Submit to each selected platform
   - Schedule posts for optimal timing

### 5.2 Background Processing Implementation

```python
# tasks.py
from celery import Celery, chain, group
from celery.signals import task_success, task_failure
import os
import logging

app = Celery('youtube_shorts_machine', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3)
def analyze_music(self, project_id, music_track_path):
    """Analyze music track to extract beats and tempo"""
    try:
        # Music analysis code
        return {
            'project_id': project_id,
            'beats': [...],  # Beat timestamps
            'tempo': 120,    # BPM
            'waveform': [...],  # Waveform data
            'key_moments': [...],  # Important moments for transitions
        }
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

@app.task(bind=True, max_retries=3)
def create_video_composition(self, music_analysis, media_assets, video_style):
    """Create video composition based on music analysis"""
    # Video composition code
    return {
        'project_id': music_analysis['project_id'],
        'timeline': {...},  # Timeline data
        'transitions': [...],  # Transition data
        'effects': [...],  # Effects data
    }

@app.task(bind=True, max_retries=3)
def render_video(self, composition_data, output_path):
    """Render the final video"""
    # FFMPEG rendering code
    return {
        'project_id': composition_data['project_id'],
        'output_path': output_path,
        'duration': 60,  # Video duration in seconds
        'resolution': '1080x1920',
    }

@app.task(bind=True, max_retries=3)
def upload_to_platforms(self, render_result, platforms):
    """Upload video to selected platforms"""
    results = {}
    for platform in platforms:
        # Platform-specific upload code
        results[platform] = {
            'status': 'success',
            'url': f'https://{platform}.com/watch?v=abc123',
            'platform_id': 'abc123',
        }
    
    return {
        'project_id': render_result['project_id'],
        'upload_results': results
    }

@app.task
def update_project_status(upload_results):
    """Update project status after processing"""
    project_id = upload_results['project_id']
    # Update project status in database
    return {
        'project_id': project_id,
        'status': 'completed'
    }

def create_video_processing_workflow(project_id, music_track_path, media_assets, video_style, output_path, platforms):
    """Create a complete video processing workflow"""
    workflow = chain(
        analyze_music.s(project_id, music_track_path),
        create_video_composition.s(media_assets, video_style),
        render_video.s(output_path),
        upload_to_platforms.s(platforms),
        update_project_status.s()
    )
    
    return workflow
```

### 5.3 Content Analysis and Recommendation Workflow

1. **Trend Analysis**:
   - Collect data from trending content on each platform
   - Analyze common patterns in successful content
   - Identify key elements (duration, style, music type)

2. **Personalized Recommendations**:
   - Analyze user's historical performance
   - Compare with trending patterns
   - Generate personalized recommendations

3. **A/B Testing Workflow**:
   - Generate multiple variants of content
   - Distribute to similar audience segments
   - Collect performance metrics
   - Identify winning variant

## 6. Security Considerations

### 6.1 Authentication and Authorization

**Implementation Requirements**:
- OAuth 2.0 with JWT for authentication
- Role-based access control (RBAC)
- Secure session management
- Multi-factor authentication option
- API key management for platform integrations

**Security Framework**:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

# Secret key and algorithm
SECRET_KEY = "your-secret-key"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "user")
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception
        
    # Get user from database
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
        
    return user

def get_admin_user(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user
```

### 6.2 Data Security

**Requirements**:
- Data encryption at rest and in transit
- Secure credential storage
- Platform API token secure management
- Personal data handling in compliance with GDPR and CCPA
- Regular security audits

**Implementation**:
- Use of HTTPS for all communications
- Database encryption for sensitive fields
- Google Cloud KMS for API key management
- Data retention policies and automatic deletion
- Logging of all sensitive operations

### 6.3 Content Security

**Requirements**:
- Content moderation for uploads
- Copyright compliance
- Age-appropriate content enforcement
- Content ownership verification
- Automated content scanning

## 7. Scalability and Performance

### 7.1 Horizontal Scaling Architecture

**Components**:
- Kubernetes-based microservices deployment
- Auto-scaling based on CPU/memory utilization
- Distributed rendering using worker pools
- Load balancing for API requests
- Caching layer for frequently accessed data

**Scaling Strategy**:
```yaml
# kubernetes/video-processor-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-processor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: video-processor
  template:
    metadata:
      labels:
        app: video-processor
    spec:
      containers:
      - name: video-processor
        image: youtube-shorts-machine/video-processor:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        env:
        - name: REDIS_HOST
          value: "redis-service"
        - name: GCS_BUCKET
          value: "youtube-shorts-machine-media"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: video-processor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: video-processor
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 7.2 Performance Optimization

**Video Processing Optimization**:
- GPU acceleration for video rendering
- Caching of intermediate results
- Progressive rendering for preview generation
- Parallel processing of independent tasks
- Adaptive quality settings based on load

**Database Optimization**:
- Database query optimization
- Index design for common queries
- Connection pooling
- Read replicas for analytics queries
- Partitioning for large tables

### 7.3 Caching Strategy

**Implementation**:
- Redis for API response caching
- CDN for media file delivery
- Browser caching for static assets
- Memory caching for frequent computation results
- Distributed caching for session data

## 8. Technical Requirements by Feature

### 8.1 AI-Powered Shorts Creation

**Beat Synchronization**:
- Librosa for beat detection and analysis
- FFT (Fast Fourier Transform) for waveform analysis
- Machine learning model for identifying optimal transition points
- Frame-accurate synchronization with FFMPEG

**Implementation**:
```python
import librosa
import numpy as np

def detect_beats(audio_path, sensitivity=1.0):
    """
    Detect beats in an audio file
    
    Args:
        audio_path (str): Path to audio file
        sensitivity (float): Beat detection sensitivity
        
    Returns:
        tuple: (tempo, beat_frames, beat_times)
    """
    y, sr = librosa.load(audio_path)
    
    # Compute onset envelope
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    
    # Dynamic beat tracker
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, 
                                         sr=sr,
                                         start_bpm=120,
                                         tightness=sensitivity)
    
    # Convert frames to time
    beat_times = librosa.frames_to_time(beats, sr=sr)
    
    # Get waveform amplitude for each beat
    amplitudes = []
    for beat in beats:
        if beat < len(onset_env):
            amplitudes.append(onset_env[beat])
        else:
            amplitudes.append(0)
    
    # Normalize amplitudes
    if amplitudes:
        max_amp = max(amplitudes)
        if max_amp > 0:
            amplitudes = [a/max_amp for a in amplitudes]
    
    return {
        'tempo': tempo,
        'beat_frames': beats.tolist(),
        'beat_times': beat_times.tolist(),
        'beat_strengths': amplitudes
    }
```

### 8.2 Dynamic Text Overlays & Animations

**Requirements**:
- Text animation templates with parameters
- Font selection based on video style
- Text positioning based on content analysis
- Motion tracking for text attachment to objects

**Implementation**:
```python
class TextOverlay:
    def __init__(self, text, style, duration, start_time):
        self.text = text
        self.style = style
        self.duration = duration
        self.start_time = start_time
        self.end_time = start_time + duration
        self.keyframes = []
        
    def add_keyframe(self, time, properties):
        """Add a keyframe for animation"""
        self.keyframes.append({
            'time': time,
            'properties': properties
        })
        
    def render(self, frame, current_time, frame_size):
        """Render text overlay on a frame"""
        if current_time < self.start_time or current_time > self.end_time:
            return frame
            
        # Calculate properties at current time using keyframe interpolation
        properties = self._interpolate_properties(current_time)
        
        # Render text using properties
        # Implementation depends on the rendering library (OpenCV, PIL, etc.)
        
        return frame
        
    def _interpolate_properties(self, current_time):
        """Interpolate properties between keyframes"""
        # Find surrounding keyframes
        prev_keyframe = None
        next_keyframe = None
        
        for keyframe in self.keyframes:
            if keyframe['time'] <= current_time:
                if prev_keyframe is None or keyframe['time'] > prev_keyframe['time']:
                    prev_keyframe = keyframe
            
            if keyframe['time'] >= current_time:
                if next_keyframe is None or keyframe['time'] < next_keyframe['time']:
                    next_keyframe = keyframe
        
        # If no keyframes or only one, use it directly
        if prev_keyframe is None and next_keyframe is None:
            return self.style
        
        if prev_keyframe is None:
            return next_keyframe['properties']
            
        if next_keyframe is None:
            return prev_keyframe['properties']
        
        # Interpolate between keyframes
        t = (current_time - prev_keyframe['time']) / (next_keyframe['time'] - prev_keyframe['time'])
        
        result = {}
        for key in prev_keyframe['properties']:
            if key in next_keyframe['properties']:
                # Linear interpolation
                result[key] = prev_keyframe['properties'][key] * (1-t) + next_keyframe['properties'][key] * t
            else:
                result[key] = prev_keyframe['properties'][key]
                
        return result
```

### 8.3 Cross-Platform Distribution

**Requirements**:
- Platform-specific format adaptation
- Metadata customization per platform
- Scheduling optimization
- Engagement tracking across platforms
- Cross-posting analytics

**Platform Format Requirements**:

| Platform | Aspect Ratio | Max Duration | Resolution | Bitrate | Audio |
|----------|--------------|--------------|------------|---------|-------|
| YouTube Shorts | 9:16 | 60s | 1080x1920 | 8 Mbps | 128 kbps |
| TikTok | 9:16 | 60s | 1080x1920 | 8 Mbps | 128 kbps |
| Instagram Reels | 9:16 | 90s | 1080x1920 | 8 Mbps | 128 kbps |
| Facebook Reels | 9:16 | 60s | 1080x1920 | 8 Mbps | 128 kbps |

**Implementation**:
```python
def optimize_video_for_platform(video_path, platform, output_path):
    """
    Optimize video for specific platform requirements
    
    Args:
        video_path (str): Path to input video
        platform (str): Target platform (youtube_shorts, tiktok, instagram, facebook)
        output_path (str): Path for optimized output
        
    Returns:
        str: Path to optimized video
    """
    platform_settings = {
        'youtube_shorts': {
            'aspect_ratio': '9:16',
            'max_duration': 60,
            'resolution': '1080x1920',
            'bitrate': '8M',
            'audio_bitrate': '128k'
        },
        'tiktok': {
            'aspect_ratio': '9:16',
            'max_duration': 60,
            'resolution': '1080x1920',
            'bitrate': '8M',
            'audio_bitrate': '128k'
        },
        'instagram': {
            'aspect_ratio': '9:16',
            'max_duration': 90,
            'resolution': '1080x1920',
            'bitrate': '8M',
            'audio_bitrate': '128k'
        },
        'facebook': {
            'aspect_ratio': '9:16',
            'max_duration': 60,
            'resolution': '1080x1920',
            'bitrate': '8M',
            'audio_bitrate': '128k'
        }
    }
    
    settings = platform_settings.get(platform, platform_settings['youtube_shorts'])
    
    # Trim if needed
    if settings['max_duration']:
        # Check video duration and trim if necessary
        pass
        
    # Create FFMPEG command for format conversion
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vf', f'scale={settings["resolution"].split("x")[0]}:{settings["resolution"].split("x")[1]}',
        '-c:v', 'libx264',
        '-b:v', settings['bitrate'],
        '-c:a', 'aac',
        '-b:a', settings['audio_bitrate'],
        '-movflags', '+faststart',
        output_path
    ]
    
    # Execute command
    subprocess.run(cmd, check=True)
    
    return output_path
```

### 8.4 AI Trend Detection & Optimization

**Requirements**:
- Data collection from platform APIs
- Time-series analysis of content performance
- Machine learning model for trend prediction
- A/B testing framework
- Recommendation engine

**Implementation**:
```python
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

class TrendAnalyzer:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_columns = [
            'duration', 'has_captions', 'music_tempo', 'num_transitions',
            'brightness', 'saturation', 'text_duration_ratio', 'hour_posted',
            'day_of_week', 'thumbnail_face_count', 'title_length'
        ]
        
    def train(self, video_data):
        """
        Train the trend prediction model
        
        Args:
            video_data (pd.DataFrame): DataFrame with video performance metrics
        """
        X = video_data[self.feature_columns]
        y = video_data['engagement_score']
        
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        
    def predict_performance(self, video_features):
        """
        Predict performance of a video based on its features
        
        Args:
            video_features (dict): Video features matching the feature_columns
            
        Returns:
            float: Predicted engagement score
        """
        features_df = pd.DataFrame([video_features])
        
        # Fill missing columns
        for col in self.feature_columns:
            if col not in features_df.columns:
                features_df[col] = 0
        
        X = features_df[self.feature_columns]
        X_scaled = self.scaler.transform(X)
        
        return self.model.predict(X_scaled)[0]
        
    def get_feature_importance(self):
        """Get importance of each feature in the model"""
        importance = self.model.feature_importances_
        
        return {
            feature: importance[i] 
            for i, feature in enumerate(self.feature_columns)
        }
        
    def suggest_improvements(self, video_features):
        """
        Suggest improvements to increase engagement
        
        Args:
            video_features (dict): Current video features
            
        Returns:
            list: Suggestions for improvement
        """
        baseline_score = self.predict_performance(video_features)
        feature_importance = self.get_feature_importance()
        
        suggestions = []
        
        # Try modifying each feature to see impact
        for feature, importance in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True):
            modified_features = video_features.copy()
            
            # Modify feature based on its type
            if feature == 'duration' and video_features.get('duration', 0) < 45:
                modified_features['duration'] = min(60, video_features.get('duration', 0) + 15)
                new_score = self.predict_performance(modified_features)
                
                if new_score > baseline_score:
                    suggestions.append({
                        'feature': feature,
                        'suggestion': f"Increase video duration to {modified_features['duration']} seconds",
                        'impact': (new_score - baseline_score) / baseline_score * 100
                    })
            
            # Add similar logic for other features
            
        return suggestions
```

## 9. Implementation Roadmap

### 9.1 Phase 1: Core System (Weeks 1-4)

**Week 1: Infrastructure Setup**
- Set up Kubernetes cluster
- Configure CI/CD pipeline
- Set up monitoring and logging
- Establish development environment

**Week 2: Core Services**
- Implement API Gateway
- Develop Authentication Service
- Set up Google Cloud Storage integration
- Create database schema

**Week 3: Video Processing**
- Implement music analysis service
- Develop basic video generation
- Create transition engine
- Set up background processing

**Week 4: YouTube API Integration**
- Implement OAuth flow
- Develop video upload service
- Create metadata management
- Build scheduling system

### 9.2 Phase 2: AI Enhancements (Weeks 5-8)

**Week 5: Advanced Video Processing**
- Implement beat synchronization
- Develop text animations
- Create effects engine
- Implement template system

**Week 6: AI Models Integration**
- Set up ML model serving
- Implement style recommendation
- Develop trend analysis
- Create engagement prediction

**Week 7: UI Development**
- Build React frontend
- Implement video preview
- Create dashboard
- Develop settings interface

**Week 8: Testing & Optimization**
- Performance testing
- Security audit
- UI/UX testing
- Beta testing with users

### 9.3 Phase 3: Platform Expansion (Weeks 9-12)

**Week 9: Multi-Platform Integration**
- Implement TikTok API integration
- Develop Instagram Reels support
- Create Facebook Reels integration
- Build cross-platform analytics

**Week 10: Subscription & Monetization**
- Implement subscription system
- Develop payment processing
- Create licensing management
- Build analytics dashboard

**Week 11: Advanced Features**
- Implement A/B testing
- Develop bulk processing
- Create content calendar
- Build advanced analytics

**Week 12: Launch Preparation**
- Final security audit
- Production environment setup
- Documentation
- User onboarding flow

### 9.4 Milestones and Deliverables

**Milestone 1: MVP Release (Week 4)**
- Core video generation capability
- YouTube upload integration
- Basic user interface
- Single video processing flow

**Milestone 2: AI Enhancement Release (Week 8)**
- AI-powered video creation
- Smart transitions and effects
- Performance recommendations
- Enhanced user interface

**Milestone 3: Multi-Platform Release (Week 12)**
- Support for all target platforms
- Subscription model
- Advanced analytics
- Bulk processing and scheduling

## 10. Testing & Quality Assurance

### 10.1 Unit Testing

**Requirements**:
- Test coverage > 80% for all services
- Automated test suite with PyTest
- CI/CD integration for continuous testing
- Mocking of external services

**Example Test Suite**:
```python
# test_video_processor.py
import pytest
from video_processor import detect_beats, create_transitions

@pytest.fixture
def sample_audio_path():
    return "tests/resources/sample_track.mp3"

def test_beat_detection(sample_audio_path):
    """Test beat detection algorithm"""
    result = detect_beats(sample_audio_path)
    
    # Check structure
    assert 'tempo' in result
    assert 'beat_times' in result
    assert 'beat_frames' in result
    assert 'beat_strengths' in result
    
    # Check values
    assert 60 <= result['tempo'] <= 200
    assert len(result['beat_times']) > 0
    assert len(result['beat_frames']) > 0
    assert len(result['beat_strengths']) > 0
    
    # Check consistency
    assert len(result['beat_times']) == len(result['beat_frames'])
    assert len(result['beat_times']) == len(result['beat_strengths'])
    
def test_transition_creation():
    """Test transition generation from beats"""
    beats = {
        'tempo': 120,
        'beat_times': [0.5, 1.0, 1.5, 2.0, 2.5],
        'beat_strengths': [0.5, 0.7, 0.9, 0.6, 0.8]
    }
    
    transitions = create_transitions(beats, 'default')
    
    # Check transitions are created at strong beats
    assert len(transitions) > 0
    assert all(t['time'] in beats['beat_times'] for t in transitions)
    
    # Check stronger beats have more dramatic transitions
    strong_transitions = [t for t in transitions if t['strength'] > 0.7]
    weak_transitions = [t for t in transitions if t['strength'] <= 0.7]
    
    if strong_transitions and weak_transitions:
        assert strong_transitions[0]['effect_intensity'] > weak_transitions[0]['effect_intensity']
```

### 10.2 Integration Testing

**Requirements**:
- End-to-end workflow testing
- API contract testing
- Service interaction verification
- Database integration testing

### 10.3 Performance Testing

**Requirements**:
- Load testing with simulated users
- Video processing benchmarks
- API response time testing
- Concurrency testing

**Test Parameters**:
- Target API response time < 200ms
- Video processing time < 2 minutes for 60s video
- Support for 100 concurrent video generations
- Storage and retrieval latency < 500ms

## 11. Monitoring and Observability

### 11.1 Monitoring Infrastructure

**Components**:
- Prometheus for metrics collection
- Grafana for visualization
- ELK stack for log management
- Jaeger for distributed tracing
- AlertManager for alerting

**Key Metrics**:
- System resource utilization (CPU, memory, disk)
- API request rates and latency
- Processing queue length and processing time
- Error rates and types
- User activity and engagement

**Alerting Rules**:
- API response time > 1s for 5 minutes
- Error rate > 5% for 5 minutes
- Processing queue > 100 items for 15 minutes
- Any service instance down for > 2 minutes
- Storage usage > 90%

### 11.2 Logging Strategy

**Log Collection**:
- Structured JSON logging format
- Centralized log collection with Filebeat
- Log correlation with request IDs
- Log retention policy (30 days)

**Log Levels**:
- ERROR: Operational errors requiring intervention
- WARNING: Issues that don't stop operation but need attention
- INFO: Normal operational events
- DEBUG: Detailed information for troubleshooting (development only)

### 11.3 Reporting

**Regular Reports**:
- System health dashboard
- Processing volume and throughput
- Error rate and common issues
- Resource utilization trends
- Performance optimization opportunities

---

This Technical PRD provides a comprehensive blueprint for implementing the YouTube Shorts Machine. The document covers architectural decisions, detailed component specifications, data models, processing workflows, security considerations, and implementation plans. This will serve as the primary reference for developers during the implementation phase.