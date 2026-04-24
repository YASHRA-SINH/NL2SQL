"""
seed_memory.py
Pre-seeds the Vanna 2.0 PersistentAgentMemory with 15+ known-good
question-SQL pairs so the agent has a head start when answering
clinic-related queries.

Usage:
    python seed_memory.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

# Re-use the shared agent_memory instance from vanna_setup
from vanna_setup import agent_memory
from vanna.core.tool import ToolContext
from vanna.core.user import User

# ---------------------------------------------------------------------------
# Seed pairs: (question, sql)
# ---------------------------------------------------------------------------
SEED_PAIRS: list[tuple[str, str]] = [
    # ── Patient queries ────────────────────────────────────────────────────
    (
        "How many patients do we have?",
        "SELECT COUNT(*) AS total_patients FROM patients",
    ),
    (
        "List all patients from Mumbai",
        "SELECT first_name, last_name, email, phone FROM patients WHERE city = 'Mumbai'",
    ),
    (
        "How many male and female patients are there?",
        "SELECT gender, COUNT(*) AS count FROM patients GROUP BY gender",
    ),
    (
        "Which city has the most patients?",
        "SELECT city, COUNT(*) AS patient_count FROM patients GROUP BY city ORDER BY patient_count DESC LIMIT 1",
    ),
    (
        "Show patient count by city",
        "SELECT city, COUNT(*) AS patient_count FROM patients GROUP BY city ORDER BY patient_count DESC",
    ),

    # ── Doctor queries ─────────────────────────────────────────────────────
    (
        "Show me all doctors and their specializations",
        "SELECT name, specialization, department FROM doctors ORDER BY specialization",
    ),
    (
        "Which doctor has the most appointments?",
        "SELECT d.name, COUNT(*) AS appointment_count "
        "FROM appointments a JOIN doctors d ON a.doctor_id = d.id "
        "GROUP BY d.id ORDER BY appointment_count DESC LIMIT 1",
    ),
    (
        "How many appointments does each doctor have?",
        "SELECT d.name, d.specialization, COUNT(*) AS appointment_count "
        "FROM appointments a JOIN doctors d ON a.doctor_id = d.id "
        "GROUP BY d.id ORDER BY appointment_count DESC",
    ),

    # ── Appointment queries ────────────────────────────────────────────────
    (
        "How many appointments are there by status?",
        "SELECT status, COUNT(*) AS count FROM appointments GROUP BY status ORDER BY count DESC",
    ),
    (
        "Show monthly appointment count for the last 12 months",
        "SELECT strftime('%Y-%m', appointment_date) AS month, COUNT(*) AS count "
        "FROM appointments GROUP BY month ORDER BY month",
    ),
    (
        "Which patients have the most appointments?",
        "SELECT p.first_name || ' ' || p.last_name AS patient_name, COUNT(*) AS visit_count "
        "FROM appointments a JOIN patients p ON a.patient_id = p.id "
        "GROUP BY a.patient_id ORDER BY visit_count DESC LIMIT 10",
    ),

    # ── Financial queries ──────────────────────────────────────────────────
    (
        "What is the total revenue?",
        "SELECT SUM(total_amount) AS total_revenue FROM invoices",
    ),
    (
        "Show revenue by doctor",
        "SELECT d.name, SUM(i.total_amount) AS total_revenue "
        "FROM invoices i "
        "JOIN appointments a ON a.patient_id = i.patient_id "
        "JOIN doctors d ON d.id = a.doctor_id "
        "GROUP BY d.name ORDER BY total_revenue DESC",
    ),
    (
        "How many invoices are unpaid or overdue?",
        "SELECT status, COUNT(*) AS count, SUM(total_amount - paid_amount) AS outstanding "
        "FROM invoices WHERE status IN ('Pending', 'Overdue') GROUP BY status",
    ),
    (
        "What is the average treatment cost?",
        "SELECT ROUND(AVG(cost), 2) AS avg_cost FROM treatments",
    ),

    # ── Time-based queries ─────────────────────────────────────────────────
    (
        "Show appointments from the last 3 months",
        "SELECT a.id, p.first_name || ' ' || p.last_name AS patient, "
        "d.name AS doctor, a.appointment_date, a.status "
        "FROM appointments a "
        "JOIN patients p ON a.patient_id = p.id "
        "JOIN doctors d ON a.doctor_id = d.id "
        "WHERE a.appointment_date >= date('now', '-3 months') "
        "ORDER BY a.appointment_date DESC",
    ),
    (
        "Show monthly revenue trend",
        "SELECT strftime('%Y-%m', invoice_date) AS month, "
        "SUM(total_amount) AS revenue, SUM(paid_amount) AS collected "
        "FROM invoices GROUP BY month ORDER BY month",
    ),
    (
        "What are the most common treatments?",
        "SELECT treatment_name, COUNT(*) AS count, ROUND(AVG(cost), 2) AS avg_cost "
        "FROM treatments GROUP BY treatment_name ORDER BY count DESC",
    ),
    (
        "Show top 5 patients by total amount billed",
        "SELECT p.first_name || ' ' || p.last_name AS patient, "
        "SUM(i.total_amount) AS total_billed "
        "FROM invoices i JOIN patients p ON i.patient_id = p.id "
        "GROUP BY i.patient_id ORDER BY total_billed DESC LIMIT 5",
    ),
]


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------
async def seed():
    """Save all seed pairs into PersistentAgentMemory."""
    # Create a dummy ToolContext for the save_tool_usage calls
    dummy_user = User(
        id="seed_admin",
        username="seed_admin",
        email="admin@clinic.local",
        group_memberships=["admin"],
    )
    ctx = ToolContext(
        user=dummy_user,
        conversation_id="seed-session",
        request_id="seed-request",
        agent_memory=agent_memory,
    )

    count = 0
    for question, sql in SEED_PAIRS:
        await agent_memory.save_tool_usage(
            question=question,
            tool_name="run_sql",
            args={"sql": sql},
            context=ctx,
            success=True,
        )
        count += 1

    print(f"[OK] Seeded {count} question-SQL pairs into PersistentAgentMemory.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(seed())
