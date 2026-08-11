const AGENT_LABELS = {
  orchestrator: 'Orchestrator',
  Orchestrator: 'Orchestrator',
  GmailFetcher: 'GmailFetcher',
  GmailFetcherAgent: 'GmailFetcher',
  ContextAgent: 'Context',
  Context: 'Context',
  ActionClassifier: 'Classifier',
  ActionClassifierAgent: 'Classifier',
  QualityAgent: 'Quality',
  Quality: 'Quality',
  NotificationAgent: 'Notification',
  Notification: 'Notification',
}

function labelFor(agent) {
  if (!agent) return 'Agent'
  return AGENT_LABELS[agent] || agent.replace(/Agent$/i, '')
}

export default function AgentLog({ entries = [], scanning }) {
  const visible = Array.isArray(entries) ? entries : []

  return (
    <section className="agent-log" aria-labelledby="agent-log-heading">
      <h2 id="agent-log-heading" className="section-heading">
        Agent activity
      </h2>
      <p className="section-sub">
        {scanning
          ? 'Pipeline running: GmailFetcher → Context → Classifier → Quality → Notification'
          : 'Orchestrator routing log from the latest scan'}
      </p>

      {visible.length === 0 ? (
        <p className="agent-log__empty">
          {scanning ? 'Waiting for the first agent step…' : 'No pipeline log yet.'}
        </p>
      ) : (
        <ol className="agent-log__list">
          {visible.map((entry, index) => {
            const key = `${entry.timestamp || 't'}-${entry.agent || 'a'}-${index}`
            const level = entry.level || 'info'
            return (
              <li
                key={key}
                className="agent-log__item"
                style={{ animationDelay: `${Math.min(index, 12) * 40}ms` }}
              >
                <span className="agent-log__agent">{labelFor(entry.agent)}</span>
                <span className={`agent-log__level agent-log__level--${level}`}>
                  {level}
                </span>
                <p className="agent-log__message">{entry.message}</p>
              </li>
            )
          })}
        </ol>
      )}
    </section>
  )
}
