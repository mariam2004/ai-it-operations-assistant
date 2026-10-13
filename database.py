"""SQLite connection, schema reflection, and guarded read-only SQL execution."""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import sqlglot
from sqlglot import exp

from config import settings

logger = logging.getLogger(__name__)
ALLOWED_TABLES = {
    "facttickets", "dimcustomer", "dimdate", "dimissue", "dimstaff",
    "dimticketcontext", "dimticketflags", "dimticketstate",
}
BLOCKED_FUNCTIONS = {"LOAD_FILE", "SLEEP", "BENCHMARK", "GET_LOCK", "RELEASE_LOCK", "LOAD_EXTENSION", "READFILE", "WRITEFILE"}
BLOCKED_COLUMNS = {"customeremail", "customername", "customerage", "customergender"}


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create the SQLAlchemy engine once. No connection is opened until needed."""
    url = settings.database_url()
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"timeout": settings.db_connect_timeout},
    )


def connection_status() -> dict[str, Any]:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        schema = inspect_schema()
        return {
            "connected": True,
            "schema_ok": schema.get("ok", False),
            "tables_found": len(schema.get("tables", {})),
            "message": "SQLite reachable; schema inspection completed." if schema.get("ok") else "SQLite reachable, but schema inspection is incomplete.",
        }
    except Exception as exc:  # don't expose connection strings or secrets
        logger.warning("Database connectivity check failed: %s", type(exc).__name__)
        return {"connected": False, "schema_ok": False, "tables_found": 0,
                "message": safe_db_error(exc)}


def safe_db_error(exc: Exception) -> str:
    message = str(exc)
    # Keep application messages useful without echoing a URL/password.
    message = re.sub(r"sqlite:///[^\s]+", "[database path hidden]", message, flags=re.I)
    message = re.sub(r"password\s*=\s*[^\s,;]+", "password=[hidden]", message, flags=re.I)
    if isinstance(exc, ValueError):
        return message[:240]
    if isinstance(exc, SQLAlchemyError):
        return "Could not query SQLite. Check the database file and configured path."
    return "Database operation failed. Check the SQLite database file and schema."


def inspect_schema() -> dict[str, Any]:
    """Reflect table names, columns, PKs, FKs, and indexes from the live database."""
    try:
        inspector = inspect(get_engine())
        names = set(inspector.get_table_names())
        tables: dict[str, Any] = {}
        for table_name in sorted(names.intersection(ALLOWED_TABLES)):
            tables[table_name] = {
                "columns": [
                    {"name": c["name"], "type": str(c["type"]), "nullable": bool(c.get("nullable", True))}
                    for c in inspector.get_columns(table_name)
                ],
                "primary_key": inspector.get_pk_constraint(table_name).get("constrained_columns", []) or [],
                "foreign_keys": [
                    {"columns": fk.get("constrained_columns", []), "referred_table": fk.get("referred_table"),
                     "referred_columns": fk.get("referred_columns", [])}
                    for fk in inspector.get_foreign_keys(table_name)
                ],
                "indexes": [
                    {"name": idx.get("name"), "columns": idx.get("column_names", []), "unique": idx.get("unique", False)}
                    for idx in inspector.get_indexes(table_name)
                ],
            }
        missing = sorted(ALLOWED_TABLES - names)
        return {"ok": not missing, "database": settings.sqlite_database, "tables": tables,
                "missing_expected_tables": missing,
                "note": "Metadata reflects the live database. Expected relationships are not assumed when foreign keys are absent."}
    except Exception as exc:
        logger.warning("Schema inspection failed: %s", type(exc).__name__)
        return {"ok": False, "database": settings.sqlite_database, "tables": {},
                "missing_expected_tables": sorted(ALLOWED_TABLES), "error": safe_db_error(exc)}


@lru_cache(maxsize=1)
def get_reflected_columns() -> dict[str, set[str]]:
    schema = inspect_schema()
    return {table.lower(): {c["name"].lower() for c in meta["columns"]}
            for table, meta in schema.get("tables", {}).items()}


def has_columns(table: str, *columns: str) -> bool:
    available = get_reflected_columns().get(table.lower(), set())
    return all(col.lower() in available for col in columns)


def query_df(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Run an application-authored query. Common analytics use bound parameters."""
    with get_engine().connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params or {})


def _column_metadata() -> dict[str, set[str]]:
    return get_reflected_columns()


