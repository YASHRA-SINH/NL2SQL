# NL2SQL Project Documentation

## Project Overview

This is a **Natural Language to SQL (NL2SQL) Chatbot** designed to allow users to query configured PostgreSQL databases using plain English questions. Instead of writing SQL manually, users can switch between profiles such as `clinic` and `sales`, ask questions like "Show monthly revenue trend", and the system generates SQL, executes it safely, validates the result, and returns data tables, summaries, and visualizations.

## End Goal

Build an intelligent AI assistant that bridges the gap between non-technical users and complex databases by accepting natural language queries and returning actionable data insights through an intuitive web interface.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Groq (llama-3.1-8b-instant) via OpenAI-compatible API |
| **NL2SQL Framework** | Vanna 2.0 Agent |
| **Backend API** | FastAPI + Uvicorn |
| **Database** | PostgreSQL profiles (`clinic`, `sales`) |
| **Frontend** | React + Vite + Tailwind CSS |
| **Charting** | Plotly.js |
| **Data Processing** | Pandas |
| **Task Queue/Async** | AsyncIO |
| **Environment Management** | Python-dotenv |

## Directory Structure & File Purposes

```
NL2SQL/
├── app/
│   ├── main.py                    # FastAPI app, profile APIs, chat response aggregation
│   ├── agent_manager.py           # Builds one Vanna agent per database profile
│   ├── database_profiles.py       # PostgreSQL profile config, schema introspection, prompt rules
│   ├── persistent_memory.py       # JSON-backed memory implementation
│   ├── read_only_postgres_runner.py # Read-only SQL runner with timeout guardrails
│   └── response_quality.py        # Clarification, result validation, summaries, chart rules
│
├── databases/
│   ├── clinic/
│   │   ├── create_clinic_database.py
│   │   ├── setup_clinic_database.py
│   │   └── seed_clinic_memory.py
│   └── sales/
│       ├── setup_sales_database.py
│       └── seed_sales_memory.py
│
├── memory_store/
│   ├── clinic.json                # Clinic-specific learned/seeded Q-SQL memory
│   └── sales.json                 # Sales-specific learned/seeded Q-SQL memory
│
├── frontend/                      # React + Vite UI
├── scripts/inspect_memory.py      # Utility to inspect memory per profile
├── main.py                        # Convenience entrypoint for app.main
├── requirements.txt
└── planning/
```

## Database Profiles & Schema

The system now supports multiple PostgreSQL profiles. Each profile has its own connection settings, schema introspection, prompt context, frontend suggestions, and memory file.

Current profiles:
- `clinic` → clinical operations data: patients, doctors, appointments, treatments, invoices
- `sales` → sales analytics data: customers, sales reps, products, orders, order items, payments, support tickets

### Clinic Schema

**5 interconnected tables:**

1. **patients**
   - Fields: `id`, `first_name`, `last_name`, `email`, `phone`, `date_of_birth`, `gender`, `city`, `registered_date`
   - 200 mock patients with Indian names/cities

2. **doctors**
   - Fields: `id`, `name`, `specialization`, `department`, `phone`
   - 15 doctors across specializations (Dermatology, Cardiology, Orthopedics, General, Pediatrics)

3. **appointments**
   - Fields: `id`, `patient_id`, `doctor_id`, `appointment_date`, `status`, `notes`
   - 500+ appointments; statuses: Scheduled, Completed, Cancelled, No-Show
   - Foreign keys to patients & doctors

4. **treatments**
   - Fields: `id`, `appointment_id`, `treatment_name`, `cost`, `duration_minutes`
   - 350+ treatments with cost data
   - Foreign key to appointments

5. **invoices**
   - Fields: `id`, `patient_id`, `invoice_date`, `total_amount`, `paid_amount`, `status`
   - 300+ invoices; statuses: Paid, Pending, Overdue
   - Foreign key to patients

Schemas are introspected from PostgreSQL and injected into the LLM prompt dynamically per active database profile.

## Workflow

1. **User Input** → User types a question in the web UI (e.g., "Show me patients from Mumbai")

2. **Frontend** → JavaScript captures form submission, sends POST request to `/api/chat`

