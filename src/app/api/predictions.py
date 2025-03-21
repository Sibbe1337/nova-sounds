"""API endpoints for engagement performance prediction."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from src.app.services.ai.performance_predictor import get_performance_predictor
from src.app.services.video.music_responsive.analytics import get_analytics_manager

router = APIRouter(prefix="/predictions", tags=["predictions"])

class PredictionRequest(BaseModel):
    """Request model for performance prediction."""
    duration: float
    effects: List[str]
    preset: str
    audio_features: Optional[Dict[str, Any]] = None

class AudioFeatures(BaseModel):
    """Audio features for prediction."""
    tempo: Optional[float] = 120.0
    energy: Optional[float] = 0.5
    beat_strength: Optional[float] = 0.6

@router.post("/", response_model=Dict[str, Any])
async def predict_performance(request: PredictionRequest):
    """
    Predict the performance of a video based on its attributes.
    
    Args:
        request: PredictionRequest containing video attributes
        
    Returns:
        Dictionary containing prediction results
    """
    try:
        # Get the performance predictor
        predictor = get_performance_predictor()
        
        # Prepare the video data
        video_data = {
            "duration": request.duration,
            "effects": request.effects,
            "preset": request.preset,
            "audio_features": request.audio_features or {}
        }
        
        # Make the prediction
        prediction_result = predictor.predict(video_data)
        
        return prediction_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error making prediction: {str(e)}")

@router.get("/test", response_model=Dict[str, Any])
async def test_prediction():
    """
    Endpoint for testing prediction functionality with default values.
    
    Returns:
        Dictionary containing prediction results
    """
    # Default test values
    video_data = {
        "duration": 60.0,
        "effects": ["pulse", "zoom"],
        "preset": "standard",
        "audio_features": {
            "tempo": 120.0,
            "energy": 0.7,
            "beat_strength": 0.6
        }
    }
    
    try:
        # Get the performance predictor
        predictor = get_performance_predictor()
        
        # Make the prediction
        prediction_result = predictor.predict(video_data)
        
        return prediction_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing prediction: {str(e)}")

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_prediction_history():
    """
    Get the history of past predictions with their actual performance data if available.
    
    Returns:
        List of prediction records with actual performance data
    """
    try:
        # Get the analytics manager
        analytics_manager = get_analytics_manager()
        
        # Get recent sessions with predictions
        sessions = analytics_manager.list_sessions(limit=10)
        
        prediction_history = []
        for session_id in sessions:
            session_data = analytics_manager.get_session(session_id)
            
            # Skip sessions without prediction data
            if not session_data or 'prediction_data' not in session_data:
                continue
                
            # Get prediction and actual performance if available
            prediction_record = {
                'session_id': session_id,
                'timestamp': session_data.get('timestamp', ''),
                'predicted': session_data['prediction_data'].get('engagement_score', 0),
                'actual': None,
                'attributes': {
                    'duration': session_data.get('duration', 0),
                    'preset': session_data.get('preset', ''),
                    'effects': session_data.get('effects', [])
                }
            }
            
            # Add actual performance if available
            if 'platform_distributions' in session_data:
                for platform, platform_data in session_data['platform_distributions'].items():
                    if 'metrics' in platform_data and 'engagement_score' in platform_data['metrics']:
                        prediction_record['actual'] = platform_data['metrics']['engagement_score']
                        prediction_record['platform'] = platform
                        break
            
            prediction_history.append(prediction_record)
        
        return prediction_history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prediction history: {str(e)}")

@router.post("/batch", response_model=List[Dict[str, Any]])
async def batch_predict(requests: List[PredictionRequest]):
    """
    Make predictions for multiple video configurations at once.
    Useful for A/B testing different video parameters.
    
    Args:
        requests: List of PredictionRequest objects
        
    Returns:
        List of prediction results
    """
    try:
        # Get the performance predictor
        predictor = get_performance_predictor()
        
        # Process each request
        results = []
        for i, request in enumerate(requests):
            # Prepare the video data
            video_data = {
                "duration": request.duration,
                "effects": request.effects,
                "preset": request.preset,
                "audio_features": request.audio_features or {}
            }
            
            # Make the prediction
            prediction_result = predictor.predict(video_data)
            
            # Add variant identifier
            prediction_result['variant_id'] = chr(65 + i)  # A, B, C, ...
            
            results.append(prediction_result)
        
        # Sort by engagement score (highest first)
        results.sort(key=lambda x: x.get('engagement_score', 0), reverse=True)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error making batch predictions: {str(e)}") 