import type { Config, Context } from "@netlify/functions";
import { eq } from "drizzle-orm";
import { PDFDocument, StandardFonts, rgb, type PDFFont, type PDFPage } from "pdf-lib";
import { db } from "../../db/index.js";
import { books, borrowedRecords, categories } from "../../db/schema.js";

const hex = (h: string) =>
  rgb(
    parseInt(h.slice(1, 3), 16) / 255,
    parseInt(h.slice(3, 5), 16) / 255,
    parseInt(h.slice(5, 7), 16) / 255,
  );

const formatDateTime = (d: Date) => d.toISOString().slice(0, 19).replace("T", " ");

export default async (_req: Request, context: Context) => {
  const recordId = Number(context.params.id);
  if (!Number.isInteger(recordId)) {
    return Response.json({ error: "Receipt not found" }, { status: 404 });
  }

  const [row] = await db
    .select({ record: borrowedRecords, book: books, category: categories })
    .from(borrowedRecords)
    .innerJoin(books, eq(borrowedRecords.bookId, books.id))
    .innerJoin(categories, eq(books.categoryId, categories.id))
    .where(eq(borrowedRecords.id, recordId));
  if (!row) {
    return Response.json({ error: "Receipt not found" }, { status: 404 });
  }
  const { record, book, category } = row;

  const pdf = await PDFDocument.create();
  const page = pdf.addPage([612, 792]); // US letter
  const regular = await pdf.embedFont(StandardFonts.Helvetica);
  const bold = await pdf.embedFont(StandardFonts.HelveticaBold);

  // Standard PDF fonts only support WinAnsi characters; replace anything else
  const safe = (font: PDFFont, text: string) =>
    [...text].map((ch) => {
      try {
        font.encodeText(ch);
        return ch;
      } catch {
        return "?";
      }
    }).join("");

  const centered = (p: PDFPage, text: string, y: number, font: PDFFont, size: number, color = rgb(0, 0, 0)) => {
    const t = safe(font, text);
    p.drawText(t, { x: (612 - font.widthOfTextAtSize(t, size)) / 2, y, size, font, color });
  };

  let y = 730;
  centered(page, "BookHaven Library", y, bold, 24, hex("#667eea"));
  y -= 30;
  centered(page, "Borrow Receipt", y, bold, 16);
  y -= 35;
  const left = 126;
  page.drawText(`Receipt #: ${record.id}`, { x: left, y, size: 10, font: regular, color: rgb(0.5, 0.5, 0.5) });
  y -= 14;
  page.drawText(`Date: ${formatDateTime(new Date())}`, { x: left, y, size: 10, font: regular, color: rgb(0.5, 0.5, 0.5) });
  y -= 25;

  const table = (title: string, color: string, stripe: string, rows: [string, string][]) => {
    const rowH = 22;
    const colA = 108;
    const width = 360;
    const grid = rgb(0.5, 0.5, 0.5);
    page.drawRectangle({ x: left, y: y - rowH, width, height: rowH, color: hex(color), borderColor: grid, borderWidth: 1 });
    page.drawText(title, { x: left + 6, y: y - 15, size: 11, font: bold, color: rgb(1, 1, 1) });
    y -= rowH;
    rows.forEach(([label, value], i) => {
      page.drawRectangle({
        x: left, y: y - rowH, width, height: rowH,
        color: i % 2 === 0 ? rgb(1, 1, 1) : hex(stripe),
        borderColor: grid, borderWidth: 1,
      });
      page.drawLine({ start: { x: left + colA, y }, end: { x: left + colA, y: y - rowH }, thickness: 1, color: grid });
      page.drawText(label, { x: left + 6, y: y - 15, size: 10, font: regular });
      page.drawText(safe(regular, value), { x: left + colA + 6, y: y - 15, size: 10, font: regular });
      y -= rowH;
    });
    y -= 18;
  };

  table("Borrower Details", "#667eea", "#f8f9ff", [
    ["Name:", record.userName],
    ["Age:", String(record.userAge)],
    ["Gender:", record.userGender],
    ["Address:", record.userAddress],
    ["Mobile:", record.userMobile],
  ]);
  table("Book Details", "#764ba2", "#f8f9ff", [
    ["Title:", book.title],
    ["Author:", book.author],
    ["Category:", category.name],
  ]);
  table("Borrow Period", "#28a745", "#f0f8f0", [
    ["Borrow Date:", formatDateTime(record.borrowTime)],
    ["Return Date:", record.returnDate.toISOString().slice(0, 10)],
    ["Duration:", `${record.borrowDays} days`],
  ]);

  y -= 10;
  centered(page, "Thank you for using BookHaven Library!", y, regular, 9, rgb(0.5, 0.5, 0.5));
  centered(page, "Please return the book on or before the return date.", y - 13, regular, 9, rgb(0.5, 0.5, 0.5));

  const bytes = await pdf.save();
  return new Response(new Uint8Array(bytes), {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename=receipt_${record.id}.pdf`,
    },
  });
};

export const config: Config = {
  path: "/receipt/:id",
  method: "GET",
};
