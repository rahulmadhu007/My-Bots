export default function NotificationItem({
  notification,
  index = 0,
  busyId,
  onComplete,
  onDismiss,
}) {
  const {
    id,
    title,
    body,
    urgency = 'medium',
    sender,
    subject,
    received_at: receivedAt,
    action_type: actionType,
    suggested_action: suggestedAction,
    confidence,
  } = notification

  const busy = busyId === id

  return (
    <li
      className={`notification-item notification-item--${urgency}`}
      style={{ animationDelay: `${Math.min(index, 10) * 55}ms` }}
    >
      <div className="notification-item__top">
        <h3 className="notification-item__title">{title || subject || 'Action needed'}</h3>
        <span className={`urgency urgency--${urgency}`}>{urgency}</span>
      </div>

      <div className="notification-item__meta">
        {sender ? (
          <span>
            From <strong>{sender}</strong>
          </span>
        ) : null}
        {subject ? <span>{subject}</span> : null}
        {receivedAt ? <span>{formatWhen(receivedAt)}</span> : null}
      </div>

      {body ? <p className="notification-item__body">{body}</p> : null}

      {suggestedAction ? (
        <p className="notification-item__action">
          <span>Suggested</span>
          {suggestedAction}
        </p>
      ) : null}

      <div className="notification-item__actions">
        <button
          type="button"
          className="btn btn--complete"
          disabled={busy}
          onClick={() => onComplete(id)}
        >
          {busy ? 'Saving…' : 'Complete'}
        </button>
        <button
          type="button"
          className="btn btn--dismiss"
          disabled={busy}
          onClick={() => onDismiss(id)}
        >
          Dismiss
        </button>
      </div>

      <div className="notification-item__footer">
        <span className="action-type">{(actionType || 'other').replace('_', ' ')}</span>
        <span>
          {typeof confidence === 'number'
            ? `${Math.round(confidence * 100)}% confidence`
            : ''}
        </span>
      </div>
    </li>
  )
}

function formatWhen(value) {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}
