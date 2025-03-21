"""
API endpoints for music recommendations.
"""
from fastapi import APIRouter, HTTPException, Query, Path, Body, UploadFile, File, Form
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.app.services.music.recommendations import get_music_recommendation_service
from src.app.services.gcs.storage import get_music_url
from src.app.core.settings import UPLOAD_DIR
import os
import tempfile
import logging

router = APIRouter(prefix="/music-recommendations", tags=["music-recommendations"])
logger = logging.getLogger(__name__)

class TrackRecommendation(BaseModel):
    """Track recommendation model for API responses."""
    track_name: str = Field(..., description="Name of the track in storage")
    title: str = Field(..., description="Title of the track")
    artist: str = Field("Nova Sounds", description="Artist of the track")
    genre: Optional[str] = Field(None, description="Genre of the track")
    bpm: float = Field(..., description="Beats per minute (tempo)")
    key: str = Field(..., description="Musical key of the track")
    duration: float = Field(..., description="Duration in seconds")
    energy: float = Field(..., description="Energy level (0-1)")
    mood: str = Field(..., description="Mood of the track")
    url: Optional[str] = Field(None, description="URL to stream the track")
    relevance_score: Optional[float] = Field(None, description="Relevance score for the recommendation")
    similarity_score: Optional[float] = Field(None, description="Similarity score for the recommendation")
    
class RecommendationRequest(BaseModel):
    """Request model for video-based recommendations."""
    video_id: str = Field(..., description="ID of the video to recommend for")
    count: int = Field(5, description="Number of recommendations to return")
    preferred_genres: Optional[List[str]] = Field(None, description="Preferred genres")
    preferred_moods: Optional[List[str]] = Field(None, description="Preferred moods")
    min_bpm: Optional[int] = Field(None, description="Minimum BPM")
    max_bpm: Optional[int] = Field(None, description="Maximum BPM")
    energy_level: Optional[float] = Field(None, description="Target energy level (0-1)")

@router.post("/for-video", response_model=List[TrackRecommendation])
async def recommend_for_video(request: RecommendationRequest):
    """
    Recommend music tracks for a specific video.
    
    Analyzes the video content and suggests music that would match well.
    """
    try:
        recommendation_service = get_music_recommendation_service()
        
        # Construct the video path
        video_path = os.path.join(UPLOAD_DIR, "videos", f"{request.video_id}.mp4")
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail=f"Video with ID {request.video_id} not found")
        
        # Get recommendations
        recommendations = recommendation_service.recommend_for_video(
            video_path=video_path,
            count=request.count,
            preferred_genres=request.preferred_genres,
            preferred_moods=request.preferred_moods,
            min_bpm=request.min_bpm,
            max_bpm=request.max_bpm,
            energy_level=request.energy_level
        )
        
        # Format the response
        formatted_recommendations = []
        for rec in recommendations:
            track_name = rec.get("track_name", "")
            formatted_recommendations.append({
                "track_name": track_name,
                "title": rec.get("title", track_name),
                "artist": rec.get("artist", "Nova Sounds"),
                "genre": rec.get("genre", "Unknown"),
                "bpm": rec.get("bpm", 120.0),
                "key": rec.get("key", "C Major"),
                "duration": rec.get("duration", 180.0),
                "energy": rec.get("energy", 0.5),
                "mood": rec.get("mood", "Neutral"),
                "url": get_music_url(track_name),
                "relevance_score": rec.get("relevance_score")
            })
        
        return formatted_recommendations
    except Exception as e:
        logger.error(f"Error recommending music for video: {e}")
        raise HTTPException(status_code=500, detail=f"Error recommending music: {str(e)}")

