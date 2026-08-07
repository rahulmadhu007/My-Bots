import type { Request, Response, NextFunction } from 'express';
import { managerAgent } from '../agents/ManagerAgent.js';
import { AppError } from '../middleware/errorHandler.js';
import type { ApiErrorResponse, ApiSearchResponse, SearchRequestBody } from '../types/index.js';
import { env, hasRequiredSecrets } from '../config/env.js';

export async function searchController(
  req: Request,
  res: Response,
  next: NextFunction,
): Promise<void> {
  try {
    if (!hasRequiredSecrets()) {
      throw new AppError(
        'Server is missing GROK_API_KEY or YOUTUBE_API_KEY. Add them to your .env file.',
        503,
        'MISSING_API_KEYS',
      );
    }

    const { description } = req.body as SearchRequestBody;
    const result = await managerAgent.run(description);

    if (!result.success || !result.video) {
      const body: ApiErrorResponse = {
        error: 'NO_MATCH',
        message:
          result.message ||
          'We could not find a confident match. Try refining your description.',
        stages: result.stages,
      };
      res.status(404).json(body);
      return;
    }

    const body: ApiSearchResponse = {
      videoId: result.video.videoId,
      title: result.video.title,
      channel: result.video.channel,
      description: result.video.description,
      thumbnail: result.video.thumbnail,
      url: result.video.url,
      publishedAt: result.video.publishedAt,
      confidence: result.video.confidence,
      reason: result.video.reason,
      stages: result.stages,
    };

    res.status(200).json(body);
  } catch (error) {
    next(error);
  }
}

export function healthController(_req: Request, res: Response): void {
  res.json({
    status: 'ok',
    service: 'ai-youtube-semantic-search',
    grokConfigured: Boolean(env.grokApiKey),
    youtubeConfigured: Boolean(env.youtubeApiKey),
    ready: hasRequiredSecrets(),
    agents: managerAgent.listAgents().map((a) => ({
      name: a.name,
      description: a.description,
    })),
  });
}
