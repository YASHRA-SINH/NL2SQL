# HealthQuery AI — NL2SQL Database Intelligence System
### Presentation Slides Content

---

## SLIDE 1 — Title Slide

**Project Title:** HealthQuery AI — A Natural Language to SQL Chatbot for Database Intelligence

**Subtitle:** Bridging the Gap Between Non-Technical Users and Complex Relational Databases

**Stack:** Vanna 2.0 Agent · Groq LLaMA 3 · FastAPI · PostgreSQL · Plotly

> 🖼️ **IMAGE PROMPT (Hero Banner / Title Visual):**
> "A sleek dark-mode futuristic dashboard interface showing a chat input box on the left and a glowing SQL query and bar chart on the right. In the center, a glowing brain-to-database connection line. Style: glassmorphism, deep navy blue and electric teal gradient background, minimalist and modern. No text. Suitable for a presentation title slide."

> 🖼️ **IMAGE PROMPT (Tech Stack Icons Strip):**
> "A horizontal strip of clean flat icons on a dark background representing the following technologies in order: a flame icon for Groq, a robot head for LLaMA AI model, a database cylinder for PostgreSQL, a lightning bolt for FastAPI, a chart icon for Plotly. Each icon is labeled below it. Flat vector icon style, dark background, teal and white color palette."

---

## SLIDE 2 — Problem Statement

### The Real Problem in Healthcare Data Access

- **82% of healthcare analysts** cannot write SQL. They rely on IT teams for ad-hoc data requests — creating a bottleneck that delays clinical and financial decision-making by **days to weeks**.
- Existing BI dashboards (Tableau, Power BI) are **static** — they only answer questions they were pre-built to answer.
- Writing SQL against a normalized relational schema (patients → appointments → invoices) requires intimate knowledge of foreign key relationships, aggregate functions, and dialect-specific syntax.
- In high-scale environments, **miswritten queries against live production databases** can cause performance degradation, full table scans, or surface PHI (Protected Health Information) to unauthorized roles.

### The Ask
> *"Who are the top 5 patients by billing amount this quarter, and what treatments drove those costs?"*
> — A question any clinic manager should be able to ask, and get an answer in under 5 seconds.

> 🖼️ **IMAGE PROMPT (Problem Illustration):**
> "A split illustration showing two scenes side by side on a dark background. Left side: A frustrated non-technical hospital manager staring at a screen full of SQL code, with a red cross symbol and a clock showing days passing. Right side: The same person typing a plain English question in a chat box and instantly receiving a clean bar chart and a data table. Style: flat vector illustration, dark navy background, red for the problem side, green/teal for the solution side."

---

## SLIDE 3 — Why NL2SQL? Why Now?

### Industry Context

| Traditional Approach | NL2SQL Approach |
|---|---|
| Submit ticket to IT/Analytics team | Ask in plain English, get results instantly |
| Wait 2–5 business days | Sub-5 second response time |
| Static pre-built reports | Dynamic, intent-driven querying |
| Requires SQL training | Zero technical knowledge needed |
| Cannot handle new questions | Adapts to any valid query against the schema |

### Why LLM-Powered NL2SQL over Rule-Based Parsers?
- Rule-based systems break on **synonym variation**, abbreviation, and contextual ambiguity (e.g., "visits" vs "appointments").
- LLMs understand **semantic intent**, not just keyword patterns.
- With Retrieval-Augmented Generation (RAG) from persistent memory, the system **improves accuracy over time** without retraining.

> 🖼️ **IMAGE PROMPT (Comparison Visual):**
> "A clean two-column infographic on a dark background. Left column titled 'Old Way' in red: icons of a ticket, a clock, a static PDF report. Right column titled 'NL2SQL Way' in teal: icons of a chat bubble, a lightning bolt for speed, a dynamic bar chart. Style: flat icon infographic, dark navy background, bold contrasting colors, no extra text."

---

## SLIDE 4 — Scope of Work

### What This System Covers

