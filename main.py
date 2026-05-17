from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import (
    PlainTextResponse,
    FileResponse,
    JSONResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timedelta
from tabulate import tabulate
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

# -------------------- Setup --------------------
app = FastAPI()
DATABASE_URL = "sqlite:///./library.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# serve frontend static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")


# -------------------- Models --------------------
class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    books = relationship("Book", back_populates="category")


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    author = Column(String)
    copies = Column(Integer)
    max_borrow_days = Column(Integer)
    category_id = Column(Integer, ForeignKey("categories.id"))

    category = relationship("Category", back_populates="books")
    borrowed_records = relationship("BorrowedRecord", back_populates="book")


class BorrowedRecord(Base):
    __tablename__ = "borrowed_records"
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String)
    user_age = Column(Integer)
    user_gender = Column(String)
    user_address = Column(String)
    user_mobile = Column(String)
    borrow_days = Column(Integer)
    borrow_time = Column(DateTime, default=datetime.now)
    return_date = Column(DateTime)

    book_id = Column(Integer, ForeignKey("books.id"))
    book = relationship("Book", back_populates="borrowed_records")


# -------------------- Create DB --------------------
Base.metadata.create_all(bind=engine)


# -------------------- Pydantic --------------------
class Borrower(BaseModel):
    name: str
    age: int
    gender: str
    address: str
    mobile: str
    category: str
    borrow_days: int = None


# -------------------- Seed Data --------------------
def seed_data():
    if session.query(Category).count() > 0:
        return  # don’t reseed if already exists

    categories = {
        "Spiritual": [
            ("Autobiography of Yogi", "Paramahansa Yogananda", 3, 7),
            ("Bhagavad Gita", "Ved Vyasa", 2, 5),
            ("The Power of Now", "Eckhart Tolle", 4, 8),
            ("Meditations", "Marcus Aurelius", 2, 10),
        ],
        "Murder-Mystery": [
            ("Sherlock Holmes", "Arthur Conan Doyle", 2, 5),
            ("Gone Girl", "Gillian Flynn", 1, 4),
            ("The Girl with the Dragon Tattoo", "Stieg Larsson", 3, 7),
            ("And Then There Were None", "Agatha Christie", 2, 6),
        ],
        "Realistic": [
            ("Rich Dad Poor Dad", "Robert Kiyosaki", 4, 10),
            ("The Alchemist", "Paulo Coelho", 2, 6),
            ("1984", "George Orwell", 3, 8),
            ("To Kill a Mockingbird", "Harper Lee", 2, 7),
        ],
        "Science Fiction": [
            ("Dune", "Frank Herbert", 3, 14),
            ("Neuromancer", "William Gibson", 2, 10),
            ("Foundation", "Isaac Asimov", 2, 12),
            ("The Martian", "Andy Weir", 4, 8),
        ],
        "History": [
            ("Sapiens", "Yuval Noah Harari", 2, 12),
            ("Guns, Germs, and Steel", "Jared Diamond", 1, 14),
            ("A Brief History of Time", "Stephen Hawking", 3, 10),
            ("The Silk Roads", "Peter Frankopan", 2, 11),
        ],
        "Self-Help": [
            ("Atomic Habits", "James Clear", 4, 7),
            ("The Power of Habit", "Charles Duhigg", 3, 7),
            ("Thinking, Fast and Slow", "Daniel Kahneman", 2, 9),
            ("Mindset", "Carol S. Dweck", 3, 8),
        ],
        "Fantasy": [
            ("The Hobbit", "J.R.R. Tolkien", 3, 10),
            ("Harry Potter", "J.K. Rowling", 5, 12),
            ("The Name of the Wind", "Patrick Rothfuss", 2, 11),
            ("A Game of Thrones", "George R.R. Martin", 2, 14),
        ],
        "Romance": [
            ("Pride and Prejudice", "Jane Austen", 2, 8),
            ("The Notebook", "Nicholas Sparks", 2, 7),
            ("Outlander", "Diana Gabaldon", 3, 9),
            ("Jane Eyre", "Charlotte Brontë", 2, 8),
        ],
        "Technology": [
            ("The Lean Startup", "Eric Ries", 3, 10),
            ("Zero to One", "Peter Thiel", 2, 9),
            ("Code Complete", "Steve McConnell", 1, 12),
            ("The Pragmatic Programmer", "Dave Thomas & Andy Hunt", 2, 10),
        ],
    }

    for cat, books in categories.items():
        category = Category(name=cat)
        session.add(category)
        session.flush()
        for title, author, copies, max_days in books:
            book = Book(
                title=title,
                author=author,
                copies=copies,
                max_borrow_days=max_days,
                category_id=category.id,
            )
            session.add(book)
    session.commit()