def validate_readonly_sql(sql: str, max_rows: int | None = None) -> str:
    """Parse and constrain LLM-generated SQL; return normalized safe SELECT SQL."""
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("SQL query is empty.")
    if len(sql) > 12000:
        raise ValueError("SQL query is too long.")

    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except Exception as exc:
        raise ValueError("SQL was rejected because it could not be parsed as SQLite.") from exc
    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        raise ValueError("Only one SQL statement is allowed.")

    tree = statements[0]
    if not isinstance(tree, exp.Select):
        raise ValueError("Only a single read-only SELECT query is allowed (set operations/CTEs are not supported).")
    disallowed_types = tuple(cls for cls in (getattr(exp, "Into", None), getattr(exp, "Command", None), getattr(exp, "Lock", None)) if cls is not None)
    if disallowed_types and any(tree.find(cls) is not None for cls in disallowed_types):
        raise ValueError("Query contains a disallowed SQL operation.")
    for projection in tree.expressions:
        if isinstance(projection, exp.Star) or (isinstance(projection, exp.Column) and projection.name == "*"):
            raise ValueError("Wildcard projections are not allowed. Select only the columns needed.")
    for node in tree.walk():
        if isinstance(node, exp.Func):
            candidates = {str(getattr(node, "sql_name", lambda: "")() or "").upper(), str(getattr(node, "name", "") or "").upper()}
            blocked = candidates.intersection(BLOCKED_FUNCTIONS)
            if blocked:
                raise ValueError(f"SQL function {sorted(blocked)[0]} is not allowed.")
        if isinstance(node, exp.Table):
            # Prevent cross-database references and external schemas.
            if node.db or node.catalog:
                raise ValueError("Cross-schema table references are not allowed.")
            if (node.name or "").lower() not in ALLOWED_TABLES:
                raise ValueError(f"Table '{node.name}' is not in the approved ticket schema.")

    # Validate explicit column references against reflected metadata. Aliases in
    # SELECT are allowed for GROUP BY / ORDER BY expressions.
    cols = _column_metadata()
    table_aliases: dict[str, str] = {}
    referenced_tables: set[str] = set()
    for table_node in tree.find_all(exp.Table):
        base = table_node.name.lower()
        referenced_tables.add(base)
        table_aliases[(table_node.alias or table_node.name).lower()] = base
    if not referenced_tables:
        raise ValueError("The query must read from an approved database table.")
    if not cols:
        raise ValueError("Cannot validate SQL columns until database schema reflection succeeds.")

    selected_aliases: set[str] = set()
    for projection in tree.expressions:
        if isinstance(projection, exp.Alias) and projection.alias:
            selected_aliases.add(projection.alias.lower())

    for column in tree.find_all(exp.Column):
        col_name = (column.name or "").lower()
        if col_name in {"", "*"}:
            continue
        if col_name in BLOCKED_COLUMNS:
            raise ValueError(f"Column '{column.name}' is not available to the assistant because it contains unnecessary personal information.")
        if column.table:
            table = table_aliases.get(column.table.lower())
            if not table or col_name not in cols.get(table, set()):
                if col_name not in selected_aliases:
                    raise ValueError(f"Column '{column.sql()}' could not be verified in the reflected schema.")
        else:
            present = any(col_name in cols.get(table, set()) for table in referenced_tables)
            if not present and col_name not in selected_aliases:
                raise ValueError(f"Column '{col_name}' could not be verified in the referenced tables.")

    limit = max_rows if max_rows is not None else settings.sql_max_rows
    limit = min(max(int(limit), 1), 1000)

    # Preserve a smaller literal LIMIT supplied by the query, while enforcing
    # the application's maximum result size.
    existing_limit = tree.args.get("limit")
    if existing_limit is not None:
        limit_expr = existing_limit.args.get("expression")
        if not isinstance(limit_expr, exp.Literal) or limit_expr.is_string:
            raise ValueError("A literal integer LIMIT is required for read-only SQL.")
        try:
            requested_limit = int(limit_expr.this)
        except (TypeError, ValueError) as exc:
            raise ValueError("The query LIMIT must be an integer.") from exc

        # Negative SQLite LIMIT values mean unlimited, so retain the safety cap.
        if requested_limit >= 0:
            limit = min(limit, requested_limit)

    # SQLGlot's AST edit avoids string concatenation around ORDER BY / UNION.
    try:
        tree = tree.limit(limit, copy=True)
    except Exception as exc:
        raise ValueError("Could not apply a safe result limit to this query.") from exc
    return tree.sql(dialect="sqlite")