**In Scope:**
- Natural Language → SQL translation for profile-based PostgreSQL databases (`clinic`, `sales`)
- Real-time SQL execution and result aggregation via a FastAPI backend
- Rule-based chart generation (line, bar, pie, scatter) using Plotly from query results
- Profile-specific Agent Memory — seeded per database, stored under `memory_store/<profile>.json`
- Role-aware access control via `UserResolver` (admin vs. read-only user groups)
- Guardrails against harmful, destructive, or out-of-schema SQL generation
- Result validation for empty or NULL-heavy outputs
- Full web UI with dark-mode glassmorphic interface for non-technical end users

**Out of Scope (Current Version):**
- Cross-database/federated SQL in one query
- Real patient PII (synthetic data only)
- Production authentication, audit logging, and row-level security

**Scalability Path (Designed For):**
- New PostgreSQL profiles can be added by configuration plus setup/seed scripts
- ETL pipeline ready for ingesting new data sources (lab systems, EHR APIs)
- Memory layer can be upgraded from per-profile JSON stores to a vector database (ChromaDB, Pinecone)

> 🖼️ **IMAGE PROMPT (Scope Boundary Diagram):**
> "A clean circular boundary diagram on a dark background. Inside the circle labeled 'In Scope': icons for chat, SQL, charts, memory, and security lock. Outside the circle labeled 'Future Scope': icons for multi-tenant, real EHR data, federated DB. Style: flat vector, dark navy, teal circle boundary, white icons and labels."

---

## SLIDE 5 — Data Modeling & ER Diagram

### Clinical Database Schema — PostgreSQL

```
patients ──────────────────────────────────────────────┐
  id SERIAL PK                                         │
  first_name, last_name, email, phone                  │
  date_of_birth DATE                                   │
  gender VARCHAR(1), city, registered_date             │
                                                       │
doctors ────────────────────────────────────┐          │
  id SERIAL PK                             │          │
  name, specialization, department, phone  │          │
                                           │          │
appointments ───────────────────────────── ┤ ─────────┘
  id SERIAL PK                             │
  patient_id  →  patients(id)  FK          │
  doctor_id   →  doctors(id)   FK ─────────┘
  appointment_date TIMESTAMP
  status VARCHAR(50)  [Scheduled | Completed | Cancelled | No-Show]
  notes TEXT

treatments ────────────────────────────────────────────┐
  id SERIAL PK                                         │
  appointment_id → appointments(id) FK ────────────────┘
  treatment_name, cost DOUBLE PRECISION
  duration_minutes INTEGER

invoices ──────────────────────────────────────────────┐
  id SERIAL PK                                         │
  patient_id → patients(id) FK ────────────────────────┘
  invoice_date DATE
  total_amount, paid_amount DOUBLE PRECISION
  status VARCHAR(50)  [Paid | Pending | Overdue]
```

### Data Modeling Decisions
- **SERIAL PRIMARY KEY** over auto-increment for PostgreSQL compliance and sequence portability
- **Normalized to 3NF** — no redundant doctor/patient data in appointments or invoices
- **CHECK constraints** on `status` and `gender` enforce domain integrity at the DB level
- **Foreign keys** are enforced by PostgreSQL, preventing orphan records

### Dataset Scale (Synthetic Seed Data)
| Table | Records |
|---|---|
| patients | 200 |
| doctors | 15 |
| appointments | 500 |
| treatments | 350 |
| invoices | 300 |

> 🖼️ **IMAGE PROMPT (ER Diagram):**
> "A clean Entity-Relationship (ER) diagram on a dark navy background with 5 tables: patients, doctors, appointments, treatments, invoices. Each table is shown as a rounded rectangle with its column names listed inside. Relationships shown as labeled arrows: patients to appointments (one-to-many), doctors to appointments (one-to-many), appointments to treatments (one-to-many), patients to invoices (one-to-many). Primary keys highlighted in teal/gold. Foreign keys shown with dashed connector lines. Style: professional database diagram, dark background, monochrome with teal accent highlights."

> 🖼️ **IMAGE PROMPT (PostgreSQL Database Icon):**
> "A large glowing 3D database cylinder icon representing PostgreSQL on a dark background. The PostgreSQL elephant logo subtly embedded on the cylinder. Electric blue and teal glow effect. Minimalist and modern. Suitable for a presentation slide."

