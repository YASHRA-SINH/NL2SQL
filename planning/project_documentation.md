# NL2SQL Project Documentation

## Project Overview

This is a **Natural Language to SQL (NL2SQL) Chatbot** designed to allow users to query a clinical database using plain English questions. Instead of writing SQL manually, users can type questions like "Show me patients from Mumbai" and the system automatically generates and executes the appropriate SQL query, then presents results with visualizations and natural language summaries.

## End Goal

Build an intelligent AI assistant that bridges the gap between non-technical users and complex databases by accepting natural language queries and returning actionable data insights through an intuitive web interface.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Groq (llama-3.3-70b-versatile) via OpenAI-compatible API |
| **NL2SQL Framework** | Vanna 2.0 Agent |
| **Backend API** | FastAPI + Uvicorn |
| **Database** | PostgreSQL (clinic) |
| **Frontend** | HTML5, CSS3 (glassmorphism), JavaScript (vanilla) |
| **Charting** | Plotly.js |
| **Code Highlighting** | Highlight.js |
| **Data Processing** | Pandas |
| **Task Queue/Async** | AsyncIO |
| **Environment Management** | Python-dotenv |

## Directory Structure & File Purposes

```
NL2SQL/
├── .env                      # Environment variables (contains GROQ_API_KEY - not in git)
├── .gitignore                # Git ignore file (only contains .env)
├── clinic.db                 # SQLite database with mock clinical data (auto-generated)
├── memory_store.json         # Persistent storage for learned Q-SQL pairs (auto-generated on saves)
│
├── main.py                   # FastAPI application entry point
│   └── Responsibilities:
│       • Initializes FastAPI app with CORS middleware
│       • lifespan events: loads persistent memory on startup, injects DDL schema
│       • POST /api/chat endpoint: receives user questions, orchestrates Vanna Agent
│       • GET / endpoint: serves index.html
│       • Aggregates async UI components into structured JSON responses
│       • Serves static files (HTML, CSS, JS)
│
├── vanna_setup.py            # Vanna 2.0 Agent initialization & configuration
│   └── Responsibilities:
│       • Instantiates OpenAILlmService pointing to Groq API
│       • Creates PostgresRunner for clinic
│       • Registers ToolRegistry with RunSqlTool & VisualizeDataTool
│       • Initializes PersistentAgentMemory
│       • Creates DefaultUserResolver for auth context
│       • Configures agent with max iterations, temperature, streaming
│
├── persistent_memory.py      # Custom AgentMemory with JSON file persistence
│   └── Responsibilities:
│       • Wraps Vanna's DemoAgentMemory (in-memory)
│       • Loads all saved Q-SQL pairs from memory_store.json on startup
│       • Auto-saves successful tool usages to JSON file
│       • Enables self-improving agent: learns from past queries
│       • Provides async load_from_disk() and query methods
│
├── setup_database.py         # Database bootstrap script
│   └── Responsibilities:
│       • Creates clinic.db schema (5 tables)
│       • Generates 200+ realistic mock patients, 15 doctors
│       • Populates 500+ appointments, 350 treatments, 300 invoices
│       • Uses Indian names and cities for realistic data
│
├── seed_memory.py            # Pre-trains agent with Q-SQL pairs
│   └── Responsibilities:
│       • Loads 15+ known-good question-SQL pairs
│       • Saves them to memory_store.json
│       • Gives agent a head start for similar queries
│
├── inspect_memory.py         # Utility to inspect saved memories
│   └── Responsibilities:
│       • Loads persistent memory from disk
│       • Displays current agent memories (questions & SQL)
│       • Debugging aid
│
├── requirements.txt          # Python package dependencies
│   └── Includes: vanna, fastapi, uvicorn, plotly, pandas, groq, openai, python-dotenv
│
├── planning/
│   ├── implementation_plan.md    # High-level implementation roadmap
│   └── knowledge_transfer.md     # System architecture & extension guide
│
├── static/
│   ├── index.html            # Web UI layout
│   │   └── Includes: chat interface, sidebar with suggestions, placeholder for messages
│   ├── script.js             # Frontend logic
│   │   └── Handles: form submission, API calls, message rendering, chart display, typing indicators
│   └── style.css             # Glassmorphism UI styling
│       └── Features: dark mode, gradient backgrounds, animations, responsive layout
│
└── f8c88490871f6169/         # Temporary output directory
    └── query_results_*.csv   # CSV files from executed queries (cached results)
```

