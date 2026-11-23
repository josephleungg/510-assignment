/*
 * CPS510 - Database Systems I
 * Assignment 9 - sample (dummy) data for the Library DBMS
 * Section 06, Team 04
 *
 * Rows are inserted parent-first (Publisher, Author, Member, Staff, Book, Loan)
 * so every foreign key already exists. The data deliberately contains the
 * special cases the reports need to show:
 *   - a publisher with no books            (NoBooks Press)
 *   - a staff member who is also a member  (Daniel Brown, Olivia Chen)
 *   - a staff member with zero loans       (Marcus Reid -> outer join in Staff_Loan_Summary)
 *   - several overdue loans, one member with two overdue (Eva Martinez)
 *   - books that were never borrowed       (used by the MINUS report)
 *   - late returns                         (ReturnDate > DueDate)
 * Active-loan dates are relative to SYSDATE so the overdue reports stay
 * meaningful no matter when the demo is run.
 */

-- Publishers
INSERT INTO Publisher (PublisherID, Name, Address, Phone, Email) VALUES (1, 'Penguin Books', '123 Main St, Toronto', '416-555-0101', 'info@penguinbooks.com');
INSERT INTO Publisher (PublisherID, Name, Address, Phone, Email) VALUES (2, 'HarperCollins', '456 Oak Ave, Montreal', '514-555-0102', 'contact@harpercollins.com');
INSERT INTO Publisher (PublisherID, Name, Address, Phone, Email) VALUES (3, 'NoBooks Press', '789 Cedar Rd, Calgary', '403-555-3001', 'info@nobookspress.com');
INSERT INTO Publisher (PublisherID, Name, Address, Phone, Email) VALUES (4, 'Active Press', '321 Elm St, Vancouver', '604-555-4001', 'hello@activepress.com');
INSERT INTO Publisher (PublisherID, Name, Address, Phone, Email) VALUES (5, 'Bantam Books', '88 Queen St W, Toronto', '416-555-5001', 'editors@bantambooks.com');

-- Authors
INSERT INTO Author (AuthorID, FirstName, LastName) VALUES (1, 'Stephen', 'King');
INSERT INTO Author (AuthorID, FirstName, LastName) VALUES (2, 'J.K.', 'Rowling');
INSERT INTO Author (AuthorID, FirstName, LastName) VALUES (3, 'Agatha', 'Christie');
INSERT INTO Author (AuthorID, FirstName, LastName) VALUES (4, 'Frank', 'Herbert');
INSERT INTO Author (AuthorID, FirstName, LastName) VALUES (5, 'George', 'Orwell');
INSERT INTO Author (AuthorID, FirstName, LastName) VALUES (6, 'Haruki', 'Murakami');
INSERT INTO Author (AuthorID, FirstName, LastName) VALUES (7, 'Jane', 'Austen');
INSERT INTO Author (AuthorID, FirstName, LastName) VALUES (8, 'Isaac', 'Asimov');
INSERT INTO Author (AuthorID, FirstName, LastName) VALUES (9, 'Margaret', 'Atwood');

-- Members
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (1, 'Alice', 'Smith', 'alice.smith@email.com', '647-555-1001', DATE '2026-01-10');
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (2, 'Bob', 'Johnson', 'bob.johnson@email.com', '647-555-1002', DATE '2026-02-15');
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (3, 'Carol', 'Lee', 'carol.lee@email.com', '416-555-1003', DATE '2026-03-01');
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (4, 'Daniel', 'Brown', 'daniel.brown@library.com', '416-555-1111', TRUNC(SYSDATE));
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (5, 'Eva', 'Martinez', 'eva.martinez@email.com', '647-555-1005', DATE '2026-03-12');
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (6, 'Frank', 'Nguyen', 'frank.nguyen@email.com', '416-555-1006', DATE '2026-03-20');
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (7, 'Grace', 'Patel', 'grace.patel@email.com', '905-555-1007', DATE '2026-04-02');
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (8, 'Henry', 'Wong', 'henry.wong@email.com', '647-555-1008', DATE '2026-04-18');
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (9, 'Isabella', 'Rossi', 'isabella.rossi@email.com', '416-555-1009', DATE '2026-05-05');
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (10, 'Jack', 'O''Connor', 'jack.oconnor@email.com', '905-555-1010', DATE '2026-05-22');
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (11, 'Karen', 'Singh', 'karen.singh@email.com', '647-555-1011', DATE '2026-06-14');
INSERT INTO Member (MemberID, FirstName, LastName, Email, Phone, MembershipDate) VALUES (12, 'Olivia', 'Chen', 'olivia.chen@library.com', '416-555-1012', DATE '2026-07-01');

-- Staff
INSERT INTO Staff (StaffID, FirstName, LastName, Position, Email) VALUES (1, 'Daniel', 'Brown', 'Librarian', 'daniel.brown@library.com');
INSERT INTO Staff (StaffID, FirstName, LastName, Position, Email) VALUES (2, 'Emma', 'Davis', 'Assistant', 'emma.davis@library.com');
INSERT INTO Staff (StaffID, FirstName, LastName, Position, Email) VALUES (3, 'Olivia', 'Chen', 'Branch Manager', 'olivia.chen@library.com');
INSERT INTO Staff (StaffID, FirstName, LastName, Position, Email) VALUES (4, 'Marcus', 'Reid', 'Assistant', 'marcus.reid@library.com');

