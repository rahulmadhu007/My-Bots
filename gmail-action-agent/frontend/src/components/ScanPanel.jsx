export default function ScanPanel({ qualityReport, pipelineMeta }) {
  if (!qualityReport && !pipelineMeta) return null

  const reviewed = qualityReport?.reviewed ?? 0
  const overridden = qualityReport?.overridden ?? 0
  const filtered = qualityReport?.filtered_out ?? 0
  const confidence = qualityReport?.average_confidence
  const notes = [
    ...(qualityReport?.notes || []),
    ...(qualityReport?.flags || []).map((f) => `Flag: ${f}`),
  ].slice(0, 5)

  return (
    <section className="scan-panel" aria-labelledby="quality-heading">
      <h2 id="quality-heading" className="section-heading">
        Quality report
      </h2>
      <p className="section-sub">
        Gate summary after classification — noise filtered before you see it.
      </p>

      <div className="quality-grid">
        <div className="quality-stat">
          <span className="quality-stat__label">Reviewed</span>
          <span className="quality-stat__value">{reviewed}</span>
        </div>
        <div className="quality-stat">
          <span className="quality-stat__label">Overridden</span>
          <span className="quality-stat__value">{overridden}</span>
        </div>
        <div className="quality-stat">
          <span className="quality-stat__label">Filtered</span>
          <span className="quality-stat__value">{filtered}</span>
        </div>
        <div className="quality-stat">
          <span className="quality-stat__label">Avg confidence</span>
          <span className="quality-stat__value">
            {typeof confidence === 'number' ? `${Math.round(confidence * 100)}%` : '—'}
          </span>
        </div>
      </div>

      {notes.length > 0 ? (
        <ul className="quality-notes">
          {notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      ) : null}

      {pipelineMeta ? (
        <p className="pipeline-meta">
          {pipelineMeta.emails_fetched ?? 0} fetched ·{' '}
          {pipelineMeta.classified ?? 0} classified ·{' '}
          {pipelineMeta.actionable ?? 0} actionable · mode{' '}
          {pipelineMeta.mode || 'demo'}
        </p>
      ) : null}
    </section>
  )
}
