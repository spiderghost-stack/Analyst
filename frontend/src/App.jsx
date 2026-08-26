import { useState, useEffect } from 'react'

// ==========================================
// Données de démonstration (mock data)
// À remplacer par de vrais appels API plus tard
// ==========================================
const MOCK_EVENTS = [
  {
    id: 1,
    name: "CPI US (Inflation)",
    type: "CPI",
    country: "US",
    datetime_utc: "2026-09-10T12:30:00Z",
    importance: "high",
    last_actual: 3.2,
    last_forecast: 3.1,
    last_surprise: 0.1,
  },
  {
    id: 2,
    name: "NFP US (Emploi)",
    type: "NFP",
    country: "US",
    datetime_utc: "2026-09-05T12:30:00Z",
    importance: "high",
    last_actual: 187000,
    last_forecast: 200000,
    last_surprise: -13000,
  },
  {
    id: 3,
    name: "Décision taux Fed",
    type: "FED",
    country: "US",
    datetime_utc: "2026-09-17T18:00:00Z",
    importance: "high",
    last_actual: 5.25,
    last_forecast: 5.25,
    last_surprise: 0,
  },
]

const MOCK_STATS = {
  1: { // CPI
    instruments: [
      {
        name: "EUR/USD",
        symbol: "EURUSD",
        horizons: {
          "1h":  { direction: "down", pct: 66, sample: 47, avg_move: -0.18 },
          "24h": { direction: "down", pct: 58, sample: 47, avg_move: -0.25 },
          "7d":  { direction: "down", pct: 53, sample: 45, avg_move: -0.31 },
        }
      },
      {
        name: "Or (Gold)",
        symbol: "XAUUSD",
        horizons: {
          "1h":  { direction: "up", pct: 61, sample: 47, avg_move: 0.42 },
          "24h": { direction: "up", pct: 55, sample: 47, avg_move: 0.65 },
          "7d":  { direction: "up", pct: 51, sample: 45, avg_move: 0.88 },
        }
      },
      {
        name: "S&P 500",
        symbol: "SPX",
        horizons: {
          "1h":  { direction: "down", pct: 57, sample: 47, avg_move: -0.35 },
          "24h": { direction: "down", pct: 52, sample: 47, avg_move: -0.22 },
          "7d":  { direction: "up", pct: 54, sample: 45, avg_move: 0.15 },
        }
      },
    ],
    distribution: [
      { range: "< -1%", count: 5, direction: "down" },
      { range: "-1% à -0.5%", count: 8, direction: "down" },
      { range: "-0.5% à -0.2%", count: 12, direction: "down" },
      { range: "-0.2% à 0%", count: 6, direction: "down" },
      { range: "0% à +0.2%", count: 5, direction: "up" },
      { range: "+0.2% à +0.5%", count: 7, direction: "up" },
      { range: "+0.5% à +1%", count: 3, direction: "up" },
      { range: "> +1%", count: 1, direction: "up" },
    ],
    explanation: {
      text_before: "Sur",
      sample: 47,
      text_condition: "publications où l'inflation US a surpris à la hausse de plus de 0,1 point depuis 2015",
      instrument: "EUR/USD",
      direction: "baissé",
      direction_class: "down",
      horizon: "l'heure suivante",
      count: 31,
      pct: 66,
    }
  },
  2: { // NFP
    instruments: [
      {
        name: "EUR/USD",
        symbol: "EURUSD",
        horizons: {
          "1h":  { direction: "up", pct: 62, sample: 52, avg_move: 0.22 },
          "24h": { direction: "up", pct: 55, sample: 52, avg_move: 0.18 },
          "7d":  { direction: "down", pct: 51, sample: 50, avg_move: -0.08 },
        }
      },
      {
        name: "Or (Gold)",
        symbol: "XAUUSD",
        horizons: {
          "1h":  { direction: "up", pct: 58, sample: 52, avg_move: 0.35 },
          "24h": { direction: "up", pct: 53, sample: 52, avg_move: 0.28 },
          "7d":  { direction: "flat", pct: 50, sample: 50, avg_move: 0.05 },
        }
      },
      {
        name: "S&P 500",
        symbol: "SPX",
        horizons: {
          "1h":  { direction: "down", pct: 60, sample: 52, avg_move: -0.41 },
          "24h": { direction: "down", pct: 54, sample: 52, avg_move: -0.30 },
          "7d":  { direction: "up", pct: 56, sample: 50, avg_move: 0.20 },
        }
      },
    ],
    distribution: [
      { range: "< -1%", count: 7, direction: "down" },
      { range: "-1% à -0.5%", count: 10, direction: "down" },
      { range: "-0.5% à -0.2%", count: 9, direction: "down" },
      { range: "-0.2% à 0%", count: 5, direction: "down" },
      { range: "0% à +0.2%", count: 6, direction: "up" },
      { range: "+0.2% à +0.5%", count: 8, direction: "up" },
      { range: "+0.5% à +1%", count: 5, direction: "up" },
      { range: "> +1%", count: 2, direction: "up" },
    ],
    explanation: {
      text_before: "Sur",
      sample: 52,
      text_condition: "publications où le NFP US est ressorti inférieur au consensus depuis 2015",
      instrument: "S&P 500",
      direction: "baissé",
      direction_class: "down",
      horizon: "l'heure suivante",
      count: 31,
      pct: 60,
    }
  },
  3: { // FED
    instruments: [
      {
        name: "EUR/USD",
        symbol: "EURUSD",
        horizons: {
          "1h":  { direction: "flat", pct: 50, sample: 12, avg_move: 0.02 },
          "24h": { direction: "down", pct: 58, sample: 12, avg_move: -0.15 },
          "7d":  { direction: "down", pct: 55, sample: 11, avg_move: -0.22 },
        }
      },
      {
        name: "Or (Gold)",
        symbol: "XAUUSD",
        horizons: {
          "1h":  { direction: "up", pct: 58, sample: 12, avg_move: 0.30 },
          "24h": { direction: "up", pct: 55, sample: 12, avg_move: 0.45 },
          "7d":  { direction: "up", pct: 60, sample: 11, avg_move: 0.72 },
        }
      },
      {
        name: "S&P 500",
        symbol: "SPX",
        horizons: {
          "1h":  { direction: "down", pct: 55, sample: 12, avg_move: -0.50 },
          "24h": { direction: "down", pct: 52, sample: 12, avg_move: -0.35 },
          "7d":  { direction: "up", pct: 58, sample: 11, avg_move: 0.28 },
        }
      },
    ],
    distribution: [
      { range: "< -1%", count: 2, direction: "down" },
      { range: "-1% à -0.5%", count: 3, direction: "down" },
      { range: "-0.5% à -0.2%", count: 2, direction: "down" },
      { range: "-0.2% à 0%", count: 1, direction: "down" },
      { range: "0% à +0.2%", count: 1, direction: "up" },
      { range: "+0.2% à +0.5%", count: 2, direction: "up" },
      { range: "+0.5% à +1%", count: 1, direction: "up" },
      { range: "> +1%", count: 0, direction: "up" },
    ],
    explanation: {
      text_before: "Sur",
      sample: 12,
      text_condition: "décisions de taux de la Fed conformes au consensus depuis 2015",
      instrument: "S&P 500",
      direction: "baissé",
      direction_class: "down",
      horizon: "l'heure suivante",
      count: 7,
      pct: 55,
    }
  }
}

