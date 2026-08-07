import type { AgentContext, AgentResult, AgentName } from './index.js';

/**
 * Base contract for all agents in the hierarchical multi-agent system.
 * Agents communicate exclusively via structured JSON (typed objects).
 */
export abstract class BaseAgent<TInput = AgentContext, TOutput = unknown> {
  abstract readonly name: AgentName;
  abstract readonly description: string;

  abstract execute(input: TInput): Promise<AgentResult<TOutput>>;

  protected ok(data: TOutput, message: string): AgentResult<TOutput> {
    return { success: true, data, message };
  }

  protected fail(error: string, message?: string): AgentResult<TOutput> {
    return {
      success: false,
      error,
      message: message ?? error,
    };
  }
}
