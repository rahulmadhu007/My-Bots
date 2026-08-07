import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = {
    hasError: false,
    message: '',
  };

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      message: error.message || 'Something went wrong',
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[ErrorBoundary]', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-aurora p-6">
          <div className="glass max-w-md rounded-3xl p-8 text-center shadow-glass">
            <h1 className="font-display text-2xl font-bold">Something went wrong</h1>
            <p className="mt-3 text-sm text-[var(--muted)]">{this.state.message}</p>
            <button
              type="button"
              className="focus-ring mt-6 rounded-2xl bg-accent px-5 py-3 text-sm font-semibold text-ink-950"
              onClick={() => window.location.reload()}
            >
              Reload app
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
