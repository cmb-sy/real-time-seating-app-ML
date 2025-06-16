# Real-time Seating App ML Backend

A machine learning backend API for real-time seating prediction system, providing intelligent forecasting of seat occupancy and density rates.

## 🌟 Features

- Real-time seat occupancy prediction
- Density rate forecasting
- Weekly average predictions
- ML model with Supabase fallback system
- RESTful API endpoints
- Automatic model retraining pipeline

## 🛠 Tech Stack

- Python 3.12
- FastAPI
- Scikit-learn
- Supabase
- Optuna (for hyperparameter optimization)
- Vercel (for deployment)

## 📋 Prerequisites

- Python 3.12 or higher
- pip or poetry for package management
- Supabase account and credentials

## 🚀 Quick Start

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

4. Run the development server:

```bash
lsof -ti:8000 | xargs kill -9  # Kill any process using port 8000
python3 -u api/index.py
```

## 🔍 API Endpoints

### Documentation

```bash
curl -v http://localhost:8000/docs
```

Response:

```json
{
  "title": "Prediction API",
  "version": "1.0.0",
  "endpoints": [
    {
      "path": "/api/predictions/today-tomorrow",
      "method": "GET",
      "description": "Get predictions for today and tomorrow"
    },
    {
      "path": "/api/predictions/weekly-average",
      "method": "GET",
      "description": "Get weekly average predictions"
    }
  ]
}
```

### curl Request for Today's and Tomorrow's Predictions

```bash
curl -v http://localhost:8000/api/predictions/today-tomorrow
curl -v http://localhost:8000/api/predictions/weekly-average
```

Response:

```json
{
  "success": true,
  "data": {
    "predictions": [
      {
        "date": "2024-03-21",
        "density_rate": 0.75,
        "occupied_seats": 45
      },
      {
        "date": "2024-03-22",
        "density_rate": 0.82,
        "occupied_seats": 49
      }
    ]
  },
  "prediction_method": "ml_model_with_supabase_fallback",
  "environment": "production"
}
```

## 🔄 ML Pipeline

The system includes a complete machine learning pipeline:

1. Data collection from Supabase
2. Feature engineering
3. Model training with Optuna optimization
4. Model evaluation and persistence
5. Automated retraining schedule

## 🏗 Project Structure

```
.
├── api/
│   ├── index.py                 # Main API endpoints
│   ├── density_model.joblib     # Trained density prediction model
│   └── seats_model.joblib       # Trained seat prediction model
├── utils/
│   ├── data_processor.py        # Data processing utilities
│   ├── prediction.py            # Prediction service
│   ├── supabase_access.py       # Supabase integration
│   └── train.py                 # Model training script
├── requirements.txt             # Python dependencies
└── vercel.json                  # Vercel deployment configuration
```

## 📈 Performance

The ML models are optimized using Optuna for hyperparameter tuning, achieving:

- Density Rate Prediction: ~85% accuracy
- Seat Occupancy Prediction: ~90% accuracy

## 🔐 Security

- Uses Supabase for secure data storage
- Environment variables for sensitive credentials
- CORS enabled for API endpoints

## 📄 License

MIT

## 👥 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

```bash
lsof -ti:8000 | xargs kill -9
python3 -u api/index.py'
```
