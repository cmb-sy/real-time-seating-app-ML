# Real-time Seating Prediction API (ML Version) Documentation

This document describes the API endpoints and request/response specifications for the machine learning-based real-time seating prediction system.

## Basic Information

- Base URL: `http://localhost:8000` (Development)
- Base URL: `https://real-time-seating-app-ml.vercel.app` (Production)
- Authentication: Not required
- Response Format: JSON
- Supported Days: Weekdays (Monday to Friday) only

## API Overview

This API uses machine learning models (Gradient Boosting Regressors) to predict seat occupancy rates and population density by day of the week. It uses only the day of the week as a feature and does not account for time-of-day variations.

## Endpoint List

### 1. Health Check

```
GET /health
```

**Response Example:**

```json
{
  "status": "ok",
  "message": "API is running"
}
```

### 2. Specific Day Prediction

Get prediction data for a specified day of the week.

```
GET /ml/predict?day_of_week={day_of_week}
```

**Parameters:**

- `day_of_week`: Day of week (0: Monday, 1: Tuesday, 2: Wednesday, 3: Thursday, 4: Friday)

**Response Example:**

```json
{
  "success": true,
  "day_of_week": 3,
  "weekday_name": "木",
  "predictions": {
    "density_rate": 28.06,
    "occupied_seats": 2
  },
  "message": "Machine learning model prediction"
}
```

### 3. Today and Tomorrow Predictions

Get prediction data for today and tomorrow (if both are weekdays) based on the current date.

```
GET /predictions/today-tomorrow
```

**Response Example:**

```json
{
  "success": true,
  "timestamp": "2023-06-12T20:45:11.596625",
  "data": {
    "today": {
      "date": "2023-06-12",
      "day_of_week": "木",
      "prediction": {
        "occupancy_rate": 0.28,
        "available_seats": 98,
        "status": "available",
        "confidence": "medium",
        "data_points": 55,
        "prediction_type": "ml_model",
        "model_details": {
          "density_rmse": 8.25,
          "seats_rmse": 0.86,
          "model_type": "gradient_boosting"
        }
      }
    },
    "tomorrow": {
      "date": "2023-06-13",
      "day_of_week": "金",
      "prediction": {
        "occupancy_rate": 0.36,
        "available_seats": 98,
        "status": "available",
        "confidence": "medium",
        "data_points": 55,
        "prediction_type": "ml_model",
        "model_details": {
          "density_rmse": 8.25,
          "seats_rmse": 0.86,
          "model_type": "gradient_boosting"
        }
      }
    }
  },
  "metadata": {
    "model_version": "1.0.0",
    "last_updated": "2023-06-12T20:45:11.596625",
    "model_type": "gradient_boosting",
    "features_used": ["day_of_week"],
    "confidence": "medium",
    "data_source": "ml_model",
    "weekday_only": true
  }
}
```

**Response Example (When Tomorrow is Weekend):**

```json
{
  "success": true,
  "timestamp": "2023-06-14T20:45:11.596625",
  "data": {
    "today": {
      "date": "2023-06-14",
      "day_of_week": "金",
      "prediction": {
        "occupancy_rate": 0.36,
        "available_seats": 98,
        "status": "available",
        "confidence": "medium",
        "data_points": 55,
        "prediction_type": "ml_model",
        "model_details": {
          "density_rmse": 8.25,
          "seats_rmse": 0.86,
          "model_type": "gradient_boosting"
        }
      }
    },
    "tomorrow": {
      "date": null,
      "day_of_week": null,
      "prediction": null,
      "message": "Tomorrow is a weekend, no service available"
    }
  },
  "metadata": {
    "model_version": "1.0.0",
    "last_updated": "2023-06-14T20:45:11.596625",
    "model_type": "gradient_boosting",
    "features_used": ["day_of_week"],
    "confidence": "medium",
    "data_source": "ml_model",
    "weekday_only": true
  }
}
```

### 4. Day-by-Day Analysis

Get predictions and analysis data for all weekdays.

```
GET /analysis/weekday_analysis
```

**Response Example:**

```json
{
  "success": true,
  "data": {
    "detailed_stats": {},
    "daily_predictions": {
      "月曜": {
        "レコード数": 55,
        "predictions": {
          "density_rate": 32.45,
          "occupied_seats": 2
        }
      },
      "火曜": {
        "レコード数": 55,
        "predictions": {
          "density_rate": 28.3,
          "occupied_seats": 2
        }
      },
      "水曜": {
        "レコード数": 55,
        "predictions": {
          "density_rate": 40.3,
          "occupied_seats": 3
        }
      },
      "木曜": {
        "レコード数": 55,
        "predictions": {
          "density_rate": 28.06,
          "occupied_seats": 2
        }
      },
      "金曜": {
        "レコード数": 55,
        "predictions": {
          "density_rate": 35.63,
          "occupied_seats": 2
        }
      }
    },
    "summary": {
      "全体": {
        "record_count": 55,
        "density_rate_mean": 32.95,
        "occupied_seats_mean": 2.2
      }
    }
  },
  "message": "Machine learning model day-by-day prediction"
}
```