// ==========================================
// Composant : Header
// ==========================================
function Header({ onMenuToggle }) {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(interval)
  }, [])

  const utcString = time.toISOString().slice(11, 19)
  const dateString = time.toISOString().slice(0, 10)

  return (
    <header className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <button className="menu-btn" onClick={onMenuToggle} aria-label="Menu">☰</button>
        <div className="header__logo">
          <span className="status-dot status-dot--live"></span>
          ANALYST
        </div>
      </div>
      <div className="header__clock">
        {utcString}<span>UTC</span> — {dateString}
      </div>
    </header>
  )
}

// ==========================================
// Composant : EventList (sidebar)
// ==========================================
function getCountdown(dateStr) {
  const target = new Date(dateStr)
  const now = new Date()
  const diff = target - now

  if (diff <= 0) return "Publié"

  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

  if (days > 0) return `${days}j ${hours}h`
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
}

function EventList({ events, selectedId, onSelect, isOpen }) {
  return (
    <aside className={`sidebar ${isOpen ? 'sidebar--open' : ''}`}>
      <div className="sidebar__title">Prochaines annonces</div>
      {events.map(event => (
        <div
          key={event.id}
          className={`event-item ${selectedId === event.id ? 'event-item--active' : ''}`}
          onClick={() => onSelect(event.id)}
        >
          <div className={`event-item__indicator event-item__indicator--${event.importance}`}></div>
          <div className="event-item__content">
            <div className="event-item__name">{event.name}</div>
            <div className="event-item__meta">
              {new Date(event.datetime_utc).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })}
              {' '}
              {new Date(event.datetime_utc).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })} UTC
            </div>
          </div>
          <div className="event-item__countdown">{getCountdown(event.datetime_utc)}</div>
        </div>
      ))}
    </aside>
  )
}

