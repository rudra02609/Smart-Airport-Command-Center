"""
Prediction service for loading models and making predictions
"""

import joblib
import os
import json
import numpy as np
from app.services.preprocessing import preprocess_single_input

class PredictionService:
    """
    Service for loading ML models and making predictions
    """
    
    def __init__(self):
        self.models = {}
        self.encoders = {}
        self.metrics = {}
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
    
    def load_metrics(self):
        """Load model_metrics.json if present. Non-fatal on failure."""
        try:
            metrics_path = os.path.join(self.models_dir, 'model_metrics.json')
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r', encoding='utf-8') as f:
                    self.metrics = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load model metrics: {str(e)}")
            self.metrics = {}
        
        return self.metrics
        
    def load_model(self, model_name):
        """Load a specific model and its encoders"""
        try:
            model_path = os.path.join(self.models_dir, f'{model_name}_model.pkl')
            encoder_path = os.path.join(self.models_dir, f'{model_name}_encoders.pkl')
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found: {model_path}")
            
            if not os.path.exists(encoder_path):
                raise FileNotFoundError(f"Encoders not found: {encoder_path}")
            
            self.models[model_name] = joblib.load(model_path)
            self.encoders[model_name] = joblib.load(encoder_path)
            
            print(f"✅ Loaded model: {model_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading model {model_name}: {str(e)}")
            raise
    
    def load_all_models(self):
        """Load all available models"""
        model_names = ['passenger_flow', 'queue_length', 'waiting_time']
        
        for model_name in model_names:
            try:
                self.load_model(model_name)
            except Exception as e:
                print(f"Warning: Could not load {model_name}: {str(e)}")
        
        self.load_metrics()
        print(f"\n✅ Loaded {len(self.models)} models successfully")
    
    def predict(self, model_name, input_data):
        """Make prediction using a specific model"""
        try:
            # Check if model is loaded
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not loaded. Start the API so models load on startup.")
            
            # Get model and encoders
            model = self.models[model_name]
            encoders = self.encoders[model_name]
            
            # Preprocess input (returns a single-row DataFrame with feature names)
            features = preprocess_single_input(input_data, encoders)
            
            if features.isnull().any().any():
                raise ValueError("Input data produced missing feature values during encoding")
            
            # Make prediction
            prediction = model.predict(features)[0]
            
            # Round to reasonable precision
            prediction = round(float(prediction), 2)
            
            return prediction
            
        except Exception as e:
            print(f"❌ Prediction error: {str(e)}")
            raise
    
    def predict_passenger_flow(self, input_data):
        """Predict passenger flow"""
        return self.predict('passenger_flow', input_data)
    
    def predict_queue_length(self, input_data):
        """Predict queue length"""
        return self.predict('queue_length', input_data)
    
    def predict_waiting_time(self, input_data):
        """Predict waiting time"""
        return self.predict('waiting_time', input_data)


# Global prediction service instance
prediction_service = PredictionService()
