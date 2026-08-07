import type {
  AgentContext,
  AgentPlugin,
  PipelineStage,
  SearchPipelineResult,
  SearchResultVideo,
} from '../types/index.js';
import { agentRegistry } from './registry.js';
import { intentAgent } from './IntentAgent.js';
import { queryOptimizationAgent } from './QueryOptimizationAgent.js';
import { youtubeSearchAgent } from './YouTubeSearchAgent.js';
import { candidateRankingAgent } from './CandidateRankingAgent.js';
import { qualityValidationAgent } from './QualityValidationAgent.js';
import type { ValidationResult } from './QualityValidationAgent.js';

/**
 * Hierarchical ManagerAgent.
 * Orchestrates specialized sub-agents and supports plugin registration
 * so future agents can be spawned without changing this class's core loop.
 */
export class ManagerAgent {
  private readonly maxRetries = 3;

  constructor() {
    this.registerCoreAgents();
  }

  /**
   * Register additional agents at runtime (plugin-style extensibility).
   * Future: TranscriptAgent, PlaylistAgent, RecommendationAgent, etc.
   */
  spawnAgent(plugin: AgentPlugin): void {
    agentRegistry.register(plugin);
  }

  listAgents(): AgentPlugin[] {
    return agentRegistry.list();
  }

  async run(userDescription: string): Promise<SearchPipelineResult> {
    const stages: PipelineStage[] = [];
    const context: AgentContext = {
      userDescription: userDescription.trim(),
      retryCount: 0,
      maxRetries: this.maxRetries,
      usedQueries: [],
    };

    if (!context.userDescription) {
      return {
        success: false,
        message: 'Please describe the video you want to watch.',
        stages,
        retries: 0,
      };
    }

    // 1) Intent
    const intentStage = this.startStage('IntentAgent', 'AI is understanding your request...');
    stages.push(intentStage);
    const intentResult = await intentAgent.execute(context);
    this.finishStage(intentStage, intentResult.success, intentResult.message, intentResult.data);
    if (!intentResult.success || !intentResult.data) {
      return {
        success: false,
        message: intentResult.message,
        stages,
        retries: 0,
      };
    }
    context.intent = intentResult.data;

    // Optional plugin hooks after intent (future agents)
    await this.runOptionalPlugins(context, stages, 'after_intent');

    // 2) Query optimization
    const queryStage = this.startStage('QueryOptimizationAgent', 'Optimizing search...');
    stages.push(queryStage);
    const queryResult = await queryOptimizationAgent.execute(context);
    this.finishStage(queryStage, queryResult.success, queryResult.message, queryResult.data);
    if (!queryResult.success || !queryResult.data) {
      return {
        success: false,
        message: queryResult.message,
        stages,
        retries: 0,
      };
    }
    context.queries = queryResult.data.queries;

    // Retry loop: search → rank → validate
    while (context.retryCount <= this.maxRetries) {
      const searchStage = this.startStage('YouTubeSearchAgent', 'Searching YouTube...');
      stages.push(searchStage);
      const searchResult = await youtubeSearchAgent.execute(context);
      this.finishStage(searchStage, searchResult.success, searchResult.message, {
        count: searchResult.data?.length ?? 0,
      });

      if (!searchResult.success || !searchResult.data?.length) {
        if (context.retryCount < this.maxRetries) {
          context.retryCount += 1;
          continue;
        }
        return {
          success: false,
          message:
            'We could not find a suitable video for that request. Try a more specific description.',
          stages,
          retries: context.retryCount,
        };
      }
      context.candidates = searchResult.data;

      const rankStage = this.startStage('CandidateRankingAgent', 'Ranking results...');
      stages.push(rankStage);
      const rankResult = await candidateRankingAgent.execute(context);
      this.finishStage(rankStage, rankResult.success, rankResult.message, {
        top: rankResult.data?.slice(0, 3),
      });
      if (!rankResult.success || !rankResult.data?.length) {
        if (context.retryCount < this.maxRetries) {
          context.retryCount += 1;
          continue;
        }
        return {
          success: false,
          message: 'We found videos but could not confidently rank them. Please try again.',
          stages,
          retries: context.retryCount,
        };
      }
      context.ranked = rankResult.data;

      const validateStage = this.startStage('QualityValidationAgent', 'Preparing video...');
      stages.push(validateStage);
      const validation = await qualityValidationAgent.execute(context);
      this.finishStage(validateStage, validation.success, validation.message, validation.data);

      const data = validation.data as ValidationResult | undefined;
      if (data?.accepted && data.selected) {
        context.selected = data.selected;
        await this.runOptionalPlugins(context, stages, 'before_return');

        const video = this.toSearchResult(data.selected);
        return {
          success: true,
          video,
          stages,
          retries: context.retryCount,
        };
      }

      if (data?.shouldRetry && context.retryCount < this.maxRetries) {
        context.retryCount += 1;
        continue;
      }

      return {
        success: false,
        message:
          data?.reason ||
          'We could not find a high-confidence, playable match. Try refining your description.',
        stages,
        retries: context.retryCount,
      };
    }

    return {
      success: false,
      message: 'Search retries exhausted. Please try a different description.',
      stages,
      retries: context.retryCount,
    };
  }

  private registerCoreAgents(): void {
    const core = [
      intentAgent,
      queryOptimizationAgent,
      youtubeSearchAgent,
      candidateRankingAgent,
      qualityValidationAgent,
    ];

    for (const agent of core) {
      this.spawnAgent({
        name: agent.name,
        description: agent.description,
        execute: (ctx) => agent.execute(ctx),
      });
    }
  }

  private async runOptionalPlugins(
    context: AgentContext,
    stages: PipelineStage[],
    phase: string,
  ): Promise<void> {
    const plugins = agentRegistry
      .list()
      .filter((plugin) => plugin.name.startsWith(`plugin:${phase}:`));

    for (const plugin of plugins) {
      const stage = this.startStage(plugin.name, `Running ${plugin.name}...`);
      stages.push(stage);
      try {
        const result = await plugin.execute(context);
        this.finishStage(stage, result.success, result.message, result.data);
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Plugin failed';
        this.finishStage(stage, false, message);
      }
    }
  }

  private startStage(agent: string, message: string): PipelineStage {
    return {
      agent,
      status: 'running',
      message,
      startedAt: new Date().toISOString(),
    };
  }

  private finishStage(
    stage: PipelineStage,
    success: boolean,
    message: string,
    data?: unknown,
  ): void {
    stage.status = success ? 'completed' : 'failed';
    stage.message = message;
    stage.completedAt = new Date().toISOString();
    if (data !== undefined) {
      stage.data = data;
    }
  }

  private toSearchResult(selected: NonNullable<AgentContext['selected']>): SearchResultVideo {
    const c = selected.candidate;
    return {
      videoId: c.videoId,
      title: c.title,
      channel: c.channel,
      description: c.description,
      thumbnail: c.thumbnail,
      url: c.url,
      publishedAt: c.publishedAt,
      confidence: selected.score,
      reason: selected.reason,
    };
  }
}

export const managerAgent = new ManagerAgent();
