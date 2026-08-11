export default function StatusBar({ status, connecting, onConnect }) {
  const mode = status?.mode || 'demo'
  const authenticated = Boolean(status?.authenticated)

  return (
    <header className="status-bar">
      <div className="status-bar__left">
        <span className={`mode-badge mode-badge--${mode}`}>
          <span className="mode-badge__dot" aria-hidden="true" />
          {mode === 'gmail' ? 'Gmail connected' : 'Demo inbox'}
        </span>
      </div>
      <div className="status-bar__right">
        {!authenticated ? (
          <button
            type="button"
            className="btn btn--soft"
            onClick={onConnect}
            disabled={connecting || !status?.auth_configured}
            title={
              status?.auth_configured
                ? 'Connect your Gmail account'
                : 'Gmail OAuth not configured — demo mode works without it'
            }
          >
            {connecting ? 'Opening…' : 'Connect Gmail'}
          </button>
        ) : (
          <span className="status-meta">Inbox linked</span>
        )}
      </div>
    </header>
  )
}
