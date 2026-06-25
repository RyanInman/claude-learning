import { db } from "../db";
import { logger } from "../logger";
import { profileSchema } from "../schemas";

export async function updateProfile(req, res) {
  const parsed = profileSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "invalid" });
  logger.info("updating profile");
  return res.json(await db.profile.update({ data: parsed.data }));
}
