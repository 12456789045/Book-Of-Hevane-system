import type { Config, Context } from "@netlify/functions";
import { asc, eq } from "drizzle-orm";
import { db } from "../../db/index.js";
import { books, categories } from "../../db/schema.js";

export default async (_req: Request, context: Context) => {
  let name = context.params.name;
  try {
    name = decodeURIComponent(name);
  } catch {
    // keep the raw value if it isn't valid percent-encoding
  }
  const [category] = await db
    .select()
    .from(categories)
    .where(eq(categories.name, name));
  if (!category) {
    return Response.json({ error: "Category not found" }, { status: 404 });
  }

  const rows = await db
    .select({
      id: books.id,
      title: books.title,
      author: books.author,
      copies: books.copies,
      max_borrow_days: books.maxBorrowDays,
    })
    .from(books)
    .where(eq(books.categoryId, category.id))
    .orderBy(asc(books.id));

  return Response.json({ category: category.name, books: rows });
};

export const config: Config = {
  path: "/api/category/:name/books",
  method: "GET",
};
