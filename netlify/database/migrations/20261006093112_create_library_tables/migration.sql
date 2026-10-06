CREATE TABLE "books" (
	"id" serial PRIMARY KEY,
	"title" text NOT NULL,
	"author" text NOT NULL,
	"copies" integer NOT NULL,
	"max_borrow_days" integer NOT NULL,
	"category_id" integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE "borrowed_records" (
	"id" serial PRIMARY KEY,
	"user_name" text NOT NULL,
	"user_age" integer NOT NULL,
	"user_gender" text NOT NULL,
	"user_address" text NOT NULL,
	"user_mobile" text NOT NULL,
	"borrow_days" integer NOT NULL,
	"borrow_time" timestamp DEFAULT now() NOT NULL,
	"return_date" timestamp NOT NULL,
	"book_id" integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE "categories" (
	"id" serial PRIMARY KEY,
	"name" text NOT NULL UNIQUE
);
--> statement-breakpoint
ALTER TABLE "books" ADD CONSTRAINT "books_category_id_categories_id_fkey" FOREIGN KEY ("category_id") REFERENCES "categories"("id");--> statement-breakpoint
ALTER TABLE "borrowed_records" ADD CONSTRAINT "borrowed_records_book_id_books_id_fkey" FOREIGN KEY ("book_id") REFERENCES "books"("id");