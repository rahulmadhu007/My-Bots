import { BaseAgent } from '../types/agents.js';
import type { AgentContext, AgentResult, IntentResult } from '../types/index.js';
import { grokService } from '../services/GrokService.js';

const SYSTEM_PROMPT = `You are IntentAgent in a YouTube semantic search pipeline.
Analyze the user request and extract structured intent.
Return ONLY valid JSON with this exact shape:
{
  "topic": "string",
  "intent": "string",
  "mood": "string",
  "duration": "short" | "medium" | "long" | "any",
  "language": "string",
  "freshness": "latest" | "recent" | "any",
  "contentTypes": ["trailer"|"tutorial"|"music"|"podcast"|"comedy"|"gameplay"|"interview"|"livestream"|"educational"|"documentary"|"animation"|"movie_clip"|"shorts"|"ambience"|"general"],
  "isOfficial": boolean,
  "isShorts": boolean,
  "keywords": ["string"]
}
Rules:
- Infer mood from tone (relaxing, funny, informative, exciting, etc.)
- Detect content types when clear (trailer, tutorial, documentary, comedy, etc.)
- Prefer English language unless user specifies another.
- Never include markdown or commentary.`;

export class IntentAgent extends BaseAgent<AgentContext, IntentResult> {
  readonly name = 'IntentAgent';
  readonly description = 'Understands user intent and extracts structured search preferences';

  async execute(context: AgentContext): Promise<AgentResult<IntentResult>> {
    try {
      const intent = await grokService.chatJson<IntentResult>({
        system: SYSTEM_PROMPT,
        user: JSON.stringify({ description: context.userDescription }),
        temperature: 0.1,
        jsonMode: true,
      });

      if (!intent.topic || !intent.intent) {
        return this.fail('Incomplete intent payload', 'Could not understand the request');
      }

      const normalized: IntentResult = {
        topic: intent.topic,
        intent: intent.intent,
        mood: intent.mood || 'neutral',
        duration: intent.duration || 'any',
        language: intent.language || 'English',
        freshness: intent.freshness || 'any',
        contentTypes: Array.isArray(intent.contentTypes) ? intent.contentTypes : ['general'],
        isOfficial: Boolean(intent.isOfficial),
        isShorts: Boolean(intent.isShorts),
        keywords: Array.isArray(intent.keywords) ? intent.keywords : [],
      };

      return this.ok(normalized, 'AI is understanding your request...');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Intent analysis failed';
      return this.fail(message, 'Could not understand your request');
    }
  }
}

export const intentAgent = new IntentAgent();
