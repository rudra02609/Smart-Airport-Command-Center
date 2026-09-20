"""
Generate synthetic airport operational data for ML training
This script creates realistic airport data with patterns for:
- Passenger Flow
- Queue Length
- Waiting Time
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

def generate_airport_data(num_records=5000):
    """
    Generate synthetic airport operational data
    """
    data = []
    
    # Start date
    start_date = datetime(2024, 1, 1)
    
    for i in range(num_records):
        # Time-based features
        current_date = start_date + timedelta(hours=i % (24*30))  # 30 days cycle
        hour = current_date.hour
        day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Terminal information
        terminal = np.random.choice(['T1', 'T2', 'T3'], p=[0.4, 0.35, 0.25])
        
        # Peak hours logic (6-9 AM and 5-8 PM are busier)
        is_peak_hour = 1 if (6 <= hour <= 9) or (17 <= hour <= 20) else 0
        
        # Number of scheduled flights
        if is_peak_hour:
            num_flights = np.random.randint(15, 30)
        else:
            num_flights = np.random.randint(5, 15)
        
        # Staff allocation
        if is_peak_hour:
            security_staff = np.random.randint(20, 35)
            checkin_staff = np.random.randint(15, 25)
        else:
            security_staff = np.random.randint(10, 20)
            checkin_staff = np.random.randint(8, 15)
        
        # Gate availability
        gates_available = np.random.randint(8, 20)
        
        # Weather condition (affects passenger behavior)
        weather = np.random.choice(['Clear', 'Rainy', 'Foggy'], p=[0.7, 0.2, 0.1])
        weather_impact = 1.2 if weather == 'Rainy' else 1.3 if weather == 'Foggy' else 1.0
        
        # Holiday season indicator
        is_holiday_season = 1 if current_date.month in [12, 1, 6, 7] else 0
        holiday_multiplier = 1.4 if is_holiday_season else 1.0
        
        # Calculate Passenger Flow (target variable 1)
        base_passengers = num_flights * np.random.uniform(120, 180)
        passenger_flow = int(base_passengers * (1 + is_peak_hour * 0.5) * 
                           (1 + is_weekend * 0.3) * 
                           holiday_multiplier * 
                           weather_impact +
                           np.random.normal(0, 50))
        passenger_flow = max(50, passenger_flow)  # Minimum 50 passengers
        
        # Calculate Queue Length (target variable 2)
        # Queue depends on passengers vs staff ratio
        staff_ratio = passenger_flow / (security_staff + checkin_staff)
        base_queue = staff_ratio * np.random.uniform(2, 4)
        queue_length = int(base_queue * weather_impact + np.random.normal(0, 5))
        queue_length = max(5, min(queue_length, 200))  # Between 5 and 200
        
        # Calculate Waiting Time in minutes (target variable 3)
        # Waiting time depends on queue length and staff efficiency
        base_waiting = queue_length / (security_staff * 0.5 + checkin_staff * 0.3)
        waiting_time = int(base_waiting * np.random.uniform(2, 4) * weather_impact + 
                          np.random.normal(0, 3))
        waiting_time = max(5, min(waiting_time, 120))  # Between 5 and 120 minutes
        
        # Additional features
        baggage_volume = int(passenger_flow * np.random.uniform(0.6, 0.9))
        international_ratio = np.random.uniform(0.3, 0.7)
        
        record = {
            'timestamp': current_date,
            'hour': hour,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'is_peak_hour': is_peak_hour,
            'terminal': terminal,
            'num_flights': num_flights,
            'security_staff': security_staff,
            'checkin_staff': checkin_staff,
            'gates_available': gates_available,
            'weather': weather,
            'is_holiday_season': is_holiday_season,
            'baggage_volume': baggage_volume,
            'international_ratio': international_ratio,
            'passenger_flow': passenger_flow,
            'queue_length': queue_length,
            'waiting_time': waiting_time
        }
        
        data.append(record)
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    print("Generating synthetic airport data...")
    df = generate_airport_data(5000)
    
    # Save to raw folder (path relative to this script, not CWD)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.abspath(os.path.join(script_dir, '..', 'datasets', 'raw'))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'airport_data.csv')
    df.to_csv(output_path, index=False)
    
    print(f"\n✅ Dataset created successfully!")
    print(f"📊 Total records: {len(df)}")
    print(f"💾 Saved to: {output_path}")
    print(f"\n📈 Dataset Summary:")
    print(df.describe())
    print(f"\n🎯 Target Variables Statistics:")
    print(f"Passenger Flow - Mean: {df['passenger_flow'].mean():.2f}, Std: {df['passenger_flow'].std():.2f}")
    print(f"Queue Length - Mean: {df['queue_length'].mean():.2f}, Std: {df['queue_length'].std():.2f}")
    print(f"Waiting Time - Mean: {df['waiting_time'].mean():.2f}, Std: {df['waiting_time'].std():.2f}")
