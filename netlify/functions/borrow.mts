import type { Config } from "@netlify/functions";
import { and, eq, gt, sql } from "drizzle-orm";
import { db } from "../../db/index.js";
import { books, borrowedRecords, categories } from "../../db/schema.js";

interface Borrower {
  name?: string;
  age?: number;
  gender?: string;
  address?: string;
  mobile?: string;
  category?: string;
  borrow_days?: number | null;
}

const error = (message: string, status: number) =>
  Response.json({ error: message }, { status });

const formatDateTime = (d: Date) => d.toISOString().slice(0, 19).replace("T", " ");

export default async (req: Request) => {
  const bookTitle = (new URL(req.url).searchParams.get("book_title") ?? "").trim();
  if (!bookTitle) {
    return error("book_title query parameter is required and must not be empty", 400);
  }

  let borrower: Borrower;
  try {
    borrower = await req.json();
  } catch {
    return error("Invalid JSON body", 400);
  }

  const name = borrower.name?.trim();
  const gender = borrower.gender?.trim();
  const address = borrower.address?.trim();
  const mobile = borrower.mobile?.trim();
  const age = Number(borrower.age);
  if (!name || !gender || !address || !mobile || !borrower.category) {
    return error("name, age, gender, address, mobile and category are required", 400);
  }
  if (!Number.isInteger(age) || age <= 0) {
    return error("age must be a positive whole number", 400);
  }
  if (
    borrower.borrow_days != null &&
    (!Number.isInteger(borrower.borrow_days) || borrower.borrow_days <= 0)
  ) {
    return error("borrow_days must be a positive whole number", 400);
  }

  const [category] = await db
    .select()
    .from(categories)
    .where(eq(categories.name, borrower.category));
  if (!category) return error("Invalid category", 400);

  const [book] = await db
    .select()
    .from(books)
    .where(
      and(
        eq(books.categoryId, category.id),
        sql`lower(${books.title}) = ${bookTitle.toLowerCase()}`,
      ),
    );
  if (!book) {
    return error(`Book '${bookTitle}' not found in category '${category.name}'`, 404);
  }

  // Decrement atomically so concurrent borrows can't take the last copy twice
  const [updated] = await db
    .update(books)
    .set({ copies: sql`${books.copies} - 1` })
    .where(and(eq(books.id, book.id), gt(books.copies, 0)))
    .returning({ copies: books.copies });
  if (!updated) return error("No copies left to borrow", 409);

  const borrowDays = borrower.borrow_days || book.maxBorrowDays;
  const borrowTime = new Date();
  const returnDate = new Date(borrowTime.getTime() + borrowDays * 86_400_000);

  const [record] = await db
    .insert(borrowedRecords)
    .values({
      userName: name,
      userAge: age,
      userGender: gender,
      userAddress: address,
      userMobile: mobile,
      borrowDays,
      borrowTime,
      returnDate,
      bookId: book.id,
    })
    .returning({ id: borrowedRecords.id });

  return Response.json({
    borrower: name,
    book: book.title,
    author: book.author,
    days: borrowDays,
    borrow_time: formatDateTime(borrowTime),
    return_date: formatDateTime(returnDate),
    remaining_copies: updated.copies,
    record_id: record.id,
  });
};

export const config: Config = {
  path: "/api/borrow",
  method: "POST",
};
