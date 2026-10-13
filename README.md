# AI Hotel Operations & Guest Experience Platform

An AI-enabled hotel management platform that combines hotel operations, guest-service automation, role-based workflows, Generative AI, and machine-learning-based occupancy-demand forecasting.

The system is designed as a final-year B.Tech project and portfolio application with a production-style architecture using React, FastAPI, PostgreSQL, Gemini AI, and scikit-learn.

---
## Live Deployment

**Frontend:**  
https://ai-hotel-frontend-fx90.onrender.com

**Backend API:**  
https://ai-hotel-api.onrender.com

**Swagger API Documentation:**  
https://ai-hotel-api.onrender.com/docs

> The application is deployed on Render. Free-tier services may take a short time to wake up after inactivity.

## Features

### Authentication and Role-Based Access

The platform supports four user roles:

- Manager
- Front Desk
- Operations
- Guest

JWT authentication and backend role-based authorization are used to restrict access to protected functionality.

---

## Room Management

The system supports:

- room categories
- room status tracking
- room availability
- room assignment to reservations

Room states are synchronized with operational workflows.

---

## Reservation Management

Managers and front-desk staff can:

- create reservations
- assign or change rooms
- check guests in
- check guests out
- cancel reservations

Guests can view their own reservations.

Checkout automatically triggers a housekeeping workflow.

---

## Automated Housekeeping Workflow

When a guest checks out:

1. The room status changes to `NEEDS_CLEANING`
2. A housekeeping task is automatically created
3. The task can be assigned to Operations
4. Starting the task changes the room status to `CLEANING`
5. Completing the task changes the room back to `AVAILABLE`

This creates an event-driven operational workflow instead of treating reservations and housekeeping as independent modules.

---

## Guest Request Management

Guests can submit requests such as:

- housekeeping requests
- maintenance issues
- amenities
- service problems

Managers can assign these requests to operational staff.

The workflow supports:

