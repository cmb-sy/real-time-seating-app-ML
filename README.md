# Real-time Seating Prediction Application (ML Version)

This project provides real-time seating predictions using Supabase as a database and Vercel serverless functions for API delivery.

## Project Overview

The system consists of the following components:

1. **Machine Learning Model** - Prediction model using scikit-learn and Optuna
2. **Data Analysis Tools** - Analysis and visualization of historical data
3. **API Endpoints** - Implemented as Vercel serverless functions
4. **Scheduler** - Updates models every two weeks

## Features

- Density rate and occupied seat prediction
- Day-of-week usage pattern analysis
- Real-time API endpoints (today and tomorrow predictions)
- Machine learning predictions by day of week
- Weekly average prediction data
- Hyperparameter optimization with Optuna
- Data visualization tools

## Technical Architecture

The project uses a gradient boosting model to predict seating density and occupancy based on the day of the week. The model is trained on historical data and deployed as serverless functions on Vercel, which provide JSON API endpoints for frontend consumption.

Key technical components:

- **Machine Learning**: Gradient Boosting Regressor models from scikit-learn
- **Backend**: Python serverless functions
- **Deployment**: Vercel serverless environment
- **Database**: Supabase

## Environment Setup

### Prerequisites

- Python 3.10 or higher
- Supabase account and API information

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/real-time-seating-app-ML.git
cd real-time-seating-app-ML
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Add project path:

```bash
pip install -e .
```

5. Set environment variables:

Create a `.env` file in the project root with the following content:

```
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key
```

## Usage

### Main Commands

```bash
python main.py train     # Train machine learning models
python main.py analyze   # Run data analysis
python main.py schedule  # Execute scheduler
```

### Training Machine Learning Models (Detailed Options)

```bash
python -m src.ml.train_ml_models --mode train --n-trials 50
```

Options:

- `--mode`: Execution mode (train, test, info)
- `--n-trials`: Number of Optuna optimization trials (default: 50)
- `--target`: Optimization target (density, seats, both)

### Testing Predictions

```bash
python -m src.ml.train_ml_models --mode test
```

### Running API Server Locally

```bash
uvicorn src.api.health:app --reload --port 8000
```

## Deployment

The application is deployed on Vercel, with pre-trained models stored in the same directory as API code. For deployment:

1. Copy model files to the API directory:

```bash
./copy_models.sh
```

2. Push to GitHub for automatic deployment via Vercel integration.

## API Endpoints

The following Vercel serverless function endpoints are available:

- `/health` - System health check
- `/predictions/today-tomorrow` - Today and tomorrow predictions
- `/predictions/weekly-average` - Weekly average predictions
- `/ml/predict` - Machine learning predictions by specific day
- `/analysis/weekday_analysis` - Day-by-day analysis data

See the [API_ENDPOINTS.md](API_ENDPOINTS.md) file for detailed API documentation.

## Implementation Details

The system uses pre-trained gradient boosting models to make predictions based solely on the day of the week feature. The API returns both raw model outputs (density rate and occupied seats) and processed data (occupancy rate, status, etc.) suitable for frontend display.

The prediction flow is:

1. Load trained models from .joblib files
2. Extract day of week (0-4) as the feature
3. Make predictions using the models
4. Transform prediction results to user-friendly format
5. Return JSON responses via API endpoints

## License

This project is released under the MIT license.
