from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any


AMBIGUOUS_SALES_TERMS = {
    "best",
    "most",
    "top",
    "highest",
    "largest",
    "sells",
    "sell",
    "selling",
    "sold",
}

REVENUE_TERMS = {"revenue", "sales amount", "amount", "value", "gmv"}
UNIT_TERMS = {"unit", "units", "quantity", "qty", "volume"}
ORDER_TERMS = {"order", "orders", "transactions"}


def clarification_for_question(database_id: str, question: str) -> str | None:
    """Return a clarification question when the user's intent is underspecified."""
    q = question.lower()
    words = set(re.findall(r"[a-z_]+", q))

    if database_id == "sales" and "category" in words and words & AMBIGUOUS_SALES_TERMS:
        has_metric = any(term in q for term in REVENUE_TERMS | UNIT_TERMS | ORDER_TERMS)
        if not has_metric:
            return (
                "For product categories, should I rank by revenue, units sold, or number of orders?"
            )

    if database_id == "sales" and {"customer", "customers"} & words and words & {"best", "top"}:
        has_metric = any(term in q for term in REVENUE_TERMS | ORDER_TERMS)
        if not has_metric:
            return "For customers, should I rank by lifetime revenue or order count?"

    return None


def validate_result_rows(rows: list[dict[str, Any]] | None) -> list[str]:
    if rows is None:
        return []
    if not rows:
        return ["The query returned no rows."]

    warnings: list[str] = []
    columns = list(rows[0].keys())
    for column in columns:
        values = [row.get(column) for row in rows]
        null_count = sum(value is None for value in values)
        if null_count == len(values):
            warnings.append(f"Column `{column}` is entirely NULL.")
        elif len(values) >= 5 and null_count / len(values) >= 0.5:
            warnings.append(f"Column `{column}` is mostly NULL ({null_count}/{len(values)} rows).")

    if len(rows) == 1:
        for column, value in rows[0].items():
            if value is None and _looks_like_metric(column):
                warnings.append(
                    f"Metric `{column}` is NULL. The SQL should usually use COALESCE around SUM/AVG expressions."
                )

    return warnings


def build_insight_summary(
    question: str,
    rows: list[dict[str, Any]] | None,
    warnings: list[str],
) -> str:
    if rows is None:
        return ""
    if not rows:
        return "No rows matched the question."

    columns = list(rows[0].keys())
    numeric_columns = [column for column in columns if _is_numeric(_first_non_null(rows, column))]
    text_columns = [column for column in columns if column not in numeric_columns]

    warning_text = f"Note: {' '.join(warnings)}\n" if warnings else ""

    if len(rows) == 1:
        metrics = [
            f"{_label(column)} is {_format_value(rows[0].get(column))}"
            for column in columns
        ]
        return warning_text + ". ".join(metrics) + "."

    if numeric_columns and text_columns:
        metric = _preferred_metric(numeric_columns, question)
        label_col = text_columns[0]
        ranked_rows = sorted(
            rows,
            key=lambda row: _safe_number(row.get(metric)),
            reverse=True,
        )
        top = ranked_rows[0]
        bottom = ranked_rows[-1]
        return (
            warning_text
            + f"{_format_value(top.get(label_col))} leads with {_format_value(top.get(metric))} "
            + f"{_label(metric)}. The lowest visible value is {_format_value(bottom.get(label_col))} "
            + f"with {_format_value(bottom.get(metric))}."
        )

    if numeric_columns:
        metric = _preferred_metric(numeric_columns, question)
        values = [_safe_number(row.get(metric)) for row in rows]
        total = sum(values)
        avg = total / len(values) if values else 0
        return (
            warning_text
            + f"Returned {len(rows)} rows. Total {_label(metric)} is {_format_value(total)} "
            + f"and average {_label(metric)} is {_format_value(avg)}."
        )

    return warning_text + f"Returned {len(rows)} rows for the requested lookup."


