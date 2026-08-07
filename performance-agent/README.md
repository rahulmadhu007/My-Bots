# Performance Intelligence Agent

## Setup

Step 1: Navigate to project
```bash
cd performance-agent
```

Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

Step 3: Start the backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

Step 4: Open the frontend
Open `frontend/index.html` in your browser
(Just double click the file)

Step 5: Test with demo data
Type "Alex" in the search box
Select "Alex Morgan"
Click "Analyse Performance"
Watch all 6 agents run in sequence

No API keys are required. The Synthesis Agent runs fully offline and
cross-references specialist findings autonomously.

## Data Files

Place these Excel files in:
`/Users/rahulm/Desktop/My Deployments/`

- `servicenow_export.xlsx`
- `quality_scores.xlsx`
- `leave_tracker.xlsx`
- `cab_records.xlsx`

If that path is unavailable, the backend also checks `~/Desktop/My Deployments/` and the project's local `data/` folder (demo datasets are included there).

## What You Will See
- 6 agents running visibly in sequence
- Real data from 4 Excel datasets analysed
- Autonomous cross-agent correlation insights
- Professional performance dashboard
- Evidence-based recommendations

## Employee Names in Demo Data
- Alex Morgan (below average — interesting findings)
- Sarah Chen (high performer — team benchmark)
- James Patel (average performer)
- Priya Sharma (top performer)

## Architecture

```
Manager selects employee
        ↓
   Orchestrator
        ↓
┌───────┬───────┬───────┬───────┐
│Ticket │Quality│ Leave │  CAB  │  ← specialist agents
└───────┴───────┴───────┴───────┘
        ↓
  Synthesis Agent (offline / autonomous)
        ↓
  Performance Dashboard
```
