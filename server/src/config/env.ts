import dotenv from 'dotenv';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, '../../../.env') });
dotenv.config();

function optional(name: string, fallback: string): string {
  return process.env[name] ?? fallback;
}

function isUsableSecret(value: string | undefined): boolean {
  if (!value) return false;
  const normalized = value.trim().toLowerCase();
  if (!normalized) return false;
  if (normalized.includes('your_') || normalized.includes('changeme') || normalized.includes('example')) {
    return false;
  }
  return true;
}

const rawGrokKey = process.env.GROK_API_KEY ?? '';
const rawYoutubeKey = process.env.YOUTUBE_API_KEY ?? '';

export const env = {
  port: Number(optional('PORT', '3001')),
  clientOrigin: optional('CLIENT_ORIGIN', 'http://localhost:5173'),
  grokApiKey: isUsableSecret(rawGrokKey) ? rawGrokKey.trim() : '',
  grokBaseUrl: optional('GROK_BASE_URL', 'https://api.x.ai/v1'),
  grokModel: optional('GROK_MODEL', 'grok-2-latest'),
  youtubeApiKey: isUsableSecret(rawYoutubeKey) ? rawYoutubeKey.trim() : '',
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

export function hasRequiredSecrets(): boolean {
  return Boolean(env.grokApiKey && env.youtubeApiKey);
}
