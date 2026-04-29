import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import os

from .agent_manager import agent_manager
from .database_profiles import get_profile, introspect_database, list_profiles
from .response_quality import (
    build_insight_summary,
    build_rule_based_chart,
    clarification_for_question,
    validate_result_rows,
)
from vanna.core.user import RequestContext

logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)

# ── Lifespan: Load Persistent Memory on Startup ──────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up... Loading persistent memory for database profiles.")
    try:
        counts = await agent_manager.load_all_memory()
        logger.info("Successfully loaded memory records: %s", counts)
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
    database_id: str = "clinic"

class ChatResponse(BaseModel):
    summary: str = ""
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    chart: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    conversation_id: Optional[str] = None
    database_id: Optional[str] = None


class DatabaseProfileResponse(BaseModel):
    id: str
    name: str
    description: str
    domain: str
    dialect: str
    database: str
    schema: str
    accent: str

# ── API Endpoints ────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Takes a natural language question and streams the Vanna Agent response.
    We aggregate the streamed UI components into a structured JSON response.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        bundle = agent_manager.get_bundle(request.database_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    clarification = clarification_for_question(bundle.profile.id, request.message)
    if clarification:
        return ChatResponse(
            summary=clarification,
            error="Question needs clarification",
            conversation_id=request.conversation_id,
            database_id=bundle.profile.id,
        )

    req_context = RequestContext(
        metadata={
            "starter_ui_request": False,
            "database_id": bundle.profile.id,
        }
    )
    
    response_data = ChatResponse(
        conversation_id=request.conversation_id,
        database_id=bundle.profile.id,
    )
    summary_parts = []
    
    try:
        async for component in bundle.agent.send_message(
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
        response_data.warnings = validate_result_rows(response_data.data)

        deterministic_summary = build_insight_summary(
            request.message,
            response_data.data,
            response_data.warnings,
        )
        if deterministic_summary:
            response_data.summary = deterministic_summary

        deterministic_chart = build_rule_based_chart(
            request.message,
            response_data.data,
            response_data.columns,
        )
        if deterministic_chart:
            response_data.chart = deterministic_chart
        
        # Fallback if no specific summary was generated
        if not response_data.summary and response_data.data is not None:
             response_data.summary = f"Query executed successfully. Returned {len(response_data.data)} rows."
             
        return response_data

    except Exception as e:
        logger.error(f"Error during chat processing: {e}", exc_info=True)
        return ChatResponse(error=str(e), summary="An internal error occurred.")


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "memory_records": agent_manager.memory_counts(),
    }


@app.get("/api/databases", response_model=List[DatabaseProfileResponse])
async def databases():
    return [
        DatabaseProfileResponse(
            id=profile.id,
            name=profile.name,
            description=profile.description,
            domain=profile.domain,
            dialect=profile.dialect,
            database=profile.database,
            schema=profile.schema,
            accent=profile.accent,
        )
        for profile in list_profiles()
    ]


@app.get("/api/databases/{database_id}")
async def database_metadata(database_id: str):
    try:
        return introspect_database(database_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Could not introspect database profile %s: %s", database_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not load database metadata: {exc}") from exc


@app.post("/api/databases/{database_id}/refresh")
async def refresh_database_metadata(database_id: str):
    try:
        get_profile(database_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    introspect_database.cache_clear()
    return introspect_database(database_id)

# ── Serve Frontend Assets ─────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
frontend_dist = os.path.join(PROJECT_ROOT, "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/")
    async def serve_placeholder():
        return {
            "error": "Frontend build not found. Run `npm run build` in the frontend directory and restart the server."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