### 5. Weekly Average Predictions

Get prediction data for all weekdays and a weekly summary, optimized for frontend display.

```
GET /predictions/weekly-average
```

**Response Example:**

```json
{
  "success": true,
  "timestamp": "2023-06-12T20:45:11.596625",
  "data": {
    "weekly_averages": [
      {
        "weekday": 0,
        "weekday_name": "月曜",
        "prediction": {
          "occupancy_rate": 0.32,
          "available_seats": 98,
          "status": "available",
          "confidence": "medium",
          "data_points": 55,
          "prediction_type": "ml_model",
          "model_details": {
            "density_rmse": 8.25,
            "seats_rmse": 0.86,
            "model_type": "gradient_boosting"
          }
        }
      },
      {
        "weekday": 1,
        "weekday_name": "火曜",
        "prediction": {
          "occupancy_rate": 0.28,
          "available_seats": 98,
          "status": "available",
          "confidence": "medium",
          "data_points": 55,
          "prediction_type": "ml_model",
          "model_details": {
            "density_rmse": 8.25,
            "seats_rmse": 0.86,
            "model_type": "gradient_boosting"
          }
        }
      },
      {
        "weekday": 2,
        "weekday_name": "水曜",
        "prediction": {
          "occupancy_rate": 0.4,
          "available_seats": 97,
          "status": "available",
          "confidence": "medium",
          "data_points": 55,
          "prediction_type": "ml_model",
          "model_details": {
            "density_rmse": 8.25,
            "seats_rmse": 0.86,
            "model_type": "gradient_boosting"
          }
        }
      },
      {
        "weekday": 3,
        "weekday_name": "木曜",
        "prediction": {
          "occupancy_rate": 0.28,
          "available_seats": 98,
          "status": "available",
          "confidence": "medium",
          "data_points": 55,
          "prediction_type": "ml_model",
          "model_details": {
            "density_rmse": 8.25,
            "seats_rmse": 0.86,
            "model_type": "gradient_boosting"
          }
        }
      },
      {
        "weekday": 4,
        "weekday_name": "金曜",
        "prediction": {
          "occupancy_rate": 0.36,
          "available_seats": 98,
          "status": "available",
          "confidence": "medium",
          "data_points": 55,
          "prediction_type": "ml_model",
          "model_details": {
            "density_rmse": 8.25,
            "seats_rmse": 0.86,
            "model_type": "gradient_boosting"
          }
        }
      }
    ],
    "summary": {
      "most_busy_day": {
        "weekday": 2,
        "weekday_name": "水曜",
        "occupancy_rate": 0.4
      },
      "least_busy_day": {
        "weekday": 3,
        "weekday_name": "木曜",
        "occupancy_rate": 0.28
      },
      "average_occupancy": 0.33,
      "recommendation": "Overall occupancy is low. Wednesday is the busiest day, but still relatively available.",
      "prediction_type": "ml_model"
    }
  },
  "metadata": {
    "model_version": "1.0.0",
    "last_updated": "2023-06-12T20:45:11.596625",
    "model_type": "gradient_boosting",
    "features_used": ["day_of_week"],
    "confidence": "medium",
    "data_source": "ml_model",
    "prediction_type": "ml_weekly_average"
  }
}
```

## Data Type Definitions

### Basic Prediction Data

- `density_rate`: Population density rate (0-100%)
- `occupied_seats`: Number of occupied seats (integer)
- `occupancy_rate`: Occupancy rate (0-1.0, density_rate divided by 100)
- `available_seats`: Available seats (100 - occupied_seats)
- `status`: Crowding status ("available", "moderate", "busy")
- `confidence`: Prediction confidence ("low", "medium", "high")

### Model Information

- `model_version`: Model version
- `features_used`: Features used for prediction
- `data_points`: Number of data points used for training
- `model_type`: Type of machine learning model (gradient_boosting)
- `density_rmse`: Root Mean Square Error for density prediction
- `seats_rmse`: Root Mean Square Error for seat prediction

## Frontend Integration

Frontend applications primarily use `/predictions/today-tomorrow` and `/predictions/weekly-average` endpoints to fetch prediction data. The API provides formatted data ready for visualization, including occupancy rates, status indicators, and recommendations.

If the API specification changes, the frontend code should be updated accordingly. The current frontend displays density rates and occupied seats for each day of the week and visualizes weekly trends in a graph.

## Technical Implementation

The predictions are made using two separate gradient boosting regression models:

1. Density Rate Model - Predicts the density percentage (0-100%)
2. Occupied Seats Model - Predicts the number of occupied seats (0-100)

Both models use only the day of the week (0-4) as the input feature, making them simple but effective for pattern-based predictions.

## Error Handling

All endpoints return a `success` field indicating whether the request was successful. In case of errors, a descriptive error message is provided in the response along with an appropriate HTTP status code (usually 500 for server errors).

Example error response:

```json
{
  "success": false,
  "error": "ML prediction model could not be loaded.",
  "timestamp": "2023-06-12T20:45:11.596625",
  "message": "Model file not found or error occurred during prediction execution."
}
```
