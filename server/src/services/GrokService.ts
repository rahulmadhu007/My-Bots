import OpenAI from 'openai';
import { env } from '../config/env.js';
import { extractJson } from '../utils/json.js';
import { withExponentialBackoff } from '../utils/retry.js';

export interface GrokChatOptions {
  system: string;
  user: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
  jsonMode?: boolean;
  retries?: number;
}

export interface GrokStreamOptions extends GrokChatOptions {
  onToken?: (token: string) => void;
}

/**
 * Reusable Grok client (OpenAI-compatible SDK).
 * All agents must call Grok through this service — never directly.
 */
export class GrokService {
  private readonly client: OpenAI;
  private readonly defaultModel: string;

  constructor(
    apiKey: string = env.grokApiKey,
    baseURL: string = env.grokBaseUrl,
    model: string = env.grokModel,
  ) {
    this.client = new OpenAI({
      apiKey: apiKey || 'missing-key',
      baseURL,
    });
    this.defaultModel = model;
  }

  async chat(options: GrokChatOptions): Promise<string> {
    if (!env.grokApiKey) {
      throw new Error('GROK_API_KEY is not configured');
    }

    return withExponentialBackoff(
      async () => {
        const response = await this.client.chat.completions.create({
          model: options.model ?? this.defaultModel,
          temperature: options.temperature ?? 0.2,
          max_tokens: options.maxTokens ?? 2048,
          response_format: options.jsonMode ? { type: 'json_object' } : undefined,
          messages: [
            { role: 'system', content: options.system },
            { role: 'user', content: options.user },
          ],
        });

        const content = response.choices[0]?.message?.content;
        if (!content) {
          throw new Error('Grok returned an empty response');
        }
        return content;
      },
      { retries: options.retries ?? 3 },
    );
  }

  async chatJson<T>(options: GrokChatOptions): Promise<T> {
    const content = await this.chat({ ...options, jsonMode: true });
    return extractJson<T>(content);
  }

  async stream(options: GrokStreamOptions): Promise<string> {
    if (!env.grokApiKey) {
      throw new Error('GROK_API_KEY is not configured');
    }

    return withExponentialBackoff(
      async () => {
        const stream = await this.client.chat.completions.create({
          model: options.model ?? this.defaultModel,
          temperature: options.temperature ?? 0.2,
          max_tokens: options.maxTokens ?? 2048,
          stream: true,
          messages: [
            { role: 'system', content: options.system },
            { role: 'user', content: options.user },
          ],
        });

        let full = '';
        for await (const chunk of stream) {
          const token = chunk.choices[0]?.delta?.content ?? '';
          if (token) {
            full += token;
            options.onToken?.(token);
          }
        }

        if (!full) {
          throw new Error('Grok stream returned an empty response');
        }
        return full;
      },
      { retries: options.retries ?? 2 },
    );
  }
}

export const grokService = new GrokService();