seed_data()


def generate_receipt_pdf(record_id):
    """Generate a PDF receipt for a borrow record"""
    record = (
        session.query(BorrowedRecord).filter(BorrowedRecord.id == record_id).first()
    )
    if not record:
        return None

    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch
    )
    elements = []

    # Title
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#667eea"),
        spaceAfter=10,
        alignment=1,  # center
    )
    elements.append(Paragraph("📚 BookHaven Library", title_style))
    elements.append(Paragraph("Borrow Receipt", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * inch))

    # Receipt header
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
    )
    elements.append(Paragraph(f"Receipt #: {record.id}", header_style))
    elements.append(
        Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", header_style)
    )
    elements.append(Spacer(1, 0.15 * inch))

    # Borrower details
    borrower_data = [
        ["Borrower Details", ""],
        ["Name:", record.user_name],
        ["Age:", str(record.user_age)],
        ["Gender:", record.user_gender],
        ["Address:", record.user_address],
        ["Mobile:", record.user_mobile],
    ]

    borrower_table = Table(borrower_data, colWidths=[1.5 * inch, 3.5 * inch])
    borrower_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#667eea")),
                ("TEXTCOLOR", (0, 0), (1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (1, 0), 11),
                ("BOTTOMPADDING", (0, 0), (1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8f9ff")],
                ),
            ]
        )
    )
    elements.append(borrower_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Book details
    book_data = [
        ["Book Details", ""],
        ["Title:", record.book.title],
        ["Author:", record.book.author],
        ["Category:", record.book.category.name],
    ]

    book_table = Table(book_data, colWidths=[1.5 * inch, 3.5 * inch])
    book_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#764ba2")),
                ("TEXTCOLOR", (0, 0), (1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (1, 0), 11),
                ("BOTTOMPADDING", (0, 0), (1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8f9ff")],
                ),
            ]
        )
    )
    elements.append(book_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Borrow period
    period_data = [
        ["Borrow Period", ""],
        ["Borrow Date:", record.borrow_time.strftime("%Y-%m-%d %H:%M:%S")],
        ["Return Date:", record.return_date.strftime("%Y-%m-%d")],
        ["Duration:", f"{record.borrow_days} days"],
    ]

    period_table = Table(period_data, colWidths=[1.5 * inch, 3.5 * inch])
    period_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#28a745")),
                ("TEXTCOLOR", (0, 0), (1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (1, 0), 11),
                ("BOTTOMPADDING", (0, 0), (1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f0f8f0")],
                ),
            ]
        )
    )
    elements.append(period_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Footer
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        alignment=1,  # center
    )
    elements.append(Paragraph("Thank you for using BookHaven Library!", footer_style))
    elements.append(
        Paragraph("Please return the book on or before the return date.", footer_style)
    )

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


@app.get("/receipt/{record_id}")
def get_receipt(record_id: int):
    """Download receipt as PDF"""
    pdf = generate_receipt_pdf(record_id)
    if not pdf:
        raise HTTPException(status_code=404, detail="Receipt not found")

    pdf.seek(0)
    return StreamingResponse(
        iter([pdf.getvalue()]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=receipt_{record_id}.pdf"
        },
    )


