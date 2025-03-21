# Enhanced Music-Responsive Video Generator

This feature creates videos that dynamically respond to music, creating a more engaging and professional-looking video output. The music-responsive video generator analyzes audio tracks to detect beats, energy levels, and other musical features, then applies visual effects that are tightly synchronized with the music.

## Features

- **Advanced Audio Analysis**: Detects beats, onsets, spectral characteristics, and energy levels
- **Multiple Dynamic Visual Effects**: Various effects that respond to different music features
- **Beat-Synchronized Image Transitions**: Images change in sync with the music's rhythm
- **Customizable Intensity**: Control how dramatic the music-responsive effects appear
- **Adaptive Effect Selection**: More complex effects are automatically enabled at higher intensity settings
- **Consistent High-Quality Output**: Professional-looking results with minimal effort

## How It Works

1. The system analyzes the music track to extract key features:
   - Beats and tempo
   - Onsets and transients
   - Spectral characteristics (centroid, contrast)
   - Harmonic and percussive separation
   - Energy levels (RMS)

2. It applies real-time effects to images based on these music features:
   - Basic effects (pulse, color shift, shake) at all intensity levels
   - Advanced effects (warp, glitch) at higher intensity levels
   - Different effects respond to different music features

3. Effects and image transitions are synchronized with the music's rhythm and energy
4. The result is a cohesive video that feels professionally produced with the music and visuals working together

## Available Effects

The music-responsive video generator includes several effect types:

### Basic Effects
1. **Pulse Effect**: Creates subtle zoom effects synchronized with beats
2. **Color Shift Effect**: Shifts colors based on spectral characteristics of the music
3. **Shake Effect**: Adds camera shake during strong onsets or percussion hits

### Advanced Effects
4. **Flash Effect**: Creates brief flashes on strong beats or percussion hits
5. **Vignette Effect**: Dynamic vignette that responds to music energy
6. **Warp Effect**: Creates dynamic warping based on music energy (enabled at intensity > 1.2)
7. **Glitch Effect**: Creates digital glitches on percussion hits (enabled at intensity > 1.5)

## Usage

### API Endpoint

```
POST /videos/music-responsive
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| music_track | string | Name of the music track to use |
| images | files | List of image files to include in the video |
| effect_intensity | float | Controls how strong the effects appear (0.0 to 2.0, default: 1.0) |
| duration | integer | Target duration in seconds (default: 60) |

### Example Request

```bash
curl -X POST http://localhost:8000/videos/music-responsive \
  -F "music_track=track1.mp3" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "images=@image3.jpg" \
  -F "effect_intensity=1.2" \
  -F "duration=45"
```

### Example Response

```json
{
  "video_id": "7f4b8e1d-6a3c-4b5d-9e8f-2d3a4b5c6d7e",
  "status": "ready_for_upload",
  "message": "Music-responsive video creation completed",
  "track": "track1.mp3",
  "effect_intensity": 1.2,
  "images_count": 3,
  "video_url": "https://storage.googleapis.com/youtubeshorts123/videos/7f4b8e1d-6a3c-4b5d-9e8f-2d3a4b5c6d7e.mp4"
}
```

## Testing

You can use the test script to quickly test the music-responsive video generation:

### Standard Test
```bash
python test_local.py --mode=standard --intensity=1.5 --debug
```

### Advanced Effects Test
```bash
python test_local.py --test-case=advanced --intensity=1.8 --debug
```

### Individual Effect Tests
```bash
python test_local.py --test-case=pulse --intensity=1.5 --debug
python test_local.py --test-case=color --intensity=1.5 --debug
python test_local.py --test-case=shake --intensity=1.5 --debug
python test_local.py --test-case=flash --intensity=1.5 --debug
python test_local.py --test-case=warp --intensity=1.5 --debug
python test_local.py --test-case=vignette --intensity=1.5 --debug
python test_local.py --test-case=glitch --intensity=1.5 --debug
```

## Intensity Guidelines

- **Low Intensity (0.5-0.8)**:
  - Subtle effects
  - Good for calm, atmospheric music
  - Only basic effects are active

- **Medium Intensity (0.9-1.2)**:
  - Moderate effects
  - Good for most music types
  - Only basic effects are active, but stronger

- **High Intensity (1.3-1.7)**:
  - Strong effects
  - Good for energetic music
  - Basic effects + warp effect

- **Maximum Intensity (1.8-2.0)**:
  - Very strong effects
  - Good for electronic/dance music
  - All effects active, including glitch

## Technical Details

The music-responsive video generator uses the following libraries and techniques:

- **Librosa**: For advanced audio analysis and beat detection
- **OpenCV**: For image manipulation and video creation
- **NumPy**: For fast numerical operations on image and audio data

The system includes fallback modes for development and debugging scenarios.

## Performance Considerations

- Processing time increases with video duration, higher FPS, and more effects
- For optimal performance, limit video duration to 30-60 seconds
- Higher intensity values enable more effects, which may increase processing time
- For optimal results, provide at least 5 high-quality images 