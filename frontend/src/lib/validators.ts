import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export type LoginFormData = z.infer<typeof loginSchema>;

export const signupSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters long"),
  full_name: z.string().min(1, "Full name is required"),
  role: z.enum(["admin", "analyst", "investigator", "viewer"]).default("viewer"),
});

export type SignupFormData = z.infer<typeof signupSchema>;
