# Real-time Seating App ML Backend

A machine learning backend API for real-time seating prediction system, providing intelligent forecasting of seat occupancy and density rates.

## 🔒 Security

### Environment Variables

Configure the following environment variables:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
```

⚠️ **Critical Security Guidelines**:

- Never hardcode API keys in your source code
- Environment files (.env) must not be committed to Git
- API key values are never logged to prevent information leakage
- Error responses hide internal details to prevent information disclosure
- Use anonymous key (not service role key) for read-only operations

### Security Features

- API key values are never exposed in logs
- Internal error details are hidden from responses
- Unnecessary test/debug files are excluded from production
- Secure HTTP-only communication with Supabase
- Row Level Security (RLS) policies enforced

## 🚀 Deployment

### Unified API System

**Single Endpoint**: `api/index.py` - Consolidated handler for all prediction APIs

### API Endpoints

#### 1. Today/Tomorrow Prediction API

```
GET /api/predictions/today-tomorrow
```

Returns predictions for today and tomorrow's seating data.

#### 2. Weekly Average Prediction API

```
GET /api/predictions/weekly-average
```

Returns weekly average predictions for all weekdays.

#### 3. Model Information API

```
GET /api/model-info
```

Returns current model performance metrics and metadata.

### API Response Format

All API endpoints return responses in the following format:

**Success Response:**

```json
{
  "success": true,
  "data": {
    "predictions": { ... },
    "model_prediction": true,
    "source": "ML Model"
  },
  "environment": "production"
}
```

**Error Response:**

```json
{
  "success": false,
  "error": "Internal server error"
}
```

## 📁 Project Structure

```
api/
├── index.py                 # Unified API handler
├── requirements.txt         # Python dependencies
├── density_model.joblib     # Density prediction model (auto-updated)
├── seats_model.joblib       # Seats prediction model (auto-updated)
├── best_params.joblib       # Optimal hyperparameters (auto-updated)
└── model_performance.joblib # Model performance metrics (auto-updated)

.github/workflows/
└── retrain-model.yml        # Weekly model retraining workflow

vercel.json                  # Vercel deployment configuration
.gitignore                   # Git ignore rules
.vercelignore               # Vercel ignore rules
```

## 🤖 Machine Learning Models

### Automated Model Updates via GitHub Workflow

- **Schedule**: Every Monday at 2:00 AM UTC (automatic execution)
- **Manual Trigger**: Can be manually triggered from GitHub Actions
- **Data Source**: Real data from Supabase database
- **Update Process**: Complete model retraining with hyperparameter optimization

### Current Model Performance

Check the latest model performance:

```bash
# View current model metrics
python -c "import joblib; print(joblib.load('api/model_performance.joblib'))"
```

**Expected Performance:**

- Density Model R²: ~0.97
- Seats Model R²: ~0.72

### Feature Engineering (10 Features)

The ML models use exactly 10 engineered features:

1. `day_of_week` - Day of week (0-4: Monday-Friday)
2. `density_seats_ratio` - Real-time calculated ratio from Supabase data
3. `is_monday` - Monday indicator (0/1)
4. `is_tuesday` - Tuesday indicator (0/1)
5. `is_wednesday` - Wednesday indicator (0/1)
6. `is_thursday` - Thursday indicator (0/1)
7. `is_friday` - Friday indicator (0/1)
8. `is_early_week` - Early week indicator (Mon-Tue)
9. `is_mid_week` - Mid week indicator (Wed)
10. `is_late_week` - Late week indicator (Thu-Fri)

## 🔧 Development Environment

### Local Development Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r api/requirements.txt

# Set environment variables
export SUPABASE_URL="your_supabase_url"
export SUPABASE_ANON_KEY="your_supabase_anon_key"
```

### Local Testing

```bash
# Test unified API (local environment only)
cd api && python -c "
import os
os.environ['SUPABASE_URL'] = 'test_url'
os.environ['SUPABASE_ANON_KEY'] = 'test_key'
from index import handler
print('✅ Unified API loaded successfully')
"
```

## 📊 Database Integration

### Supabase Configuration

- **Table**: `seating_data`
- **Fields**: `day_of_week`, `density`, `total_seats`, `created_at`
- **Authentication**: Anonymous key with RLS policies
- **Communication**: Direct HTTP REST API calls (no Python SDK)

