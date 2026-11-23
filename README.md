# CPS510 Assignment 9 - Library Database Management System

Section 06, Team 04. A text-menu application connected to Oracle.

## What it does

```
1. Drop Tables       drops the 3 views and 6 tables (safe to run when they don't exist)
2. Create Tables     creates the tables (Assignment 3) and views (Assignment 4)
3. Populate Tables   loads the dummy data (5 publishers, 9 authors, 12 members, 4 staff, 20 books, 32 loans)
4. Query Tables      22 reports + 2 searches; asks the user for genre / member ID / search text / etc.
5. Add / Edit / Delete Records
                     check out, return, renew, add / edit / delete a row in any table, browse a table
0. Exit
```

Errors from Oracle (missing tables, duplicates, foreign-key violations, bad dates...) are shown as
plain messages instead of stack traces.

## Setup

1. Python 3.9+ and an Oracle database you can log in to (school server, or local - see below).
2. Install the driver (no Oracle Client needed):
   ```
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Tell the app how to connect. Either copy `.env.example` to `.env` and fill it in, or leave things
   blank and it will ask when it starts (the password prompt is hidden).
   `DB_DSN` is `host:port/service_name`, the same host and service name you use in SQL Developer / SQL*Plus.
4. Run it:
   ```
   python cli.py
   ```

### Local Oracle on an Apple Silicon Mac (optional)
Oracle XE does not run natively on ARM. Docker works:
```
docker run -d --name oracle -p 1521:1521 -e ORACLE_PASSWORD=change_me \
  -e APP_USER=library -e APP_USER_PASSWORD=change_me gvenzl/oracle-free:slim
```
then `DB_USER=library`, `DB_PASSWORD=change_me`, `DB_DSN=localhost:1521/FREEPDB1`.

## Suggested demo order (about 5 minutes)

1. `1` Drop, `2` Create, `3` Populate (shows row counts per table).
2. `4` Query: *Books of a genre* (type `horror`), *Overdue report*, *Staff workload* (note the staff
   member with 0 loans - that is the outer join), *Search books* (try `king`, then `dune`).
   Every SQL statement is echoed in the terminal as it runs (`SQL> ...;` plus its bind values). Press `s` in the Query menu to turn that off or on.
3. `5` Check out a book that is already on loan (refused), then one that is free; return it; renew a loan.
4. `5` Edit a member's phone number. Delete publisher 3 (NoBooks Press - works), then publisher 1 (refused:
   it has books).
5. `0` Exit.

## Files

| Path | Purpose |
|---|---|
| `cli.py` | The text menu (prompts only). |
| `app.py`, `templates/`, `static/` | The Flask web interface (routes only; no SQL). |
| `lib/db.py` | Connection, `query()` / `execute()` with bind variables, ORA- error translation, SQL file splitter, table printer. |
| `lib/schema.py` | Drop / Create / Populate. |
| `lib/reports.py` | All read-only queries. **Add or swap in your Assignment 5 advanced queries in the `ADVANCED` list.** |
| `lib/records.py` | Add / edit / delete / check out / return / renew. The `TABLES` dictionary describes every table and can drive web forms later. |
| `sql/create.sql`, `sql/views.sql`, `sql/populate.sql` | The SQL, also runnable by hand in SQL Developer. |

## SQL echo

Whenever the program runs SQL (menu or web), it prints the statement in the terminal first, for example:
```
SQL> SELECT * FROM Book WHERE UPPER(Genre) = UPPER(:genre);
       binds: {'genre': 'horror'}
```
It is on by default. Put `SHOW_SQL=0` in `.env` to turn it off. Passwords are never printed.

## Notes for the oral

- Every user value goes in as a **bind variable** (`:genre`, `:member_id`); table and column names only come
  from the fixed `TABLES` dictionary, so there is no SQL injection.
- The queries in parts 1 and 2 are the Assignment 4 queries; the hard-coded values became bind variables.
  The only wording change: genre comparisons use `UPPER()` so `horror` matches `Horror`.
- Dropping a table does not drop its views, so views are dropped first. `DROP TABLE IF EXISTS` (used in
  the Assignment 3 file) only exists in Oracle 23ai, so the app ignores ORA-00942 instead.
- The schema has no sequences, so new IDs are `MAX(id) + 1` (fine for one user).
- No `ON DELETE CASCADE`: a member, book, etc. with loan history cannot be deleted (ORA-02292, shown as a
  friendly message). Only rows nothing refers to can be deleted.
- A book can only be out once; the schema can't express that, so `checkout_book()` checks it.
- Active-loan dates in the dummy data are relative to `SYSDATE`, so overdue reports work on any demo day.

## Web interface (bonus)

```
pip install -r requirements.txt     # adds Flask
python app.py                       # then open http://127.0.0.1:5001
```
It uses the same `lib/` code as the text menu. If `.env` has DB_USER, DB_PASSWORD and DB_DSN it connects
automatically; otherwise it shows a login page.

| Page | What it does |
|---|---|
| Home | Drop / Create / Populate Tables buttons, row counts per table, links to the rest. Stop the server with Ctrl+C. |
| Queries | Every report; the ones that need input show a form (with a list of valid values). "Show SQL" under each result. |
| Tables | One page per table: list, search across all columns, add, edit, delete. Foreign keys are dropdowns (e.g. a Loan picks its Book, Member and Staff by name). |
| Circulation | Check out (only free books are offered), return and renew. |

Port 5001 is used because macOS reserves 5000 for AirPlay. The server handles one request at a time on purpose
(one shared database connection), so run it for one person.