-- Books
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (1, 'The Shining', '978-0450040184', 'Horror', 1, 1);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (2, 'Harry Potter and the Philosopher''s Stone', '978-0747532699', 'Fantasy', 2, 2);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (3, 'Murder on the Orient Express', '978-0062693662', 'Mystery', 3, 1);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (4, 'Dune', '978-0441013593', 'Sci-Fi', 4, 2);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (5, 'Death on the Nile', '978-0062073556', 'Mystery', 3, 4);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (6, 'It', '978-1501142970', 'Horror', 1, 1);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (7, 'And Then There Were None', '978-0062073488', 'Mystery', 3, 1);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (8, 'Harry Potter and the Chamber of Secrets', '978-0747538493', 'Fantasy', 2, 2);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (9, 'Pet Sematary', '978-1501156700', 'Horror', 1, 4);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (10, '1984', '978-0451524935', 'Dystopian', 5, 1);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (11, 'Animal Farm', '978-0451526342', 'Dystopian', 5, 1);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (12, 'Norwegian Wood', '978-0375704024', 'Fiction', 6, 2);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (13, 'Kafka on the Shore', '978-1400079278', 'Fiction', 6, 2);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (14, 'Pride and Prejudice', '978-0141439518', 'Romance', 7, 1);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (15, 'Emma', '978-0141439587', 'Romance', 7, 4);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (16, 'Foundation', '978-0553293357', 'Sci-Fi', 8, 5);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (17, 'I, Robot', '978-0553382563', 'Sci-Fi', 8, 5);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (18, 'The Handmaid''s Tale', '978-0385490818', 'Dystopian', 9, 5);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (19, 'Carrie', '978-0307743664', 'Horror', 1, 4);
INSERT INTO Book (BookID, Title, ISBN, Genre, AuthorID, PublisherID) VALUES (20, 'Dune Messiah', '978-0593098233', 'Sci-Fi', 4, 2);

-- Loans (ReturnDate NULL = still checked out)
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (1, 1, 1, 1, DATE '2026-04-01', DATE '2026-04-08', DATE '2026-04-07');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (2, 2, 2, 2, DATE '2026-04-05', DATE '2026-04-12', NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (3, 3, 3, 1, DATE '2026-04-06', DATE '2026-04-13', DATE '2026-04-12');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (4, 1, 1, 1, TRUNC(SYSDATE) - 3, TRUNC(SYSDATE) + 11, NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (5, 3, 2, 2, TRUNC(SYSDATE) - 7, TRUNC(SYSDATE) + 7, NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (6, 4, 3, 1, TRUNC(SYSDATE) - 10, TRUNC(SYSDATE) + 4, NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (7, 5, 4, 2, TRUNC(SYSDATE) - 14, TRUNC(SYSDATE), NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (8, 6, 1, 2, TRUNC(SYSDATE) - 1, TRUNC(SYSDATE) + 13, NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (9, 7, 3, 1, TRUNC(SYSDATE), TRUNC(SYSDATE) + 14, NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (10, 10, 5, 3, TRUNC(SYSDATE) - 30, TRUNC(SYSDATE) - 16, NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (11, 11, 5, 3, TRUNC(SYSDATE) - 25, TRUNC(SYSDATE) - 11, NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (12, 12, 6, 1, TRUNC(SYSDATE) - 21, TRUNC(SYSDATE) - 7, NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (13, 14, 7, 2, TRUNC(SYSDATE) - 40, TRUNC(SYSDATE) - 26, NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (14, 10, 6, 1, DATE '2026-05-02', DATE '2026-05-16', DATE '2026-05-14');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (15, 2, 7, 2, DATE '2026-05-10', DATE '2026-05-24', DATE '2026-05-30');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (16, 8, 8, 3, DATE '2026-05-15', DATE '2026-05-29', DATE '2026-05-28');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (17, 1, 8, 1, DATE '2026-06-01', DATE '2026-06-15', DATE '2026-06-10');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (18, 9, 9, 2, DATE '2026-06-03', DATE '2026-06-17', DATE '2026-06-17');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (19, 19, 10, 3, DATE '2026-06-20', DATE '2026-07-04', DATE '2026-07-01');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (20, 16, 9, 1, DATE '2026-07-02', DATE '2026-07-16', DATE '2026-07-20');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (21, 18, 10, 2, DATE '2026-07-10', DATE '2026-07-24', DATE '2026-07-22');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (22, 6, 11, 1, DATE '2026-07-15', DATE '2026-07-29', DATE '2026-07-28');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (23, 3, 11, 3, DATE '2026-08-01', DATE '2026-08-15', DATE '2026-08-12');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (24, 7, 12, 2, DATE '2026-08-10', DATE '2026-08-24', DATE '2026-08-23');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (25, 14, 5, 1, DATE '2026-08-18', DATE '2026-09-01', DATE '2026-09-05');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (26, 5, 6, 2, DATE '2026-09-02', DATE '2026-09-16', DATE '2026-09-15');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (27, 1, 10, 3, DATE '2026-09-10', DATE '2026-09-24', DATE '2026-09-22');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (28, 2, 1, 1, DATE '2026-09-20', DATE '2026-10-04', DATE '2026-10-03');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (29, 4, 12, 2, DATE '2026-10-01', DATE '2026-10-15', DATE '2026-10-14');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (30, 6, 5, 1, DATE '2026-10-05', DATE '2026-10-19', DATE '2026-10-18');
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (31, 8, 7, 3, TRUNC(SYSDATE) - 2, TRUNC(SYSDATE) + 12, NULL);
INSERT INTO Loan (LoanID, BookID, MemberID, StaffID, LoanDate, DueDate, ReturnDate) VALUES (32, 19, 8, 2, TRUNC(SYSDATE) - 5, TRUNC(SYSDATE) + 9, NULL);

COMMIT;
