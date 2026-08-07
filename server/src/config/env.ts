import dotenv from 'dotenv';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, '../../../.env') });
dotenv.config();

function required(name: string, fallback?: string): string {
  const value = process.env[name] ?? fallback;
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function optional(name: string, fallback: string): string {
  return process.env[name] ?? fallback;
}

export const env = {
  port: Number(optional('PORT', '3001')),
  clientOrigin: optional('CLIENT_ORIGIN', 'http://localhost:5173'),
  grokApiKey: process.env.GROK_API_KEY ?? '',
  grokBaseUrl: optional('GROK_BASE_URL', 'https://api.x.ai/v1'),
  grokModel: optional('GROK_MODEL', 'grok-2-latest'),
  youtubeApiKey: process.env.YOUTUBE_API_KEY ?? '',
  nodeEnv: optional('NODE_ENV', 'development'),
};

export function assertRuntimeSecrets(): void {
  if (!env.grokApiKey) {
    console.warn('[config] GROK_API_KEY is not set. AI agents will fail until configured.');
  }
  if (!env.youtubeApiKey) {
    console.warn('[config] YOUTUBE_API_KEY is not set. YouTube search will fail until configured.');
  }
}

export function requireSecrets(): void {
  required('GROK_API_KEY', env.grokApiKey || undefined);
  required('YOUTUBE_API_KEY', env.youtubeApiKey || undefined);
}
