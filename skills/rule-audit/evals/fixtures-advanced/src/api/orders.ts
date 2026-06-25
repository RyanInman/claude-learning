import { Request, Response } from "express";
import { db } from "../db";
import { orderSchema } from "../schemas";

export async function createOrder(req: Request, res: Response) {
  const parsed = orderSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "invalid" });
  const rows = await db.query("INSERT INTO orders (item) VALUES ($1)", [parsed.data.item]);
  return res.json(rows);
}
