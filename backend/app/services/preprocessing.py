"""
Data preprocessing service for airport data
Handles data cleaning, feature engineering, and transformation
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import os

# Feature columns used for training and inference (order matters).
# Must stay in sync between training (DataPreprocessor.prepare_features)
# and inference (preprocess_single_input).
FEATURE_COLUMNS = [
    'hour', 'day_of_week', 'is_weekend', 'is_peak_hour',
    'num_flights', 'security_staff', 'checkin_staff',
    'gates_available', 'is_holiday_season', 'baggage_volume',
    'international_ratio', 'terminal_encoded', 'weather_encoded',
    'total_staff', 'staff_per_flight',
    'is_morning', 'is_afternoon', 'is_evening', 'is_night'
]


class DataPreprocessor:
    """
    Handles all data preprocessing tasks
    """
    
    def __init__(self):
        self.label_encoders = {}
    
    def load_raw_data(self, filepath):
        """Load raw data from CSV"""
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    def clean_data(self, df):
        """Clean the dataset"""
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        df = df.fillna(df.median(numeric_only=True))
        
        # Remove outliers (optional - keeping for now as data is synthetic)
        return df
    
    def encode_categorical_features(self, df, fit=True):
        """Encode categorical variables"""
        categorical_cols = ['terminal', 'weather']
        
        for col in categorical_cols:
            if fit:
                le = LabelEncoder()
                df[f'{col}_encoded'] = le.fit_transform(df[col])
                self.label_encoders[col] = le
            else:
                if col in self.label_encoders:
                    df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
        
        return df
    
    def create_features(self, df):
        """Create additional features"""
        # Total staff
        df['total_staff'] = df['security_staff'] + df['checkin_staff']
        
        # Staff to flight ratio
        df['staff_per_flight'] = df['total_staff'] / (df['num_flights'] + 1)
        
        # Time-based features
        df['is_morning'] = (df['hour'] >= 6) & (df['hour'] < 12)
        df['is_afternoon'] = (df['hour'] >= 12) & (df['hour'] < 18)
        df['is_evening'] = (df['hour'] >= 18) & (df['hour'] < 24)
        df['is_night'] = (df['hour'] >= 0) & (df['hour'] < 6)
        
        # Convert boolean to int
        df['is_morning'] = df['is_morning'].astype(int)
        df['is_afternoon'] = df['is_afternoon'].astype(int)
        df['is_evening'] = df['is_evening'].astype(int)
        df['is_night'] = df['is_night'].astype(int)
        
        return df
    
    def prepare_features(self, df, target_column):
        """Prepare features for model training"""
        X = df[FEATURE_COLUMNS]
        y = df[target_column]
        
        return X, y
    
    def split_data(self, X, y, test_size=0.2, random_state=42):
        """Split data into train and test sets"""
        return train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    def preprocess_pipeline(self, raw_data_path, target_column):
        """Complete preprocessing pipeline"""
        print(f"\n🔧 Starting preprocessing for target: {target_column}")
        
        # Load data
        df = self.load_raw_data(raw_data_path)
        print(f"✅ Loaded {len(df)} records")
        
        # Clean data
        df = self.clean_data(df)
        print(f"✅ Data cleaned: {len(df)} records remaining")
        
        # Encode categorical features
        df = self.encode_categorical_features(df, fit=True)
        print("✅ Categorical features encoded")
        
        # Create features
        df = self.create_features(df)
        print("✅ Additional features created")
        
        # Prepare features
        X, y = self.prepare_features(df, target_column)
        print(f"✅ Features prepared: {X.shape[1]} features")
        
        # Split data
        X_train, X_test, y_train, y_test = self.split_data(X, y)
        print(f"✅ Data split: Train={len(X_train)}, Test={len(X_test)}")
        
        return X_train, X_test, y_train, y_test, df


def preprocess_single_input(input_data, label_encoders):
    """
    Preprocess a single input for prediction.
    Used by the API for real-time predictions.
    Returns a single-row DataFrame with the FEATURE_COLUMNS columns
    so that sklearn does not complain about missing feature names.
    """
    df = pd.DataFrame([input_data])
    
    # Encode categorical features
    for col, encoder in label_encoders.items():
        if col in df.columns:
            df[f'{col}_encoded'] = encoder.transform(df[col])
    
    # Create features
    df['total_staff'] = df['security_staff'] + df['checkin_staff']
    df['staff_per_flight'] = df['total_staff'] / (df['num_flights'] + 1)
    
    df['is_morning'] = ((df['hour'] >= 6) & (df['hour'] < 12)).astype(int)
    df['is_afternoon'] = ((df['hour'] >= 12) & (df['hour'] < 18)).astype(int)
    df['is_evening'] = ((df['hour'] >= 18) & (df['hour'] < 24)).astype(int)
    df['is_night'] = ((df['hour'] >= 0) & (df['hour'] < 6)).astype(int)
    
    return df[FEATURE_COLUMNS]
