import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';
import type { ToastItem } from '../hooks/useToast';

interface ToastProps {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}

export function ToastViewport({ toasts, onDismiss }: ToastProps) {
  return (
    <div
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-[min(92vw,24rem)] flex-col gap-2"
      aria-live="polite"
      aria-relevant="additions"
    >
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            className={`pointer-events-auto glass flex items-start gap-3 rounded-2xl px-4 py-3 shadow-glass ${
              toast.type === 'error'
                ? 'border-ember/40'
                : toast.type === 'success'
                  ? 'border-accent/40'
                  : ''
            }`}
            role="status"
          >
            <p className="flex-1 text-sm">{toast.message}</p>
            <button
              type="button"
              className="focus-ring rounded-lg p-1 text-[var(--muted)] hover:text-[var(--fg)]"
              aria-label="Dismiss notification"
              onClick={() => onDismiss(toast.id)}
            >
              <X className="h-4 w-4" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
