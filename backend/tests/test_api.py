"""
Test script for API endpoints
Run this after starting the FastAPI server
"""

import requests
import json

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

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("🏥 Testing Health Endpoint")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_passenger_flow():
    """Test passenger flow prediction"""
    print("\n" + "="*60)
    print("👥 Testing Passenger Flow Prediction")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/predict/passenger-flow",
            json=test_input
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

def test_queue_length():
    """Test queue length prediction"""
    print("\n" + "="*60)
    print("📊 Testing Queue Length Prediction")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/predict/queue-length",
            json=test_input
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

def test_waiting_time():
    """Test waiting time prediction"""
    print("\n" + "="*60)
    print("⏱️  Testing Waiting Time Prediction")
    print("="*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/predict/waiting-time",
            json=test_input
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

def test_invalid_input():
    """Test with invalid input"""
    print("\n" + "="*60)
    print("🔍 Testing Invalid Input Handling")
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
            json=invalid_input
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 422:
            print("✅ Invalid input properly rejected")
            print(f"Error details: {response.json()}")
        else:
            print(f"❌ Expected 422 status code, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("🧪 SMART AIRPORT COMMAND CENTER - API TESTING")
    print("#"*60)
    
    print("\n📝 Test Input Data:")
    print(json.dumps(test_input, indent=2))
    
    # Run tests
    test_health()
    test_passenger_flow()
    test_queue_length()
    test_waiting_time()
    test_invalid_input()
    
    print("\n" + "#"*60)
    print("✅ ALL TESTS COMPLETED")
    print("#"*60 + "\n")

if __name__ == "__main__":
    print("\n⚠️  Make sure the FastAPI server is running!")
    print("Start server with: uvicorn app.main:app --reload")
    input("\nPress Enter to start testing...")
    
    run_all_tests()
