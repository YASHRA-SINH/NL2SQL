# Technical Walkthrough: The Lifecycle of a Query
### Presentation Illustration Guide

This document is designed to be presented as a step-by-step technical illustration. It breaks down exactly what happens under the hood when a user asks a question in the HealthQuery AI system.

---

## 🟢 Phase 1: User Intent & Ingestion

### 1. The Trigger
The user sits at the React frontend and types a natural language question into the chat interface:
> *"Show me the monthly revenue trend for Q1 2026."*

### 2. API Routing (`FastAPI`)
- The React app sends an HTTP `POST /api/chat` request to the Python backend.
- The payload includes the user's question, their session ID, and the **target database context** (e.g., `clinic` vs `sales`).

### 3. Agent Instantiation (`AgentManager`)
- The `agent_manager.py` intercepts the request.
- It dynamically loads the correct database profile (schema definitions, memory paths) and instantiates a localized **Vanna 2.0 Agent** specifically tuned for that database.

> **Visual Idea for Slide:** A diagram showing a user typing on a laptop → an arrow to a FastAPI icon → branching into two Vanna Agent icons (Clinic Agent / Sales Agent).

---

## 🧠 Phase 2: Context Retrieval & Prompt Construction (RAG)

Before sending the question to the AI, the agent needs to give it context. It does not send the raw question blindly.

### 1. Persistent Memory Lookup (`PersistentAgentMemory`)
- The agent queries the localized JSON vector store (`memory_store/clinic.json`).
- It looks for **semantically similar questions** asked in the past.
- *Example Match Found:* *"What was the revenue by month last year?" → `SELECT TO_CHAR(invoice_date, 'YYYY-MM') AS month, SUM(total_amount) FROM invoices...`*

### 2. System Prompt Injection (`SystemPromptBuilder`)
The agent builds a massive "System Prompt" containing:
1. **The Database Schema:** Exactly what tables and columns exist.
2. **The Rules:** Strict instructions (e.g., "PostgreSQL requires non-aggregated columns in the GROUP BY clause. Do not read from CSV files.").
3. **The Examples (RAG):** The similar Q&A pairs retrieved from memory to serve as a few-shot learning template.

> **Visual Idea for Slide:** A puzzle being assembled. Pieces labeled: "User Question", "Memory Match (RAG)", "Schema Context", and "Guardrails". These combine into one giant text block sent to the LLM.

---

## ⚙️ Phase 3: LLM Generation & Tool Calling

### 1. Inference Engine (`Groq + LLaMA 3`)
- The massive prompt is sent to the **Groq LPU API**.
- Because Groq runs LPUs (Language Processing Units), inference takes ~0.5 seconds for a 70B parameter model.
- The model acts as a reasoning engine. It does not just output text; it decides to invoke a **Tool Call**.

### 2. The Tool Call Payload
Instead of talking back to the user, the LLM outputs a structured JSON command:
```json
{
  "name": "run_sql",
  "parameters": {
    "sql": "SELECT TO_CHAR(invoice_date, 'YYYY-MM') AS month, SUM(total_amount) AS revenue FROM invoices WHERE invoice_date >= '2026-01-01' AND invoice_date <= '2026-03-31' GROUP BY month ORDER BY month;"
  }
}
```

> **Visual Idea for Slide:** The Groq logo parsing the puzzle from Phase 2, and outputting a glowing JSON code block instead of human text.

---

## 🛡️ Phase 4: Execution & Safety Guardrails

### 1. Interception (`ToolRegistry`)
Vanna intercepts the LLM's tool call. Before executing it against the database, it passes it through the security layer.

### 2. Read-Only Enforcement (`ReadOnlyPostgresRunner`)
- The `read_only_postgres_runner.py` receives the SQL string.
- It parses the SQL to ensure it does not contain destructive keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`).
- It connects to the PostgreSQL instance using a restricted database user role.

### 3. Execution & Dataframes
- The SQL is executed.
- The results are fetched and immediately converted into a **Pandas DataFrame** in server memory.
- *Result:* A 3-row table with months and revenue totals.

> **Visual Idea for Slide:** A SQL query approaching a PostgreSQL database, but passing through a glowing shield icon (ReadOnly Runner) first. On the other side, the database spits out a neat Excel-like table (Pandas).

---

## 📊 Phase 5: Visualization & Self-Correction

### 1. Secondary LLM Call (`VisualizeDataTool`)
- Vanna passes the Pandas DataFrame back to the LLM and says: *"You successfully retrieved this data. Now, write Python Plotly code to visualize it."*
- The LLM generates Python code (e.g., `px.bar(df, x='month', y='revenue')`).
- Vanna executes this Python code in a secure sandbox, generating an interactive JSON chart object.

### 2. The Self-Correction Loop (What if it fails?)
If Phase 4 threw an error (e.g., a syntax error), the system **does not crash**.
- The error is captured (e.g., *"column must appear in GROUP BY"*).
- It is sent back to the LLM automatically.
- The LLM rewrites the SQL and tries again until it succeeds (up to 10 attempts).

> **Visual Idea for Slide:** Two paths. A green path (Success) leading to a Python script drawing a chart. A red path (Error) looping backward to the LLM with a "Try Again" arrow.

---

## 🚀 Phase 6: Delivery & Learning

### 1. Package the Response
The backend bundles all generated artifacts into a single response payload:
- The human-readable summary
- The generated SQL string
- The raw data (JSON array)
- The interactive chart configuration (Plotly JSON)

### 2. Commit to Memory
Because the query was successful, the `PersistentAgentMemory` takes the original user question and the final, successful SQL query and saves it to `memory_store/clinic.json`. **The system is now permanently smarter.**

### 3. Render on Frontend
The React frontend receives the payload and renders the glassmorphic UI components, delivering the insight to the user in under 3 seconds total.

> **Visual Idea for Slide:** A sleek dashboard lighting up with a bar chart, while a "Save" icon drops the successful query into a glowing brain/memory drive for the future.
