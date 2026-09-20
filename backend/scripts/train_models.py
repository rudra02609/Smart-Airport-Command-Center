"""
Train Machine Learning models for airport predictions.
Models: Passenger Flow, Queue Length, Waiting Time
Algorithms: Random Forest Regressor (primary) + Linear Regression (comparison)
"""

import sys
# Configure UTF-8 encoding for standard output on Windows to avoid UnicodeEncodeError
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import joblib
import json
from app.services.preprocessing import DataPreprocessor, FEATURE_COLUMNS
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def evaluate_model(y_true, y_pred, model_name):
    """Calculate and display evaluation metrics."""
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    
    print(f"\n{'='*60}")
    print(f"📊 {model_name} - Evaluation Metrics")
    print(f"{'='*60}")
    print(f"Mean Absolute Error (MAE):      {mae:.2f}")
    print(f"Mean Squared Error (MSE):       {mse:.2f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")
    print(f"R² Score:                       {r2:.4f}")
    print(f"{'='*60}\n")
    
    return {
        'mae': round(mae, 4),
        'mse': round(mse, 4),
        'rmse': round(rmse, 4),
        'r2': round(r2, 4)
    }


def train_model(target_name, target_column, raw_data_path):
    """
    Train both Random Forest and Linear Regression models for a specific target.
    Returns the RF model (primary), preprocessor, and metrics for both algorithms.
    """
    print(f"\n{'#'*60}")
    print(f"🚀 Training Models: {target_name}")
    print(f"{'#'*60}")
    
    # Preprocess data
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, df = preprocessor.preprocess_pipeline(
        raw_data_path, target_column
    )
    
    # ===== Random Forest Regressor (Primary) =====
    print(f"\n🤖 Training Random Forest Regressor...")
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    print("✅ Random Forest training completed")
    
    # Evaluate RF
    rf_pred_train = rf_model.predict(X_train)
    rf_pred_test = rf_model.predict(X_test)
    
    print("\n📈 Random Forest - Training Set:")
    rf_train_metrics = evaluate_model(y_train, rf_pred_train, f"{target_name} RF (Train)")
    
    print("\n📉 Random Forest - Test Set:")
    rf_test_metrics = evaluate_model(y_test, rf_pred_test, f"{target_name} RF (Test)")
    
    # ===== Linear Regression (Comparison) =====
    print(f"\n🤖 Training Linear Regression (comparison)...")
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    print("✅ Linear Regression training completed")
    
    # Evaluate LR
    lr_pred_train = lr_model.predict(X_train)
    lr_pred_test = lr_model.predict(X_test)
    
    print("\n📈 Linear Regression - Training Set:")
    lr_train_metrics = evaluate_model(y_train, lr_pred_train, f"{target_name} LR (Train)")
    
    print("\n📉 Linear Regression - Test Set:")
    lr_test_metrics = evaluate_model(y_test, lr_pred_test, f"{target_name} LR (Test)")
    
    # ===== Comparison =====
    print(f"\n{'='*60}")
    print(f"📊 MODEL COMPARISON: {target_name}")
    print(f"{'='*60}")
    print(f"{'Metric':<12} {'Random Forest':>15} {'Linear Reg':>15} {'Winner':>15}")
    print(f"{'-'*57}")
    for metric in ['mae', 'rmse', 'r2']:
        rf_val = rf_test_metrics[metric]
        lr_val = lr_test_metrics[metric]
        if metric == 'r2':
            winner = 'RF ✅' if rf_val > lr_val else 'LR ✅'
        else:
            winner = 'RF ✅' if rf_val < lr_val else 'LR ✅'
        print(f"{metric.upper():<12} {rf_val:>15.4f} {lr_val:>15.4f} {winner:>15}")
    print(f"{'='*60}")
    
    # Feature importance (RF only)
    feature_names = FEATURE_COLUMNS
    
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🎯 Top 5 Important Features (Random Forest):")
    print(feature_importance.head().to_string(index=False))
    
    metrics = {
        'random_forest': rf_test_metrics,
        'linear_regression': lr_test_metrics,
        'selected_model': 'random_forest'
    }
    
    return rf_model, preprocessor, metrics, feature_importance


if __name__ == "__main__":
    # Resolve paths relative to this script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_data_path = os.path.abspath(os.path.join(script_dir, '../datasets/raw/airport_data.csv'))
    models_dir = os.path.abspath(os.path.join(script_dir, '../models'))
    
    # Create models directory if it doesn't exist
    os.makedirs(models_dir, exist_ok=True)
    
    # Store all results
    all_metrics = {}
    
    print("\n" + "="*60)
    print("🏗️  SMART AIRPORT COMMAND CENTER - MODEL TRAINING")
    print("    Random Forest (Primary) + Linear Regression (Comparison)")
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
    print("  • passenger_flow_model.pkl (Random Forest)")
    print("  • queue_length_model.pkl (Random Forest)")
    print("  • waiting_time_model.pkl (Random Forest)")
    print("\nEncoder Files:")
    print("  • passenger_flow_encoders.pkl")
    print("  • queue_length_encoders.pkl")
    print("  • waiting_time_encoders.pkl")
    print("\nMetrics: model_metrics.json")
    
    print("\n" + "="*60)
    print("📊 FINAL MODEL COMPARISON SUMMARY")
    print("="*60)
    for model_name, metrics in all_metrics.items():
        rf = metrics['random_forest']
        lr = metrics['linear_regression']
        print(f"\n{model_name.upper().replace('_', ' ')}:")
        print(f"  Random Forest  → R²: {rf['r2']:.4f}, RMSE: {rf['rmse']:.2f}, MAE: {rf['mae']:.2f}")
        print(f"  Linear Regr.   → R²: {lr['r2']:.4f}, RMSE: {lr['rmse']:.2f}, MAE: {lr['mae']:.2f}")
        print(f"  Selected: {metrics['selected_model'].replace('_', ' ').title()} ✅")
