import { BaseAgent } from '../types/agents.js';
import type { AgentContext, AgentResult, YouTubeVideoCandidate } from '../types/index.js';
import { youtubeService } from '../services/YouTubeService.js';

export class YouTubeSearchAgent extends BaseAgent<AgentContext, YouTubeVideoCandidate[]> {
  readonly name = 'YouTubeSearchAgent';
  readonly description = 'Searches YouTube concurrently for optimized queries and merges candidates';

  async execute(context: AgentContext): Promise<AgentResult<YouTubeVideoCandidate[]>> {
    const queries = context.queries ?? [];
    if (queries.length === 0) {
      return this.fail('No queries provided', 'Search queries are required');
    }

    const unusedQueries = queries.filter((q) => !context.usedQueries.includes(q));
    const activeQueries =
      unusedQueries.length > 0
        ? unusedQueries.slice(0, 3)
        : queries.slice(0, Math.min(3, queries.length));

    try {
      const searchResults = await Promise.all(
        activeQueries.map(async (query) => {
          try {
            return await youtubeService.searchVideos(query, 10);
          } catch (error) {
            console.error(`[YouTubeSearchAgent] Query failed: ${query}`, error);
            return [] as YouTubeVideoCandidate[];
          }
        }),
      );

      const merged = this.dedupe(searchResults.flat());
      if (merged.length === 0) {
        return this.fail('No videos found', 'No matching videos were found on YouTube');
      }

      const details = await youtubeService.getVideoDetails(merged.map((v) => v.videoId));
      const byId = new Map(details.map((d) => [d.videoId, d]));
      const enriched = merged.map((item) => byId.get(item.videoId) ?? item);

      context.usedQueries = [...context.usedQueries, ...activeQueries];

      return this.ok(enriched, 'Searching YouTube...');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'YouTube search failed';
      return this.fail(message, 'YouTube search failed');
    }
  }

  private dedupe(candidates: YouTubeVideoCandidate[]): YouTubeVideoCandidate[] {
    const seen = new Set<string>();
    const unique: YouTubeVideoCandidate[] = [];
    for (const candidate of candidates) {
      if (seen.has(candidate.videoId)) continue;
      seen.add(candidate.videoId);
      unique.push(candidate);
    }
    return unique;
  }
}

export const youtubeSearchAgent = new YouTubeSearchAgent();
