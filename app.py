#!/usr/bin/env python3
"""
CPS510 - Database Systems I - Assignment 9 (bonus)
Library Database Management System - Flask web interface
Section 06, Team 04

Run:  python app.py     then open  http://127.0.0.1:5001

Same features as the text menu (cli.py), reusing the same lib/ code:
  Home          Drop / Create / Populate Tables, row counts
  Queries       every report from lib/reports.py, with input forms
  Tables        one page per table: list, search, add, edit, delete
  Circulation   check out, return and renew
This file only handles web requests; all SQL is in lib/.

It is a single-user local app: one shared database connection, so the server
runs without threads (see the bottom of this file).
Stop the server with Ctrl+C in the terminal.
"""
from __future__ import annotations

import os
import secrets
from datetime import date, datetime

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from lib import records, reports, schema
from lib.db import DBError, connect, format_value, load_env, query

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET") or secrets.token_hex(16)   # needed for flash()
app.jinja_env.filters["fmt"] = format_value        # {{ value|fmt }} prints dates/NULLs nicely

STATE = {"conn": None}                             # the one shared database connection
ALL_REPORTS = [rep for _, group in reports.GROUPS for rep in group]   # /queries/<n> is 1-based


# --------------------------------------------------------------------------
# Connection handling
# --------------------------------------------------------------------------
def _try_env_login() -> None:
    """Connect automatically when DB_USER / DB_PASSWORD / DB_DSN are all set in .env."""
    load_env()
    if all(os.environ.get(k) for k in ("DB_USER", "DB_PASSWORD", "DB_DSN")):
        try:
            STATE["conn"] = connect(interactive=False)
        except DBError as err:
            flash(str(err), "error")


@app.before_request
def require_connection():
    """Every page needs a connection; otherwise send the user to the login form."""
    if request.endpoint in ("login", "static"):
        return None
    if STATE["conn"] is None:
        _try_env_login()
    if STATE["conn"] is None:
        return redirect(url_for("login"))
    return None


def db():
    return STATE["conn"]


@app.route("/login", methods=["GET", "POST"])
def login():
    load_env()
    if request.method == "POST":
        try:
            STATE["conn"] = connect(request.form.get("user", "").strip(),
                                    request.form.get("password", ""),
                                    request.form.get("dsn", "").strip(),
                                    interactive=False)
            return redirect(url_for("index"))
        except DBError as err:
            flash(str(err), "error")
    return render_template("login.html",
                           user=request.form.get("user") or os.environ.get("DB_USER", ""),
                           dsn=request.form.get("dsn") or os.environ.get("DB_DSN", ""))


# --------------------------------------------------------------------------
# Home: Drop / Create / Populate
# --------------------------------------------------------------------------
@app.route("/")
def index():
    try:
        counts = schema.row_counts(db())
    except DBError:
        counts = None                      # tables do not exist yet
    return render_template("index.html", counts=counts)


ADMIN_ACTIONS = {
    "drop": ("Drop Tables", schema.drop_tables),
    "create": ("Create Tables", schema.create_tables),
    "populate": ("Populate Tables", schema.populate_tables),
}


@app.route("/admin/<action>", methods=["POST"])
def admin(action):
    if action not in ADMIN_ACTIONS:
        abort(404)
    label, func = ADMIN_ACTIONS[action]
    try:
        log = func(db())
        flash(f"{label}: done.\n" + "\n".join(line.strip() for line in log), "ok")
    except DBError as err:
        flash(f"{label}: {err}", "error")
    return redirect(url_for("index"))


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------
@app.route("/queries")
def queries():
    numbered, n = [], 0
    for heading, group in reports.GROUPS:
        items = []
        for rep in group:
            n += 1
            items.append((n, rep))
        numbered.append((heading, items))
    return render_template("queries.html", groups=numbered)


@app.route("/queries/<int:n>")
def run_query(n):
    if not 1 <= n <= len(ALL_REPORTS):
        abort(404)
    rep = ALL_REPORTS[n - 1]
    values = {p.name: request.args.get(p.name, "").strip() for p in rep.params}
    result = None
    hints = []
    try:
        for p in rep.params:                      # reference lists (valid genres, IDs ...)
            if p.hint_sql:
                hints.append((p.prompt, query(db(), p.hint_sql)))
        ready = all(values.values())              # run once every parameter has a value
        if ready:
            binds = {}
            for p in rep.params:
                if p.kind == "int":
                    try:
                        binds[p.name] = int(values[p.name])
                    except ValueError:
                        raise DBError(f"{p.prompt} must be a whole number.") from None
                else:
                    binds[p.name] = values[p.name]
            result = reports.run_report(db(), rep, binds)
    except DBError as err:
        flash(str(err), "error")
    return render_template("query.html", n=n, rep=rep, values=values, hints=hints, result=result)


# --------------------------------------------------------------------------
# Tables: list / search / add / edit / delete
# --------------------------------------------------------------------------
def _table_or_404(name: str) -> records.TableDef:
    if name not in records.TABLES:
        abort(404)
    return records.TABLES[name]