// ==========================================
// Composant : ProbabilityTable
// ==========================================
function ProbabilityTable({ instruments }) {
  const horizons = ["1h", "24h", "7d"]

  return (
    <div className="prob-section">
      <div className="prob-section__title">Probabilités historiques par instrument et horizon</div>
      <table className="prob-table">
        <thead>
          <tr>
            <th>Instrument</th>
            {horizons.map(h => <th key={h}>{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {instruments.map(inst => (
            <tr key={inst.symbol}>
              <td className="prob-cell__instrument">{inst.name}</td>
              {horizons.map(h => {
                const data = inst.horizons[h]
                const isLowSample = data.sample < 15
                return (
                  <td key={h}>
                    <div className="prob-cell">
                      <span className={`prob-cell__value prob-cell__value--${data.direction}`}>
                        {data.direction === "up" ? "▲" : data.direction === "down" ? "▼" : "—"} {data.pct}%
                      </span>
                      <span className="prob-cell__sample">N = {data.sample}</span>
                      <span className="prob-cell__sample">moy. {data.avg_move > 0 ? '+' : ''}{data.avg_move.toFixed(2)}%</span>
                      {isLowSample && (
                        <div className="warning-badge">⚠ Échantillon faible</div>
                      )}
                    </div>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ==========================================
// Composant : ExplanationText
// ==========================================
function ExplanationText({ data }) {
  return (
    <div className="explanation">
      <p className="explanation__text">
        <span className="explanation__icon">ℹ</span>
        <strong>{data.text_before} {data.sample} {data.text_condition}</strong>, le{' '}
        <strong>{data.instrument}</strong> a{' '}
        <span className={data.direction_class}>{data.direction}</span> dans{' '}
        {data.horizon} dans <strong>{data.count} cas ({data.pct}%)</strong>.
      </p>
      {data.sample < 30 && (
        <div className="warning-badge" style={{ marginTop: '8px' }}>
          ⚠ Échantillon modéré ({data.sample} cas) — Interpréter avec prudence
        </div>
      )}
    </div>
  )
}

// ==========================================
// Composant : DistributionChart
// ==========================================
function DistributionChart({ distribution }) {
  const maxCount = Math.max(...distribution.map(d => d.count), 1)

  return (
    <div className="chart-section">
      <div className="chart-section__title">Distribution des réactions historiques (EUR/USD, +1h)</div>
      <div className="chart-container">
        {distribution.map((d, i) => (
          <div key={i} className="chart-bar" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', position: 'relative' }}>
            <div
              className={`chart-bar__fill chart-bar__fill--${d.direction}`}
              style={{ height: `${(d.count / maxCount) * 100}%`, minHeight: d.count > 0 ? '2px' : '0' }}
            ></div>
            <div className="chart-bar__label">{d.range}</div>
          </div>
        ))}
      </div>
      <div className="chart-legend">
        <div className="chart-legend__item">
          <div className="chart-legend__color" style={{ background: 'var(--color-down)' }}></div>
          Réaction négative
        </div>
        <div className="chart-legend__item">
          <div className="chart-legend__color" style={{ background: 'var(--color-up)' }}></div>
          Réaction positive
        </div>
      </div>
    </div>
  )
}

// ==========================================
// Composant : AnalysisPanel (panneau droit)
// ==========================================
function AnalysisPanel({ event, stats }) {
  if (!event || !stats) {
    return (
      <main className="main-panel">
        <div className="main-panel__empty">
          ← Sélectionnez une annonce pour voir l'analyse
        </div>
      </main>
    )
  }

  const surpriseClass = event.last_surprise > 0 ? 'positive' : event.last_surprise < 0 ? 'negative' : ''
  const surpriseSign = event.last_surprise > 0 ? '+' : ''

  return (
    <main className="main-panel">
      <div className="analysis-header">
        <h1 className="analysis-header__title">{event.name}</h1>
        <div className="analysis-header__subtitle">
          Dernière publication — Réel: {event.last_actual} | Consensus: {event.last_forecast}
        </div>
        {event.last_surprise !== 0 && (
          <div className={`analysis-header__surprise analysis-header__surprise--${surpriseClass}`}>
            Surprise: {surpriseSign}{event.last_surprise}
          </div>
        )}
      </div>

      <ProbabilityTable instruments={stats.instruments} />
      <ExplanationText data={stats.explanation} />
      <DistributionChart distribution={stats.distribution} />
    </main>
  )
}

// ==========================================
// App principal — connecté à l'API FastAPI
// ==========================================
const API_BASE = "http://localhost:8000"

function App() {
  const [events, setEvents] = useState([])
  const [selectedEventId, setSelectedEventId] = useState(null)
  const [selectedStats, setSelectedStats] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadingStats, setLoadingStats] = useState(false)
  const [error, setError] = useState(null)

  // Charger la liste des événements au démarrage
  useEffect(() => {
    fetch(`${API_BASE}/api/events`)
      .then(res => {
        if (!res.ok) throw new Error(`Erreur HTTP ${res.status}`)
        return res.json()
      })
      .then(data => {
        setEvents(data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Erreur chargement événements:", err)
        setError("Impossible de se connecter à l'API. Vérifiez que le backend tourne sur le port 8000.")
        setLoading(false)
      })
  }, [])

  // Charger les stats quand on sélectionne un événement
  useEffect(() => {
    if (!selectedEventId) {
      setSelectedStats(null)
      return
    }

    setLoadingStats(true)
    fetch(`${API_BASE}/api/events/${selectedEventId}/stats`)
      .then(res => {
        if (!res.ok) throw new Error(`Erreur HTTP ${res.status}`)
        return res.json()
      })
      .then(data => {
        setSelectedStats(data)
        setLoadingStats(false)
      })
      .catch(err => {
        console.error("Erreur chargement stats:", err)
        setLoadingStats(false)
      })
  }, [selectedEventId])

  const selectedEvent = events.find(e => e.id === selectedEventId) || null

  const handleSelectEvent = (id) => {
    setSelectedEventId(id)
    setSidebarOpen(false)
  }

  if (error) {
    return (
      <div className="app-layout">
        <Header onMenuToggle={() => {}} />
        <main className="main-panel" style={{ gridColumn: '1 / -1' }}>
          <div className="main-panel__empty" style={{ flexDirection: 'column', gap: '12px' }}>
            <div style={{ color: 'var(--color-down)', fontSize: '16px' }}>⚠ Connexion impossible</div>
            <div style={{ fontSize: '12px', maxWidth: '400px', textAlign: 'center' }}>{error}</div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="app-layout">
      <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />
      <div
        className={`sidebar-overlay ${sidebarOpen ? 'sidebar-overlay--visible' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />
      <EventList
        events={loading ? [] : events}
        selectedId={selectedEventId}
        onSelect={handleSelectEvent}
        isOpen={sidebarOpen}
      />
      {loadingStats ? (
        <main className="main-panel">
          <div className="main-panel__empty">Chargement des statistiques...</div>
        </main>
      ) : (
        <AnalysisPanel event={selectedEvent} stats={selectedStats} />
      )}
    </div>
  )
}

export default App

