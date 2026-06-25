import { db } from "../db";

export async function createUser(req, res) {
  console.log("creating user", req.body);
  const body = req.body;
  return res.json(await db.user.create({ data: body }));
}
