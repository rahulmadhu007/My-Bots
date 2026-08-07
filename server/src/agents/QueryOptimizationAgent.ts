import { BaseAgent } from '../types/agents.js';
import type { AgentContext, AgentResult, OptimizedQueries } from '../types/index.js';
import { grokService } from '../services/GrokService.js';

const SYSTEM_PROMPT = `You are QueryOptimizationAgent in a YouTube semantic search pipeline.
Given structured intent JSON, generate 3 to 5 optimized YouTube search queries.
Return ONLY valid JSON:
{
  "queries": ["query1", "query2", "query3"],
  "reasoning": "short explanation"
}
Rules:
- Queries must be concise and YouTube-friendly.
- Cover synonyms, formats (4K, HDR, official, tutorial), and related phrasing.
- Prefer high-intent keywords over conversational language.
- Exactly 3 to 5 queries.
- Never include markdown or commentary.`;

export class QueryOptimizationAgent extends BaseAgent<AgentContext, OptimizedQueries> {
  readonly name = 'QueryOptimizationAgent';
  readonly description = 'Generates optimized YouTube search queries from intent JSON';

  async execute(context: AgentContext): Promise<AgentResult<OptimizedQueries>> {
    if (!context.intent) {
      return this.fail('Missing intent', 'Intent must be resolved before query optimization');
    }

    try {
      const result = await grokService.chatJson<OptimizedQueries>({
        system: SYSTEM_PROMPT,
        user: JSON.stringify({
          originalRequest: context.userDescription,
          intent: context.intent,
        }),
        temperature: 0.4,
        jsonMode: true,
      });

      const queries = (result.queries ?? [])
        .map((q) => q.trim())
        .filter(Boolean)
        .slice(0, 5);

      if (queries.length < 3) {
        const fallback = this.buildFallbackQueries(context);
        return this.ok(
          { queries: fallback, reasoning: result.reasoning || 'Fallback query expansion' },
          'Optimizing search...',
        );
      }

      return this.ok(
        { queries, reasoning: result.reasoning || 'Generated optimized queries' },
        'Optimizing search...',
      );
    } catch (error) {
      const fallback = this.buildFallbackQueries(context);
      if (fallback.length >= 3) {
        return this.ok(
          { queries: fallback, reasoning: 'Heuristic fallback after model error' },
          'Optimizing search...',
        );
      }
      const message = error instanceof Error ? error.message : 'Query optimization failed';
      return this.fail(message, 'Could not optimize search queries');
    }
  }

  private buildFallbackQueries(context: AgentContext): string[] {
    const intent = context.intent;
    if (!intent) return [context.userDescription];

    const base = intent.topic;
    const mood = intent.mood && intent.mood !== 'neutral' ? intent.mood : '';
    const type = intent.contentTypes[0] ?? 'video';
    const extras = intent.keywords.slice(0, 2).join(' ');

    return [
      [base, mood, type].filter(Boolean).join(' '),
      [base, 'official', type].filter(Boolean).join(' '),
      [base, extras, 'youtube'].filter(Boolean).join(' '),
      [base, mood, '4K'].filter(Boolean).join(' '),
      context.userDescription.slice(0, 80),
    ]
      .map((q) => q.trim())
      .filter(Boolean)
      .slice(0, 5);
  }
}

export const queryOptimizationAgent = new QueryOptimizationAgent();
