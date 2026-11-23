"""
records.py - the write side of the application: add, edit, delete and the
three circulation actions (check out, return, renew).

Table and column names are NEVER taken from user input: they come from the
TABLES dictionary below, and every value is passed as a bind variable.
The same dictionary is meant to drive the web forms later (Assignment 9 bonus).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .db import DBError, execute, query

LOAN_DAYS = 14     # standard loan period for a check-out
RENEW_DAYS = 7     # extra days added by a renewal


@dataclass(frozen=True)
class Col:
    name: str
    kind: str = "str"            # "str" | "int" | "date"
    required: bool = False       # NOT NULL in the schema
    default_today: bool = False  # blank input on ADD means "today"


@dataclass(frozen=True)
class TableDef:
    pk: str
    cols: tuple                  # every column except the primary key


TABLES: dict[str, TableDef] = {
    "Publisher": TableDef("PublisherID", (
        Col("Name", required=True), Col("Address"), Col("Phone"), Col("Email"))),
    "Author": TableDef("AuthorID", (
        Col("FirstName", required=True), Col("LastName", required=True))),
    "Member": TableDef("MemberID", (
        Col("FirstName", required=True), Col("LastName", required=True),
        Col("Email", required=True), Col("Phone"),
        Col("MembershipDate", "date", required=True, default_today=True))),
    "Staff": TableDef("StaffID", (
        Col("FirstName", required=True), Col("LastName", required=True),
        Col("Position", required=True), Col("Email", required=True))),
    "Book": TableDef("BookID", (
        Col("Title", required=True), Col("ISBN", required=True), Col("Genre", required=True),
        Col("AuthorID", "int", required=True), Col("PublisherID", "int", required=True))),
    "Loan": TableDef("LoanID", (
        Col("BookID", "int", required=True), Col("MemberID", "int", required=True),
        Col("StaffID", "int", required=True),
        Col("LoanDate", "date", required=True, default_today=True),
        Col("DueDate", "date", required=True), Col("ReturnDate", "date"))),
}


# --------------------------------------------------------------------------
# Input conversion
# --------------------------------------------------------------------------
def parse(col: Col, text: str | None, *, adding: bool):
    """Convert what the user typed into a Python value for the bind variable."""
    text = (text or "").strip()
    if text == "":
        if adding and col.default_today:
            return date.today()
        if col.required:
            raise DBError(f"{col.name} is required.")
        return None                      # optional column -> NULL
    if col.kind == "int":
        try:
            return int(text)
        except ValueError:
            raise DBError(f"{col.name} must be a whole number.") from None
    if col.kind == "date":
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            raise DBError(f"{col.name} must be a date like 2026-11-30.") from None
    return text


def _table(name: str) -> TableDef:
    if name not in TABLES:
        raise DBError(f"Unknown table: {name}")
    return TABLES[name]


# --------------------------------------------------------------------------
# Generic read / add / edit / delete
# --------------------------------------------------------------------------
def browse(conn, table: str):
    """Every row of a table, ordered by primary key."""
    t = _table(table)
    return query(conn, f"SELECT * FROM {table} ORDER BY {t.pk}")


def find(conn, table: str, pk_value: int):
    """One row by primary key (empty result if it does not exist)."""
    t = _table(table)
    return query(conn, f"SELECT * FROM {table} WHERE {t.pk} = :id", {"id": pk_value})


def next_id(conn, table: str) -> int:
    """
    The schema (Assignment 3) has no sequences, so the next key is MAX + 1.
    Fine for a single-user demo; a multi-user system would use a sequence.
    """
    t = _table(table)
    _, rows = query(conn, f"SELECT NVL(MAX({t.pk}), 0) + 1 FROM {table}")
    return int(rows[0][0])


def add_record(conn, table: str, raw: dict) -> int:
    """INSERT one row built from {column name: typed text}. Returns the new ID."""
    t = _table(table)
    values = [parse(c, raw.get(c.name), adding=True) for c in t.cols]
    new_id = next_id(conn, table)
    names = [t.pk] + [c.name for c in t.cols]
    binds = {f"b{i}": v for i, v in enumerate([new_id] + values)}
    marks = ", ".join(f":b{i}" for i in range(len(names)))
    execute(conn, f"INSERT INTO {table} ({', '.join(names)}) VALUES ({marks})", binds)
    return new_id


def update_record(conn, table: str, pk_value: int, column: str, text: str) -> None:
    """UPDATE a single column of one row. An empty value clears optional columns (sets NULL)."""
    t = _table(table)
    col = next((c for c in t.cols if c.name.lower() == column.lower()), None)
    if col is None:
        raise DBError(f"{table} has no editable column called {column}.")
    value = parse(col, text, adding=False)
    changed = execute(conn, f"UPDATE {table} SET {col.name} = :v WHERE {t.pk} = :id",
                      {"v": value, "id": pk_value})
    if changed == 0:
        raise DBError(f"No {table} with ID {pk_value}.")


def delete_record(conn, table: str, pk_value: int) -> None:
    """
    DELETE one row.  The schema has no ON DELETE CASCADE, so Oracle refuses (ORA-02292)
    when other rows still point at it - e.g. a member with loan history.  db.translate()
    turns that into a readable message.  Deleting is only possible for 'leaf' rows.
    """
    t = _table(table)
    changed = execute(conn, f"DELETE FROM {table} WHERE {t.pk} = :id", {"id": pk_value})
    if changed == 0:
        raise DBError(f"No {table} with ID {pk_value}.")


# --------------------------------------------------------------------------
# Circulation (the everyday library actions from Assignment 1)
# --------------------------------------------------------------------------
def checkout_book(conn, book_id: int, member_id: int, staff_id: int) -> int:
    """
    Check a book out: INSERT a Loan due LOAN_DAYS from today.
    Business rule the schema cannot express: a book can only be out once, so we
    refuse if an unreturned loan already exists for it.  Unknown book / member /
    staff IDs are caught by the foreign keys (ORA-02291).
    """
    _, rows = query(conn, "SELECT COUNT(*) FROM Loan WHERE BookID = :b AND ReturnDate IS NULL",
                    {"b": book_id})
    if rows[0][0] > 0:
        raise DBError("That book is already on loan.")
    loan_id = next_id(conn, "Loan")
    execute(conn,
            """INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate)
               VALUES (:id, :b, :m, :s, TRUNC(SYSDATE), TRUNC(SYSDATE) + :days)""",
            {"id": loan_id, "b": book_id, "m": member_id, "s": staff_id, "days": LOAN_DAYS})
    return loan_id


def return_book(conn, loan_id: int) -> None:
    """Check a book in: set ReturnDate to today, but only if it is still out."""
    changed = execute(conn,
                      "UPDATE Loan SET ReturnDate = TRUNC(SYSDATE) "
                      "WHERE LoanID = :id AND ReturnDate IS NULL", {"id": loan_id})
    if changed == 0:
        raise DBError(f"Loan {loan_id} does not exist or was already returned.")


def renew_loan(conn, loan_id: int) -> None:
    """Renew: push the due date back RENEW_DAYS, only for loans that are still out."""
    changed = execute(conn,
                      "UPDATE Loan SET DueDate = DueDate + :days "
                      "WHERE LoanID = :id AND ReturnDate IS NULL",
                      {"days": RENEW_DAYS, "id": loan_id})
    if changed == 0:
        raise DBError(f"Loan {loan_id} does not exist or was already returned.")