def _form_fields(table: str, current: dict, adding: bool):
    """Describe every input of the add/edit form (name, type, dropdown choices, value)."""
    fields = []
    for col in records.TABLES[table].cols:
        value = current.get(col.name, "")
        if value is None:
            value = ""
        if isinstance(value, (datetime, date)):
            value = value.strftime("%Y-%m-%d")
        if adding and col.default_today and value == "":
            value = date.today().strftime("%Y-%m-%d")
        choices = records.fk_options(db(), *col.fk) if col.fk else None
        fields.append({"col": col, "value": value, "choices": choices})
    return fields


@app.route("/tables")
def tables():
    try:
        counts = dict(schema.row_counts(db()))
    except DBError as err:
        flash(str(err), "error")
        counts = {}
    return render_template("tables.html", names=list(records.TABLES), counts=counts)


@app.route("/t/<table>")
def table_list(table):
    t = _table_or_404(table)
    q = request.args.get("q", "").strip()
    cols, rows = [], []
    try:
        cols, rows = records.search_rows(db(), table, q) if q else records.browse(db(), table)
    except DBError as err:
        flash(str(err), "error")
    return render_template("table.html", table=table, t=t, cols=cols, rows=rows, q=q)


@app.route("/t/<table>/new", methods=["GET", "POST"])
def table_new(table):
    t = _table_or_404(table)
    current = {}
    if request.method == "POST":
        current = {c.name: request.form.get(c.name, "") for c in t.cols}
        try:
            new_id = records.add_record(db(), table, current)
            flash(f"Added {table} {new_id}.", "ok")
            return redirect(url_for("table_list", table=table))
        except DBError as err:
            flash(str(err), "error")
    try:
        fields = _form_fields(table, current, adding=True)
    except DBError as err:
        flash(str(err), "error")
        return redirect(url_for("tables"))
    return render_template("form.html", table=table, t=t, fields=fields, pk_value=None)


@app.route("/t/<table>/<int:pk>/edit", methods=["GET", "POST"])
def table_edit(table, pk):
    t = _table_or_404(table)
    try:
        cols, rows = records.find(db(), table, pk)
    except DBError as err:
        flash(str(err), "error")
        return redirect(url_for("tables"))
    if not rows:
        flash(f"No {table} with ID {pk}.", "error")
        return redirect(url_for("table_list", table=table))
    # Oracle returns upper-case column names; map them back to our column names.
    stored = {c.name: v for c in t.cols for cn, v in zip(cols, rows[0]) if cn.upper() == c.name.upper()}
    current = stored
    if request.method == "POST":
        current = {c.name: request.form.get(c.name, "") for c in t.cols}
        try:
            records.update_row(db(), table, pk, current)
            flash(f"Updated {table} {pk}.", "ok")
            return redirect(url_for("table_list", table=table))
        except DBError as err:
            flash(str(err), "error")
    fields = _form_fields(table, current, adding=False)
    return render_template("form.html", table=table, t=t, fields=fields, pk_value=pk)


@app.route("/t/<table>/<int:pk>/delete", methods=["POST"])
def table_delete(table, pk):
    _table_or_404(table)
    try:
        records.delete_record(db(), table, pk)
        flash(f"Deleted {table} {pk}.", "ok")
    except DBError as err:
        flash(str(err), "error")
    return redirect(url_for("table_list", table=table))


# --------------------------------------------------------------------------
# Circulation
# --------------------------------------------------------------------------
@app.route("/circulation")
def circulation():
    try:
        options = records.circulation_options(db())
    except DBError as err:
        flash(str(err), "error")
        return redirect(url_for("index"))
    return render_template("circulation.html", o=options, days=records.LOAN_DAYS, renew=records.RENEW_DAYS)


def _int_field(name: str) -> int:
    try:
        return int(request.form.get(name, ""))
    except ValueError:
        raise DBError("Please choose a value from every list.") from None


@app.route("/circulation/<action>", methods=["POST"])
def circulation_action(action):
    try:
        if action == "checkout":
            loan_id = records.checkout_book(db(), _int_field("book"), _int_field("member"), _int_field("staff"))
            flash(f"Checked out. New loan {loan_id}.", "ok")
        elif action == "return":
            records.return_book(db(), _int_field("loan"))
            flash("Book returned.", "ok")
        elif action == "renew":
            records.renew_loan(db(), _int_field("loan"))
            flash(f"Loan renewed (+{records.RENEW_DAYS} days).", "ok")
        else:
            abort(404)
    except DBError as err:
        flash(str(err), "error")
    return redirect(url_for("circulation"))


if __name__ == "__main__":
    # Port 5001: on macOS port 5000 is taken by AirPlay Receiver.
    # threaded=False: one shared Oracle connection, handled one request at a time.
    app.run(host="127.0.0.1", port=5001, debug=False, threaded=False)