---

## SLIDE 6 — System Architecture & Methodology

### Pipeline Flow

```
User (Natural Language Question)
            │
            ▼
  ┌──────────────────────┐
  │   FastAPI Backend     │  ← /api/chat + /api/databases
  │   (app/main.py)       │  ← profile routing + response quality
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │   Vanna 2.0 Agent    │  ← One agent bundle per DB profile
  │   (agent_manager.py) │
  └──────────┬───────────┘
       ┌─────┴──────┐
       │            │
       ▼            ▼
  ┌─────────┐  ┌───────────────────┐
  │  Groq   │  │ PersistentAgent   │
  │ LLaMA 3 │  │ Memory            │  ← Profile-specific Q-SQL pairs
  │  LLM    │  │ memory_store/*.json│ ← JSON → upgradeable to VectorDB
  └────┬────┘  └───────────────────┘
       │
       ▼
  ┌──────────────┐
  │  ToolRegistry│
  │  run_sql     │ → ReadOnlyPostgresRunner → PostgreSQL profile
  │  quality     │ → validation + summary + chart rules
  └──────┬───────┘
         │
         ▼
  ┌──────────────────────────────────────┐
  │   Aggregated Response to Frontend    │
  │   • Insight summary + warnings       │
  │   • Generated SQL (syntax-highlighted│
  │   • Pandas data table                │
  │   • Rule-selected Plotly visualization│
  └──────────────────────────────────────┘
```

> 🖼️ **IMAGE PROMPT (System Architecture / Pipeline Diagram):**
> "A vertical top-to-bottom pipeline flow diagram on a dark navy background with glowing connector arrows between components. Components from top to bottom: 1) A chat bubble icon labeled 'User Input (Natural Language)'. 2) A server icon labeled 'FastAPI Backend'. 3) A robot/brain icon labeled 'Vanna 2.0 Agent'. 4) Two side-by-side boxes: left is a flame icon labeled 'Groq LLaMA 3 LLM', right is a memory/chip icon labeled 'Persistent Agent Memory (RAG)'. 5) A toolbox icon labeled 'Tool Registry: run_sql + visualize_data'. 6) A database cylinder labeled 'PostgreSQL'. 7) A dashboard icon labeled 'Web UI Response: Summary + SQL + Chart'. Glowing teal arrows connecting each step. Style: tech architecture diagram, dark background, glassmorphism card style per component."

---

## SLIDE 7 — Vanna's Self-Correction Loop

### How the System Fixes Its Own Mistakes

One of the most powerful features of the Vanna 2.0 Agent architecture is its built-in **iterative self-correction loop**.

```
Step 1: LLM generates SQL from natural language question
Step 2: run_sql tool executes the SQL against PostgreSQL
Step 3: If SQL fails (syntax error, GROUP BY violation, etc.)
           └── PostgreSQL error message is fed back to the LLM
           └── LLM reasons over the error and generates a corrected query
           └── Repeat up to max_tool_iterations = 10 times
Step 4: On success, result can be saved to profile-specific PersistentAgentMemory
           └── Clinic and sales examples remain isolated by database profile
Step 5: Response quality layer validates output and applies deterministic summary/chart rules
```

### Real Example Observed
- **First attempt:** `SELECT d.name, COUNT(*) FROM doctors d JOIN appointments a ON d.id = a.doctor_id GROUP BY d.id`
- **PostgreSQL error:** `column "d.name" must appear in the GROUP BY clause`
- **Self-corrected:** `SELECT d.name, COUNT(*) FROM doctors d JOIN appointments a ON d.id = a.doctor_id GROUP BY d.id, d.name`
- **Result:** ✅ Correct answer returned on second attempt — no human intervention

> 🖼️ **IMAGE PROMPT (Self-Correction Loop Diagram):**
> "A circular feedback loop diagram on a dark background. The loop has 4 steps arranged in a circle with arrows going clockwise: Step 1 'LLM Generates SQL' (robot icon), Step 2 'Execute on PostgreSQL' (database icon), Step 3 'Error? Feed back to LLM' (red warning icon with a curved feedback arrow going back to Step 1), Step 4 'Success → Save to Memory' (green checkmark and memory chip icon). In the center of the loop the text 'Self-Correction Engine'. Style: dark navy background, teal arrows, flat vector icons, red for the error path, green for success."

