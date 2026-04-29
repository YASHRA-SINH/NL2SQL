"""
Seed sales-specific NL2SQL examples into memory_store/sales.json.

Run from the project root:
    python databases/sales/seed_sales_memory.py
"""

import asyncio
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from app.agent_manager import agent_manager
from vanna.core.tool import ToolContext
from vanna.core.user import User


SEED_PAIRS = [
    (
        "What is total revenue by month?",
        "SELECT TO_CHAR(o.order_date, 'YYYY-MM') AS month, "
        "SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS revenue "
        "FROM orders o JOIN order_items oi ON oi.order_id = o.id "
        "WHERE o.status IN ('completed', 'processing') "
        "GROUP BY month ORDER BY month",
    ),
    (
        "Show top 10 customers by lifetime revenue",
        "SELECT first_name || ' ' || last_name AS customer, city, region, lifetime_value "
        "FROM customers ORDER BY lifetime_value DESC LIMIT 10",
    ),
    (
        "Which product categories sell the most?",
        "SELECT p.category, SUM(oi.quantity) AS units_sold, "
        "SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS revenue "
        "FROM order_items oi JOIN products p ON p.id = oi.product_id "
        "JOIN orders o ON o.id = oi.order_id "
        "WHERE o.status IN ('completed', 'processing') "
        "GROUP BY p.category ORDER BY revenue DESC",
    ),
    (
        "What is the average order value by sales channel?",
        "SELECT o.channel, AVG(order_totals.order_value) AS average_order_value "
        "FROM orders o JOIN ("
        "  SELECT order_id, SUM(quantity * unit_price * (1 - discount_pct)) AS order_value "
        "  FROM order_items GROUP BY order_id"
        ") order_totals ON order_totals.order_id = o.id "
        "GROUP BY o.channel ORDER BY average_order_value DESC",
    ),
    (
        "Which sales reps closed the most revenue?",
        "SELECT sr.name, sr.region, SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS revenue "
        "FROM sales_reps sr JOIN orders o ON o.sales_rep_id = sr.id "
        "JOIN order_items oi ON oi.order_id = o.id "
        "WHERE o.status IN ('completed', 'processing') "
        "GROUP BY sr.id, sr.name, sr.region ORDER BY revenue DESC",
    ),
    (
        "Show payment status counts",
        "SELECT status, COUNT(*) AS payment_count, SUM(amount) AS total_amount "
        "FROM payments GROUP BY status ORDER BY payment_count DESC",
    ),
    (
        "Which regions generate the most revenue?",
        "SELECT o.shipping_region, SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS revenue "
        "FROM orders o JOIN order_items oi ON oi.order_id = o.id "
        "WHERE o.status IN ('completed', 'processing') "
        "GROUP BY o.shipping_region ORDER BY revenue DESC",
    ),
    (
        "Show support tickets by priority",
        "SELECT priority, COUNT(*) AS ticket_count "
        "FROM support_tickets GROUP BY priority ORDER BY ticket_count DESC",
    ),
]


async def seed():
    bundle = agent_manager.get_bundle("sales")
    ctx = ToolContext(
        user=User(id="sales_seed_admin", username="sales_seed_admin", group_memberships=["admin"]),
        conversation_id="sales-seed-session",
        request_id="sales-seed-request",
        agent_memory=bundle.memory,
    )
    for question, sql in SEED_PAIRS:
        await bundle.memory.save_tool_usage(
            question=question,
            tool_name="run_sql",
            args={"sql": sql},
            context=ctx,
            success=True,
        )
    print(f"[OK] Seeded {len(SEED_PAIRS)} sales examples into {bundle.profile.memory_path}.")


if __name__ == "__main__":
    asyncio.run(seed())