@app.get("/")
def serve_frontend():
    import os

    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    return FileResponse(frontend_path, media_type="text/html")


# -------------------- Endpoints --------------------
@app.get("/categories", response_class=PlainTextResponse)
def get_categories():
    categories = session.query(Category).all()
    table = [[c.id, c.name] for c in categories]
    return tabulate(table, headers=["ID", "Category"], tablefmt="grid")


@app.get("/api/categories")
def api_get_categories():
    categories = session.query(Category).all()
    return JSONResponse([{"id": c.id, "name": c.name} for c in categories])


@app.get("/category/{category_name}", response_class=PlainTextResponse)
def get_books_in_category(category_name: str):
    category = session.query(Category).filter(Category.name == category_name).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    table = [
        [b.id, b.title, b.author, b.copies, b.max_borrow_days] for b in category.books
    ]
    return tabulate(
        table,
        headers=["Book ID", "Title", "Author", "Available Copies", "Max Borrow Days"],
        tablefmt="grid",
    )


@app.get("/api/category/{category_name}/books")
def api_get_books_in_category(category_name: str):
    category = session.query(Category).filter(Category.name == category_name).first()
    if not category:
        return JSONResponse({"error": "Category not found"}, status_code=404)
    books = [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "copies": b.copies,
            "max_borrow_days": b.max_borrow_days,
        }
        for b in category.books
    ]
    return JSONResponse({"category": category.name, "books": books})


@app.post("/borrow", response_class=PlainTextResponse)
def borrow_book(borrower: Borrower, book_title: str = Query(...)):
    # normalize user input: trim whitespace and perform case-insensitive matching
    normalized_title = (book_title or "").strip()
    if not normalized_title:
        raise HTTPException(
            status_code=400,
            detail="book_title query parameter is required and must not be empty",
        )

    category = (
        session.query(Category).filter(Category.name == borrower.category).first()
    )
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category")
    # match titles case-insensitively to be resilient to capitalization and extra spaces
    book = (
        session.query(Book)
        .filter(
            Book.category_id == category.id,
            func.lower(Book.title) == normalized_title.lower(),
        )
        .first()
    )
    if not book:
        raise HTTPException(
            status_code=404,
            detail=f"Book '{normalized_title}' not found in category '{category.name}'",
        )

    if book.copies <= 0:
        raise HTTPException(status_code=409, detail="No copies left to borrow")

    # update copies
    book.copies -= 1
    borrow_days = borrower.borrow_days or book.max_borrow_days
    record = BorrowedRecord(
        user_name=borrower.name,
        user_age=borrower.age,
        user_gender=borrower.gender,
        user_address=borrower.address,
        user_mobile=borrower.mobile,
        borrow_days=borrow_days,
        borrow_time=datetime.now(),
        return_date=datetime.now() + timedelta(days=borrow_days),
        book=book,
    )
    session.add(record)
    session.commit()

    table = [
        [
            borrower.name,
            book.title,
            book.author,
            borrow_days,
            record.borrow_time.strftime("%Y-%m-%d %H:%M:%S"),
            record.return_date.strftime("%Y-%m-%d %H:%M:%S"),
            book.copies,
        ]
    ]
    return tabulate(
        table,
        headers=[
            "Borrower",
            "Book",
            "Author",
            "Days",
            "Borrow Time",
            "Return Date",
            "Remaining Copies",
        ],
        tablefmt="grid",
    )