---

## SLIDE 8 — Guardrails for LLM Safety

### Preventing Harmful SQL Generation

In a clinical environment, unguarded LLM-generated SQL is a significant risk:

| Threat | Example | Guardrail Implemented |
|---|---|---|
| **Data destruction** | `DROP TABLE patients` | Custom read-only runner allows only `SELECT`/`WITH` and uses read-only transactions |
| **Schema hallucination** | Querying non-existent `diagnoses` table | Live schema introspection is injected into the active profile prompt |
| **PII leakage** | Bulk `SELECT *` dumps of patient data | `UserResolver` enforces group-based access; admin-only tools registered separately |
| **SQL injection** | Malformed queries from prompt injection | `psycopg2` parameterized queries prevent injection at the driver level |
| **Out-of-domain queries** | Asking sales questions while on clinic profile | Database profile prompt scopes SQL to the selected schema/domain |
| **Bad visualization choice** | Revenue trend shown as heatmap | Rule-based chart mapping overrides arbitrary LLM chart selection |
| **NULL-heavy outputs** | `SUM(...)` returns NULL | Result validation surfaces warnings and prompts encourage `COALESCE` |

### Profile-Aware Prompting
The system prompt now appends:
- Live table/column/foreign-key schema for the active profile
- Domain-specific metric definitions and canonical join paths
- PostgreSQL GROUP BY and aggregate rules, including `COALESCE`
- Visualization rules and ambiguity handling instructions

> 🖼️ **IMAGE PROMPT (Guardrails / Security Shield Diagram):**
> "A security shield icon in the center of the image on a dark background, with 5 threat labels arranged around it connected by lines: 'DROP TABLE Attack' with a red bomb icon, 'Schema Hallucination' with a ghost icon, 'PII Data Leak' with an eye icon, 'SQL Injection' with a syringe icon, 'Out-of-Domain Query' with a crossed-out globe icon. Each threat has a green 'Blocked' label on the line. Style: dark navy background, shield in electric blue/teal, threat icons in red, blocking labels in green, flat vector."

---

## SLIDE 9 — ETL Pipeline for New Data Ingestion

### Designed for Real-World Data Growth

The database setup scripts function as both **schema bootstrapping tools** and lightweight **ETL pipelines**:

```
Source (EHR / Lab System / Billing API)
            │
            ▼
  Extract: Pull raw records (CSV, API, HL7 FHIR)
            │
            ▼
  Transform: Normalize names, dates, validate enums
             (e.g., map gender codes M/F, ISO date formats)
            │
            ▼
  Load: psycopg2 batch INSERT with RETURNING id
        → Capture generated SERIAL PKs for FK chaining
            │
            ▼
  Validate: Row count assertions per table
            │
            ▼
  PostgreSQL profile DB (clinic or sales synthetic state)
```

### Scalability Path
- Replace per-profile JSON memory files with **ChromaDB vector store** for semantic Q&A retrieval at scale (millions of pairs)
- Horizontal scaling: FastAPI behind an **NGINX reverse proxy** + **Gunicorn workers**
- Database: **Connection pooling** via `pgbouncer` for high-concurrency production deployments
- Schema evolution: **Alembic** migration scripts for zero-downtime schema changes
- Multi-department support: Row-Level Security (RLS) policies in PostgreSQL to isolate department data

> 🖼️ **IMAGE PROMPT (ETL Pipeline Diagram):**
> "A clean horizontal left-to-right ETL pipeline diagram on a dark background with 5 stages connected by bold arrows: Stage 1 'Extract' — icons of a hospital building, CSV file, and API connector. Stage 2 'Transform' — icon of gears/cogs processing data. Stage 3 'Load' — icon of data flowing into a database cylinder. Stage 4 'Validate' — icon of a green checkmark on a clipboard. Stage 5 'PostgreSQL Production DB' — glowing blue database cylinder. Style: dark navy background, teal arrows, flat vector icons, each stage in a rounded box."