## Database Schema (clinic.db)

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

These schemas are injected into the LLM's context on startup so it understands table structures.

## Workflow

1. **User Input** → User types a question in the web UI (e.g., "Show me patients from Mumbai")

2. **Frontend** → JavaScript captures form submission, sends POST request to `/api/chat`

3. **FastAPI** (`main.py`) → Receives request, creates RequestContext, calls `agent.send_message()`

4. **Vanna Agent** (`vanna_setup.py`) → 
   - Receives message and context
   - Uses Groq LLM to interpret the question
   - Generates SQL query
   - Executes via SqliteRunner
   - Optionally generates visualization data
   - Returns async stream of UI components

5. **Main.py (Response Aggregation)** → 
   - Processes async stream of components:
     - `status_card` → Extracts SQL query
     - `dataframe` → Extracts result rows & column names
     - `chart` → Extracts Plotly chart data
     - `rich_text` → Extracts natural language summary
   - Aggregates into structured JSON response

6. **Persistent Memory** → 
   - If query succeeded, saves Q-SQL pair to JSON file
   - Next similar query benefits from this learning

7. **Frontend Rendering** → 
   - Receives JSON with `{ sql, data, columns, chart, summary, conversation_id }`
   - Renders SQL in syntax-highlighted code block
   - Renders data table
   - Renders Plotly chart
   - Displays natural language summary

## Key Features

✅ **Natural Language Interface** — Users ask in English; system generates SQL  
✅ **Persistent Learning** — Successful queries saved to `memory_store.json`; agent improves over time  
✅ **Real-time Data** — Results streamed asynchronously  
✅ **Visual Insights** — Plotly charts for data visualization  
✅ **Syntax Highlighting** — Generated SQL displayed with Highlight.js  
✅ **Glassmorphism UI** — Modern, dark-mode web interface  
✅ **Suggested Queries** — Sidebar with pre-seeded common questions  
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

4. **Init Database**
   ```bash
   python setup_database.py  # Creates clinic.db with schema + mock data
   ```

5. **Seed Memory**
   ```bash
   python seed_memory.py  # Pre-trains agent with 15+ Q-SQL pairs
   ```

6. **Launch Server**
   ```bash
   python main.py  # Starts on http://localhost:8000
   ```

7. **Access UI** → Open browser to `http://localhost:8000`

## Extension Points

- **New Tables**: Update `setup_database.py`, inject DDL in `main.py` lifespan, update `vanna_setup.py` system prompt
- **Change LLM**: Swap `OpenAILlmService` in `vanna_setup.py` to different provider
- **Frontend Customization**: Modify `static/` files; API expects `{ sql, data, columns, chart, summary }` JSON structure
- **Tools**: Register additional tools in `vanna_setup.py` tool registry for new capabilities

## Important Notes

⚠️ **Memory Persistence** — Only tool usages (successful queries) are persisted to disk. Text memories are session-only. Pre-seeded pairs prevent total loss on restart.

⚠️ **SQL Security** — Currently validates SELECT queries but runs against full database access. For production, implement row-level security and query validation.

⚠️ **.env Required** — `GROQ_API_KEY` must be set in `.env` file (git-ignored for security)

---

This is a fully functional NL2SQL system designed for clinical data querying with a modern, user-friendly interface and intelligent query learning capabilities. All components are modular and can be extended or swapped independently.