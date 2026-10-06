# Library App

A full-featured library management system with a modern web frontend and REST API.

## Features

- 📚 **9 categories** with 4+ books each
- 💳 **PDF receipts** for every borrow transaction
- 🎨 **Modern responsive frontend** with real-time updates
- 📋 **REST API** with JSON responses
- 🔍 **Case-insensitive book search**
- ✨ **Professional UI** with animations and icons

## Run on Netlify

The site deploys to Netlify as-is: `frontend/` is published as the static site, the
JSON API runs as Netlify Functions (`netlify/functions/`), and data lives in Netlify
Database (Postgres). The schema is defined in `db/schema.ts`, and migrations in
`netlify/database/migrations/` (including the seeded book catalog) are applied
automatically on deploy.

```bash
npm install
netlify dev
```

## Run the legacy Python server locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open the frontend in your browser:

http://127.0.0.1:8000/

## API Endpoints

### JSON API (for frontend)

- `GET /api/categories` - List all categories
- `GET /api/category/{name}/books` - Get books in a category
- `POST /api/borrow?book_title=...` - Borrow a book (JSON body with borrower details)
- `GET /receipt/{record_id}` - Download borrow receipt as PDF

### Plain-text API (CLI/legacy, Python server only)

- `GET /categories` - List categories (tabulated)
- `GET /category/{name}` - Books in category (tabulated)
- `POST /borrow?book_title=...` - Borrow a book (returns table)
- `GET /stats` - Library statistics
- `GET /common-books` - Most borrowed books
- `GET /borrowers` - All borrow records

## Borrower Details Needed

When borrowing a book:

- Full name
- Age
- Gender
- Address
- Mobile number
- Category
- Book title
- Borrow days (optional, defaults to book's max borrow days)

## PDF Receipt

After successfully borrowing a book, you'll receive:

- Borrower details
- Book information (title, author, category)
- Borrow and return dates
- Borrow duration

Download and keep your receipt as proof of borrowing!
