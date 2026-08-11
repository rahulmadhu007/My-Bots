export default function Hero({ onScan, scanning, error }) {
  return (
    <section className="hero" aria-labelledby="relay-brand">
      <div className="hero__inner">
        <h1 id="relay-brand" className="hero__brand">
          Relay
        </h1>
        <p className="hero__headline">Only the emails that need you.</p>
        <p className="hero__support">
          A quiet agent pipeline that scans your inbox and surfaces what actually
          requires a reply, approval, or follow-up.
        </p>
        <div className="hero__cta">
          <button
            type="button"
            className={`btn btn--primary${scanning ? ' is-scanning' : ''}`}
            onClick={onScan}
            disabled={scanning}
          >
            {scanning ? 'Scanning inbox…' : 'Scan inbox'}
          </button>
        </div>
        {error ? <p className="hero__error" role="alert">{error}</p> : null}
      </div>
    </section>
  )
}
