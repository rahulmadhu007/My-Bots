export type DurationPreference = 'short' | 'medium' | 'long' | 'any';
export type FreshnessPreference = 'latest' | 'recent' | 'any';
export type ContentType =
  | 'trailer'
  | 'tutorial'
  | 'music'
  | 'podcast'
  | 'comedy'
  | 'gameplay'
  | 'interview'
  | 'livestream'
  | 'educational'
  | 'documentary'
  | 'animation'
  | 'movie_clip'
  | 'shorts'
  | 'ambience'
  | 'general';

export interface IntentResult {
  topic: string;
  intent: string;
  mood: string;
  duration: DurationPreference;
  language: string;
  freshness: FreshnessPreference;
  contentTypes: ContentType[];
  isOfficial: boolean;
  isShorts: boolean;
  keywords: string[];
}

export interface OptimizedQueries {
  queries: string[];
  reasoning: string;
}

export interface YouTubeVideoCandidate {
  videoId: string;
  title: string;
  channel: string;
  channelId: string;
  description: string;
  thumbnail: string;
  publishedAt: string;
  url: string;
  viewCount?: number;
  likeCount?: number;
  durationSeconds?: number;
  embeddable?: boolean;
  privacyStatus?: string;
  madeForKids?: boolean;
  definition?: string;
}

export interface RankedCandidate {
  videoId: string;
  score: number;
  reason: string;
  candidate: YouTubeVideoCandidate;
}

export interface SearchResultVideo {
  videoId: string;
  title: string;
  channel: string;
  description: string;
  thumbnail: string;
  url: string;
  publishedAt: string;
  confidence: number;
  reason: string;
}

export interface SearchPipelineResult {
  success: boolean;
  video?: SearchResultVideo;
  message?: string;
  stages: PipelineStage[];
  retries: number;
}

export interface PipelineStage {
  agent: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  message: string;
  startedAt?: string;
  completedAt?: string;
  data?: unknown;
}

export interface AgentContext {
  userDescription: string;
  intent?: IntentResult;
  queries?: string[];
  candidates?: YouTubeVideoCandidate[];
  ranked?: RankedCandidate[];
  selected?: RankedCandidate;
  retryCount: number;
  maxRetries: number;
  usedQueries: string[];
}

export interface AgentResult<T> {
  success: boolean;
  data?: T;
  error?: string;
  message: string;
}

export type AgentName =
  | 'ManagerAgent'
  | 'IntentAgent'
  | 'QueryOptimizationAgent'
  | 'YouTubeSearchAgent'
  | 'CandidateRankingAgent'
  | 'QualityValidationAgent'
  | string;

export interface AgentPlugin {
  name: AgentName;
  description: string;
  execute: (context: AgentContext) => Promise<AgentResult<unknown>>;
}

export interface SearchRequestBody {
  description: string;
}

export interface ApiSearchResponse {
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

export interface ApiErrorResponse {
  error: string;
  message: string;
  stages?: PipelineStage[];
}
