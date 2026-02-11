import { z } from "zod";

export const TailorResultSchema = z.object({
  keywords: z.array(z.string()).min(5),
  change_summary: z.array(z.string()).min(3),
  tailored_latex: z.string().min(200),
});

export type TailorResult = z.infer<typeof TailorResultSchema>;
