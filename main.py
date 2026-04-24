import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import os

from vanna_setup import agent, agent_memory
from vanna.core.user import RequestContext
from vanna.components import (
    UiComponent,
    SimpleTextComponent,
    RichTextComponent,
    ChartComponent,
    DataFrameComponent,
    StatusCardComponent,
    NotificationComponent,
)

logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)

# ── Lifespan: Load Persistent Memory on Startup ──────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up... Loading persistent memory.")
    try:
        count = await agent_memory.load_from_disk()
        logger.info(f"Successfully loaded {count} memory records.")
        
        # Inject DDL into RAM so the LLM knows the exact table structures
        schema_ddl = """
        CREATE TABLE patients (
            id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT, phone TEXT,
            date_of_birth DATE, gender TEXT, city TEXT, registered_date DATE
        );
        CREATE TABLE doctors (
            id INTEGER PRIMARY KEY, name TEXT, specialization TEXT, department TEXT, phone TEXT
        );
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY, patient_id INTEGER, doctor_id INTEGER,
            appointment_date DATETIME, status TEXT, notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        );
        CREATE TABLE treatments (
            id INTEGER PRIMARY KEY, appointment_id INTEGER, treatment_name TEXT,
            cost REAL, duration_minutes INTEGER,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        );
        CREATE TABLE invoices (
            id INTEGER PRIMARY KEY, patient_id INTEGER, invoice_date DATE,
            total_amount REAL, paid_amount REAL, status TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        """
        from vanna.core.tool import ToolContext
        from vanna.core.user import User
        ctx = ToolContext(user=User(id="admin", username="admin", group_memberships=["admin"]), conversation_id="startup", request_id="startup-req", agent_memory=agent_memory)
        await agent_memory.save_text_memory(schema_ddl, ctx)
        logger.info("Database schema injected into RAM.")
        
    except Exception as e:
        logger.error(f"Failed to load memory: {e}")
    yield
    logger.info("Shutting down...")

app = FastAPI(title="Vanna NL2SQL Chatbot", lifespan=lifespan)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ───────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    summary: str = ""
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    chart: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    conversation_id: Optional[str] = None

# ── API Endpoints ────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Takes a natural language question and streams the Vanna Agent response.
    We aggregate the streamed UI components into a structured JSON response.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    req_context = RequestContext(metadata={"starter_ui_request": False})
    
    response_data = ChatResponse(conversation_id=request.conversation_id)
    summary_parts = []
    
    try:
        async for component in agent.send_message(
            request_context=req_context,
            message=request.message,
            conversation_id=request.conversation_id
        ):
            # Inspect the rich component type to map it to our JSON response
            if not component.rich_component:
                continue
                
            rich_comp = component.rich_component
            comp_type = rich_comp.type
            
            # 1. SQL Code
            if comp_type == "status_card":
                # Vanna often uses status cards for tool execution status
                # If it's a run_sql tool, we can extract the SQL from metadata
                if rich_comp.title == "Executing run_sql" and rich_comp.metadata:
                    response_data.sql = rich_comp.metadata.get("sql")
            
            # 2. DataFrame Results
            elif comp_type == "dataframe":
                response_data.data = rich_comp.rows
                cols = getattr(rich_comp, "columns", [])
                response_data.columns = [col.get("name") if isinstance(col, dict) else col for col in cols] if cols else []
                if not response_data.columns and rich_comp.rows:
                    response_data.columns = list(rich_comp.rows[0].keys())
                    
            # 3. Chart
            elif comp_type == "chart":
                if rich_comp.chart_type == "plotly":
                    response_data.chart = rich_comp.data
            
            # 4. Text / Summary
            elif comp_type == "rich_text":
                summary_parts.append(rich_comp.content)
                
            # Error Notifications
            elif comp_type == "notification" and getattr(rich_comp, "level", "") == "error":
                response_data.error = getattr(rich_comp, "message", "Unknown error")
                
            # Keep capturing simple text components just in case
            elif getattr(component, "simple_component", None):
                text = getattr(component.simple_component, "text", "")
                if text and "Executing" not in text and "Ready" not in text:
                    # Append it if it hasn't been added already
                    if text not in summary_parts:
                        summary_parts.append(text)

        response_data.summary = "\n".join(summary_parts).strip()
        
        # Fallback if no specific summary was generated
        if not response_data.summary and response_data.data is not None:
             response_data.summary = f"Query executed successfully. Returned {len(response_data.data)} rows."
             
        return response_data

    except Exception as e:
        logger.error(f"Error during chat processing: {e}", exc_info=True)
        return ChatResponse(error=str(e), summary="An internal error occurred.")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "db_path": agent_memory._demo.max_items} # just returning something from memory config to show it's alive

# ── Serve Static Files ───────────────────────────────────────────────────
# Mount the static directory to serve HTML, CSS, JS
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
