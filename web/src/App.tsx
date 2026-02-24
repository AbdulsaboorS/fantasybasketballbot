import { useState } from 'react'
import { RefreshCw, Play, XCircle, Sparkles, Loader2, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

const API_BASE = '/api'

type Suggestions = {
  ir: string[]
  lineup: string[]
  streaming: string[]
}

type TeamInfo = {
  name: string
  record: string
}

type AnalyzeResponse = Suggestions & {
  team: TeamInfo
}

type UrgentSwap = {
  starter_name: string
  starter_status: string
  starter_ppg: number
  replacement_name: string
  replacement_ppg: number
  starter_player_id: number
  replacement_player_id: number
  starter_slot: string
}

type QuestionablePlayer = {
  name: string
  status: string
  ppg: number
}

type LineupStatus = {
  urgent_swaps: UrgentSwap[]
  questionable: QuestionablePlayer[]
  no_game_swaps: UrgentSwap[]
}

function StatusBadge({ status }: { status: string }) {
  const s = status.toUpperCase()
  if (s === 'OUT' || s === 'DOUBTFUL') {
    return (
      <span className="inline-block rounded px-1.5 py-0.5 text-xs font-semibold bg-red-900/60 text-red-300 ml-1">
        {status}
      </span>
    )
  }
  if (s === 'DTD' || s === 'QUESTIONABLE') {
    return (
      <span className="inline-block rounded px-1.5 py-0.5 text-xs font-semibold bg-yellow-900/60 text-yellow-300 ml-1">
        {status}
      </span>
    )
  }
  return (
    <span className="inline-block rounded px-1.5 py-0.5 text-xs font-semibold bg-green-900/60 text-green-300 ml-1">
      ACTIVE
    </span>
  )
}

function SwapRow({
  swap,
  onExecute,
  loading,
  rowClass,
  nameClass,
}: {
  swap: UrgentSwap
  onExecute: (swap: UrgentSwap) => void
  loading: boolean
  rowClass: string
  nameClass: string
}) {
  return (
    <div className={cn('flex items-center justify-between rounded-md px-3 py-2 text-sm', rowClass)}>
      <div className="flex flex-wrap items-center gap-1 min-w-0">
        <span className={cn('font-medium', nameClass)}>{swap.starter_name}</span>
        <StatusBadge status={swap.starter_status} />
        <span className="text-zinc-400 mx-1">→</span>
        <span className="text-green-300 font-medium">{swap.replacement_name}</span>
        <span className="text-zinc-500">({swap.replacement_ppg.toFixed(1)} PPG)</span>
      </div>
      <button
        onClick={() => onExecute(swap)}
        disabled={loading}
        className={cn(
          'ml-3 flex-shrink-0 rounded px-2 py-1 text-xs font-semibold bg-orange-600 text-white',
          'hover:bg-orange-500 disabled:opacity-50',
        )}
      >
        Swap now
      </button>
    </div>
  )
}

function GameDayAlerts({
  lineupStatus,
  onExecuteSwap,
  loading,
}: {
  lineupStatus: LineupStatus
  onExecuteSwap: (swap: UrgentSwap) => void
  loading: boolean
}) {
  const { urgent_swaps, questionable, no_game_swaps = [] } = lineupStatus
  const totalAlerts = urgent_swaps.length + no_game_swaps.length

  if (totalAlerts === 0 && questionable.length === 0) {
    return (
      <section className="rounded-lg border border-zinc-700/50 bg-zinc-900/50 p-4">
        <h3 className="mb-2 font-semibold text-zinc-200 flex items-center gap-2">
          Game Day Alerts
        </h3>
        <p className="text-sm text-green-400">All starters are active with games today.</p>
      </section>
    )
  }

  return (
    <section className="rounded-lg border border-orange-700/50 bg-orange-950/20 p-4">
      <h3 className="mb-3 font-semibold text-orange-200 flex items-center gap-2">
        <AlertTriangle className="h-4 w-4" />
        Game Day Alerts
        {totalAlerts > 0 && (
          <span className="rounded-full bg-red-700 px-2 py-0.5 text-xs text-white">
            {totalAlerts} swap{totalAlerts !== 1 ? 's' : ''}
          </span>
        )}
      </h3>

      {urgent_swaps.length > 0 && (
        <div className="mb-3 space-y-2">
          <p className="text-xs text-zinc-500 mb-1">Injury / status alert:</p>
          {urgent_swaps.map((swap, i) => (
            <SwapRow
              key={i}
              swap={swap}
              onExecute={onExecuteSwap}
              loading={loading}
              rowClass="bg-red-950/30 border border-red-800/40"
              nameClass="text-red-300"
            />
          ))}
        </div>
      )}

      {no_game_swaps.length > 0 && (
        <div className="mb-3 space-y-2">
          <p className="text-xs text-zinc-500 mb-1">No game today — bench for someone active:</p>
          {no_game_swaps.map((swap, i) => (
            <SwapRow
              key={i}
              swap={swap}
              onExecute={onExecuteSwap}
              loading={loading}
              rowClass="bg-yellow-950/30 border border-yellow-800/40"
              nameClass="text-yellow-300"
            />
          ))}
        </div>
      )}

      {questionable.length > 0 && (
        <div>
          <p className="text-xs text-zinc-500 mb-1">Monitor (questionable — no auto-swap):</p>
          <ul className="space-y-1 text-sm text-zinc-300">
            {questionable.map((p, i) => (
              <li key={i} className="flex items-center gap-1">
                <span className="text-zinc-500">•</span>
                {p.name}
                <StatusBadge status={p.status} />
                <span className="text-zinc-500 ml-1">({p.ppg.toFixed(1)} PPG)</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

function Section({
  title,
  items,
  emptyMessage,
}: {
  title: string
  items: string[]
  emptyMessage: string
}) {
  return (
    <section className="rounded-lg border border-zinc-700/50 bg-zinc-900/50 p-4">
      <h3 className="mb-2 font-semibold text-zinc-200">{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-zinc-500">{emptyMessage}</p>
      ) : (
        <ul className="space-y-1 text-sm text-zinc-300">
          {items.map((line, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-zinc-500">•</span>
              {line}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function App() {
  const [suggestions, setSuggestions] = useState<Suggestions | null>(null)
  const [teamInfo, setTeamInfo] = useState<TeamInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [executed, setExecuted] = useState<string[] | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [lineupStatus, setLineupStatus] = useState<LineupStatus | null>(null)
  const [lineupLoading, setLineupLoading] = useState(false)
  const [swapResult, setSwapResult] = useState<string | null>(null)

  async function analyze() {
    setLoading(true)
    setError(null)
    setExecuted(null)
    setSwapResult(null)
    try {
      const r = await fetch(`${API_BASE}/analyze`)
      if (!r.ok) throw new Error(await r.text())
      const data: AnalyzeResponse = await r.json()
      setSuggestions({ ir: data.ir, lineup: data.lineup, streaming: data.streaming })
      if (data.team) setTeamInfo(data.team)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      setSuggestions(null)
    } finally {
      setLoading(false)
    }
  }

  async function checkLineup() {
    setLineupLoading(true)
    setError(null)
    setSwapResult(null)
    try {
      const r = await fetch(`${API_BASE}/lineup-status`)
      if (!r.ok) throw new Error(await r.text())
      const data: LineupStatus = await r.json()
      setLineupStatus(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLineupLoading(false)
    }
  }

  async function executeSwap(swap: UrgentSwap) {
    setLineupLoading(true)
    setError(null)
    try {
      const r = await fetch(`${API_BASE}/execute-lineup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          starter_player_id: swap.starter_player_id,
          replacement_player_id: swap.replacement_player_id,
          starter_slot: swap.starter_slot,
        }),
      })
      if (!r.ok) throw new Error(await r.text())
      const data: { success: boolean; message: string } = await r.json()
      setSwapResult(data.message)
      await checkLineup()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLineupLoading(false)
    }
  }

  async function execute() {
    setConfirmOpen(false)
    setLoading(true)
    setError(null)
    try {
      const r = await fetch(`${API_BASE}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: true }),
      })
      if (!r.ok) throw new Error(await r.text())
      const data: { executed: boolean; actions: string[] } = await r.json()
      setExecuted(data.actions ?? [])
      setSuggestions(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  async function generateNew() {
    setLoading(true)
    setError(null)
    setExecuted(null)
    try {
      const r = await fetch(`${API_BASE}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ generate_new: true }),
      })
      if (!r.ok) throw new Error(await r.text())
      const data: { suggestions?: Suggestions } = await r.json()
      if (data.suggestions) setSuggestions(data.suggestions)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  const hasSuggestions =
    suggestions &&
    (suggestions.ir.length > 0 || suggestions.lineup.length > 0 || suggestions.streaming.length > 0)
  const hasStreamingAction =
    suggestions?.streaming.some((s) => s.startsWith('WOULD DROP')) ?? false

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto max-w-2xl px-4 py-10">

        {/* Header */}
        <div className="mb-8">
          {teamInfo ? (
            <>
              <h1 className="mb-0.5 text-2xl font-bold tracking-tight">{teamInfo.name}</h1>
              <p className="text-sm text-zinc-500">Record: {teamInfo.record}</p>
            </>
          ) : (
            <h1 className="mb-2 text-2xl font-bold tracking-tight">ESPN Fantasy Bot</h1>
          )}
          <p className="mt-2 text-zinc-400">
            Analyze your roster and run suggested IR, lineup, and streaming changes.
          </p>
        </div>

        {/* Action buttons */}
        <div className="mb-6 flex flex-wrap gap-3">
          <button
            onClick={analyze}
            disabled={loading}
            className={cn(
              'inline-flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-sm font-medium',
              'text-zinc-200 hover:bg-zinc-700 disabled:opacity-50',
            )}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Analyze roster
          </button>

          <button
            onClick={checkLineup}
            disabled={loading || lineupLoading}
            className={cn(
              'inline-flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-sm font-medium',
              'text-zinc-200 hover:bg-zinc-700 disabled:opacity-50',
            )}
          >
            {lineupLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <AlertTriangle className="h-4 w-4" />
            )}
            Check lineup now
          </button>

          {hasSuggestions && (
            <>
              <button
                onClick={() => setConfirmOpen(true)}
                disabled={loading || !hasStreamingAction}
                className={cn(
                  'inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium',
                  'text-white hover:bg-emerald-500 disabled:opacity-50',
                )}
              >
                <Play className="h-4 w-4" />
                Execute these changes
              </button>
              <button
                onClick={generateNew}
                disabled={loading}
                className={cn(
                  'inline-flex items-center gap-2 rounded-lg bg-zinc-700 px-4 py-2 text-sm font-medium',
                  'text-zinc-200 hover:bg-zinc-600 disabled:opacity-50',
                )}
              >
                <Sparkles className="h-4 w-4" />
                Generate new suggestions
              </button>
              <button
                onClick={() => {
                  setSuggestions(null)
                  setExecuted(null)
                  setError(null)
                }}
                disabled={loading}
                className={cn(
                  'inline-flex items-center gap-2 rounded-lg border border-zinc-600 px-4 py-2 text-sm font-medium',
                  'text-zinc-400 hover:bg-zinc-800 disabled:opacity-50',
                )}
              >
                <XCircle className="h-4 w-4" />
                Decline fully
              </button>
            </>
          )}
        </div>

        {/* Swap result banner */}
        {swapResult && (
          <div className="mb-6 rounded-lg border border-orange-800/50 bg-orange-950/20 p-4 text-sm text-orange-200">
            {swapResult}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-800/50 bg-red-950/30 p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Execution success */}
        {executed && executed.length > 0 && (
          <div className="mb-6 rounded-lg border border-emerald-800/50 bg-emerald-950/20 p-4">
            <h3 className="mb-2 font-semibold text-emerald-200">Execution complete</h3>
            <ul className="space-y-1 text-sm text-emerald-300/90">
              {executed.map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Suggestions + Game Day Alerts */}
        {(suggestions || lineupStatus) && (
          <div className="space-y-4">
            {lineupStatus && (
              <GameDayAlerts
                lineupStatus={lineupStatus}
                onExecuteSwap={executeSwap}
                loading={lineupLoading}
              />
            )}
            {suggestions && (
              <>
                <Section
                  title="IR moves"
                  items={suggestions.ir}
                  emptyMessage="No IR moves suggested."
                />
                <Section
                  title="Lineup changes"
                  items={suggestions.lineup}
                  emptyMessage="No lineup changes suggested."
                />
                <Section
                  title="Streaming"
                  items={suggestions.streaming}
                  emptyMessage="No streaming moves suggested."
                />
              </>
            )}
          </div>
        )}

        {!suggestions && !lineupStatus && !loading && !error && !executed && (
          <p className="text-zinc-500">
            Click &quot;Analyze roster&quot; to load suggestions, or &quot;Check lineup now&quot; for game-day alerts.
          </p>
        )}
      </div>

      {/* Confirm modal */}
      {confirmOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => setConfirmOpen(false)}
        >
          <div
            className="w-full max-w-md rounded-xl border border-zinc-700 bg-zinc-900 p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-2 text-lg font-semibold text-zinc-100">
              Execute these changes?
            </h3>
            <p className="mb-6 text-sm text-zinc-400">
              This will apply streaming add/drop and log IR/lineup suggestions.
              IR and lineup execution are not yet implemented.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmOpen(false)}
                className="rounded-lg border border-zinc-600 px-4 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800"
              >
                Cancel
              </button>
              <button
                onClick={execute}
                disabled={loading}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="inline h-4 w-4 animate-spin" />
                ) : (
                  'Execute'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