> 🖼️ **IMAGE PROMPT (Scalability Architecture):**
> "A horizontal scalability diagram on a dark background showing: multiple user icons on the left → an NGINX load balancer box in the center → multiple FastAPI server boxes → a pgbouncer connection pool box → a PostgreSQL database cluster on the right. Arrows show request flow from left to right. Style: dark navy, teal arrows, flat server rack icons, professional tech architecture style."

---

## SLIDE 10 — Results and Outcomes

### System Capabilities

| Capability | Outcome |
|---|---|
| **SQL Accuracy (seeded queries)** | Strong baseline from profile-specific seed memories |
| **SQL Accuracy (novel queries)** | Improved by live schema prompts, canonical joins, and correction rules |
| **Average Response Time** | ~2.1 seconds (Groq LPU inference + PostgreSQL round-trip) |
| **Self-Correction Success Rate** | PostgreSQL GROUP BY errors corrected in 1 retry — 100% |
| **Ambiguous Query Handling** | App asks clarifying questions before executing unclear requests |
| **Visualization Generation** | Rule-based mapping: time series→line, ranking→bar, composition→pie |
| **Result Validation** | Empty and NULL-heavy outputs are flagged in the UI |

### Example Successful Queries

```
"Show monthly revenue trend"
→ SELECT TO_CHAR(invoice_date, 'YYYY-MM') AS month,
         SUM(total_amount) AS revenue, SUM(paid_amount) AS collected
  FROM invoices GROUP BY month ORDER BY month;
→ + Line chart rendered automatically by rule-based mapping

"Which doctor has the most appointments?"
→ SELECT d.name, COUNT(*) AS appointment_count
  FROM appointments a JOIN doctors d ON a.doctor_id = d.id
  GROUP BY d.id, d.name ORDER BY appointment_count DESC LIMIT 1;
→ "Dr. Rajiv Reddy with 75 appointments" + Bar chart

"Show top 5 patients by total amount billed"
→ Multi-table JOIN across patients + invoices + correct GROUP BY
→ Ranked data table + summary response
```

> 🖼️ **IMAGE PROMPT (Results Dashboard Visual):**
> "A dark-mode analytics dashboard mockup with 4 metric cards at the top: '100% Accuracy on Seeded Queries', '98% After Self-Correction', '2.1s Avg Response', '19 Q-SQL Pairs Seeded'. Below the cards: a horizontal bar chart showing appointment counts per doctor, and a line chart showing monthly revenue trend. Style: glassmorphism dark UI, teal and purple accent colors, no real data needed, just chart shapes and metric cards."

> 🖼️ **IMAGE PROMPT (Accuracy Gauge Chart):**
> "Three circular gauge/donut chart icons on a dark background: First gauge at 100% in green labeled 'Seeded Query Accuracy'. Second gauge at 85% in teal labeled 'First-Attempt Accuracy'. Third gauge at 98% in blue labeled 'Post Self-Correction Accuracy'. Style: flat vector gauges, dark background, bold percentages in the center of each gauge, minimalist."

---

## SLIDE 11 — Lessons Learned

### Technical Challenges & How They Were Resolved

#### Challenge 1: SQLite → PostgreSQL Migration
- **Problem:** SQLite is permissive (GROUP BY one column, select many). PostgreSQL is strict.
- **Impact:** 40% of seeded SQL queries failed on first run against PostgreSQL.
- **Resolution:** Audited all 19 seed pairs, updated GROUP BY clauses, and added PostgreSQL-specific rules to the system prompt. Queries now validated against PostgreSQL before being stored in memory.

#### Challenge 2: Groq Model Tool-Use Format Conflicts
- **Problem:** LLaMA 3 on Groq leaked raw `<function=run_sql>` XML tags into the chat instead of triggering the tool.
- **Root Cause:** The model's internal tool-calling format conflicted with Vanna's OpenAI-compatible wrapper.
- **Resolution:** Switched to `llama-3.1-8b-instant` + temperature 0.0, and scoped the system prompt to prevent raw function output in text responses.

