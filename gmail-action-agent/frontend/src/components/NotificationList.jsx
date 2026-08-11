import NotificationItem from './NotificationItem.jsx'

export default function NotificationList({
  notifications = [],
  hasScanned,
  busyId,
  onComplete,
  onDismiss,
}) {
  const open = notifications.filter((n) => (n.status || 'open') === 'open')

  return (
    <section className="notifications" aria-labelledby="notifications-heading">
      <h2 id="notifications-heading" className="section-heading">
        Needs your attention
      </h2>
      <p className="section-sub">
        Actionable items only — complete or dismiss when you are done.
      </p>

      {open.length === 0 ? (
        <div className="empty-state">
          <h3>{hasScanned ? 'Inbox is clear' : 'No notifications yet'}</h3>
          <p>
            {hasScanned
              ? 'Nothing open after the latest scan. Run another scan when new mail arrives.'
              : 'Scan your inbox to surface replies, approvals, and follow-ups that need you.'}
          </p>
        </div>
      ) : (
        <ul className="notification-list">
          {open.map((n, index) => (
            <NotificationItem
              key={n.id}
              notification={n}
              index={index}
              busyId={busyId}
              onComplete={onComplete}
              onDismiss={onDismiss}
            />
          ))}
        </ul>
      )}
    </section>
  )
}
