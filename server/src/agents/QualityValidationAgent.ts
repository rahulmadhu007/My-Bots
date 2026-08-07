import { BaseAgent } from '../types/agents.js';
import type { AgentContext, AgentResult, RankedCandidate } from '../types/index.js';
import { youtubeService } from '../services/YouTubeService.js';

export interface ValidationResult {
  accepted: boolean;
  selected?: RankedCandidate;
  reason: string;
  shouldRetry: boolean;
}

const CONFIDENCE_THRESHOLD = 70;

export class QualityValidationAgent extends BaseAgent<AgentContext, ValidationResult> {
  readonly name = 'QualityValidationAgent';
  readonly description =
    'Validates embeddability, availability, privacy, and confidence before playback';

  async execute(context: AgentContext): Promise<AgentResult<ValidationResult>> {
    const ranked = context.ranked ?? [];
    if (ranked.length === 0) {
      return this.ok(
        {
          accepted: false,
          reason: 'No ranked candidates available',
          shouldRetry: context.retryCount < context.maxRetries,
        },
        'Preparing video...',
      );
    }

    for (const candidate of ranked) {
      if (candidate.score < CONFIDENCE_THRESHOLD) {
        continue;
      }

      try {
        const validation = await youtubeService.validateVideo(candidate.videoId);
        if (!validation.valid || !validation.video) {
          continue;
        }

        const selected: RankedCandidate = {
          ...candidate,
          candidate: validation.video,
        };

        return this.ok(
          {
            accepted: true,
            selected,
            reason: candidate.reason,
            shouldRetry: false,
          },
          'Preparing video...',
        );
      } catch (error) {
        console.error(
          `[QualityValidationAgent] Validation failed for ${candidate.videoId}`,
          error,
        );
      }
    }

    const best = ranked[0];
    const belowThreshold = !best || best.score < CONFIDENCE_THRESHOLD;
    const canRetry = context.retryCount < context.maxRetries;

    return this.ok(
      {
        accepted: false,
        selected: best,
        reason: belowThreshold
          ? `Best confidence ${best?.score ?? 0} is below threshold ${CONFIDENCE_THRESHOLD}`
          : 'No embeddable public videos passed validation',
        shouldRetry: canRetry,
      },
      'Preparing video...',
    );
  }
}

export const qualityValidationAgent = new QualityValidationAgent();