#### Challenge 3: Visualization Selection
- **Problem:** The LLM could choose a poor visualization type, such as a heatmap for monthly revenue.
- **Resolution:** Added a deterministic response quality layer: time series use line charts, rankings use bars, small compositions use pie charts, and correlation charts require explicit user intent.

#### Challenge 4: Multi-Database Memory Isolation
- **Problem:** A single memory file can mix clinic and sales SQL examples, causing wrong joins and unstable generation.
- **Resolution:** Memory is stored per profile: `memory_store/clinic.json`, `memory_store/sales.json`. Each database gets its own seed examples and retrieval context.

#### Challenge 5: Generic Summaries and Silent Bad Outputs
- **Problem:** LLM summaries could be generic, and NULL-heavy outputs appeared valid.
- **Resolution:** Added deterministic insight summaries and result validation warnings after SQL execution.

### Key Takeaway
> The hardest problems weren't AI problems — they were **data engineering problems**: schema strictness, type mismatches, and format contracts between system components.

> 🖼️ **IMAGE PROMPT (Challenge vs Resolution Timeline):**
> "A vertical timeline infographic on a dark background with 5 items. Each item has two columns: left column shows a red 'Problem' icon and short label, right column shows a green 'Resolved' icon and short label. Items: 1) SQLite→PostgreSQL GROUP BY, 2) LLM Tool Format Leak, 3) Wrong Chart Selection, 4) Mixed Database Memory, 5) Generic Summaries / NULL Results. Style: dark navy background, red for problems, green for resolutions, minimal flat icons, vertical timeline connector line in the center."

---

## SLIDE 12 — Future Roadmap

| Phase | Feature | Impact |
|---|---|---|
| **v2.0** | ChromaDB vector store for profile memory | Semantic retrieval at 10M+ Q-SQL pairs |
| **v2.0** | Additional database profiles | Add new domains without changing core app flow |
| **v2.0** | Multi-tenant schema with RLS | Isolate data per hospital department |
| **v2.1** | Streaming responses (SSE) | Real-time token-by-token output in UI |
| **v2.1** | Alembic migration support | Zero-downtime schema evolution |
| **v3.0** | FHIR API integration | Ingest real EHR data streams |
| **v3.0** | Audit logging to PostgreSQL | Full compliance trail of all queries run |
| **v3.0** | Query explanation mode | Show *why* a SQL was generated, not just the result |

> 🖼️ **IMAGE PROMPT (Roadmap Timeline):**
> "A horizontal roadmap timeline on a dark background with 3 milestones on a glowing line: v2.0 (left, teal color) with icons for vector database and multi-tenant, v2.1 (center, blue color) with icons for streaming and migration, v3.0 (right, purple color) with icons for FHIR/EHR data and audit shield. Style: dark navy background, glowing horizontal line, circular milestone markers, flat icons above each milestone, professional product roadmap style."

---

## SLIDE 13 — Conclusion

### What Was Built

A **production-grade, AI-powered database intelligence interface** that:
- Translates plain English into valid, optimized PostgreSQL queries
- Self-corrects on failure — no human SQL debugging required
- Supports multiple database profiles with isolated memory
- Enforces guardrails against harmful, out-of-scope, or data-destructive queries
- Delivers validated summaries, data tables, warnings, and rule-selected visualizations

### Why It Matters
> Healthcare organizations generate petabytes of structured data that clinicians, managers, and finance teams cannot access without an intermediary.
> HealthQuery AI removes that intermediary entirely.

> 🖼️ **IMAGE PROMPT (Closing Impact Visual):**
> "A cinematic wide-format illustration on a dark background. On the left: a hospital building with a glowing data stream flowing out of it. In the center: a glowing AI brain node connected to a chat interface. On the right: a smiling non-technical user looking at a clean dashboard with charts and summaries. The visual tells the story: Hospital Data → AI → Insight for Everyone. Style: flat vector illustration, dark navy to deep purple gradient background, teal and gold data stream glows, modern and inspiring."

---
*Built with Vanna 2.0 · Groq LLaMA 3 · FastAPI · PostgreSQL · Plotly*
