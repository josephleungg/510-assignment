#!/usr/bin/env python3
"""
CPS510 Assignment 9: text menu for the Library DBMS.
Section 06, Team 04

Run with `python cli.py`. This file only handles menus and prompts;
the SQL is in lib/schema.py, lib/reports.py and lib/records.py.
"""
from __future__ import annotations

import sys

from lib import records, reports, schema
from lib.db import DBError, connect, print_table, query, set_show_sql, show_sql


class Cancel(Exception):
    """Raised when the user leaves a prompt blank to back out."""


# Input helpers
def ask(prompt: str, *, required: bool = True, default: str = "") -> str:
    """Prompt for text. A blank answer cancels when the value is required."""
    suffix = f" [{default}]" if default else ""
    text = input(f"  {prompt}{suffix}: ").strip()
    if not text:
        text = default
    if required and not text:
        raise Cancel()
    return text


def ask_int(prompt: str) -> int:
    """Prompt until a whole number is typed (blank cancels)."""
    while True:
        text = ask(prompt)
        try:
            return int(text)
        except ValueError:
            print("  Please enter a whole number.")


def ask_param(param: reports.Param, conn):
    """Ask for one report parameter, first showing the valid values if there is a hint."""
    if param.hint_sql:
        cols, rows = query(conn, param.hint_sql)
        print()
        print_table(cols, rows)
        print()
    return ask_int(param.prompt) if param.kind == "int" else ask(param.prompt)


def pause() -> None:
    input("\n  Press Enter to continue...")


def choose(options: list[str], title: str = "") -> str:
    """Show a numbered list and return the chosen number as text ('0' = back)."""
    if title:
        print(f"\n  {title}")
    for i, text in enumerate(options, 1):
        print(f"   {i}. {text}")
    return input("  > ").strip()


def choose_table(prompt: str = "Which table?") -> str:
    names = list(records.TABLES)
    pick = choose(names, prompt + " (blank to cancel)")
    if not pick.isdigit() or not (1 <= int(pick) <= len(names)):
        raise Cancel()
    return names[int(pick) - 1]


def show_row(conn, table: str, pk_value: int) -> None:
    cols, rows = records.find(conn, table, pk_value)
    print_table(cols, rows)


# Menu options 1-3: Drop / Create / Populate
def do_drop(conn) -> None:
    if input("  This deletes ALL tables and data. Type yes to continue: ").strip().lower() != "yes":
        raise Cancel()
    for line in schema.drop_tables(conn):
        print(line)
    print("  Done.")


def do_create(conn) -> None:
    for line in schema.create_tables(conn):
        print(line)
    print("  Done.")


def do_populate(conn) -> None:
    for line in schema.populate_tables(conn):
        print(line)
    print("  Done.")


# Menu option 4: Query Tables
def query_menu(conn) -> None:
    # Flatten the report groups into one numbered list.
    while True:
        print("\n  ===== QUERY TABLES =====")
        index = []
        n = 0
        for heading, group in reports.GROUPS:
            print(f"\n  {heading}")
            for rep in group:
                n += 1
                index.append(rep)
                print(f"   {n:>2}. {rep.title}")
        print(f"\n    s. Echo every SQL statement in the terminal: {'ON' if show_sql() else 'OFF'}")
        print("    0. Back")
        pick = input("  > ").strip().lower()
        if pick == "0" or pick == "":
            return
        if pick == "s":
            set_show_sql(not show_sql())
            continue
        if not pick.isdigit() or not (1 <= int(pick) <= len(index)):
            print("  Not a valid choice.")
            continue
        try:
            run_one_report(conn, index[int(pick) - 1])
        except Cancel:
            print("  Cancelled.")
        except DBError as err:
            print(f"  ! {err}")
            pause()


def run_one_report(conn, rep: reports.Report) -> None:
    values = {p.name: ask_param(p, conn) for p in rep.params}
    print(f"\n  --- {rep.title} ---")
    if rep.note:
        print(f"  ({rep.note})")
    cols, rows = reports.run_report(conn, rep, values)
    print_table(cols, rows)
    pause()


