import { BaseAgent } from '../types/agents.js';
import type {
  AgentContext,
  AgentResult,
  RankedCandidate,
  YouTubeVideoCandidate,
} from '../types/index.js';
import { grokService } from '../services/GrokService.js';

interface RankingResponse {
  rankings: Array<{
    videoId: string;
    score: number;
    reason: string;
  }>;
}

const SYSTEM_PROMPT = `You are CandidateRankingAgent in a YouTube semantic search pipeline.
Rank candidate videos against the ORIGINAL user request.
Return ONLY valid JSON:
{
  "rankings": [
    { "videoId": "string", "score": 0-100, "reason": "string" }
  ]
}
Scoring criteria (weighted judgment):
- Semantic similarity to the original request
- Topic match
- Official / reputable channel signals
- Popularity (views/likes when available)
- Educational quality when relevant
- Clickbait detection (penalize)
- Language match
- Freshness when requested
- Video quality signals (4K, HDR, duration fit)
Rules:
- Include every provided videoId exactly once.
- score must be an integer 0-100.
- Prefer the single best match for immediate playback.
- Never include markdown or commentary.`;

export class CandidateRankingAgent extends BaseAgent<AgentContext, RankedCandidate[]> {
  readonly name = 'CandidateRankingAgent';
  readonly description = 'Ranks YouTube candidates against the original user request using Grok';

  async execute(context: AgentContext): Promise<AgentResult<RankedCandidate[]>> {
    const candidates = context.candidates ?? [];
    if (candidates.length === 0) {
      return this.fail('No candidates', 'No candidates available to rank');
    }

    try {
      const payload = {
        originalRequest: context.userDescription,
        intent: context.intent,
        candidates: candidates.map((c) => ({
          videoId: c.videoId,
          title: c.title,
          channel: c.channel,
          description: c.description.slice(0, 280),
          publishedAt: c.publishedAt,
          viewCount: c.viewCount ?? null,
          likeCount: c.likeCount ?? null,
          durationSeconds: c.durationSeconds ?? null,
        })),
      };

      const response = await grokService.chatJson<RankingResponse>({
        system: SYSTEM_PROMPT,
        user: JSON.stringify(payload),
        temperature: 0.2,
        jsonMode: true,
        maxTokens: 4096,
      });

      const byId = new Map(candidates.map((c) => [c.videoId, c]));
      const ranked: RankedCandidate[] = (response.rankings ?? [])
        .map((r) => {
          const candidate = byId.get(r.videoId);
          if (!candidate) return null;
          return {
            videoId: r.videoId,
            score: Math.max(0, Math.min(100, Math.round(r.score))),
            reason: r.reason || 'Ranked by semantic similarity',
            candidate,
          };
        })
        .filter((r): r is RankedCandidate => r !== null)
        .sort((a, b) => b.score - a.score);

      if (ranked.length === 0) {
        return this.ok(this.heuristicRank(candidates, context), 'Ranking results...');
      }

      // Ensure any missing candidates still appear via heuristic
      const rankedIds = new Set(ranked.map((r) => r.videoId));
      for (const candidate of candidates) {
        if (!rankedIds.has(candidate.videoId)) {
          ranked.push({
            videoId: candidate.videoId,
            score: this.heuristicScore(candidate, context),
            reason: 'Heuristic fallback score',
            candidate,
          });
        }
      }

      ranked.sort((a, b) => b.score - a.score);
      return this.ok(ranked, 'Ranking results...');
    } catch (error) {
      console.error('[CandidateRankingAgent] Falling back to heuristic ranking', error);
      return this.ok(this.heuristicRank(candidates, context), 'Ranking results...');
    }
  }

  private heuristicRank(
    candidates: YouTubeVideoCandidate[],
    context: AgentContext,
  ): RankedCandidate[] {
    return candidates
      .map((candidate) => ({
        videoId: candidate.videoId,
        score: this.heuristicScore(candidate, context),
        reason: 'Heuristic ranking based on metadata overlap and popularity',
        candidate,
      }))
      .sort((a, b) => b.score - a.score);
  }

  private heuristicScore(candidate: YouTubeVideoCandidate, context: AgentContext): number {
    const text = `${candidate.title} ${candidate.description} ${candidate.channel}`.toLowerCase();
    const tokens = context.userDescription
      .toLowerCase()
      .split(/[^a-z0-9]+/)
      .filter((t) => t.length > 2);

    let overlap = 0;
    for (const token of tokens) {
      if (text.includes(token)) overlap += 1;
    }

    const overlapScore = tokens.length > 0 ? (overlap / tokens.length) * 60 : 30;
    const views = candidate.viewCount ?? 0;
    const popularity = Math.min(25, Math.log10(views + 1) * 4);
    const embedBonus = candidate.embeddable ? 10 : 0;
    const officialBonus = /official|vevo|bbc|nat geo|TED/i.test(candidate.channel) ? 5 : 0;

    return Math.round(Math.min(100, overlapScore + popularity + embedBonus + officialBonus));
  }
}

export const candidateRankingAgent = new CandidateRankingAgent();
