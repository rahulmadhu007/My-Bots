import { motion } from 'framer-motion';
import { Copy, ExternalLink, Share2 } from 'lucide-react';
import { useState } from 'react';
import ReactPlayer from 'react-player/youtube';
import type { SearchVideoResult } from '../types';
import { copyToClipboard, formatDate, shareContent } from '../utils/storage';

interface VideoPlayerProps {
  video: SearchVideoResult;
  onNotify: (message: string, type?: 'success' | 'error' | 'info') => void;
}

export function VideoPlayer({ video, onNotify }: VideoPlayerProps) {
  const [ready, setReady] = useState(false);

  const handleCopy = async () => {
    const ok = await copyToClipboard(video.url);
    onNotify(ok ? 'Link copied to clipboard' : 'Could not copy link', ok ? 'success' : 'error');
  };

  const handleShare = async () => {
    const result = await shareContent({
      title: video.title,
      text: `Watch: ${video.title}`,
      url: video.url,
    });
    if (result === 'shared') onNotify('Shared successfully', 'success');
    else if (result === 'copied') onNotify('Link copied for sharing', 'success');
    else onNotify('Sharing is unavailable', 'error');
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: 'easeOut' }}
      className="mx-auto mt-10 w-full max-w-5xl"
      aria-labelledby="video-title"
    >
      <div className="glass overflow-hidden rounded-3xl shadow-glass">
        <div className="relative aspect-video bg-black">
          {!ready && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-ink-950/70">
              <div className="h-10 w-10 animate-spin rounded-full border-2 border-accent/30 border-t-accent" />
            </div>
          )}
          <ReactPlayer
            url={video.url}
            width="100%"
            height="100%"
            playing
            controls
            onReady={() => setReady(true)}
            config={{
              playerVars: {
                autoplay: 1,
                modestbranding: 1,
                rel: 0,
              },
            }}
          />
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
        <div>
          <h2 id="video-title" className="font-display text-2xl font-bold leading-tight sm:text-3xl">
            {video.title}
          </h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            {video.channel}
            <span className="mx-2" aria-hidden>
              ·
            </span>
            {formatDate(video.publishedAt)}
            {typeof video.confidence === 'number' && (
              <>
                <span className="mx-2" aria-hidden>
                  ·
                </span>
                {video.confidence}% match
              </>
            )}
          </p>
          {video.reason && (
            <p className="mt-3 text-sm text-accent-soft dark:text-accent">{video.reason}</p>
          )}
          <p className="mt-4 max-h-40 overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-[var(--muted)]">
            {video.description || 'No description available.'}
          </p>
        </div>

        <aside className="glass rounded-3xl p-4">
          {video.thumbnail && (
            <img
              src={video.thumbnail}
              alt=""
              className="mb-4 aspect-video w-full rounded-2xl object-cover"
            />
          )}
          <div className="flex flex-col gap-2">
            <a
              href={video.url}
              target="_blank"
              rel="noreferrer"
              className="focus-ring inline-flex items-center justify-center gap-2 rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-ink-950 transition hover:bg-accent-soft"
            >
              <ExternalLink className="h-4 w-4" aria-hidden />
              Open on YouTube
            </a>
            <button
              type="button"
              onClick={handleCopy}
              className="focus-ring inline-flex items-center justify-center gap-2 rounded-2xl border border-[var(--border)] px-4 py-3 text-sm font-medium transition hover:border-accent/40"
            >
              <Copy className="h-4 w-4" aria-hidden />
              Copy Link
            </button>
            <button
              type="button"
              onClick={handleShare}
              className="focus-ring inline-flex items-center justify-center gap-2 rounded-2xl border border-[var(--border)] px-4 py-3 text-sm font-medium transition hover:border-accent/40"
            >
              <Share2 className="h-4 w-4" aria-hidden />
              Share
            </button>
          </div>
        </aside>
      </div>
    </motion.section>
  );
}
