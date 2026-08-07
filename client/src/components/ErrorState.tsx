import { AlertCircle, RotateCcw } from 'lucide-react';
import { motion } from 'framer-motion';

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass mx-auto mt-8 w-full max-w-2xl rounded-3xl p-6 shadow-glass"
      role="alert"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 text-ember" aria-hidden />
        <div className="flex-1">
          <h2 className="font-semibold">We couldn't find a great match</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">{message}</p>
          <button
            type="button"
            onClick={onRetry}
            className="focus-ring mt-4 inline-flex items-center gap-2 rounded-2xl bg-accent px-4 py-2.5 text-sm font-semibold text-ink-950"
          >
            <RotateCcw className="h-4 w-4" aria-hidden />
            Retry search
          </button>
        </div>
      </div>
    </motion.div>
  );
}
