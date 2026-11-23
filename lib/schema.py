"""
schema.py - the first three menu options: Drop, Create and Populate Tables.
"""
from __future__ import annotations

import os

import oracledb

from .db import DBError, execute, query, run_script, run_sql, translate

SQL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql")

# Child tables first, so a foreign key never blocks a drop (same order as Assignment 3).
TABLES_DROP_ORDER = ["Loan", "Book", "Member", "Staff", "Author", "Publisher"]
VIEWS = ["Overdue_Loans", "Staff_Loan_Summary", "ActiveLoans"]


def _drop(conn, kind: str, name: str) -> str:
    """Drop one object; 'does not exist' (ORA-00942) is not an error."""
    sql = f"DROP {kind} {name}" + (" CASCADE CONSTRAINTS PURGE" if kind == "TABLE" else "")
    try:
        with conn.cursor() as cur:
            run_sql(cur, sql)
        return f"  dropped {kind.lower()} {name}"
    except oracledb.DatabaseError as exc:
        err = exc.args[0]
        if getattr(err, "code", None) == 942:
            return f"  {kind.lower()} {name} was not there (skipped)"
        raise DBError(translate(exc)) from exc


def drop_tables(conn) -> list[str]:
    """
    Menu option 1.  Views are dropped first: dropping a table leaves the views
    that use it behind as INVALID objects, so they would otherwise pile up.
    """
    log = [_drop(conn, "VIEW", v) for v in VIEWS]
    log += [_drop(conn, "TABLE", t) for t in TABLES_DROP_ORDER]
    return log


def create_tables(conn) -> list[str]:
    """Menu option 2.  Runs create.sql (Assignment 3) then views.sql (Assignment 4)."""
    n_tables = run_script(conn, os.path.join(SQL_DIR, "create.sql"))
    n_views = run_script(conn, os.path.join(SQL_DIR, "views.sql"))
    return [f"  created {n_tables} tables", f"  created {n_views} views"]


def row_counts(conn) -> list[tuple[str, int]]:
    """Number of rows in every table (names come from our own fixed list)."""
    counts = []
    for table in reversed(TABLES_DROP_ORDER):
        _, rows = query(conn, f"SELECT COUNT(*) FROM {table}")
        counts.append((table, rows[0][0]))
    return counts


def populate_tables(conn) -> list[str]:
    """
    Menu option 3.  Loads sql/populate.sql.  Refuses to run on top of existing
    data (it would just fail on the duplicate primary keys half-way through).
    """
    _, rows = query(conn, "SELECT COUNT(*) FROM Publisher")      # ORA-00942 if no tables
    if rows[0][0] > 0:
        raise DBError("The tables already contain data. Use 'Drop Tables' then 'Create Tables' first.")
    n = run_script(conn, os.path.join(SQL_DIR, "populate.sql"))
    log = [f"  ran {n} INSERT statements"]
    log += [f"  {table:<10} {count:>3} rows" for table, count in row_counts(conn)]
    return log
