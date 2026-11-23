"""
db.py - connection, SQL helpers, friendly Oracle errors and table printing.

Everything that talks to Oracle goes through query() / execute() / run_script()
so that (a) user input is always passed as bind variables, never glued into the
SQL text, and (b) every ORA- error is turned into a message a user can act on.
"""
from __future__ import annotations

import getpass
import os
from datetime import date, datetime

import oracledb


class DBError(Exception):
    """An error whose message is safe to show directly to the user."""


# ORA- error number -> plain-English explanation (the cases this app can hit).
ORA_MESSAGES = {
    1:     "That value already exists (duplicate ID, email or ISBN).",
    942:   "A table or view does not exist yet. Choose 'Create Tables' first.",
    955:   "Tables already exist. Choose 'Drop Tables' first.",
    1400:  "A required field was left empty.",
    1722:  "A number was expected.",
    2290:  "A rule was broken (for example a return or due date earlier than the loan date).",
    2291:  "That ID does not exist in the related table (check the book, member, staff, author or publisher ID).",
    2292:  "This record cannot be deleted because other records (for example loan history) depend on it.",
    12899: "A value was too long for its column.",
}


def _code(exc: oracledb.DatabaseError):
    """Return the numeric ORA- code of a driver exception (or None)."""
    err = exc.args[0] if exc.args else None
    return getattr(err, "code", None)


def translate(exc: oracledb.DatabaseError) -> str:
    """Friendly message for an Oracle error, with the ORA code kept for debugging."""
    code = _code(exc)
    if code in ORA_MESSAGES:
        return f"{ORA_MESSAGES[code]} (ORA-{code:05d})"
    return str(exc).strip().splitlines()[0] if str(exc).strip() else "Unknown database error."


# --------------------------------------------------------------------------
# Connection
# --------------------------------------------------------------------------
def load_env(path: str = ".env") -> None:
    """Tiny .env reader (KEY=VALUE per line) so no extra package is needed."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def connect() -> oracledb.Connection:
    """
    Connect using DB_USER / DB_PASSWORD / DB_DSN (from .env or the environment).
    Anything missing is asked for interactively, so a password never has to be
    stored in a file.  DSN looks like  host:1521/service_name.
    """
    load_env()
    if os.environ.get("ORACLE_CLIENT_LIB"):
        # Only needed for very old servers; python-oracledb's default "thin" mode
        # needs no Oracle Client.
        oracledb.init_oracle_client(lib_dir=os.environ["ORACLE_CLIENT_LIB"])

    user = os.environ.get("DB_USER") or input("Oracle username: ").strip()
    password = os.environ.get("DB_PASSWORD") or getpass.getpass("Oracle password: ")
    dsn = os.environ.get("DB_DSN") or input("Oracle DSN (host:1521/service): ").strip()

    try:
        conn = oracledb.connect(user=user, password=password, dsn=dsn)
    except oracledb.DatabaseError as exc:
        raise DBError(f"Could not connect to Oracle: {translate(exc)}") from exc

    # Same date format the Assignment 4 report used, so dates print as 2026-11-22.
    with conn.cursor() as cur:
        cur.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD'")
    return conn


# --------------------------------------------------------------------------
# Running SQL
# --------------------------------------------------------------------------
def query(conn, sql: str, params: dict | None = None):
    """Run a SELECT. Returns (column_names, rows)."""
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            cols = [d[0] for d in cur.description]
            return cols, cur.fetchall()
    except oracledb.DatabaseError as exc:
        raise DBError(translate(exc)) from exc


def execute(conn, sql: str, params: dict | None = None) -> int:
    """Run INSERT / UPDATE / DELETE, commit, and return the number of rows changed."""
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            changed = cur.rowcount
        conn.commit()
        return changed
    except oracledb.DatabaseError as exc:
        conn.rollback()
        raise DBError(translate(exc)) from exc


def split_sql(text: str) -> list[str]:
    """
    Split a .sql file into single statements.
    The driver runs ONE statement at a time (and rejects the trailing ';'),
    so we split on ';' while ignoring semicolons inside quotes and dropping
    -- line comments and /* block */ comments.
    """
    statements, buf = [], []
    i, n, in_str = 0, len(text), False
    while i < n:
        ch = text[i]
        if in_str:
            buf.append(ch)
            if ch == "'":
                if i + 1 < n and text[i + 1] == "'":   # escaped quote ''
                    buf.append("'")
                    i += 1
                else:
                    in_str = False
        elif ch == "'":
            in_str = True
            buf.append(ch)
        elif text.startswith("--", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        elif ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def run_script(conn, path: str) -> int:
    """Execute every statement of a .sql file in one transaction. Returns the count."""
    with open(path, encoding="utf-8") as fh:
        statements = split_sql(fh.read())
    done = 0
    try:
        with conn.cursor() as cur:
            for stmt in statements:
                if stmt.upper() == "COMMIT":     # we commit ourselves at the end
                    continue
                try:
                    cur.execute(stmt)
                except oracledb.DatabaseError as exc:
                    snippet = " ".join(stmt.split())[:70]
                    raise DBError(f"{translate(exc)}\n    while running: {snippet}...") from exc
                done += 1
        conn.commit()
    except DBError:
        conn.rollback()
        raise
    return done


# --------------------------------------------------------------------------
# Printing
# --------------------------------------------------------------------------
def format_value(value) -> str:
    """Turn a database value into display text."""
    if value is None:
        return "-"
    if isinstance(value, datetime):
        if (value.hour, value.minute, value.second) == (0, 0, 0):
            return value.strftime("%Y-%m-%d")
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:.1f}"
    return str(value)


def print_table(cols, rows, max_width: int = 38) -> None:
    """Print rows as an aligned text table with readable headings."""
    headings = [c.replace("_", " ") for c in cols]
    cells = [[format_value(v) for v in row] for row in rows]
    widths = [
        min(max_width, max([len(h)] + [len(r[i]) for r in cells]))
        for i, h in enumerate(headings)
    ]

    def fit(text, w):
        return text if len(text) <= w else text[: w - 1] + "…"

    def line(values):
        return " | ".join(fit(v, w).ljust(w) for v, w in zip(values, widths))

    print(line(headings))
    print("-+-".join("-" * w for w in widths))
    for r in cells:
        print(line(r))
    print(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")
