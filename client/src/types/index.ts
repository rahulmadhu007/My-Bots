export interface PipelineStage {
  agent: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  message: string;
  startedAt?: string;
  completedAt?: string;
  data?: unknown;
}

export interface SearchVideoResult {
  videoId: string;
  title: string;
  channel: string;
  description: string;
  thumbnail: string;
  url: string;
  publishedAt: string;
  confidence?: number;
  reason?: string;
  stages?: PipelineStage[];
}

export interface SearchErrorPayload {
  error: string;
  message: string;
  stages?: PipelineStage[];
}

export interface RecentSearch {
  id: string;
  query: string;
  timestamp: number;
  videoId?: string;
  title?: string;
}

export type ThemeMode = 'dark' | 'light';

export type SearchProgressStep =
  | 'understanding'
  | 'optimizing'
  | 'searching'
  | 'ranking'
  | 'preparing'
  | 'done';