3. **FastAPI** (`app/main.py`) → Receives request, resolves `database_id`, creates RequestContext, calls the matching profile agent

4. **Vanna Agent** (`app/agent_manager.py`) → 
   - Receives message and context
   - Uses Groq LLM to interpret the question
   - Generates SQL query
   - Executes via read-only PostgreSQL runner
   - Returns SQL and result data
   - Returns async stream of UI components

5. **Response Quality Layer** (`app/response_quality.py`) →
   - Asks clarification for ambiguous questions
   - Validates NULL-heavy or empty results
   - Generates concise insight summaries from result rows
   - Selects deterministic Plotly charts by rules

6. **Main.py (Response Aggregation)** → 
   - Processes async stream of components:
     - `status_card` → Extracts SQL query
     - `dataframe` → Extracts result rows & column names
     - `rich_text` → Extracts natural language summary
   - Aggregates into structured JSON response

7. **Profile-Specific Persistent Memory** → 
   - Successful examples are saved to `memory_store/<profile>.json`
   - Clinic and sales memories remain isolated, preventing cross-domain query pollution

8. **Frontend Rendering** → 
   - Receives JSON with `{ sql, data, columns, chart, summary, warnings, conversation_id, database_id }`
   - Renders SQL in syntax-highlighted code block
   - Renders data table
   - Renders Plotly chart
   - Displays natural language summary

## Key Features

✅ **Natural Language Interface** — Users ask in English; system generates SQL  
✅ **Multi-Database Profiles** — Switch between `clinic` and `sales` PostgreSQL databases  
✅ **Profile-Specific Memory** — Successful queries saved to `memory_store/<profile>.json`  
✅ **Real-time Data** — Results streamed asynchronously  
✅ **Rule-Based Visual Insights** — Time series → line chart, rankings → bar chart, composition → pie  
✅ **Result Validation** — Empty or NULL-heavy outputs are flagged with warnings  
✅ **Glassmorphism UI** — Modern, dark-mode web interface  
✅ **Dynamic Suggested Queries** — Suggestions change with the selected database profile  
✅ **Multi-table Queries** — Handles joins, grouping, aggregations  
✅ **Error Handling** — Graceful error messages  

## How to Rebuild from Scratch

1. **Clone/Initialize** → Clone repo or create folder structure

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment**
   ```bash
   echo "GROQ_API_KEY=gsk_..." > .env
   ```

4. **Init Databases**
   ```bash
   python databases/clinic/create_clinic_database.py
   python databases/clinic/setup_clinic_database.py
   python databases/sales/setup_sales_database.py
   ```

5. **Seed Profile Memory**
   ```bash
   python databases/clinic/seed_clinic_memory.py
   python databases/sales/seed_sales_memory.py
   ```

6. **Launch Server**
   ```bash
   python main.py  # Starts on http://localhost:8000
   ```

7. **Access UI** → Open browser to `http://localhost:8000`

## Extension Points

- **New Database Profile**: Add a `DatabaseProfile` in `app/database_profiles.py`, then create matching setup and seed scripts under `databases/<profile>/`
- **Prompt Rules**: Add domain-specific SQL definitions and join rules in `app/database_profiles.py`
- **Response Quality**: Extend `app/response_quality.py` for clarification, validation, summaries, or visualization mapping
- **Change LLM**: Swap `OpenAILlmService` in `app/agent_manager.py` to a different provider
- **Frontend Customization**: Modify `frontend/src/App.jsx`; API expects `{ sql, data, columns, chart, summary, warnings }`

## Important Notes

⚠️ **Memory Persistence** — Memory is now profile-specific. Clinic examples live separately from sales examples to avoid accidental reuse across schemas.

⚠️ **SQL Security** — The custom runner allows read-only SELECT/WITH queries and applies a statement timeout. For production, also use restricted database users, row-level security, and audit logging.

⚠️ **.env Required** — `GROQ_API_KEY` must be set in `.env` file (git-ignored for security)

---

This is a functional NL2SQL system designed for profile-based PostgreSQL querying with a modern web interface, isolated memory, stronger prompt grounding, result validation, and deterministic visualization behavior. All components are modular and can be extended or swapped independently.
