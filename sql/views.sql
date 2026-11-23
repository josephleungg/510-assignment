-- CPS510 Assignment 9: Library Database Management System
-- Section 06, Team 04 (Nathan Romero, Joseph Leung, Aidan Lee)
-- Views from Assignment 4 Part 2. Dropping a table doesn't drop its views,
-- so the app drops these separately (see lib/schema.py).

-- Overdue_Loans: books still checked out and past their due date,
-- with the member's contact info. Read only since it's a report.
CREATE OR REPLACE VIEW Overdue_Loans
      (Loan_ID, Book_Title, Member_Name, Member_Email, Member_Phone,
       Loan_Date, Due_Date, Days_Overdue) AS
      (SELECT l.LoanID, b.Title,
              m.FirstName || ' ' || m.LastName, m.Email, m.Phone,
              l.LoanDate, l.DueDate,
              TRUNC(SYSDATE) - TRUNC(l.DueDate)
       FROM Loan l, Book b, Member m
       WHERE l.BookID = b.BookID
         AND l.MemberID = m.MemberID
         AND l.ReturnDate IS NULL
         AND l.DueDate < TRUNC(SYSDATE))
      WITH READ ONLY;

-- Staff_Loan_Summary: loans processed and still out for each staff member.
-- The outer join keeps staff with zero loans.
CREATE OR REPLACE VIEW Staff_Loan_Summary
      (Staff_Name, Position, Loans_Processed, Loans_Open) AS
      (SELECT s.FirstName || ' ' || s.LastName, s.Position,
              COUNT(l.LoanID),
              COUNT(l.LoanID) - COUNT(l.ReturnDate)
       FROM Staff s LEFT OUTER JOIN Loan l ON s.StaffID = l.StaffID
       GROUP BY s.StaffID, s.FirstName, s.LastName, s.Position)
      WITH READ ONLY;

-- ActiveLoans: books currently on loan
CREATE OR REPLACE VIEW ActiveLoans AS
SELECT l.LoanID, b.Title, m.FirstName, m.LastName, l.DueDate
FROM Loan l, Book b, Member m
WHERE l.BookID = b.BookID
  AND l.MemberID = m.MemberID
  AND l.ReturnDate IS NULL;
