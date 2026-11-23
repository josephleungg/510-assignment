/*
 * CPS510 - Database Systems I
 * Assignment 9 - Views (from Assignment 4, Part 2)
 * Library Database Management System
 * Section 06, Team 04
 *
 * Created right after the tables. Dropping a table does NOT drop the views
 * built on it (they become INVALID), so the application drops them explicitly.
 */

/* VIEW: Overdue_Loans
*  Every book that is currently checked out (no return date) and
*  past its due date, with the borrowing member's contact info.
*  Joins Loan, Book and Member. Read-only because it is a report. */
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

/* VIEW: Staff_Loan_Summary
*  How many loans each staff member has processed and how many of
*  those are still out. Outer join keeps staff with zero loans. */
CREATE OR REPLACE VIEW Staff_Loan_Summary
      (Staff_Name, Position, Loans_Processed, Loans_Open) AS
      (SELECT s.FirstName || ' ' || s.LastName, s.Position,
              COUNT(l.LoanID),
              COUNT(l.LoanID) - COUNT(l.ReturnDate)
       FROM Staff s LEFT OUTER JOIN Loan l ON s.StaffID = l.StaffID
       GROUP BY s.StaffID, s.FirstName, s.LastName, s.Position)
      WITH READ ONLY;

/* VIEW: ActiveLoans
*  Books that are currently on loan */
CREATE OR REPLACE VIEW ActiveLoans AS
SELECT l.LoanID, b.Title, m.FirstName, m.LastName, l.DueDate
FROM Loan l, Book b, Member m
WHERE l.BookID = b.BookID
  AND l.MemberID = m.MemberID
  AND l.ReturnDate IS NULL;
