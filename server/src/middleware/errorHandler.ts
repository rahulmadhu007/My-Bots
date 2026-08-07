import type { NextFunction, Request, Response } from 'express';
import type { ApiErrorResponse } from '../types/index.js';

export class AppError extends Error {
  statusCode: number;
  code: string;

  constructor(message: string, statusCode = 500, code = 'INTERNAL_ERROR') {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
  }
}

export function notFoundHandler(_req: Request, res: Response): void {
  const body: ApiErrorResponse = {
    error: 'NOT_FOUND',
    message: 'The requested endpoint does not exist.',
  };
  res.status(404).json(body);
}

export function errorHandler(
  err: unknown,
  _req: Request,
  res: Response,
  _next: NextFunction,
): void {
  if (err instanceof AppError) {
    const body: ApiErrorResponse = {
      error: err.code,
      message: err.message,
    };
    res.status(err.statusCode).json(body);
    return;
  }

  console.error('[errorHandler]', err);
  const body: ApiErrorResponse = {
    error: 'INTERNAL_ERROR',
    message: 'Something went wrong. Please try again.',
  };
  res.status(500).json(body);
}