### Data Format

- `day_of_week`: 0-6 (Monday-Sunday)
- `density`: 0-100 (occupancy percentage)
- `total_seats`: 0-8 (total available seats)
- `created_at`: ISO timestamp

### Row Level Security (RLS)

```sql
-- Enable RLS on seating_data table
ALTER TABLE seating_data ENABLE ROW LEVEL SECURITY;

-- Allow read access for anonymous users
CREATE POLICY "Allow read access" ON seating_data
FOR SELECT USING (true);
```

## 🔧 Technology Stack

- **Runtime**: Python 3.9+
- **Framework**: Native Python HTTP handler (Vercel Serverless)
- **Database**: Supabase (PostgreSQL) via HTTP REST API
- **Deployment**: Vercel
- **ML Framework**: scikit-learn
- **Model Storage**: joblib format
- **Dependencies**: scikit-learn, joblib, numpy, requests

## 📈 Prediction System

### Prediction Strategy

1. **Primary**: GitHub Workflow-trained ML models with real Supabase data
2. **Fallback**: Database historical averages when ML models fail
3. **Real-time**: Dynamic `density_seats_ratio` calculation from live data

### Model Update Workflow

1. **Trigger**: GitHub Actions runs weekly (Monday 2 AM UTC)
2. **Data Collection**: Fetch latest data from Supabase via HTTP API
3. **Feature Engineering**: Create 10 engineered features
4. **Optimization**: Hyperparameter tuning with Optuna
5. **Training**: Train optimized models on real data
6. **Deployment**: Save models to `api/` directory
7. **Auto-deploy**: Vercel automatically deploys updated models

### Fallback Mechanism

When ML models fail:

- API automatically switches to database averages
- Response includes `"model_prediction": false`
- System remains operational with historical data

## 🚨 Troubleshooting

### Common Issues

1. **500 Internal Server Error**

   - Check environment variables are properly set in Vercel
   - Verify Supabase URL and anonymous key are correct

2. **Model Loading Errors**

   - Ensure GitHub Workflow completed successfully
   - Check if model files exist in `api/` directory

3. **Database Connection Issues**

   - Verify Supabase credentials
   - Check RLS policies allow read access
   - Confirm table structure matches expected format

4. **Feature Mismatch Errors**
   - Ensure feature engineering creates exactly 10 features
   - Verify feature names match training pipeline

### Debugging

**Check Vercel Logs:**

- Go to Vercel Dashboard → Functions → View logs

**Verify Model Info:**

```bash
# Check model performance and metadata
curl https://your-app.vercel.app/api/model-info
```

**Test Supabase Connection:**

```bash
# Test database connectivity (replace with your credentials)
curl -H "apikey: YOUR_ANON_KEY" \
     -H "Authorization: Bearer YOUR_ANON_KEY" \
     "https://your-project.supabase.co/rest/v1/seating_data"
```

## 🔄 Continuous Integration

### GitHub Workflow Features

- **Automated Training**: Weekly model retraining
- **Data Validation**: Ensures data quality before training
- **Performance Monitoring**: Tracks model performance over time
- **Automatic Deployment**: Updates production models seamlessly
- **Error Handling**: Graceful failure with notifications

### Manual Model Update

To manually trigger model retraining:

1. Go to GitHub repository
2. Navigate to Actions tab
3. Select "Retrain ML Models" workflow
4. Click "Run workflow"

## 📝 API Usage Examples

### Today/Tomorrow Predictions

```javascript
// Fetch today and tomorrow predictions
const response = await fetch("/api/predictions/today-tomorrow");
const data = await response.json();

console.log(data.data.predictions);
// Output: { today: {...}, tomorrow: {...} }
```

### Weekly Average Predictions

```javascript
// Fetch weekly averages
const response = await fetch("/api/predictions/weekly-average");
const data = await response.json();

console.log(data.data.predictions);
// Output: { monday: {...}, tuesday: {...}, ... }
```

### Model Information

```javascript
// Check model status and performance
const response = await fetch("/api/model-info");
const data = await response.json();

console.log(data.data.performance);
// Output: { density_r2: 0.97, seats_r2: 0.72, ... }
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:

- Check the troubleshooting section above
- Review Vercel deployment logs
- Verify Supabase configuration
- Ensure environment variables are properly set