@router.post("/for-uploaded-video", response_model=List[TrackRecommendation])
async def recommend_for_uploaded_video(
    video: UploadFile = File(...),
    count: int = Form(5),
    preferred_genres: Optional[str] = Form(None),
    preferred_moods: Optional[str] = Form(None),
    min_bpm: Optional[int] = Form(None),
    max_bpm: Optional[int] = Form(None),
    energy_level: Optional[float] = Form(None)
):
    """
    Recommend music tracks for an uploaded video.
    
    Upload a video file and get music recommendations that would match it.
    """
    try:
        recommendation_service = get_music_recommendation_service()
        
        # Parse comma-separated strings to lists if provided
        genres_list = None
        if preferred_genres:
            genres_list = [g.strip() for g in preferred_genres.split(",")]
            
        moods_list = None
        if preferred_moods:
            moods_list = [m.strip() for m in preferred_moods.split(",")]
        
        # Save the uploaded video to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file_path = temp_file.name
            content = await video.read()
            temp_file.write(content)
        
        try:
            # Get recommendations
            recommendations = recommendation_service.recommend_for_video(
                video_path=temp_file_path,
                count=count,
                preferred_genres=genres_list,
                preferred_moods=moods_list,
                min_bpm=min_bpm,
                max_bpm=max_bpm,
                energy_level=energy_level
            )
            
            # Format the response
            formatted_recommendations = []
            for rec in recommendations:
                track_name = rec.get("track_name", "")
                formatted_recommendations.append({
                    "track_name": track_name,
                    "title": rec.get("title", track_name),
                    "artist": rec.get("artist", "Nova Sounds"),
                    "genre": rec.get("genre", "Unknown"),
                    "bpm": rec.get("bpm", 120.0),
                    "key": rec.get("key", "C Major"),
                    "duration": rec.get("duration", 180.0),
                    "energy": rec.get("energy", 0.5),
                    "mood": rec.get("mood", "Neutral"),
                    "url": get_music_url(track_name),
                    "relevance_score": rec.get("relevance_score")
                })
            
            return formatted_recommendations
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        logger.error(f"Error recommending music for uploaded video: {e}")
        raise HTTPException(status_code=500, detail=f"Error recommending music: {str(e)}")

@router.get("/similar/{track_name}", response_model=List[TrackRecommendation])
async def recommend_similar_tracks(
    track_name: str = Path(..., description="Name of the reference track"),
    count: int = Query(5, description="Number of similar tracks to return")
):
    """
    Recommend tracks similar to the specified track.
    
    Finds tracks with similar genre, mood, tempo, and energy level.
    """
    try:
        recommendation_service = get_music_recommendation_service()
        
        # Get similar tracks
        similar_tracks = recommendation_service.recommend_similar(
            track_name=track_name,
            count=count
        )
        
        # Format the response
        formatted_recommendations = []
        for rec in similar_tracks:
            track_name = rec.get("track_name", "")
            formatted_recommendations.append({
                "track_name": track_name,
                "title": rec.get("title", track_name),
                "artist": rec.get("artist", "Nova Sounds"),
                "genre": rec.get("genre", "Unknown"),
                "bpm": rec.get("bpm", 120.0),
                "key": rec.get("key", "C Major"),
                "duration": rec.get("duration", 180.0),
                "energy": rec.get("energy", 0.5),
                "mood": rec.get("mood", "Neutral"),
                "url": get_music_url(track_name),
                "similarity_score": rec.get("similarity_score")
            })
        
        return formatted_recommendations
    except Exception as e:
        logger.error(f"Error finding similar tracks: {e}")
        raise HTTPException(status_code=500, detail=f"Error finding similar tracks: {str(e)}")

@router.get("/trending", response_model=List[TrackRecommendation])
async def get_trending_tracks(
    count: int = Query(5, description="Number of trending tracks to return")
):
    """
    Get currently trending music tracks.
    
    Returns tracks that are currently popular or trending.
    """
    try:
        recommendation_service = get_music_recommendation_service()
        
        # Get trending tracks
        trending_tracks = recommendation_service.recommend_trending(count=count)
        
        # Format the response
        formatted_recommendations = []
        for rec in trending_tracks:
            track_name = rec.get("track_name", "")
            formatted_recommendations.append({
                "track_name": track_name,
                "title": rec.get("title", track_name),
                "artist": rec.get("artist", "Nova Sounds"),
                "genre": rec.get("genre", "Unknown"),
                "bpm": rec.get("bpm", 120.0),
                "key": rec.get("key", "C Major"),
                "duration": rec.get("duration", 180.0),
                "energy": rec.get("energy", 0.5),
                "mood": rec.get("mood", "Neutral"),
                "url": get_music_url(track_name),
                "popularity": rec.get("popularity", 0.5),
                "trending_position": rec.get("trending_position")
            })
        
        return formatted_recommendations
    except Exception as e:
        logger.error(f"Error getting trending tracks: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting trending tracks: {str(e)}")