def run_readonly_sql(sql: str) -> dict[str, Any]:
    try:
        safe_sql = validate_readonly_sql(sql)
        frame = query_df(safe_sql)
        # Restrict output size and types before sending to the model.
        frame = frame.head(settings.sql_max_rows).astype(object).where(pd.notna(frame), None)
        rows = frame.to_dict(orient="records")
        return {"ok": True, "row_count": len(rows), "columns": list(frame.columns), "rows": rows,
                "limited": len(rows) >= settings.sql_max_rows}
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    except Exception as exc:
        logger.warning("Read-only SQL execution failed: %s", type(exc).__name__)
        return {"ok": False, "error": safe_db_error(exc)}



@lru_cache(maxsize=64)
def verify_relationship(source_table: str, source_column: str, target_table: str, target_column: str) -> dict[str, Any]:
    """Check an expected key relationship using reflected columns and live data.

    A declared FK is recorded, but the check also measures non-null source keys
    that have no corresponding target key. No rows are changed.
    """
    source_table = source_table.lower()
    target_table = target_table.lower()
    cols = get_reflected_columns()
    if source_table not in ALLOWED_TABLES or target_table not in ALLOWED_TABLES:
        return {"verified": False, "reason": "Relationship references a table outside the approved schema."}
    if source_column.lower() not in cols.get(source_table, set()) or target_column.lower() not in cols.get(target_table, set()):
        return {"verified": False, "reason": "One or more relationship columns are missing."}
    try:
        schema = inspect_schema().get("tables", {})
        actual_source = next(t for t in schema if t.lower() == source_table)
        actual_target = next(t for t in schema if t.lower() == target_table)
        source_meta = schema[actual_source]
        target_meta = schema[actual_target]
        actual_source_col = next(c["name"] for c in source_meta["columns"] if c["name"].lower() == source_column.lower())
        actual_target_col = next(c["name"] for c in target_meta["columns"] if c["name"].lower() == target_column.lower())
        fk_declared = any(
            [c.lower() for c in fk.get("columns", [])] == [source_column.lower()]
            and (fk.get("referred_table") or "").lower() == target_table
            and [c.lower() for c in fk.get("referred_columns", [])] == [target_column.lower()]
            for fk in source_meta.get("foreign_keys", [])
        )
        # The table/column names above come only from the allowlist and reflection.
        sql = f"""SELECT COUNT(*) AS source_count,
            SUM(CASE WHEN t.`{actual_target_col}` IS NOT NULL THEN 1 ELSE 0 END) AS matched_count
            FROM `{actual_source}` s LEFT JOIN `{actual_target}` t
              ON s.`{actual_source_col}` = t.`{actual_target_col}`
            WHERE s.`{actual_source_col}` IS NOT NULL"""
        row = query_df(sql).iloc[0]
        source_count = int(row["source_count"] or 0)
        matched_count = int(row["matched_count"] or 0)
        unmatched = source_count - matched_count
        verified = source_count > 0 and unmatched == 0
        return {"verified": verified, "foreign_key_declared": fk_declared,
                "source_non_null_count": source_count, "matched_count": matched_count,
                "unmatched_count": unmatched,
                "reason": "All non-null observed source keys matched." if verified else "Relationship could not be fully verified against existing key values."}
    except Exception as exc:
        logger.warning("Relationship check failed for %s.%s -> %s.%s: %s", source_table, source_column, target_table, target_column, type(exc).__name__)
        return {"verified": False, "reason": "Relationship verification query failed."}

def distinct_values(table: str, column: str, limit: int = 100) -> dict[str, Any]:
    """Return bounded category values only after metadata validates names."""
    table, column = table.lower(), column
    cols = get_reflected_columns()
    if table not in ALLOWED_TABLES or column.lower() not in cols.get(table, set()):
        return {"ok": False, "error": "Requested table or column is not available."}
    quoted_table = f"`{table}`"
    # Use the reflected canonical column name to preserve identifier casing.
    canonical = next(c["name"] for t, meta in inspect_schema().get("tables", {}).items()
                    if t.lower() == table for c in meta["columns"] if c["name"].lower() == column.lower())
    sql = f"SELECT DISTINCT `{canonical}` AS value FROM {quoted_table} ORDER BY value LIMIT :limit"
    try:
        df = query_df(sql, {"limit": min(max(limit, 1), 100)})
        return {"ok": True, "values": df["value"].where(pd.notna(df["value"]), None).tolist()}
    except Exception as exc:
        return {"ok": False, "error": safe_db_error(exc)}
