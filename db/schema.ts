import { pgTable, serial, text, integer, timestamp } from "drizzle-orm/pg-core";

export const categories = pgTable("categories", {
  id: serial().primaryKey(),
  name: text().notNull().unique(),
});

export const books = pgTable("books", {
  id: serial().primaryKey(),
  title: text().notNull(),
  author: text().notNull(),
  copies: integer().notNull(),
  maxBorrowDays: integer("max_borrow_days").notNull(),
  categoryId: integer("category_id")
    .notNull()
    .references(() => categories.id),
});

export const borrowedRecords = pgTable("borrowed_records", {
  id: serial().primaryKey(),
  userName: text("user_name").notNull(),
  userAge: integer("user_age").notNull(),
  userGender: text("user_gender").notNull(),
  userAddress: text("user_address").notNull(),
  userMobile: text("user_mobile").notNull(),
  borrowDays: integer("borrow_days").notNull(),
  borrowTime: timestamp("borrow_time").notNull().defaultNow(),
  returnDate: timestamp("return_date").notNull(),
  bookId: integer("book_id")
    .notNull()
    .references(() => books.id),
});