```text
SUBMITTED
    ↓
ACKNOWLEDGED
    ↓
IN_PROGRESS
    ↓
RESOLVED

Gemini AI Integration
Guest requests are automatically analyzed using Gemini AI.
The AI generates:
- request category
- priority
- short summary
The backend includes retry handling for transient Gemini API failures and falls back safely when the AI service is temporarily unavailable.
Machine Learning Occupancy-Demand Forecasting
The project includes a separate machine-learning pipeline for hotel demand forecasting.
Dataset
The ML pipeline uses the public Hotel Booking Demand dataset.
The model focuses on City Hotel bookings.
Because the dataset does not contain verified historical physical room inventory, the target is defined as:
Daily occupied-room demand proxy based on non-cancelled City Hotel stays.

It should therefore not be interpreted as an exact occupancy percentage.
Data Processing
The pipeline:
1. filters City Hotel bookings
2. removes cancelled stays
3. calculates stay duration
4. expands reservations into occupied room-night dates
5. aggregates occupied-room demand by date
6. creates a continuous daily time series
Final derived dataset:
Period: 2015-07-01 to 2017-08-31
Daily observations: 793

Feature Engineering
The forecasting model uses calendar, lag, and rolling-history features.
Examples include:
- day of week
- month
- day of year
- weekend indicator
- 1-day lag
- 2-day lag
- 3-day lag
- 7-day lag
- 14-day lag
- 28-day lag
- rolling means
- rolling standard deviation
Model Comparison
Several regression models were evaluated:
- Ridge Regression
- Random Forest Regressor
- Extra Trees Regressor
- Gradient Boosting Regressor
- HistGradientBoosting Regressor
The models were compared against a persistence baseline.
Time-Series Validation
A rolling expanding-window validation strategy was used instead of random train/test splitting.
The selected model was:
GradientBoostingRegressor

Rolling-validation results:
Model mean MAE:        11.8386
Persistence mean MAE:  12.8733
Improvement:            8.04%

Gradient Boosting achieved the best average rolling-validation performance among the evaluated models.
Forecast Horizon
The current model performs:
one-day-ahead forecasting

This is important because lag features require actual historical occupancy-demand values through the previous day.
The system does not claim arbitrary long-range forecasting.
Demand Classification
The forecast is translated into an operational demand level using historical demand quantiles:
LOW
MEDIUM
HIGH

The system then generates an operational recommendation for hotel managers.
Example:
Demand level: HIGH

Recommendation:
Review housekeeping coverage, front-desk staffing,
and room readiness before the forecast date.

ML API
The trained model is exposed through FastAPI:
GET /api/v1/forecast/occupancy

The endpoint is restricted to the MANAGER role.
Example response:
{
  "forecast_date": "2017-09-01",
  "predicted_occupied_rooms": 219.5,
  "demand_level": "HIGH",
  "operational_recommendation": "High historical demand is expected. Review housekeeping coverage, front-desk staffing, and room readiness before the forecast date.",
  "model": "GradientBoostingRegressor",
  "forecast_horizon": "one_day_ahead",
  "historical_data_end": "2017-08-31",
  "validation_mean_mae": 11.8386,
  "baseline_mean_mae": 12.8733,
  "improvement_vs_baseline_percent": 8.04
}

Manager Dashboard
Managers can view:
- available rooms
- active reservations
- pending operational tasks
- unresolved guest requests
- ML occupancy-demand forecast
- demand level
- operational recommendation
- model validation metrics
The ML section is explicitly labelled as a historical model demonstration so that public historical training data is not presented as live hotel occupancy.
Tech Stack
Frontend
- React
- Vite
- Tailwind CSS
- React Router
- Axios
Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- AsyncPG
- Alembic
- JWT authentication
- Pydantic
AI
- Google Gemini API
Machine Learning
- Python
- pandas
- NumPy
- scikit-learn
- joblib
Infrastructure
- Docker
- Docker Compose
- PostgreSQL 16

Project Structure
ai-hotel-platform/
│
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── requirements.txt
│   └── requirements-dev.txt
│
├── frontend/
│   ├── public/
│   └── src/
│       ├── api/
│       ├── components/
│       └── pages/
│
├── ml/
│   ├── data/
│   ├── models/
│   └── src/
│
├── docker-compose.yml
└── README.md

Automated Tests
The project includes automated tests for the ML service and forecast API.
Currently tested:
- model artifact loading
- ML feature generation
- non-negative prediction
- expected forecast response fields
- demand classification
- recommendation generation
- unauthenticated access
- Front Desk RBAC restriction
- Manager forecast access
- API demand-level response
- API recommendation response
Current result:
12 passed

Run the backend tests with:
cd backend
python -m pytest tests -v

Local Setup
1. Clone the Repository
git clone https://github.com/kavya1342/ai-hotel-platform.git
cd ai-hotel-platform

2. Start PostgreSQL
Docker Desktop must be running.
docker compose up -d postgres

3. Backend Setup
cd backend
python -m venv .venv

Activate the environment.
Windows PowerShell:
.\.venv\Scripts\Activate.ps1

Install dependencies:
pip install -r requirements.txt

Create:
backend/.env

using:
backend/.env.example

as the configuration template.
Never commit the real .env file.
Run database migrations:
alembic upgrade head

Start the backend:
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Swagger documentation:
http://127.0.0.1:8000/docs

4. Frontend Setup
Open another terminal:
cd frontend
npm install
npm run dev

The frontend normally runs at:
http://localhost:5173

Security
The repository intentionally excludes:
- .env
- virtual environments
- node_modules
- raw large training dataset
- API secrets
- database passwords
Secrets should always be supplied using environment variables.
Current ML Limitations
The forecasting model is intentionally presented with its limitations.
- Public historical data ends in August 2017
- Dataset occupancy is a demand proxy rather than verified physical hotel occupancy
- Forecast horizon is one day ahead
- The model is not trained using the demo hotel's live reservation history
- The historical ML demonstration should not be interpreted as a live 2026 hotel forecast
These limitations are explicitly displayed in the application rather than hidden.
Future Improvements
Potential extensions include:
- retraining using live hotel reservation history
- multi-day forecasting
- occupancy-rate forecasting using verified room inventory
- dynamic staffing recommendations
- room pricing recommendations
- automated model retraining
- richer analytics dashboards
- model monitoring and drift detection

Author
Kavya
B.Tech Computer Science — Artificial Intelligence & Machine Learning

Project focus:
Full-Stack Development
Backend Architecture
Generative AI
Machine Learning
Hotel Operations Automation