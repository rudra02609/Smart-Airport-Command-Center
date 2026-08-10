# 🛫 Smart Airport Command Center

An AI-powered airport operations management system that predicts passenger flow, queue lengths, and waiting times to help airport authorities make data-driven decisions.

## 📋 Project Overview

**Problem Statement:**  
Modern airports handle thousands of passengers and hundreds of flights daily. Manual management leads to congestion, delays, inefficient staff allocation, and poor passenger experience. Most existing systems are reactive rather than predictive.

**Solution:**  
An AI-powered command center that analyzes airport data, predicts operational challenges, and provides intelligent assistance to airport authorities.

## 🎯 Key Features

1. **Passenger Flow Prediction** - Predict the number of passengers at any given time
2. **Queue Length Prediction** - Estimate queue lengths at security and check-in
3. **Waiting Time Prediction** - Forecast passenger waiting times
4. **AI Airport Assistant** - LLM + RAG-based intelligent assistance (Coming in Week 4+)
5. **Smart Dashboard** - Real-time operational dashboard (Coming in Week 4+)
6. **Alerts & Recommendations** - AI-based operational insights (Coming in Week 4+)

## 🛠️ Technologies

- **Backend:** Python, FastAPI, Uvicorn
- **Machine Learning:** Scikit-learn, Pandas, NumPy
- **Model:** Random Forest Regressor
- **Data:** Joblib for model serialization
- **Frontend:** Next.js (Coming in Week 4+)
- **AI:** LLM + RAG (Coming in Week 4+)

## 📊 Current Status - Week 3 Complete

✅ **Completed:**
- Dataset generation (5,000 records)
- Data preprocessing pipeline
- 3 ML models trained and evaluated
- FastAPI backend with prediction endpoints
- API testing and validation
- Comprehensive documentation

❌ **Not Yet Implemented:**
- Frontend dashboard
- LLM integration
- RAG system
- Deployment

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
cd "Smart Airport Command Center"
```

2. Create and activate virtual environment:
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

1. Start the FastAPI server:
```bash
cd backend
uvicorn app.main:app --reload
```

2. Access the API:
- **API Base URL:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Testing the API

Run the automated test suite:
```bash
cd backend/tests
python test_api_auto.py
```

## 📡 API Endpoints

### Health Check
```
GET /api/health
```

### Passenger Flow Prediction
```
POST /api/predict/passenger-flow
```

### Queue Length Prediction
```
POST /api/predict/queue-length
```

### Waiting Time Prediction
```
POST /api/predict/waiting-time
```

## 📝 API Request Example

```json
{
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
```

## 📈 Model Performance

| Model | R² Score | RMSE | Status |
|-------|----------|------|--------|
| Passenger Flow | 0.9731 | 509.14 | Excellent |
| Queue Length | 0.6264 | 14.48 | Good |
| Waiting Time | 0.6697 | 11.60 | Good |

## 📁 Project Structure

```
Smart Airport Command Center/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── utils/            # Helper functions
│   │   └── main.py           # FastAPI app
│   ├── datasets/
│   │   ├── raw/              # Raw datasets
│   │   └── processed/        # Processed data
│   ├── models/               # Trained ML models
│   ├── notebooks/            # Jupyter notebooks
│   ├── scripts/              # Training scripts
│   ├── tests/                # API tests
│   └── requirements.txt
├── frontend/                 # Next.js app (Week 4+)
├── rag/                      # RAG system (Week 4+)
└── docs/                     # Documentation
```

## 📖 Documentation

Detailed documentation available in:
- [Week 3 ML Report](docs/reports/WEEK3_ML_REPORT.md)

## 🗓️ Development Roadmap

### Week 1 ✅
- Project planning and research
- Technology stack finalization

### Week 2 ✅
- Dataset preparation
- Project architecture design
- Initial ML module setup

### Week 3 ✅ (Current)
- ML model training and evaluation
- FastAPI backend development
- API endpoint implementation
- Testing and validation

### Week 4+ 🔜
- Frontend dashboard (Next.js)
- LLM integration
- RAG system implementation
- Deployment

## 🤝 Contributing

This is an educational project. Contributions, suggestions, and feedback are welcome!

## 📄 License

This project is for educational purposes.

## 👨‍💻 Author

AI/ML College Project - Smart Airport Command Center

## 🙏 Acknowledgments

- Scikit-learn for machine learning algorithms
- FastAPI for modern Python web framework
- Airport operational data insights

---

**Note:** This is an educational project using synthetic data for demonstration purposes. In production, real airport operational data should be used.