@router.post("/batch-recommend", response_model=Dict[str, List[TrackRecommendation]])
async def batch_recommend(
    video_ids: List[str] = Body(..., description="List of video IDs to get recommendations for"),
    count_per_video: int = Body(3, description="Number of recommendations per video")
):
    """
    Get recommendations for multiple videos in a single request.
    
    Batch processing for music recommendations across multiple videos.
    """
    try:
        recommendation_service = get_music_recommendation_service()
        
        # Process each video
        results = {}
        for video_id in video_ids:
            video_path = os.path.join(UPLOAD_DIR, "videos", f"{video_id}.mp4")
            
            # Skip if video doesn't exist
            if not os.path.exists(video_path):
                logger.warning(f"Video {video_id} not found, skipping")
                continue
            
            # Get recommendations
            recommendations = recommendation_service.recommend_for_video(
                video_path=video_path,
                count=count_per_video
            )
            
            # Format the recommendations
            formatted_recommendations = []
            for rec in recommendations:
                track_name = rec.get("track_name", "")
                formatted_recommendations.append({
                    "track_name": track_name,
                    "title": rec.get("title", track_name),
                    "artist": rec.get("artist", "Nova Sounds"),
                    "genre": rec.get("genre", "Unknown"),
                    "bpm": rec.get("bpm", 120.0),
                    "key": rec.get("key", "C Major"),
                    "duration": rec.get("duration", 180.0),
                    "energy": rec.get("energy", 0.5),
                    "mood": rec.get("mood", "Neutral"),
                    "url": get_music_url(track_name),
                    "relevance_score": rec.get("relevance_score")
                })
            
            results[video_id] = formatted_recommendations
        
        return results
    except Exception as e:
        logger.error(f"Error batch recommending music: {e}")
        raise HTTPException(status_code=500, detail=f"Error batch recommending music: {str(e)}")

@router.get("/debug/database-status")
async def debug_database_status():
    """
    Debug endpoint to check the state of the music preferences database.
    
    For troubleshooting and development only. Should be disabled in production.
    """
    try:
        recommendation_service = get_music_recommendation_service()
        debug_info = recommendation_service.debug_database_state()
        return debug_info
    except Exception as e:
        logger.error(f"Error checking database status: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking database status: {str(e)}")

@router.get("/debug/user-preferences/{user_id}")
async def debug_get_user_preferences(user_id: str):
    """
    Debug endpoint to get user preferences for a specific user.
    
    For troubleshooting and development only. Should be disabled in production.
    """
    try:
        recommendation_service = get_music_recommendation_service()
        preferences = recommendation_service.export_user_preferences(user_id)
        if not preferences:
            return {"message": f"No preferences found for user {user_id}", "preferences": {}}
        return {"message": "User preferences found", "preferences": preferences}
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting user preferences: {str(e)}")

@router.post("/debug/create-test-preferences/{user_id}")
async def debug_create_test_preferences(
    user_id: str,
    num_tracks: int = Query(5, description="Number of random liked tracks to create")
):
    """
    Debug endpoint to create test user preferences.
    
    For troubleshooting and development only. Should be disabled in production.
    """
    try:
        import random
        from src.app.services.gcs.storage import list_music_tracks
        
        recommendation_service = get_music_recommendation_service()
        
        # Get some random tracks
        all_tracks = list_music_tracks(limit=100)
        if not all_tracks:
            raise HTTPException(status_code=404, detail="No music tracks found")
        
        # Select random tracks
        liked_tracks = random.sample(all_tracks, min(num_tracks, len(all_tracks)))
        
        # Create preferences
        preferences = {
            "favorite_genres": ["Electronic", "Hip Hop"],
            "favorite_moods": ["Energetic", "Upbeat"],
            "liked_tracks": liked_tracks,
            "disliked_tracks": [],
            "listened_tracks": liked_tracks.copy()
        }
        
        # Import preferences
        success = recommendation_service.import_user_preferences(user_id, preferences)
        
        return {
            "success": success,
            "message": f"Created test preferences for user {user_id}",
            "preferences": preferences
        }
    except Exception as e:
        logger.error(f"Error creating test preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating test preferences: {str(e)}")

