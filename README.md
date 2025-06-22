# Real-time Seating App ML Backend

A machine learning backend API for real-time seating prediction system, providing intelligent forecasting of seat occupancy and density rates.

## Features

- Real-time seat occupancy prediction
- Density rate forecasting
- Weekly average predictions
- ML model with Supabase fallback system
- RESTful API endpoints
- Automatic model retraining pipeline

## Tech Stack

- Python 3.12
- FastAPI
- Scikit-learn
- Supabase
- Optuna (for hyperparameter optimization)
- Vercel (for deployment)

## Prerequisites

- Python 3.12 or higher
- pip or poetry for package management
- Supabase account and credentials

## Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/cmb-sy/real-time-seating-app-ML.git
```

2. uv setup

```bash
cd real-time-seating-app-ML
uv venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

3. Install dependencies:

```bash
uv install -r requirements.txt
```

4. Set up environment variables:

```bash
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

4. Run the development server:

```bash
lsof -ti:8000 | xargs kill -9
python3 -u api/index.py
uv run ~.py
```

## Technical Implementation Challenge

Originally planned to build an API using machine learning models to predict seat occupancy and density rates
Due to Vercel's 250MB deployment limit, couldn't load joblib models and had to abandon this approach
Changed the implementation to save results in JSON format and return them to the frontend
An alternative approach would have been to save model parameters in JSON format and perform linear calculations or feature importance-based predictions
Chose the former approach because it was easier to implement
Since model updates are infrequent, the impact of this design choice was minimal

## frontend

https://github.com/cmb-sy/real-time-seating-app

## License

MIT
