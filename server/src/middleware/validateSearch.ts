import type { NextFunction, Request, Response } from 'express';
import { z } from 'zod';
import type { ApiErrorResponse } from '../types/index.js';

const searchSchema = z.object({
  description: z
    .string()
    .trim()
    .min(3, 'Description must be at least 3 characters')
    .max(500, 'Description must be 500 characters or fewer'),
});

export function validateSearch(req: Request, res: Response, next: NextFunction): void {
  const parsed = searchSchema.safeParse(req.body);
  if (!parsed.success) {
    const body: ApiErrorResponse = {
      error: 'VALIDATION_ERROR',
      message: parsed.error.issues[0]?.message ?? 'Invalid request body',
    };
    res.status(400).json(body);
    return;
  }

  req.body = parsed.data;
  next();
}
