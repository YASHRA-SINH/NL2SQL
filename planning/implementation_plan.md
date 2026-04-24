# FastAPI Backend & Frontend Implementation Plan

Build the final piece of the NL2SQL chatbot: a FastAPI backend that orchestrates Vanna 2.0 and a premium web interface.

## User Review Required

> [!IMPORTANT]
> The application uses `DemoAgentMemory`, which is **in-memory**. All "learned" queries (except the pre-seeded ones) will be lost if the server restarts.

## Proposed Changes

### [Backend] FastAPI Application

#### [NEW] [main.py](file:///c:/NLP-SQL/main.py)
- Initialize FastAPI app.
- On startup: Seed `agent_memory` using `seed_memory.py`.
- Implement `POST /api/chat` endpoint:
    - Receive user question.
    - Call `agent.send_message`.
    - Process the stream of UI components (SQL, DataFrame, Chart, Summary).
    - Return a structured response.
- Implement SQL validation: Ensure only `SELECT` queries are executed.

### [Frontend] Modern Web Interface

#### [NEW] [index.html](file:///c:/NLP-SQL/index.html)
- A premium, dark-mode, glassmorphic UI.
- Chat interface with:
    - Message history.
    - Typing indicators.
    - Elegant rendering of SQL code blocks (syntax highlighted).
    - Responsive data tables.
    - Plotly charts integration.
- Sidebar with "Suggested Questions" (from our seed memory).

#### [NEW] [style.css](file:///c:/NLP-SQL/style.css)
- Custom CSS for the premium look and feel.
- Animations for message bubbles and data loading.

## Verification Plan

### Automated Tests
- `pytest` (if requested) to verify the `/api/chat` endpoint returns valid JSON.

### Manual Verification
1. Run `python main.py`.
2. Open `http://localhost:8000` in the browser.
3. Ask: "Show me the top 5 patients by total amount billed".
4. Verify:
    - SQL is displayed.
    - A table of patients appears.
    - A chart (bar/pie) is rendered.
    - A natural language summary is provided.
