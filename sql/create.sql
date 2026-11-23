-- CPS510 Assignment 9: Library Database Management System
-- Section 06, Team 04 (Nathan Romero, Joseph Leung, Aidan Lee)
-- Tables from Assignment 3. Parent tables come first so each foreign key
-- points at a table that already exists.

CREATE TABLE Publisher (
  PublisherID  NUMBER(10),
  Name         VARCHAR2(100)  NOT NULL,
  Address      VARCHAR2(200),
  Phone        VARCHAR2(20),
  Email        VARCHAR2(100),
  CONSTRAINT pk_publisher       PRIMARY KEY (PublisherID),
  CONSTRAINT uq_publisher_email UNIQUE (Email)
);

CREATE TABLE Author (
  AuthorID   NUMBER(10),
  FirstName  VARCHAR2(50)  NOT NULL,
  LastName   VARCHAR2(50)  NOT NULL,
  CONSTRAINT pk_author PRIMARY KEY (AuthorID)
);

CREATE TABLE Member (
  MemberID        NUMBER(10),
  FirstName       VARCHAR2(50)   NOT NULL,
  LastName        VARCHAR2(50)   NOT NULL,
  Email           VARCHAR2(100)  NOT NULL,
  Phone           VARCHAR2(20),
  MembershipDate  DATE           DEFAULT SYSDATE NOT NULL,
  CONSTRAINT pk_member       PRIMARY KEY (MemberID),
  CONSTRAINT uq_member_email UNIQUE (Email)
);

CREATE TABLE Staff (
  StaffID    NUMBER(10),
  FirstName  VARCHAR2(50)   NOT NULL,
  LastName   VARCHAR2(50)   NOT NULL,
  Position   VARCHAR2(50)   NOT NULL,
  Email      VARCHAR2(100)  NOT NULL,
  CONSTRAINT pk_staff       PRIMARY KEY (StaffID),
  CONSTRAINT uq_staff_email UNIQUE (Email)
);

CREATE TABLE Book (
  BookID       NUMBER(10),
  Title        VARCHAR2(200)  NOT NULL,
  ISBN         VARCHAR2(20)   NOT NULL,
  Genre        VARCHAR2(50)   DEFAULT 'Unclassified' NOT NULL,
  AuthorID     NUMBER(10)     NOT NULL,
  PublisherID  NUMBER(10)     NOT NULL,
  CONSTRAINT pk_book           PRIMARY KEY (BookID),
  CONSTRAINT uq_book_isbn      UNIQUE (ISBN),
  CONSTRAINT fk_book_author    FOREIGN KEY (AuthorID)    REFERENCES Author (AuthorID),
  CONSTRAINT fk_book_publisher FOREIGN KEY (PublisherID) REFERENCES Publisher (PublisherID)
);

CREATE TABLE Loan (
  LoanID      NUMBER(10),
  BookID      NUMBER(10)  NOT NULL,
  MemberID    NUMBER(10)  NOT NULL,
  StaffID     NUMBER(10)  NOT NULL,
  LoanDate    DATE        DEFAULT SYSDATE NOT NULL,
  DueDate     DATE        NOT NULL,
  ReturnDate  DATE,
  CONSTRAINT pk_loan        PRIMARY KEY (LoanID),
  CONSTRAINT fk_loan_book   FOREIGN KEY (BookID)   REFERENCES Book (BookID),
  CONSTRAINT fk_loan_member FOREIGN KEY (MemberID) REFERENCES Member (MemberID),
  CONSTRAINT fk_loan_staff  FOREIGN KEY (StaffID)  REFERENCES Staff (StaffID),
  CONSTRAINT ck_loan_due    CHECK (DueDate >= LoanDate),
  CONSTRAINT ck_loan_return CHECK (ReturnDate >= LoanDate)
);
