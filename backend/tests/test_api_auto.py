"""
Automated test script for API endpoints (no user input required)
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

# Test data
test_input = {
    "hour": 8,
    "day_of_week": 1,
    "is_weekend": 0,
    "is_peak_hour": 1,
    "terminal": "T1",
    "num_flights": 25,
    "security_staff": 30,
    "checkin_staff": 20,
    "gates_available": 15,
    "is_holiday_season": 0,
    "baggage_volume": 3500,
    "international_ratio": 0.6,
    "weather": "Clear"
}

print("\n" + "#"*60)
print("🧪 SMART AIRPORT COMMAND CENTER - API TESTING")
print("#"*60)

print("\n📝 Test Input Data:")
print(json.dumps(test_input, indent=2))

# Give server a moment to be ready
time.sleep(2)

# Test 1: Health Check
print("\n" + "="*60)
print("🏥 Test 1: Health Endpoint")
print("="*60)

try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Health check passed")
    else:
        print("❌ Health check failed")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Test 2: Passenger Flow Prediction
print("\n" + "="*60)
print("👥 Test 2: Passenger Flow Prediction")
print("="*60)

try:
    response = requests.post(
        f"{BASE_URL}/api/predict/passenger-flow",
        json=test_input,
        timeout=5
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Prediction successful!")
        print(f"Predicted Passenger Flow: {result['predicted_passenger_flow']}")
        print(f"Model: {result['model']}")
    else:
        print(f"❌ Prediction failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Test 3: Queue Length Prediction
print("\n" + "="*60)
print("📊 Test 3: Queue Length Prediction")
print("="*60)

try:
    response = requests.post(
        f"{BASE_URL}/api/predict/queue-length",
        json=test_input,
        timeout=5
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Prediction successful!")
        print(f"Predicted Queue Length: {result['predicted_queue_length']} people")
        print(f"Model: {result['model']}")
    else:
        print(f"❌ Prediction failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Test 4: Waiting Time Prediction
print("\n" + "="*60)
print("⏱️  Test 4: Waiting Time Prediction")
print("="*60)

try:
    response = requests.post(
        f"{BASE_URL}/api/predict/waiting-time",
        json=test_input,
        timeout=5
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Prediction successful!")
        print(f"Predicted Waiting Time: {result['predicted_waiting_time']} minutes")
        print(f"Model: {result['model']}")
    else:
        print(f"❌ Prediction failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Test 5: Invalid Input Handling
print("\n" + "="*60)
print("🔍 Test 5: Invalid Input Handling")
print("="*60)

invalid_input = {
    "hour": 25,  # Invalid: hour should be 0-23
    "day_of_week": 1,
    "is_weekend": 0,
    "is_peak_hour": 1,
    "terminal": "T1",
    "num_flights": 25,
    "security_staff": 30,
    "checkin_staff": 20,
    "gates_available": 15,
    "is_holiday_season": 0,
    "baggage_volume": 3500,
    "international_ratio": 0.6,
    "weather": "Clear"
}

try:
    response = requests.post(
        f"{BASE_URL}/api/predict/passenger-flow",
        json=invalid_input,
        timeout=5
    )
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 422:
        print("✅ Invalid input properly rejected (validation working)")
    else:
        print(f"⚠️  Expected 422 status code, got {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Test 6: Different Scenarios
print("\n" + "="*60)
print("🌟 Test 6: Multiple Scenarios")
print("="*60)

scenarios = [
    {
        "name": "Peak Hour - Morning Rush",
        "data": {
            "hour": 7,
            "day_of_week": 1,
            "is_weekend": 0,
            "is_peak_hour": 1,
            "terminal": "T1",
            "num_flights": 28,
            "security_staff": 35,
            "checkin_staff": 25,
            "gates_available": 18,
            "is_holiday_season": 0,
            "baggage_volume": 4200,
            "international_ratio": 0.7,
            "weather": "Clear"
        }
    },
    {
        "name": "Off-Peak - Late Night",
        "data": {
            "hour": 23,
            "day_of_week": 3,
            "is_weekend": 0,
            "is_peak_hour": 0,
            "terminal": "T2",
            "num_flights": 8,
            "security_staff": 12,
            "checkin_staff": 10,
            "gates_available": 10,
            "is_holiday_season": 0,
            "baggage_volume": 800,
            "international_ratio": 0.4,
            "weather": "Clear"
        }
    },
    {
        "name": "Holiday Season - Busy Weekend",
        "data": {
            "hour": 10,
            "day_of_week": 6,
            "is_weekend": 1,
            "is_peak_hour": 0,
            "terminal": "T3",
            "num_flights": 22,
            "security_staff": 28,
            "checkin_staff": 20,
            "gates_available": 14,
            "is_holiday_season": 1,
            "baggage_volume": 3800,
            "international_ratio": 0.65,
            "weather": "Rainy"
        }
    }
]

for scenario in scenarios:
    print(f"\n📍 Scenario: {scenario['name']}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/predict/passenger-flow",
            json=scenario['data'],
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   Passenger Flow: {result['predicted_passenger_flow']}")
    except Exception as e:
        print(f"   Error: {str(e)}")

print("\n" + "#"*60)
print("✅ ALL TESTS COMPLETED")
print("#"*60 + "\n")