def build_rule_based_chart(
    question: str,
    rows: list[dict[str, Any]] | None,
    columns: list[str] | None = None,
) -> dict[str, Any] | None:
    if not rows or len(rows) < 2:
        return None

    available_columns = columns or list(rows[0].keys())
    numeric_columns = [
        column for column in available_columns if _is_numeric(_first_non_null(rows, column))
    ]
    if not numeric_columns:
        return None

    time_column = _find_time_column(rows, available_columns)
    metric = _preferred_metric(numeric_columns, question)
    q = question.lower()

    if time_column:
        return {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": [row.get(time_column) for row in rows],
                    "y": [row.get(metric) for row in rows],
                    "name": _label(metric),
                }
            ],
            "layout": {
                "title": _chart_title(question, "Trend"),
                "xaxis": {"title": _label(time_column)},
                "yaxis": {"title": _label(metric)},
            },
        }

    category_column = _find_category_column(rows, available_columns, numeric_columns)
    if category_column:
        chart_type = "bar"
        if "share" in q or "percentage" in q or "proportion" in q:
            chart_type = "pie" if len(rows) <= 8 else "bar"

        if chart_type == "pie":
            return {
                "data": [
                    {
                        "type": "pie",
                        "labels": [row.get(category_column) for row in rows],
                        "values": [row.get(metric) for row in rows],
                        "name": _label(metric),
                    }
                ],
                "layout": {"title": _chart_title(question, "Breakdown")},
            }

        ordered_rows = sorted(rows, key=lambda row: _safe_number(row.get(metric)), reverse=True)
        return {
            "data": [
                {
                    "type": "bar",
                    "x": [row.get(category_column) for row in ordered_rows],
                    "y": [row.get(metric) for row in ordered_rows],
                    "name": _label(metric),
                }
            ],
            "layout": {
                "title": _chart_title(question, "Ranking"),
                "xaxis": {"title": _label(category_column)},
                "yaxis": {"title": _label(metric)},
            },
        }

    if len(numeric_columns) >= 2 and ("correlation" in q or "relationship" in q):
        return {
            "data": [
                {
                    "type": "scatter",
                    "mode": "markers",
                    "x": [row.get(numeric_columns[0]) for row in rows],
                    "y": [row.get(numeric_columns[1]) for row in rows],
                    "name": "Relationship",
                }
            ],
            "layout": {
                "title": _chart_title(question, "Relationship"),
                "xaxis": {"title": _label(numeric_columns[0])},
                "yaxis": {"title": _label(numeric_columns[1])},
            },
        }

    return None


def _looks_like_metric(column: str) -> bool:
    return any(token in column.lower() for token in ["sum", "total", "revenue", "amount", "count", "avg", "average"])


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _safe_number(value: Any) -> float:
    if _is_numeric(value):
        return float(value)
    return 0.0


def _first_non_null(rows: list[dict[str, Any]], column: str) -> Any:
    for row in rows:
        value = row.get(column)
        if value is not None:
            return value
    return None


def _find_time_column(rows: list[dict[str, Any]], columns: list[str]) -> str | None:
    for column in columns:
        lower = column.lower()
        sample = _first_non_null(rows, column)
        if isinstance(sample, (date, datetime)):
            return column
        if any(token in lower for token in ["date", "month", "year", "week", "day", "period"]):
            return column
    return None


def _find_category_column(rows: list[dict[str, Any]], columns: list[str], numeric_columns: list[str]) -> str | None:
    for column in columns:
        if column in numeric_columns:
            continue
        values = [row.get(column) for row in rows]
        non_null = [value for value in values if value is not None]
        if non_null and len(set(non_null)) <= max(30, len(rows)):
            return column
    return None


def _preferred_metric(numeric_columns: list[str], question: str) -> str:
    q = question.lower()
    priority_groups = [
        ("revenue", ["revenue", "sales", "amount", "value", "total"]),
        ("quantity", ["quantity", "units", "count"]),
        ("average", ["avg", "average"]),
    ]
    for _name, tokens in priority_groups:
        if any(token in q for token in tokens):
            for column in numeric_columns:
                if any(token in column.lower() for token in tokens):
                    return column
    return numeric_columns[-1]


def _format_value(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _label(column: str) -> str:
    return column.replace("_", " ").title()


def _chart_title(question: str, fallback: str) -> str:
    cleaned = question.strip().rstrip("?")
    if not cleaned:
        return fallback
    return cleaned[0].upper() + cleaned[1:]