@router.get("/for-user/{user_id}", response_model=List[TrackRecommendation])
async def recommend_for_user(
    user_id: str,
    count: int = Query(5, description="Number of recommendations to return"),
    context: Optional[str] = Query(None, description="Context (e.g., 'editing', 'browsing')"),
    include_genres: Optional[str] = Query(None, description="Comma-separated list of genres to include")
):
    """
    Recommend music tracks for a specific user based on their preferences.
    
    Uses the user's listening history and preferences to suggest tracks they might like.
    """
    try:
        recommendation_service = get_music_recommendation_service()
        
        # Parse comma-separated genres if provided
        preferred_genres = None
        if include_genres:
            preferred_genres = [g.strip() for g in include_genres.split(",")]
        
        # Get recommendations
        recommendations = recommendation_service.recommend_for_user(
            user_id=user_id,
            count=count,
            include_waveform=False,
            preferred_genres=preferred_genres,
            context=context
        )
        
        # Format the response
        formatted_recommendations = []
        for rec in recommendations:
            track_name = rec.get("track_name", "")
            formatted_recommendations.append({
                "track_name": track_name,
                "title": rec.get("title", track_name),
                "artist": rec.get("artist", "Nova Sounds"),
                "genre": rec.get("genre", "Unknown"),
                "bpm": rec.get("bpm", 120.0),
                "key": rec.get("key", "C Major"),
                "duration": rec.get("duration", 180.0),
                "energy": rec.get("energy", 0.5),
                "mood": rec.get("mood", "Neutral"),
                "url": get_music_url(track_name),
                "user_score": rec.get("user_score")
            })
        
        return formatted_recommendations
    except Exception as e:
        logger.error(f"Error recommending music for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error recommending music: {str(e)}")

@router.get("/debug/test-user-recommendations/{user_id}")
async def debug_test_user_recommendations(
    user_id: str,
    create_prefs_if_missing: bool = Query(True, description="Create test preferences if none exist")
):
    """
    Debug endpoint to test user-based recommendations.
    
    For troubleshooting and development only. Should be disabled in production.
    """
    try:
        recommendation_service = get_music_recommendation_service()
        result = {
            "steps": [],
            "recommendations": []
        }
        
        # Step 1: Check if user preferences exist
        preferences = recommendation_service.export_user_preferences(user_id)
        if preferences:
            result["steps"].append({
                "step": "check_preferences",
                "status": "found",
                "message": f"Found existing preferences for user {user_id}"
            })
        else:
            result["steps"].append({
                "step": "check_preferences",
                "status": "not_found",
                "message": f"No preferences found for user {user_id}"
            })
            
            # Create test preferences if requested
            if create_prefs_if_missing:
                import random
                from src.app.services.gcs.storage import list_music_tracks
                
                result["steps"].append({
                    "step": "create_preferences",
                    "status": "started",
                    "message": "Creating test preferences"
                })
                
                # Get some random tracks
                all_tracks = list_music_tracks(limit=100)
                liked_tracks = random.sample(all_tracks, min(5, len(all_tracks)))
                
                # Create preferences
                preferences = {
                    "favorite_genres": ["Electronic", "Hip Hop"],
                    "favorite_moods": ["Energetic", "Upbeat"],
                    "liked_tracks": liked_tracks,
                    "disliked_tracks": [],
                    "listened_tracks": liked_tracks.copy()
                }
                
                # Import preferences
                success = recommendation_service.import_user_preferences(user_id, preferences)
                
                result["steps"].append({
                    "step": "create_preferences",
                    "status": "completed" if success else "failed",
                    "message": "Test preferences created successfully" if success else "Failed to create test preferences"
                })
        
        # Step 2: Get recommendations
        result["steps"].append({
            "step": "get_recommendations",
            "status": "started",
            "message": "Getting user recommendations"
        })
        
        recommendations = recommendation_service.recommend_for_user(
            user_id=user_id,
            count=5,
            include_waveform=False
        )
        
        # Format the recommendations
        formatted_recommendations = []
        for rec in recommendations:
            track_name = rec.get("track_name", "")
            formatted_recommendations.append({
                "track_name": track_name,
                "title": rec.get("title", track_name),
                "artist": rec.get("artist", "Nova Sounds"),
                "genre": rec.get("genre", "Unknown"),
                "mood": rec.get("mood", "Neutral"),
                "user_score": rec.get("user_score")
            })
        
        result["recommendations"] = formatted_recommendations
        result["steps"].append({
            "step": "get_recommendations",
            "status": "completed",
            "message": f"Found {len(formatted_recommendations)} recommendations"
        })
        
        # Final status
        result["success"] = True
        result["message"] = "User recommendation test completed successfully"
        
        return result
    except Exception as e:
        logger.error(f"Error testing user recommendations: {e}")
        return {
            "success": False,
            "message": f"Error testing user recommendations: {str(e)}",
            "steps": result.get("steps", []),
            "error_details": str(e)
        } 