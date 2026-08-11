import { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'
import {
  completeNotification,
  dismissNotification,
  getAuthUrl,
  getNotifications,
  getStatus,
  scanInbox,
} from './api.js'
import AgentLog from './components/AgentLog.jsx'
import Hero from './components/Hero.jsx'
import NotificationList from './components/NotificationList.jsx'
import ScanPanel from './components/ScanPanel.jsx'
import StatusBar from './components/StatusBar.jsx'

const PIPELINE_STAGES = [
  { agent: 'Orchestrator', message: 'Routing scan_inbox to specialist agents…' },
  { agent: 'GmailFetcher', message: 'Fetching recent inbox messages…' },
  { agent: 'Context', message: 'Extracting intent, entities, and deadlines…' },
  { agent: 'Classifier', message: 'Classifying actionable items and urgency…' },
  { agent: 'Quality', message: 'Running quality gate on classifications…' },
  { agent: 'Notification', message: 'Formatting notifications for the feed…' },
]

export default function App() {
  const [status, setStatus] = useState(null)
  const [notifications, setNotifications] = useState([])
  const [agentLog, setAgentLog] = useState([])
  const [qualityReport, setQualityReport] = useState(null)
  const [pipelineMeta, setPipelineMeta] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [busyId, setBusyId] = useState(null)
  const [error, setError] = useState('')
  const [hasScanned, setHasScanned] = useState(false)
  const [showWorkspace, setShowWorkspace] = useState(false)
  const workspaceRef = useRef(null)
  const stageTimers = useRef([])

  const refreshStatus = useCallback(async () => {
    try {
      const next = await getStatus()
      setStatus(next)
    } catch (err) {
      setError(err.message || 'Could not reach the API')
    }
  }, [])

  const loadNotifications = useCallback(async () => {
    try {
      const data = await getNotifications(false)
      setNotifications(data.notifications || [])
      if ((data.notifications || []).length > 0 || data.last_scan) {
        setHasScanned(true)
        setShowWorkspace(true)
      }
    } catch {
      // Backend may be cold; hero still works for first scan.
    }
  }, [])

  useEffect(() => {
    refreshStatus()
    loadNotifications()

    const params = new URLSearchParams(window.location.search)
    if (params.get('auth') === 'success') {
      refreshStatus()
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [refreshStatus, loadNotifications])

  useEffect(() => {
    return () => {
      stageTimers.current.forEach(clearTimeout)
    }
  }, [])

  function clearStageTimers() {
    stageTimers.current.forEach(clearTimeout)
    stageTimers.current = []
  }

  function startOptimisticLog() {
    clearStageTimers()
    setAgentLog([])
    PIPELINE_STAGES.forEach((stage, i) => {
      const timer = setTimeout(() => {
        setAgentLog((prev) => [
          ...prev,
          {
            timestamp: new Date().toISOString(),
            agent: stage.agent,
            level: i === 0 ? 'decision' : 'info',
            message: stage.message,
          },
        ])
      }, 180 + i * 320)
      stageTimers.current.push(timer)
    })
  }

  async function handleScan() {
    setError('')
    setScanning(true)
    setShowWorkspace(true)
    setHasScanned(true)
    startOptimisticLog()

    requestAnimationFrame(() => {
      workspaceRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })

    try {
      const result = await scanInbox({ max_emails: 20 })
      clearStageTimers()
      setNotifications(result.notifications || [])
      setAgentLog(result.agent_log || [])
      setQualityReport(result.quality_report || null)
      setPipelineMeta(result.pipeline_meta || null)
      await refreshStatus()
    } catch (err) {
      clearStageTimers()
      setError(err.message || 'Scan failed')
    } finally {
      setScanning(false)
    }
  }

  async function handleConnect() {
    setConnecting(true)
    setError('')
    try {
      const data = await getAuthUrl()
      if (data.url) {
        window.location.href = data.url
        return
      }
      setError(data.message || 'Gmail OAuth is not configured. Demo mode still works.')
    } catch (err) {
      setError(err.message || 'Could not start Gmail auth')
    } finally {
      setConnecting(false)
    }
  }

  async function handleComplete(id) {
    setBusyId(id)
    setError('')
    try {
      await completeNotification(id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, status: 'completed' } : n)),
      )
      await refreshStatus()
    } catch (err) {
      setError(err.message || 'Could not complete notification')
    } finally {
      setBusyId(null)
    }
  }

  async function handleDismiss(id) {
    setBusyId(id)
    setError('')
    try {
      await dismissNotification(id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, status: 'dismissed' } : n)),
      )
      await refreshStatus()
    } catch (err) {
      setError(err.message || 'Could not dismiss notification')
    } finally {
      setBusyId(null)
    }
  }

  const openNotifications = notifications.filter((n) => (n.status || 'open') === 'open')

  return (
    <div className="app">
      <StatusBar
        status={status}
        connecting={connecting}
        onConnect={handleConnect}
      />

      <Hero onScan={handleScan} scanning={scanning} error={error && !showWorkspace ? error : ''} />

      {showWorkspace ? (
        <div className="workspace" ref={workspaceRef}>
          {error ? (
            <div className="error-banner" role="alert">
              {error}
            </div>
          ) : null}

          <AgentLog entries={agentLog} scanning={scanning} />

          {(qualityReport || pipelineMeta) && !scanning ? (
            <ScanPanel qualityReport={qualityReport} pipelineMeta={pipelineMeta} />
          ) : null}

          {!scanning ? (
            <NotificationList
              notifications={openNotifications}
              hasScanned={hasScanned}
              busyId={busyId}
              onComplete={handleComplete}
              onDismiss={handleDismiss}
            />
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
