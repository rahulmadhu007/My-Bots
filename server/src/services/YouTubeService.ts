import axios, { type AxiosInstance } from 'axios';
import { env } from '../config/env.js';
import type { YouTubeVideoCandidate } from '../types/index.js';
import { withExponentialBackoff } from '../utils/retry.js';

interface YouTubeSearchItem {
  id: { videoId?: string };
  snippet: {
    title: string;
    description: string;
    channelTitle: string;
    channelId: string;
    publishedAt: string;
    thumbnails: {
      high?: { url: string };
      medium?: { url: string };
      default?: { url: string };
    };
  };
}

interface YouTubeVideoItem {
  id: string;
  snippet: {
    title: string;
    description: string;
    channelTitle: string;
    channelId: string;
    publishedAt: string;
    thumbnails: {
      high?: { url: string };
      medium?: { url: string };
      default?: { url: string };
    };
  };
  contentDetails?: {
    duration?: string;
  };
  statistics?: {
    viewCount?: string;
    likeCount?: string;
  };
  status?: {
    embeddable?: boolean;
    privacyStatus?: string;
    madeForKids?: boolean;
  };
}

function parseIso8601Duration(duration?: string): number | undefined {
  if (!duration) return undefined;
  const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) return undefined;
  const hours = Number(match[1] ?? 0);
  const minutes = Number(match[2] ?? 0);
  const seconds = Number(match[3] ?? 0);
  return hours * 3600 + minutes * 60 + seconds;
}

/**
 * Reusable YouTube Data API v3 client.
 * All YouTube access goes through this service.
 */
export class YouTubeService {
  private readonly http: AxiosInstance;
  private readonly apiKey: string;

  constructor(apiKey: string = env.youtubeApiKey) {
    this.apiKey = apiKey;
    this.http = axios.create({
      baseURL: 'https://www.googleapis.com/youtube/v3',
      timeout: 15000,
    });
  }

  private ensureKey(): void {
    if (!this.apiKey) {
      throw new Error('YOUTUBE_API_KEY is not configured');
    }
  }

  async searchVideos(query: string, maxResults = 10): Promise<YouTubeVideoCandidate[]> {
    this.ensureKey();

    const response = await withExponentialBackoff(() =>
      this.http.get<{ items: YouTubeSearchItem[] }>('/search', {
        params: {
          key: this.apiKey,
          part: 'snippet',
          q: query,
          type: 'video',
          maxResults,
          videoEmbeddable: 'true',
          safeSearch: 'moderate',
        },
      }),
    );

    const items = response.data.items ?? [];
    return items
      .filter((item) => Boolean(item.id.videoId))
      .map((item) => {
        const videoId = item.id.videoId as string;
        return {
          videoId,
          title: item.snippet.title,
          channel: item.snippet.channelTitle,
          channelId: item.snippet.channelId,
          description: item.snippet.description,
          thumbnail:
            item.snippet.thumbnails.high?.url ??
            item.snippet.thumbnails.medium?.url ??
            item.snippet.thumbnails.default?.url ??
            '',
          publishedAt: item.snippet.publishedAt,
          url: `https://www.youtube.com/watch?v=${videoId}`,
        };
      });
  }

  async getVideoDetails(videoIds: string[]): Promise<YouTubeVideoCandidate[]> {
    this.ensureKey();
    if (videoIds.length === 0) return [];

    const uniqueIds = [...new Set(videoIds)];
    const chunks: string[][] = [];
    for (let i = 0; i < uniqueIds.length; i += 50) {
      chunks.push(uniqueIds.slice(i, i + 50));
    }

    const results: YouTubeVideoCandidate[] = [];

    for (const chunk of chunks) {
      const response = await withExponentialBackoff(() =>
        this.http.get<{ items: YouTubeVideoItem[] }>('/videos', {
          params: {
            key: this.apiKey,
            part: 'snippet,contentDetails,statistics,status',
            id: chunk.join(','),
          },
        }),
      );

      for (const item of response.data.items ?? []) {
        results.push({
          videoId: item.id,
          title: item.snippet.title,
          channel: item.snippet.channelTitle,
          channelId: item.snippet.channelId,
          description: item.snippet.description,
          thumbnail:
            item.snippet.thumbnails.high?.url ??
            item.snippet.thumbnails.medium?.url ??
            item.snippet.thumbnails.default?.url ??
            '',
          publishedAt: item.snippet.publishedAt,
          url: `https://www.youtube.com/watch?v=${item.id}`,
          viewCount: item.statistics?.viewCount
            ? Number(item.statistics.viewCount)
            : undefined,
          likeCount: item.statistics?.likeCount
            ? Number(item.statistics.likeCount)
            : undefined,
          durationSeconds: parseIso8601Duration(item.contentDetails?.duration),
          embeddable: item.status?.embeddable ?? false,
          privacyStatus: item.status?.privacyStatus,
          madeForKids: item.status?.madeForKids,
          definition: undefined,
        });
      }
    }

    return results;
  }

  async validateVideo(videoId: string): Promise<{
    valid: boolean;
    reason?: string;
    video?: YouTubeVideoCandidate;
  }> {
    const [video] = await this.getVideoDetails([videoId]);
    if (!video) {
      return { valid: false, reason: 'Video not found or unavailable' };
    }
    if (video.privacyStatus && video.privacyStatus !== 'public') {
      return { valid: false, reason: `Video is ${video.privacyStatus}`, video };
    }
    if (video.embeddable === false) {
      return { valid: false, reason: 'Video is not embeddable', video };
    }
    return { valid: true, video };
  }
}

export const youtubeService = new YouTubeService();
