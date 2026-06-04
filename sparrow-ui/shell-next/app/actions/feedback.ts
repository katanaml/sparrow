"use server";

import { save_user_feedback } from "@/lib/db_pool";

export async function save_feedback(email: string, feedbackText: string): Promise<boolean> {
  return save_user_feedback(email, feedbackText);
}