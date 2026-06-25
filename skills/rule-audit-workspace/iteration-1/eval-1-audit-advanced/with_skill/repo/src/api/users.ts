import { db } from "../db";

export async function findUser(req, res) {
  console.log("query", req.query.name);
  const rows = await db.query(`SELECT * FROM users WHERE name = '${req.query.name}'`);
  return res.json(rows);
}
