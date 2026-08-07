export function VideoSkeleton() {
  return (
    <div className="mx-auto mt-10 w-full max-w-5xl animate-pulse" aria-hidden>
      <div className="glass aspect-video w-full rounded-3xl" />
      <div className="mt-5 space-y-3 px-1">
        <div className="h-7 w-3/4 rounded-xl bg-[var(--border)]" />
        <div className="h-4 w-1/3 rounded-xl bg-[var(--border)]" />
        <div className="h-20 w-full rounded-2xl bg-[var(--border)]" />
      </div>
    </div>
  );
}
