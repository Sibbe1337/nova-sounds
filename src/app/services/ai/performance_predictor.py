"""
Performance prediction module for music-responsive videos.

This module uses historical data to predict the engagement potential
of videos before they are published.
"""

import logging
import os
import pickle
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from src.app.services.video.music_responsive.analytics import get_analytics_manager

logger = logging.getLogger(__name__)

class PerformancePredictor:
    """Predicts engagement performance for videos based on their attributes."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one predictor instance exists."""
        if cls._instance is None:
            cls._instance = super(PerformancePredictor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the performance predictor."""
        if self._initialized:
            return
            
        self._initialized = True
        self.analytics_manager = get_analytics_manager()
        self.model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.model_path = os.path.join(self.model_dir, 'performance_model.pkl')
        self.scaler_path = os.path.join(self.model_dir, 'performance_scaler.pkl')
        
        # Try to load existing model, or create a new one
        try:
            self._load_model()
        except (FileNotFoundError, EOFError):
            logger.info("No existing model found. Will train on first prediction request.")
            self.model = None
            self.scaler = StandardScaler()
    
    def _load_model(self):
        """Load the trained model from disk."""
        with open(self.model_path, 'rb') as f:
            self.model = pickle.load(f)
        with open(self.scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
    
    def _save_model(self):
        """Save the trained model to disk."""
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
    
    def _extract_features(self, video_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract features from video data for prediction.
        
        Args:
            video_data: Dictionary containing video attributes
            
        Returns:
            NumPy array of features
        """
        # Extract features that might impact engagement
        features = []
        
        # Duration in seconds
        duration = video_data.get('duration', 0)
        features.append(duration)
        
        # Number of effects used
        effects = video_data.get('effects', [])
        features.append(len(effects))
        
        # Specific effects (one-hot encoded)
        all_possible_effects = [
            'pulse', 'zoom', 'shake', 'flash', 'color_shift', 'blur', 'warp', 'glitch'
        ]
        for effect in all_possible_effects:
            features.append(1 if effect in effects else 0)
        
        # Preset encoding (simple numeric mapping)
        preset_mapping = {
            'standard': 1,
            'subtle': 2,
            'energetic': 3,
            'dramatic': 4,
            'cinematic': 5
        }
        preset = video_data.get('preset', 'standard')
        features.append(preset_mapping.get(preset, 0))
        
        # Audio features if available
        audio_features = video_data.get('audio_features', {})
        features.append(audio_features.get('tempo', 120))
        features.append(audio_features.get('beat_strength', 0.5))
        features.append(audio_features.get('energy', 0.5))
        
        return np.array(features).reshape(1, -1)
    
    def _extract_target(self, platform_data: Dict[str, Any]) -> float:
        """
        Extract the target value (engagement score) from platform data.
        
        Args:
            platform_data: Dictionary containing platform performance metrics
            
        Returns:
            Engagement score
        """
        # Simple engagement score calculation
        metrics = platform_data.get('metrics', {})
        
        views = metrics.get('views', 0)
        likes = metrics.get('likes', 0)
        comments = metrics.get('comments', 0)
        shares = metrics.get('shares', 0)
        
        # Simple weighted engagement formula
        engagement_score = (
            views * 1.0 + 
            likes * 2.0 + 
            comments * 3.0 + 
            shares * 4.0
        ) / 100.0
        
        return min(engagement_score, 10.0)  # Cap at 10.0
    
    def train_model(self) -> bool:
        """
        Train the prediction model using historical data.
        
        Returns:
            True if training was successful, False otherwise
        """
        # Collect training data from analytics
        training_data = []
        target_values = []
        
        sessions = self.analytics_manager.list_sessions()
        for session_id in sessions:
            session_data = self.analytics_manager.get_session(session_id)
            if not session_data:
                continue
                
            # Only include sessions that have platform distribution data with engagement metrics
            if 'platform_distributions' not in session_data:
                continue
                
            for platform, platform_data in session_data['platform_distributions'].items():
                if not platform_data.get('metrics', {}).get('views'):
                    continue
                    
                # Extract features and target
                try:
                    features = self._extract_features(session_data)
                    target = self._extract_target(platform_data)
                    
                    training_data.append(features[0])
                    target_values.append(target)
                except Exception as e:
                    logger.warning(f"Error extracting features for session {session_id}: {str(e)}")
        
        # Train the model if we have enough data
        if len(training_data) < 10:
            logger.warning(f"Not enough training data: {len(training_data)} samples. Need at least 10.")
            return False
            
        try:
            # Normalize features
            X = np.array(training_data)
            y = np.array(target_values)
            
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train random forest regressor
            self.model = RandomForestRegressor(
                n_estimators=100, 
                max_depth=10,
                random_state=42
            )
            self.model.fit(X_scaled, y)
            
            # Save the model
            self._save_model()
            
            logger.info(f"Model trained successfully on {len(training_data)} samples")
            return True
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
    
    def predict(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict the engagement performance of a video.
        
        Args:
            video_data: Dictionary containing video attributes
            
        Returns:
            Dictionary containing prediction results
        """
        # Train model if it doesn't exist
        if self.model is None:
            logger.info("Training model for first-time prediction")
            success = self.train_model()
            if not success:
                # Fall back to a simple heuristic if we can't train a model
                return self._heuristic_prediction(video_data)
        
        try:
            # Extract features
            features = self._extract_features(video_data)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Make prediction
            engagement_score = float(self.model.predict(features_scaled)[0])
            
            # Calculate confidence based on feature importance
            feature_importances = self.model.feature_importances_
            confidence = min(0.95, sum(feature_importances) / len(feature_importances))
            
            # Generate recommendations
            recommendations = self._generate_recommendations(video_data, features[0], feature_importances)
            
            return {
                'engagement_score': engagement_score,
                'confidence': confidence,
                'performance_category': self._categorize_score(engagement_score),
                'recommendations': recommendations
            }
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            return self._heuristic_prediction(video_data)
    
    def _heuristic_prediction(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a prediction using simple heuristics when the model is unavailable.
        
        Args:
            video_data: Dictionary containing video attributes
            
        Returns:
            Dictionary containing prediction results
        """
        # Extract basic features
        effects = video_data.get('effects', [])
        num_effects = len(effects)
        duration = video_data.get('duration', 0)
        
        # Simple heuristic formula
        base_score = 5.0  # Average score
        
        # Duration factor (optimal range is 15-60 seconds)
        if duration < 15:
            duration_factor = duration / 15.0
        elif duration <= 60:
            duration_factor = 1.0
        else:
            duration_factor = 1.0 - min(0.5, (duration - 60) / 120.0)
        
        # Effects factor (optimal range is 2-4 effects)
        if num_effects == 0:
            effects_factor = 0.7
        elif num_effects <= 4:
            effects_factor = 0.85 + (num_effects * 0.05)
        else:
            effects_factor = 1.0 - min(0.3, (num_effects - 4) * 0.1)
        
        # Calculate score
        engagement_score = base_score * duration_factor * effects_factor
        
        # Generate recommendations
        recommendations = []
        if duration < 15:
            recommendations.append("Consider making the video longer (15-60 seconds is optimal)")
        elif duration > 90:
            recommendations.append("Consider shortening the video (15-60 seconds is optimal)")
            
        if num_effects == 0:
            recommendations.append("Add some visual effects to increase engagement")
        elif num_effects > 5:
            recommendations.append("Consider using fewer effects (2-4 is optimal)")
        
        return {
            'engagement_score': engagement_score,
            'confidence': 0.6,  # Lower confidence for heuristic predictions
            'performance_category': self._categorize_score(engagement_score),
            'recommendations': recommendations,
            'note': 'Prediction based on heuristics due to insufficient training data'
        }
    
    def _categorize_score(self, score: float) -> str:
        """
        Categorize an engagement score.
        
        Args:
            score: Engagement score
            
        Returns:
            Category label
        """
        if score < 3.0:
            return 'Low Engagement'
        elif score < 6.0:
            return 'Average Engagement'
        elif score < 8.0:
            return 'High Engagement'
        else:
            return 'Viral Potential'
    
    def _generate_recommendations(self, video_data: Dict[str, Any], features: np.ndarray, importances: np.ndarray) -> List[str]:
        """
        Generate recommendations to improve engagement based on model insights.
        
        Args:
            video_data: Dictionary containing video attributes
            features: Feature array
            importances: Feature importance array
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Get most important features
        feature_names = [
            'duration', 'num_effects', 'pulse', 'zoom', 'shake', 'flash', 
            'color_shift', 'blur', 'warp', 'glitch', 'preset', 
            'tempo', 'beat_strength', 'energy'
        ]
        
        important_indices = np.argsort(importances)[-3:]  # Top 3 important features
        
        for idx in important_indices:
            feature_name = feature_names[idx]
            feature_value = features[idx]
            
            if feature_name == 'duration':
                if feature_value < 15:
                    recommendations.append("Consider making the video longer (15-60 seconds is optimal)")
                elif feature_value > 90:
                    recommendations.append("Consider shortening the video (15-60 seconds is optimal)")
                    
            elif feature_name == 'num_effects':
                if feature_value == 0:
                    recommendations.append("Add some visual effects to increase engagement")
                elif feature_value > 5:
                    recommendations.append("Consider using fewer effects (2-4 is optimal)")
                    
            elif feature_name in ['pulse', 'zoom', 'shake', 'flash', 'color_shift', 'blur', 'warp', 'glitch']:
                if feature_value == 0 and importances[idx] > 0.1:
                    recommendations.append(f"Consider adding the '{feature_name}' effect to improve engagement")
                    
            elif feature_name == 'preset':
                preset_mapping_reverse = {
                    1: 'standard',
                    2: 'subtle',
                    3: 'energetic',
                    4: 'dramatic',
                    5: 'cinematic'
                }
                current_preset = video_data.get('preset', 'standard')
                best_presets = ['energetic', 'dramatic'] if importances[idx] > 0.1 else []
                
                if best_presets and current_preset not in best_presets:
                    recommendations.append(f"Consider using the '{best_presets[0]}' preset for higher engagement")
        
        return recommendations


def get_performance_predictor() -> PerformancePredictor:
    """Get the singleton instance of the performance predictor."""
    return PerformancePredictor() 