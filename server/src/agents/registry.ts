import type { AgentPlugin } from '../types/index.js';

/**
 * Plugin-style agent registry.
 * Future agents (TranscriptAgent, PlaylistAgent, etc.) register here
 * without modifying ManagerAgent orchestration code.
 */
export class AgentRegistry {
  private readonly plugins = new Map<string, AgentPlugin>();

  register(plugin: AgentPlugin): void {
    this.plugins.set(plugin.name, plugin);
  }

  get(name: string): AgentPlugin | undefined {
    return this.plugins.get(name);
  }

  has(name: string): boolean {
    return this.plugins.has(name);
  }

  list(): AgentPlugin[] {
    return [...this.plugins.values()];
  }
}

export const agentRegistry = new AgentRegistry();
