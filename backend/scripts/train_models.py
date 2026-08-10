"""
Train Machine Learning models for airport predictions
Models: Passenger Flow, Queue Length, Waiting Time
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.preprocessing import DataPreprocessor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import joblib
import json

def evaluate_model(y_true, y_pred, model_name):
    """Calculate evaluation metrics"""
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    
    print(f"\n{'='*60}")
    print(f"📊 {model_name} - Evaluation Metrics")
    print(f"{'='*60}")
    print(f"Mean Absolute Error (MAE):  {mae:.2f}")
    print(f"Mean Squared Error (MSE):   {mse:.2f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")
    print(f"R² Score:                   {r2:.4f}")
    print(f"{'='*60}\n")
    
    return {
        'mae': mae,
        'mse': mse,
        'rmse': rmse,
        'r2': r2
    }

def train_model(target_name, target_column, raw_data_path):
    """Train a Random Forest model for a specific target"""
    print(f"\n{'#'*60}")
    print(f"🚀 Training Model: {target_name}")
    print(f"{'#'*60}")
    
    # Preprocess data
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, df = preprocessor.preprocess_pipeline(
        raw_data_path, target_column
    )
    
    # Train Random Forest model
    print(f"\n🤖 Training Random Forest Regressor...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    print("✅ Model training completed")
    
    # Make predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Evaluate on training set
    print("\n📈 Training Set Performance:")
    train_metrics = evaluate_model(y_train, y_pred_train, f"{target_name} (Train)")
    
    # Evaluate on test set
    print("\n📉 Test Set Performance:")
    test_metrics = evaluate_model(y_test, y_pred_test, f"{target_name} (Test)")
    
    # Feature importance
    feature_names = [
        'hour', 'day_of_week', 'is_weekend', 'is_peak_hour',
        'num_flights', 'security_staff', 'checkin_staff',
        'gates_available', 'is_holiday_season', 'baggage_volume',
        'international_ratio', 'terminal_encoded', 'weather_encoded',
        'total_staff', 'staff_per_flight',
        'is_morning', 'is_afternoon', 'is_evening', 'is_night'
    ]
    
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🎯 Top 5 Important Features:")
    print(feature_importance.head().to_string(index=False))
    
    return model, preprocessor, test_metrics, feature_importance

if __name__ == "__main__":
    import pandas as pd
    
    # Paths
    raw_data_path = '../datasets/raw/airport_data.csv'
    models_dir = '../models'
    
    # Create models directory if it doesn't exist
    os.makedirs(models_dir, exist_ok=True)
    
    # Store all results
    all_metrics = {}
    
    print("\n" + "="*60)
    print("🏗️  SMART AIRPORT COMMAND CENTER - MODEL TRAINING")
    print("="*60)
    
    # 1. Train Passenger Flow Model
    passenger_model, passenger_preprocessor, passenger_metrics, passenger_fi = train_model(
        "Passenger Flow Prediction",
        "passenger_flow",
        raw_data_path
    )
    
    # Save model and preprocessor
    joblib.dump(passenger_model, f'{models_dir}/passenger_flow_model.pkl')
    joblib.dump(passenger_preprocessor.label_encoders, f'{models_dir}/passenger_flow_encoders.pkl')
    print(f"💾 Saved: passenger_flow_model.pkl")
    all_metrics['passenger_flow'] = passenger_metrics
    
    # 2. Train Queue Length Model
    queue_model, queue_preprocessor, queue_metrics, queue_fi = train_model(
        "Queue Length Prediction",
        "queue_length",
        raw_data_path
    )
    
    # Save model and preprocessor
    joblib.dump(queue_model, f'{models_dir}/queue_length_model.pkl')
    joblib.dump(queue_preprocessor.label_encoders, f'{models_dir}/queue_length_encoders.pkl')
    print(f"💾 Saved: queue_length_model.pkl")
    all_metrics['queue_length'] = queue_metrics
    
    # 3. Train Waiting Time Model
    waiting_model, waiting_preprocessor, waiting_metrics, waiting_fi = train_model(
        "Waiting Time Prediction",
        "waiting_time",
        raw_data_path
    )
    
    # Save model and preprocessor
    joblib.dump(waiting_model, f'{models_dir}/waiting_time_model.pkl')
    joblib.dump(waiting_preprocessor.label_encoders, f'{models_dir}/waiting_time_encoders.pkl')
    print(f"💾 Saved: waiting_time_model.pkl")
    all_metrics['waiting_time'] = waiting_metrics
    
    # Save metrics summary
    with open(f'{models_dir}/model_metrics.json', 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ ALL MODELS TRAINED AND SAVED SUCCESSFULLY!")
    print("="*60)
    print(f"\n📁 Models saved in: {models_dir}/")
    print("\nModel Files:")
    print("  • passenger_flow_model.pkl")
    print("  • queue_length_model.pkl")
    print("  • waiting_time_model.pkl")
    print("\nEncoder Files:")
    print("  • passenger_flow_encoders.pkl")
    print("  • queue_length_encoders.pkl")
    print("  • waiting_time_encoders.pkl")
    print("\nMetrics:")
    print("  • model_metrics.json")
    
    print("\n📊 SUMMARY OF MODEL PERFORMANCE:")
    print("="*60)
    for model_name, metrics in all_metrics.items():
        print(f"\n{model_name.upper().replace('_', ' ')}:")
        print(f"  R² Score: {metrics['r2']:.4f}")
        print(f"  RMSE: {metrics['rmse']:.2f}")
        print(f"  MAE: {metrics['mae']:.2f}")
