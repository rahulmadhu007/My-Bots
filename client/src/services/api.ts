import axios, { AxiosError } from 'axios';
import type { SearchErrorPayload, SearchVideoResult } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function searchVideos(description: string): Promise<SearchVideoResult> {
  try {
    const { data } = await api.post<SearchVideoResult>('/search', { description });
    return data;
  } catch (error) {
    if (error instanceof AxiosError && error.response?.data) {
      const payload = error.response.data as SearchErrorPayload;
      const err = new Error(payload.message || 'Search failed') as Error & {
        code?: string;
        stages?: SearchErrorPayload['stages'];
      };
      err.code = payload.error;
      err.stages = payload.stages;
      throw err;
    }
    throw new Error('Unable to reach the search service. Please try again.');
  }
}

export async function getHealth(): Promise<{
  status: string;
  grokConfigured: boolean;
  youtubeConfigured: boolean;
}> {
  const { data } = await api.get('/health');
  return data;
}

export default api;