@app.post("/api/borrow")
def api_borrow_book(borrower: Borrower, book_title: str = Query(...)):
    # normalize user input: trim whitespace and perform case-insensitive matching
    normalized_title = (book_title or "").strip()
    if not normalized_title:
        return JSONResponse(
            {"error": "book_title query parameter is required and must not be empty"},
            status_code=400,
        )

    category = (
        session.query(Category).filter(Category.name == borrower.category).first()
    )
    if not category:
        return JSONResponse({"error": "Invalid category"}, status_code=400)

    book = (
        session.query(Book)
        .filter(
            Book.category_id == category.id,
            func.lower(Book.title) == normalized_title.lower(),
        )
        .first()
    )
    if not book:
        return JSONResponse(
            {
                "error": f"Book '{normalized_title}' not found in category '{category.name}'"
            },
            status_code=404,
        )

    if book.copies <= 0:
        return JSONResponse({"error": "No copies left to borrow"}, status_code=409)

    book.copies -= 1
    borrow_days = borrower.borrow_days or book.max_borrow_days
    record = BorrowedRecord(
        user_name=borrower.name,
        user_age=borrower.age,
        user_gender=borrower.gender,
        user_address=borrower.address,
        user_mobile=borrower.mobile,
        borrow_days=borrow_days,
        borrow_time=datetime.now(),
        return_date=datetime.now() + timedelta(days=borrow_days),
        book=book,
    )
    session.add(record)
    session.commit()

    return JSONResponse(
        {
            "borrower": borrower.name,
            "book": book.title,
            "author": book.author,
            "days": borrow_days,
            "borrow_time": record.borrow_time.strftime("%Y-%m-%d %H:%M:%S"),
            "return_date": record.return_date.strftime("%Y-%m-%d %H:%M:%S"),
            "remaining_copies": book.copies,
            "record_id": record.id,
        }
    )


@app.get("/stats", response_class=PlainTextResponse)
def get_stats():
    total_categories = session.query(func.count(Category.id)).scalar()
    total_books = session.query(func.count(Book.id)).scalar()
    total_borrowed = session.query(func.count(BorrowedRecord.id)).scalar()
    total_users = session.query(
        func.count(func.distinct(BorrowedRecord.user_name))
    ).scalar()

    table = [[total_categories, total_books, total_borrowed, total_users]]
    return tabulate(
        table,
        headers=["Categories", "Books", "Borrowed Records", "Unique Borrowers"],
        tablefmt="grid",
    )


@app.get("/common-books", response_class=PlainTextResponse)
def get_common_books():
    results = (
        session.query(Book.title, func.count(func.distinct(BorrowedRecord.user_name)))
        .join(BorrowedRecord, Book.id == BorrowedRecord.book_id)
        .group_by(Book.title)
        .having(func.count(func.distinct(BorrowedRecord.user_name)) > 1)
        .all()
    )

    if not results:
        return "No common books borrowed by multiple users yet."

    table = [[title, count] for title, count in results]
    return tabulate(
        table, headers=["Book Title", "Borrowed by # Users"], tablefmt="grid"
    )


@app.get("/borrowers", response_class=PlainTextResponse)
def get_all_borrowers():
    """Show all borrowers with the book they borrowed"""
    records = (
        session.query(
            BorrowedRecord.user_name,
            BorrowedRecord.user_age,
            BorrowedRecord.user_gender,
            BorrowedRecord.user_address,
            BorrowedRecord.user_mobile,
            Book.title,
            Book.author,
            Category.name.label("category"),
            BorrowedRecord.borrow_days,
            BorrowedRecord.borrow_time,
            BorrowedRecord.return_date,
        )
        .join(Book, BorrowedRecord.book_id == Book.id)
        .join(Category, Book.category_id == Category.id)
        .all()
    )

    if not records:
        return "No borrowers yet."

    table = [
        [
            r.user_name,
            r.user_age,
            r.user_gender,
            r.user_address,
            r.user_mobile,
            r.title,
            r.author,
            r.category,
            r.borrow_days,
            r.borrow_time.strftime("%Y-%m-%d %H:%M:%S"),
            r.return_date.strftime("%Y-%m-%d %H:%M:%S"),
        ]
        for r in records
    ]

    return tabulate(
        table,
        headers=[
            "Name",
            "Age",
            "Gender",
            "Address",
            "Mobile",
            "Book",
            "Author",
            "Category",
            "Days",
            "Borrow Time",
            "Return Date",
        ],
        tablefmt="grid",
    )
