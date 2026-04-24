# Vanna AI NL2SQL Chatbot - Knowledge Transfer Document

## Project Overview

This project is a Natural Language to SQL (NL2SQL) chatbot designed to query a clinical database using plain English. It leverages the **Vanna 2.0 Agent framework** to interpret user questions, generate SQL queries, execute them against a SQLite database, and optionally visualize the results. 

The backend is built with **FastAPI**, which bridges the Vanna Agent with a modern web interface.

## System Architecture

The application is composed of the following layers:

1.  **Frontend (Web UI):** A glassmorphic, dark-mode web interface (`static/index.html`, `static/script.js`, `static/style.css`) where users can type natural language questions and view chat responses, SQL queries, data tables, and charts.
2.  **API Backend (FastAPI):** `main.py` serves as the entry point. It hosts the REST API endpoints (`/api/chat`) and serves the static frontend files.
3.  **Vanna Agent Core:** `vanna_setup.py` configures the Vanna Agent. It binds together the LLM, the database runner, the tools, and the memory.
4.  **LLM Provider (Groq):** The system uses Groq's `llama-3.3-70b-versatile` model via an OpenAI-compatible API wrapper for high-speed, accurate SQL generation.
5.  **Database (SQLite):** `clinic.db` is the local SQLite database containing mock clinical data (patients, doctors, appointments, treatments, invoices).
6.  **Persistent Memory:** `persistent_memory.py` is a custom wrapper around Vanna's `DemoAgentMemory`. It automatically saves successful Q&A pairs (tool usages) to a local JSON file (`memory_store.json`), allowing the agent to "remember" previous queries across server restarts.

---

## File Structure

```text
c:\NLP-SQL\
├── .env                     # Contains sensitive environment variables (e.g., GROQ_API_KEY)
├── clinic.db                # SQLite database with mock clinical data
├── inspect_memory.py        # Utility script to view contents of the memory store
├── main.py                  # FastAPI application and routing
├── memory_store.json        # Persistent storage for agent memories (auto-generated)
├── persistent_memory.py     # Custom AgentMemory implementation for JSON persistence
├── requirements.txt         # Python dependencies
├── seed_memory.py           # Utility to pre-train the agent with initial QA pairs
├── setup_database.py        # Script to create tables and insert mock data into clinic.db
├── vanna_setup.py           # Vanna 2.0 Agent initialization and configuration
└── static/                  # Frontend assets
    ├── index.html           # Main web interface layout
    ├── script.js            # Frontend logic (API calls, UI updates, chart rendering)
    └── style.css            # Styling and glassmorphism effects
```

---

## Database Schema (`clinic.db`)

The database consists of 5 interconnected tables:
*   `patients`: id, first_name, last_name, email, phone, date_of_birth, gender, city, registered_date
*   `doctors`: id, name, specialization, department, phone
*   `appointments`: id, patient_id, doctor_id, appointment_date, status, notes
*   `treatments`: id, appointment_id, treatment_name, cost, duration_minutes
*   `invoices`: id, patient_id, invoice_date, total_amount, paid_amount, status

During the FastAPI startup (`main.py`), the Data Definition Language (DDL) for these tables is actively injected into the agent's RAM memory so the LLM has exact structural context.

---

## Key Components

### 1. `vanna_setup.py` (The Brain)
This file instantiates the Vanna components:
*   **OpenAILlmService**: Configured to use Groq's API endpoint with a Llama 3.3 model.
*   **SqliteRunner**: Connects to `clinic.db`.
*   **ToolRegistry**: Registers `RunSqlTool` and `VisualizeDataTool` allowing the agent to execute SQL and plot data.
*   **ClinicSystemPromptBuilder**: Appends the database schema directly to the system prompt to ensure the LLM knows what tables are available.

### 2. `main.py` (The API)
*   **Lifespan Events**: On startup, it calls `agent_memory.load_from_disk()` to hydrate the agent's RAM with past learnings, and injects the DDL schema.
*   `/api/chat`: This POST endpoint receives user messages, passes them to `agent.send_message()`, and aggregates the asynchronous stream of UI components (`status_card`, `dataframe`, `chart`, `rich_text`) into a structured JSON response for the frontend.

### 3. `persistent_memory.py` (The Memory)
Vanna's default memory is volatile (RAM-only) or relies on external vector databases. To keep it local and lightweight:
*   `PersistentAgentMemory` wraps `DemoAgentMemory`.
*   It intercepts `save_tool_usage` events. If the tool usage (like generating and running SQL) was successful, it appends the metadata to `memory_store.json`.
*   This creates a self-improving loop: the more queries run successfully, the smarter the agent gets at answering similar queries in the future.

---

## How to Run the Project

1.  **Environment Setup**: Ensure `GROQ_API_KEY` is set in the `.env` file.
2.  **Install Dependencies**: `pip install -r requirements.txt`
3.  **Database Initialization (if needed)**: Run `python setup_database.py` to recreate `clinic.db`.
4.  **Start the Server**: Run `python main.py` (or `uvicorn main:app --reload`).
5.  **Access UI**: Open a browser and navigate to `http://localhost:8000/`.

---

## How to Extend / Modify

*   **Adding new tables**: Update `setup_database.py` to create the table, then update the DDL injection in `main.py` (lifespan function) AND the `ClinicSystemPromptBuilder` in `vanna_setup.py`.
*   **Changing the LLM**: Edit the `OpenAILlmService` configuration in `vanna_setup.py` to point to a different OpenAI-compatible provider, or swap it for a different Vanna LLM integration.
*   **Frontend changes**: Modify files in the `static/` directory. The UI expects a specific JSON structure from `/api/chat` containing `sql`, `data`, `columns`, `chart`, and `summary`.
