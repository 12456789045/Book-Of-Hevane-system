import type { Config } from "@netlify/functions";
import { asc } from "drizzle-orm";
import { db } from "../../db/index.js";
import { categories } from "../../db/schema.js";

export default async () => {
  const rows = await db
    .select({ id: categories.id, name: categories.name })
    .from(categories)
    .orderBy(asc(categories.id));
  return Response.json(rows);
};

export const config: Config = {
  path: "/api/categories",
  method: "GET",
};
