import { motion } from 'framer-motion';
import type { SearchProgressStep } from '../types';

const STEPS: Array<{ key: SearchProgressStep; label: string }> = [
  { key: 'understanding', label: 'AI is understanding your request...' },
  { key: 'optimizing', label: 'Optimizing search...' },
  { key: 'searching', label: 'Searching YouTube...' },
  { key: 'ranking', label: 'Ranking results...' },
  { key: 'preparing', label: 'Preparing video...' },
];

interface SearchProgressProps {
  activeStep: SearchProgressStep;
}

export function SearchProgress({ activeStep }: SearchProgressProps) {
  const activeIndex = STEPS.findIndex((s) => s.key === activeStep);
  const current = STEPS[Math.max(0, activeIndex)] ?? STEPS[0];

  return (
    <div className="glass mx-auto mt-8 w-full max-w-2xl rounded-3xl p-6 shadow-glass" role="status" aria-live="polite">
      <div className="flex items-center gap-3">
        <span className="relative flex h-3 w-3">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-60" />
          <span className="relative inline-flex h-3 w-3 rounded-full bg-accent" />
        </span>
        <p className="font-medium">{current.label}</p>
      </div>

      <div className="mt-5 space-y-3">
        {STEPS.map((step, index) => {
          const done = activeIndex > index || activeStep === 'done';
          const active = activeIndex === index;
          return (
            <div key={step.key} className="flex items-center gap-3">
              <div
                className={`h-2.5 w-2.5 rounded-full ${
                  done ? 'bg-accent' : active ? 'bg-accent-soft' : 'bg-[var(--border)]'
                }`}
              />
              <div className="flex-1">
                <p
                  className={`text-sm ${
                    active || done ? 'text-[var(--fg)]' : 'text-[var(--muted)]'
                  }`}
                >
                  {step.label}
                </p>
                {active && (
                  <motion.div
                    className="mt-2 h-1 origin-left rounded-full bg-accent/80"
                    initial={{ scaleX: 0.2 }}
                    animate={{ scaleX: [0.25, 1, 0.55, 1] }}
                    transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
