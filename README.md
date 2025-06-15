# Real-time Seating Prediction ML API

This project provides real-time seating predictions using machine learning models with Supabase as the database backend.

<img width="709" alt="SS 2025-06-12 22 12 25" src="https://github.com/user-attachments/assets/83e1e09b-b468-4856-8872-507d85b7c419" />

## 🚀 Project Overview

This system provides the following features:

- **Today & Tomorrow Predictions** - High-accuracy predictions using ML models
- **Weekly Average Predictions** - Statistical averages from Supabase data
- **Automatic Model Retraining** - Regular model updates via GitHub Actions
- **Feature Engineering** - Advanced features including time, day of week, and seasonality

## 📋 System Requirements

- Python
- Node.js(for Vercel CLI)
- Supabase account

## 🛠️ Setup

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

```

### 2. Configure Environment Variables

Create a `.env` file with the following:

```env
NEXT_PUBLIC_SUPABASE_URL=your_NEXT_PUBLIC_SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=your_SUPABASE_SERVICE_ROLE_KEY
```

## 🖥️ Running the Backend

### Method 1: Direct API Router

```bash
# Start the API router (combines all API endpoints)
python3 src/api/api_router.py

# Access at: http://localhost:8000
# Test endpoints:
# curl http://localhost:8000/api/predictions/today-tomorrow
# curl http://localhost:8000/api/predictions/weekly-average
```

### Method 2: Individual API Testing

```bash
# Today & Tomorrow Predictions API
python src/api/predictions_today_tomorrow.py

# Weekly Average Predictions API
python src/api/predictions_weekly_average.py

# Supabase Sync API
python src/api/supabase_sync.py
```

## 🤖 Updating ML Models

### Basic Model Training

```bash
# Train with feature engineering (recommended)
python src/ml/train_ml_models.py
```

### Advanced Options

```bash
# Optimize density rate only
python src/ml/train_ml_models.py --mode train --target density --n-trials 30

# Optimize seat count only
python src/ml/train_ml_models.py --mode train --target seats --n-trials 30

# Fast training (fewer trials)
python src/ml/train_ml_models.py --mode train --n-trials 20

# High-accuracy training (more trials)
python src/ml/train_ml_models.py --mode train --n-trials 100
```

### Testing and Verifying Models

```bash
# Test predictions
python src/ml/train_ml_models.py --mode test

# Display model information
python src/ml/train_ml_models.py --mode info
```

### Training Process Details

1. **Data Preparation** - Fetch weekday data from Supabase
2. **Feature Engineering** - Generate features for time, day of week, season, moving averages, etc.
3. **Hyperparameter Optimization** - Optimize models using Optuna
4. **Model Training** - Train models with optimal parameters
5. **Model Saving** - Save trained models to `src/api/` directory
6. **Prediction Testing** - Verify prediction accuracy for each day of week

## 📡 API Endpoints

### Today & Tomorrow Predictions

```
GET /api/predictions/today-tomorrow
```

### Weekly Average Predictions

```
GET /api/predictions/weekly-average
```

## 📈 Performance Optimization

- **Feature Engineering**: Recommended for improved prediction accuracy
- **Trial Count Adjustment**: Balance accuracy and training time
- **Regular Retraining**: Update models with latest data

## 📝 License

MIT License

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request
