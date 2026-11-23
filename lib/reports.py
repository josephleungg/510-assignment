"""
reports.py - every read-only query of the application ("Query Tables" menu).

Parts 1 and 2 are the Assignment 4 queries, kept word-for-word where possible so
the relational algebra written for Assignment 10 still matches.  The only
change is that values that used to be hard-coded ('Horror', MemberID = 1, ...)
are now bind variables (:genre, :member_id ...) that the user types in.

Each Report holds its SQL text, the parameters to ask for, and a short note on
what it demonstrates.  The menu (cli.py) is generic: it just walks GROUPS.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .db import query


@dataclass
class Param:
    name: str                    # bind variable name used in the SQL (:name)
    prompt: str                  # what the user is asked
    kind: str = "str"            # "str" or "int"
    hint_sql: str | None = None  # optional SELECT shown first so the user can see valid values


@dataclass
class Report:
    title: str
    sql: str
    params: list[Param] = field(default_factory=list)
    note: str = ""               # what this query demonstrates (shown in the menu / for the oral)


# Reference lists shown before prompting, so the user does not have to guess IDs.
HINT_GENRES = "SELECT DISTINCT Genre FROM Book ORDER BY Genre"
HINT_PUBLISHERS = "SELECT PublisherID, Name FROM Publisher ORDER BY PublisherID"
HINT_MEMBERS = ("SELECT MemberID, FirstName || ' ' || LastName AS Member_Name "
                "FROM Member ORDER BY MemberID")

# ---------------------------------------------------------------------------
# PART 1 - simple queries (Assignment 4, part 1)
# ---------------------------------------------------------------------------
PART1 = [
    Report(
        "Books of a genre",
        # UPPER() on both sides so 'horror' and 'Horror' both work.
        "SELECT * FROM Book WHERE UPPER(Genre) = UPPER(:genre)",
        [Param("genre", "Genre", hint_sql=HINT_GENRES)],
        "selection on one table with a user-supplied value",
    ),
    Report(
        "All staff members",
        "SELECT * FROM Staff",
        note="plain projection of a whole table",
    ),
    Report(
        "Staff who also hold a library membership",
        "SELECT m.*, s.StaffID, s.Position FROM Member m, Staff s WHERE m.Email = s.Email",
        note="join on a non-key column (Email)",
    ),
    Report(
        "Publishers that have not published a book",
        """SELECT p.* FROM Publisher p WHERE NOT EXISTS (
               SELECT * FROM Book b WHERE b.PublisherID = p.PublisherID)""",
        note="NOT EXISTS (correlated subquery) = set difference",
    ),
    Report(
        "Authors with at least one book in a genre",
        """SELECT DISTINCT a.* FROM Author a, Book b
           WHERE b.AuthorID = a.AuthorID AND UPPER(b.Genre) = UPPER(:genre)""",
        [Param("genre", "Genre", hint_sql=HINT_GENRES)],
        "DISTINCT removes authors counted once per book",
    ),
    Report(
        "Staff ordered by last name",
        "SELECT FirstName, LastName, Position FROM Staff ORDER BY LastName",
        note="ORDER BY",
    ),
    Report(
        "Books published by a publisher",
        "SELECT Title FROM Book WHERE PublisherID = :publisher_id",
        [Param("publisher_id", "Publisher ID", "int", HINT_PUBLISHERS)],
        "selection by foreign key",
    ),
]

# ---------------------------------------------------------------------------
# PART 2 - views and joins (Assignment 4, part 2)
# The views themselves are created in sql/views.sql.
# ---------------------------------------------------------------------------
PART2 = [
    Report(
        "Overdue report (view Overdue_Loans)",
        """SELECT Book_Title, Member_Name, Member_Email, Member_Phone,
                  Due_Date, Days_Overdue
           FROM Overdue_Loans
           ORDER BY Days_Overdue DESC, Member_Name ASC""",
        note="query on a 3-table join view; most overdue first",
    ),
    Report(
        "Members with overdue books, and how many",
        """SELECT Member_Name, Member_Email, COUNT(*) AS Overdue_Books
           FROM Overdue_Loans
           GROUP BY Member_Name, Member_Email
           ORDER BY Overdue_Books DESC, Member_Name""",
        note="GROUP BY + COUNT on top of a view",
    ),
    Report(
        "Staff workload (view Staff_Loan_Summary)",
        """SELECT *
           FROM Staff_Loan_Summary
           ORDER BY Loans_Processed DESC, Staff_Name""",
        note="the view uses a LEFT OUTER JOIN so staff with 0 loans still appear",
    ),
    Report(
        "Everything currently on loan (view ActiveLoans)",
        "SELECT * FROM ActiveLoans ORDER BY DueDate",
        note="view; earliest due date first",
    ),
    Report(
        "Full circulation log",
        # 4-table join: Loan, Book, Member, Staff.  NVL shows 'Not returned' for NULL.
        """SELECT l.LoanID AS Loan_ID,
                  b.Title AS Book_Title,
                  m.FirstName || ' ' || m.LastName AS Member_Name,
                  s.FirstName || ' ' || s.LastName AS Staff_Name,
                  l.LoanDate AS Loan_Date,
                  l.DueDate AS Due_Date,
                  NVL(TO_CHAR(l.ReturnDate, 'YYYY-MM-DD'), 'Not returned') AS Returned_On
           FROM Loan l, Book b, Member m, Staff s
           WHERE l.BookID = b.BookID
             AND l.MemberID = m.MemberID
             AND l.StaffID = s.StaffID
           ORDER BY l.LoanDate DESC, l.LoanID""",
        note="4-table join",
    ),
    Report(
        "Borrowing history of one member",
        # 4-table join: Member, Loan, Book, Author.
        """SELECT b.Title AS Book_Title,
                  a.FirstName || ' ' || a.LastName AS Author_Name,
                  b.Genre,
                  l.LoanDate AS Loan_Date,
                  NVL(TO_CHAR(l.ReturnDate, 'YYYY-MM-DD'), 'Not returned') AS Returned_On
           FROM Member m, Loan l, Book b, Author a
           WHERE m.MemberID = :member_id
             AND l.MemberID = m.MemberID
             AND l.BookID = b.BookID
             AND b.AuthorID = a.AuthorID
           ORDER BY l.LoanDate DESC""",
        [Param("member_id", "Member ID", "int", HINT_MEMBERS)],
        "4-table join filtered by a user-supplied member",
    ),
    Report(
        "Checked-out books with author and publisher",
        # 4-table join: Loan, Book, Author, Publisher.
        """SELECT b.Title AS Book_Title,
                  a.FirstName || ' ' || a.LastName AS Author_Name,
                  p.Name AS Publisher_Name,
                  l.DueDate AS Due_Date
           FROM Loan l, Book b, Author a, Publisher p
           WHERE l.ReturnDate IS NULL
             AND l.BookID = b.BookID
             AND b.AuthorID = a.AuthorID
             AND b.PublisherID = p.PublisherID
           ORDER BY l.DueDate ASC, b.Title""",
        note="what is currently unavailable, 4-table join",
    ),
    Report(
        "Members who borrowed a book of a genre",
        """SELECT DISTINCT m.FirstName || ' ' || m.LastName AS Member_Name,
                  m.Email AS Member_Email
           FROM Member m, Loan l, Book b
           WHERE UPPER(b.Genre) = UPPER(:genre)
             AND l.BookID = b.BookID
             AND l.MemberID = m.MemberID
           ORDER BY Member_Name""",
        [Param("genre", "Genre", hint_sql=HINT_GENRES)],
        "3-table join with DISTINCT",
    ),
    Report(
        "Most popular authors (times borrowed)",
        """SELECT a.FirstName || ' ' || a.LastName AS Author_Name,
                  COUNT(l.LoanID) AS Times_Borrowed
           FROM Author a, Book b, Loan l
           WHERE a.AuthorID = b.AuthorID
             AND b.BookID = l.BookID
           GROUP BY a.AuthorID, a.FirstName, a.LastName
           ORDER BY Times_Borrowed DESC, Author_Name""",
        note="3-table join with GROUP BY and COUNT",
    ),
]

# ---------------------------------------------------------------------------
# ADVANCED - set operations, aggregates, subqueries.
# These were written for Assignment 9 as stand-ins; replace or add your own
# Assignment 5 advanced queries here (same Report(...) format).
# ---------------------------------------------------------------------------
ADVANCED = [
    Report(
        "Books that have never been borrowed",
        # MINUS = every book, minus the books that appear in at least one loan.
        """SELECT b.BookID, b.Title FROM Book b
           MINUS
           SELECT b.BookID, b.Title FROM Book b, Loan l WHERE b.BookID = l.BookID
           ORDER BY 1""",
        note="set operation: MINUS",
    ),
    Report(
        "Members who borrowed BOTH of two genres",
        # INTERSECT = members found in both result sets.
        """SELECT m.MemberID, m.FirstName || ' ' || m.LastName AS Member_Name
           FROM Member m, Loan l, Book b
           WHERE m.MemberID = l.MemberID AND l.BookID = b.BookID
             AND UPPER(b.Genre) = UPPER(:genre1)
           INTERSECT
           SELECT m.MemberID, m.FirstName || ' ' || m.LastName
           FROM Member m, Loan l, Book b
           WHERE m.MemberID = l.MemberID AND l.BookID = b.BookID
             AND UPPER(b.Genre) = UPPER(:genre2)
           ORDER BY 1""",
        [Param("genre1", "First genre", hint_sql=HINT_GENRES), Param("genre2", "Second genre")],
        "set operation: INTERSECT",
    ),
    Report(
        "Combined contact list (members + staff)",
        # UNION merges two tables into one list and removes duplicates; the literal
        # column tells the reader where each row came from.
        """SELECT FirstName, LastName, Email, 'Member' AS Person_Type FROM Member
           UNION
           SELECT FirstName, LastName, Email, 'Staff' AS Person_Type FROM Staff
           ORDER BY 2, 1""",
        note="set operation: UNION",
    ),
    Report(
        "Members with at least N loans",
        # HAVING filters AFTER grouping (WHERE filters before), so it can use COUNT.
        """SELECT m.MemberID, m.FirstName || ' ' || m.LastName AS Member_Name,
                  COUNT(l.LoanID) AS Total_Loans
           FROM Member m, Loan l
           WHERE m.MemberID = l.MemberID
           GROUP BY m.MemberID, m.FirstName, m.LastName
           HAVING COUNT(l.LoanID) >= :min_loans
           ORDER BY Total_Loans DESC, Member_Name""",
        [Param("min_loans", "Minimum number of loans", "int")],
        "GROUP BY ... HAVING with a user-supplied threshold",
    ),
    Report(
        "Average loan length by genre (returned books)",
        # Subtracting two DATEs in Oracle gives a number of days.
        """SELECT b.Genre, COUNT(*) AS Returned_Loans,
                  ROUND(AVG(l.ReturnDate - l.LoanDate), 1) AS Avg_Days
           FROM Loan l, Book b
           WHERE l.BookID = b.BookID AND l.ReturnDate IS NOT NULL
           GROUP BY b.Genre
           ORDER BY Avg_Days DESC""",
        note="aggregate functions AVG / COUNT / ROUND and date arithmetic",
    ),
    Report(
        "Authors with more books than the average author",
        # The inner query counts books per author, the middle one averages those
        # counts, and HAVING compares each author's count to that average.
        """SELECT a.FirstName || ' ' || a.LastName AS Author_Name,
                  COUNT(b.BookID) AS Books_In_Catalog
           FROM Author a, Book b
           WHERE a.AuthorID = b.AuthorID
           GROUP BY a.AuthorID, a.FirstName, a.LastName
           HAVING COUNT(b.BookID) > (SELECT AVG(cnt) FROM
                                       (SELECT COUNT(*) AS cnt FROM Book GROUP BY AuthorID))
           ORDER BY Books_In_Catalog DESC, Author_Name""",
        note="nested subquery inside HAVING",
    ),
]

# ---------------------------------------------------------------------------
# SEARCH - find specific records from free text typed by the user.
# ---------------------------------------------------------------------------
SEARCH = [
    Report(
        "Search books (title, author, genre or ISBN) + availability",
        # The same :q is reused several times; LIKE '%..%' = "contains".
        # The CASE/EXISTS column answers "is it on loan right now?" (Assignment 1).
        """SELECT b.BookID, b.Title,
                  a.FirstName || ' ' || a.LastName AS Author_Name,
                  b.Genre, b.ISBN,
                  CASE WHEN EXISTS (SELECT 1 FROM Loan l
                                    WHERE l.BookID = b.BookID AND l.ReturnDate IS NULL)
                       THEN 'On loan' ELSE 'Available' END AS Status
           FROM Book b, Author a
           WHERE b.AuthorID = a.AuthorID
             AND (UPPER(b.Title)     LIKE '%' || UPPER(:q) || '%'
               OR UPPER(a.FirstName || ' ' || a.LastName) LIKE '%' || UPPER(:q) || '%'
               OR UPPER(b.Genre)     LIKE '%' || UPPER(:q) || '%'
               OR b.ISBN = :q)
           ORDER BY b.Title""",
        [Param("q", "Search text")],
        "LIKE search across several columns + CASE/EXISTS availability",
    ),
    Report(
        "Search members (name or email)",
        """SELECT MemberID, FirstName, LastName, Email, Phone, MembershipDate
           FROM Member
           WHERE UPPER(FirstName || ' ' || LastName) LIKE '%' || UPPER(:q) || '%'
              OR UPPER(Email) LIKE '%' || UPPER(:q) || '%'
           ORDER BY LastName, FirstName""",
        [Param("q", "Search text")],
        "LIKE search",
    ),
]

# Menu order: (heading, reports)
GROUPS = [
    ("PART 1 - Simple queries", PART1),
    ("PART 2 - Views and join queries", PART2),
    ("ADVANCED - set operations, aggregates, subqueries", ADVANCED),
    ("SEARCH", SEARCH),
]


def run_report(conn, report: Report, values: dict):
    """Run a report with the user's (already converted) values. Returns (cols, rows)."""
    return query(conn, report.sql, values)