# Menu option 5: Add / Edit / Delete records and circulation
def records_menu(conn) -> None:
    actions = {
        "1": ("Check out a book", do_checkout),
        "2": ("Return a book", do_return),
        "3": ("Renew a loan", do_renew),
        "4": ("Add a record to any table", do_add),
        "5": ("Edit a record", do_edit),
        "6": ("Delete a record", do_delete),
        "7": ("Browse a whole table", do_browse),
    }
    while True:
        pick = choose([a[0] for a in actions.values()] + ["Back"], "===== ADD / EDIT / DELETE RECORDS =====")
        if pick in ("0", "8", ""):
            return
        if pick not in actions:
            print("  Not a valid choice.")
            continue
        try:
            actions[pick][1](conn)
        except Cancel:
            print("  Cancelled.")
        except DBError as err:
            print(f"  ! {err}")
        pause()


def do_checkout(conn) -> None:
    book = ask_int("Book ID")
    member = ask_int("Member ID")
    staff = ask_int("Staff ID (who is processing)")
    loan_id = records.checkout_book(conn, book, member, staff)
    print(f"  Checked out. New loan {loan_id}:")
    show_row(conn, "Loan", loan_id)


def do_return(conn) -> None:
    loan_id = ask_int("Loan ID")
    records.return_book(conn, loan_id)
    print("  Returned:")
    show_row(conn, "Loan", loan_id)


def do_renew(conn) -> None:
    loan_id = ask_int("Loan ID")
    records.renew_loan(conn, loan_id)
    print(f"  Renewed (+{records.RENEW_DAYS} days):")
    show_row(conn, "Loan", loan_id)


def do_add(conn) -> None:
    table = choose_table("Add to which table?")
    t = records.TABLES[table]
    print(f"  New {table} (the {t.pk} is assigned automatically). Blank = skip/default.")
    raw = {}
    for col in t.cols:
        hint = " (YYYY-MM-DD)" if col.kind == "date" else ""
        hint += " [required]" if col.required and not col.default_today else ""
        raw[col.name] = ask(f"{col.name}{hint}", required=False)
    new_id = records.add_record(conn, table, raw)
    print(f"  Added {table} {new_id}:")
    show_row(conn, table, new_id)


def do_edit(conn) -> None:
    table = choose_table("Edit which table?")
    t = records.TABLES[table]
    pk_value = ask_int(f"{t.pk}")
    cols, rows = records.find(conn, table, pk_value)
    if not rows:
        raise DBError(f"No {table} with ID {pk_value}.")
    print_table(cols, rows)
    pick = choose([c.name for c in t.cols], "Which column?")
    if not pick.isdigit() or not (1 <= int(pick) <= len(t.cols)):
        raise Cancel()
    col = t.cols[int(pick) - 1]
    new_value = ask(f"New value for {col.name} (blank = clear/NULL)", required=False)
    records.update_record(conn, table, pk_value, col.name, new_value)
    print("  Updated:")
    show_row(conn, table, pk_value)


def do_delete(conn) -> None:
    table = choose_table("Delete from which table?")
    t = records.TABLES[table]
    pk_value = ask_int(f"{t.pk}")
    cols, rows = records.find(conn, table, pk_value)
    if not rows:
        raise DBError(f"No {table} with ID {pk_value}.")
    print_table(cols, rows)
    if input("  Delete this record? (y/N): ").strip().lower() != "y":
        raise Cancel()
    records.delete_record(conn, table, pk_value)
    print("  Deleted.")


def do_browse(conn) -> None:
    table = choose_table("Browse which table?")
    cols, rows = records.browse(conn, table)
    print()
    print_table(cols, rows)


# Main menu
def main() -> None:
    try:
        conn = connect()
    except DBError as err:
        print(f"\n  ! {err}")
        sys.exit(1)
    print(f"\n  Connected to Oracle as {conn.username} ({conn.dsn})")

    actions = {
        "1": ("Drop Tables", do_drop),
        "2": ("Create Tables", do_create),
        "3": ("Populate Tables", do_populate),
        "4": ("Query Tables", query_menu),
        "5": ("Add / Edit / Delete Records", records_menu),
    }
    try:
        while True:
            print("\n  ===== LIBRARY DATABASE MANAGEMENT SYSTEM =====")
            for key, (label, _) in actions.items():
                print(f"   {key}. {label}")
            print("   0. Exit")
            pick = input("  > ").strip()
            if pick in ("0", "q", "exit"):
                break
            if pick not in actions:
                print("  Not a valid choice.")
                continue
            try:
                actions[pick][1](conn)
            except Cancel:
                print("  Cancelled.")
            except DBError as err:
                print(f"  ! {err}")
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        conn.close()
        print("  Disconnected. Goodbye.")


if __name__ == "__main__":
    main()
