# QoS Buddy v2.0 - Setup Guide

## Prerequisites

- **Python 3.11** (recommended - 3.13 has compatibility issues)
- Node.js 18+ and npm
- Git (optional)

## Step 1: Get an LLM API Key (FREE)

Agent 1 (Chatbot) requires an API key. Choose one:

### Option A: Google Gemini (recommended)
1. Visit **https://aistudio.google.com/app/apikey**
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

### Option B: OpenRouter
1. Visit **https://openrouter.ai/keys**
2. Create an account and generate a key

**Free Tier Limits (Gemini):**
- 60 requests per minute
- 1,500 requests per day
- No credit card required

## Step 2: Install Python Dependencies

```bash
cd backend
pip install -r ../requirements.txt
```

**Installation time:** ~5-10 minutes

## Step 3: Configure Environment Variables

```bash
copy .env.example .env
```

Edit `.env` and fill in your API key:
```
GEMINI_API_KEY=AIza_your_actual_key_here
JWT_SECRET_KEY=your-random-secret-string
```

## Step 4: Generate Data & Initialize Agents

```bash
cd backend
python data_pipeline.py
python agent1_chatbot.py   # optional test
python agent2_diagnostic.py # optional test
```

## Step 5: Start Backend Server

```bash
cd backend
python main.py
```

The API will be available at:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

## Step 6: Install & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard opens at: **http://localhost:5173**

## Step 7: Create Your Account

1. Open http://localhost:5173
2. Click "Register" to create an account
3. Log in with your credentials

## New Features (v2.0)

### Authentication
- JWT-based login/registration
- Per-user sessions with role support (viewer, analyst, admin)

### Agent Simulator
- Start/stop from dashboard
- Configurable interval (1-60 minutes)
- Autonomous diagnostic cycles

### Model Improvements
- K-fold cross-validation (5 folds)
- Model versioning (outputs/versions/)
- Feature importance tracking
- RMSE metric added

### Data Drift Detection
- PSI (Population Stability Index) per feature
- Warning/critical thresholds
- Accessible via `GET /api/ml/drift`

### New Visualizations
- SLA breach risk timeline (BO2)
- CAPEX investment heatmap (BO3)
- Alert trend chart (hourly distribution)
- Model performance dashboard (radar + bar charts)

### Export
- Alerts CSV
- KPIs CSV
- Zones CSV
- Full diagnostic report (TXT)

### Architecture
- Routes split into modules (routes/chat, diagnostics, ml, data, auth, simulator)
- KPI thresholds externalized to config.py
- CORS restricted to configured origins
- Chat input validation (max 2000 chars)
- DB alerts enabled by default

## Project Structure

```
qos-buddy/
├── backend/
│   ├── main.py                    # App factory (thin)
│   ├── agent1_chatbot.py          # RAG chatbot
│   ├── agent2_diagnostic.py       # Diagnostic worker
│   ├── database.py                # SQLite schema + User model
│   ├── scheduler.py               # Background tasks
│   ├── routes/
│   │   ├── auth.py                # JWT register/login/me
│   │   ├── chat.py                # Agent 1 endpoints
│   │   ├── diagnostics.py         # Agent 2 endpoints
│   │   ├── ml.py                  # Detection, prediction, drift
│   │   ├── data.py                # Refresh, enrichment
│   │   ├── simulator.py           # Start/stop simulator
│   │   └── deps.py                # Shared dependencies
│   ├── core/
│   │   ├── config.py              # All settings + KPI thresholds
│   │   ├── schemas.py             # Pydantic DTOs
│   │   └── filled_transform.py    # CSV column mapping
│   └── services/
│       ├── orchestrator.py        # Agent coordinator
│       ├── data_manager.py        # CSV loader + cache
│       ├── detection_agent.py     # Isolation Forest
│       ├── prediction_agent.py    # RandomForest + CV + versioning
│       ├── drift_detector.py      # PSI-based drift detection
│       ├── alert_agent.py         # Alert merging
│       └── recommendation_service.py
├── frontend/
│   └── src/
│       ├── App.jsx                # Auth wrapper + shell
│       ├── components/
│       │   ├── LoginPage.jsx      # Login/register page
│       │   └── dashboard/
│       │       ├── DashboardMain.jsx
│       │       ├── SlaTimelineChart.jsx
│       │       ├── CapexHeatmapPanel.jsx
│       │       ├── AlertTrendChart.jsx
│       │       ├── ModelPerformancePanel.jsx
│       │       ├── SimulatorToggle.jsx
│       │       └── ExportPanel.jsx
│       └── services/
│           └── api.js             # Auth interceptor + all APIs
├── outputs/
│   ├── bo1/                       # Pre-trained models
│   └── versions/                  # Versioned model history
├── .env.example                   # Environment template
├── requirements.txt
└── README.md
```

## API Endpoints (v2.0)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Create account |
| `/api/auth/login` | POST | Login (returns JWT) |
| `/api/auth/me` | GET | Current user info |
| `/api/chat` | POST | Chat with AI advisor |
| `/api/diagnostics/latest` | GET | Latest alerts |
| `/api/diagnostics/analyze` | POST | Trigger analysis |
| `/api/bo/overview` | GET | BO1/BO2/BO3 overview |
| `/api/ml/detect` | POST | Anomaly detection |
| `/api/ml/predict` | POST | QoS prediction |
| `/api/ml/drift` | GET | Data drift check |
| `/api/ml/models/status` | GET | Model health |
| `/api/simulator/start` | POST | Start simulator |
| `/api/simulator/stop` | POST | Stop simulator |
| `/api/simulator/status` | GET | Simulator status |
| `/api/data/refresh` | POST | Reload dataset |
| `/api/enrichment/catalog` | GET | External datasets |

## Troubleshooting

### "Gemini API Error"
- Verify your API key is correct in `.env`
- Check free tier limits (60 req/min)

### "No data available"
- Check that `backend/unified_telecom_dataset_FILLED.csv` exists
- Run `python data_pipeline.py`

### "ChromaDB error"
- Delete `data/chroma_db` folder and restart

### Frontend won't connect
- Verify backend is running on port 8000
- Check `CORS_ORIGINS` in `.env` includes your frontend URL

## For Development

```bash
# Backend (hot reload)
cd backend
DEV_MODE=true python main.py

# Frontend (hot reload)
cd frontend
npm run dev
```

## Support

- API docs: http://localhost:8000/docs
- Check console logs for agent diagnostics
