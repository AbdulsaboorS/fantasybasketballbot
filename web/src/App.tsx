import { useState, useEffect } from 'react'
import { RefreshCw, Play, XCircle, Sparkles, Loader2, AlertTriangle, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api'
const READ_ONLY = import.meta.env.VITE_READ_ONLY === 'true'

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

type LastRunData = {
  last_run_utc: string | null
  moves_made_today: string[]
  weekly_transactions_used: number
  plan_for_tomorrow: string
  current_record: string
}

// --- Utilities ---

function timeAgo(isoStr: string): string {
  const diffMs = Date.now() - new Date(isoStr).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function parseStreamingString(s: string) {
  const m = s.match(/WOULD DROP (.+?) \(([^)]+)\) FOR (.+?) \(([^)]+)\)/)
  if (m) return { dropName: m[1], dropDetails: m[2], addName: m[3], addDetails: m[4] }
  const m2 = s.match(/dropped (.+?) \(([^)]+)\) for (.+?) \(([^)]+)\)/)
  if (m2) return { dropName: m2[1], dropDetails: m2[2], addName: m2[3], addDetails: m2[4] }
  return null
}

// --- Shared Components ---

function PosBadge({ pos }: { pos: string }) {
  const p = pos.toUpperCase()
  const styles: Record<string, string> = {
    PG: 'bg-blue-700/70 text-blue-200',
    SG: 'bg-cyan-700/70 text-cyan-200',
    SF: 'bg-green-700/70 text-green-200',
    PF: 'bg-orange-700/70 text-orange-200',
    C: 'bg-red-700/70 text-red-200',
    G: 'bg-purple-700/70 text-purple-200',
    F: 'bg-teal-700/70 text-teal-200',
    UT: 'bg-gray-600/70 text-gray-200',
    UTIL: 'bg-gray-600/70 text-gray-200',
    BE: 'bg-zinc-700/70 text-zinc-300',
    IR: 'bg-zinc-800/80 text-zinc-400',
  }
  return (
    <span className={cn('inline-block rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide', styles[p] ?? 'bg-zinc-700/70 text-zinc-300')}>
      {p}
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const s = status.toUpperCase()
  if (s === 'OUT' || s === 'DOUBTFUL')
    return <span className="inline-block rounded px-1.5 py-0.5 text-[10px] font-bold uppercase bg-red-900/70 text-red-300 border border-red-700/50">{s}</span>
  if (s === 'DTD' || s === 'DAY_TO_DAY')
    return <span className="inline-block rounded px-1.5 py-0.5 text-[10px] font-bold uppercase bg-amber-900/70 text-amber-300 border border-amber-700/50">DTD</span>
  if (s === 'QUESTIONABLE')
    return <span className="inline-block rounded px-1.5 py-0.5 text-[10px] font-bold uppercase bg-yellow-900/70 text-yellow-300 border border-yellow-700/50">{s}</span>
  if (s === 'NO GAME')
    return <span className="inline-block rounded px-1.5 py-0.5 text-[10px] font-bold uppercase bg-zinc-700/70 text-zinc-400 border border-zinc-600/50">NO GAME</span>
  return null
}

// --- Last Run Panel ---

function LastRunPanel({ data }: { data: LastRunData }) {
  if (!data.last_run_utc) return null

  const dateStr = new Date(data.last_run_utc).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZoneName: 'short',
  })

  function actionStyle(action: string): { icon: string; cls: string } {
    const a = action.toLowerCase()
    if (a.includes('executed') || a.includes('✅')) return { icon: '✓', cls: 'text-[#00d4aa]' }
    if (a.includes('skipped') || a.includes('⚠️') || a.includes('not yet implemented') || a.includes('limit'))
      return { icon: '!', cls: 'text-amber-400' }
    if (a.includes('failed') || a.includes('❌') || a.includes('error')) return { icon: '✕', cls: 'text-red-400' }
    return { icon: '·', cls: 'text-[#8b949e]' }
  }

  return (
    <section className="rounded-lg border border-[#30363d] bg-[#161b22] p-4 mb-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[10px] font-semibold text-[#8b949e] uppercase tracking-widest flex items-center gap-1.5">
          <Clock className="h-3 w-3" />
          Last Run
        </h3>
        <span className="text-xs text-zinc-300">{timeAgo(data.last_run_utc)}</span>
      </div>
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="text-xs text-[#8b949e]">{dateStr}</span>
        {data.current_record && (
          <span className="rounded-full bg-[#0d1117] border border-[#30363d] px-2 py-0.5 text-xs text-zinc-300 font-medium">
            {data.current_record}
          </span>
        )}
        <span className="text-xs text-[#8b949e]">{data.weekly_transactions_used} tx this week</span>
      </div>
      {data.moves_made_today.length > 0 ? (
        <ul className="space-y-1">
          {data.moves_made_today.map((move, i) => {
            const { icon, cls } = actionStyle(move)
            return (
              <li key={i} className="flex items-start gap-2 text-xs text-zinc-400">
                <span className={cn('font-bold mt-0.5 flex-shrink-0 w-3 text-center', cls)}>{icon}</span>
                <span>{move}</span>
              </li>
            )
          })}
        </ul>
      ) : (
        <p className="text-xs text-[#8b949e]">No moves logged yet today.</p>
      )}
    </section>
  )
}

// --- Streaming Row ---

function StreamingRow({ text }: { text: string }) {
  const parsed = parseStreamingString(text)
  if (!parsed) {
    const isSkip = text.toLowerCase().includes('skipped') || text.toLowerCase().includes('limit')
    const isError = text.toLowerCase().includes('failed') || text.toLowerCase().includes('error')
    return (
      <div className={cn(
        'rounded-md px-3 py-2.5 text-sm border',
        isError ? 'bg-red-950/20 border-red-800/30 text-red-300'
          : isSkip ? 'bg-[#0d1117] border-[#30363d] text-[#8b949e]'
          : 'bg-[#0d1117] border-[#30363d] text-zinc-300'
      )}>
        {text}
      </div>
    )
  }
  return (
    <div className="rounded-md bg-[#0d1117] border border-[#30363d] px-3 py-2.5 text-sm">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase bg-red-900/60 text-red-300 border border-red-800/40">DROP</span>
        <span className="text-red-300 font-medium">{parsed.dropName}</span>
        <span className="text-[#8b949e] text-xs">{parsed.dropDetails}</span>
        <span className="text-[#8b949e] mx-1">→</span>
        <span className="rounded px-1.5 py-0.5 text-[10px] font-bold uppercase bg-[#00d4aa]/20 text-[#00d4aa] border border-[#00d4aa]/30">ADD</span>
        <span className="text-[#00d4aa] font-medium">{parsed.addName}</span>
        <span className="text-[#8b949e] text-xs">{parsed.addDetails}</span>
      </div>
    </div>
  )
}

// --- Suggestion Panels ---

function SuggestionPanel({ title, items, emptyMessage }: { title: string; items: string[]; emptyMessage: string }) {
  return (
    <section className="rounded-lg border border-[#30363d] bg-[#161b22] p-4">
      <h3 className="mb-3 text-[10px] font-semibold text-[#8b949e] uppercase tracking-widest">{title}</h3>
      {items.length === 0 ? (
        <p className="text-sm text-[#8b949e]">{emptyMessage}</p>
      ) : (
        <div className="space-y-1.5">
          {items.map((item, i) => (
            <div key={i} className="flex items-start gap-2 rounded-md bg-[#0d1117] border border-[#30363d] px-3 py-2.5 text-sm">
              <span className="text-[#00d4aa] mt-0.5 flex-shrink-0">›</span>
              <span className="text-zinc-300">{item}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

function StreamingPanel({ items }: { items: string[] }) {
  return (
    <section className="rounded-lg border border-[#30363d] bg-[#161b22] p-4">
      <h3 className="mb-3 text-[10px] font-semibold text-[#8b949e] uppercase tracking-widest">Streaming</h3>
      {items.length === 0 ? (
        <p className="text-sm text-[#8b949e]">No streaming moves suggested.</p>
      ) : (
        <div className="space-y-1.5">
          {items.map((item, i) => <StreamingRow key={i} text={item} />)}
        </div>
      )}
    </section>
  )
}

// --- Game Day Alerts ---

function SwapCard({ swap, onExecute, loading }: { swap: UrgentSwap; onExecute: (s: UrgentSwap) => void; loading: boolean }) {
  const isOut = swap.starter_status === 'OUT' || swap.starter_status === 'DOUBTFUL'
  const isNoGame = swap.starter_status === 'NO GAME'
  return (
    <div className={cn(
      'flex items-center justify-between rounded-md px-3 py-2.5 border',
      isOut ? 'bg-red-950/20 border-red-900/40'
        : isNoGame ? 'bg-zinc-900/50 border-[#30363d]'
        : 'bg-amber-950/20 border-amber-900/40'
    )}>
      <div className="flex items-center gap-2 min-w-0 flex-wrap">
        <PosBadge pos={swap.starter_slot} />
        <StatusBadge status={swap.starter_status} />
        <span className={cn('font-medium text-sm', isOut ? 'text-red-300' : isNoGame ? 'text-zinc-300' : 'text-amber-300')}>
          {swap.starter_name}
        </span>
        <span className="text-[#8b949e] text-xs">({swap.starter_ppg.toFixed(1)} PPG)</span>
        <span className="text-[#8b949e] mx-0.5">→</span>
        <span className="text-[#00d4aa] font-medium text-sm">{swap.replacement_name}</span>
        <span className="text-[#8b949e] text-xs">({swap.replacement_ppg.toFixed(1)} PPG)</span>
      </div>
      {!READ_ONLY && (
        <button
          onClick={() => onExecute(swap)}
          disabled={loading}
          className="ml-3 flex-shrink-0 rounded-md bg-[#00d4aa]/10 border border-[#00d4aa]/30 text-[#00d4aa] px-2.5 py-1 text-xs font-semibold hover:bg-[#00d4aa]/20 disabled:opacity-40"
        >
          Swap
        </button>
      )}
    </div>
  )
}

function GameDayAlerts({ lineupStatus, onExecuteSwap, loading }: {
  lineupStatus: LineupStatus
  onExecuteSwap: (s: UrgentSwap) => void
  loading: boolean
}) {
  const { urgent_swaps, questionable, no_game_swaps = [] } = lineupStatus
  const totalAlerts = urgent_swaps.length + no_game_swaps.length

  if (totalAlerts === 0 && questionable.length === 0) {
    return (
      <section className="rounded-lg border border-[#30363d] bg-[#161b22] p-4">
        <h3 className="mb-2 text-[10px] font-semibold text-[#8b949e] uppercase tracking-widest">Game Day Alerts</h3>
        <p className="text-sm text-[#00d4aa]">All starters active with games today.</p>
      </section>
    )
  }

  return (
    <section className="rounded-lg border border-amber-700/30 bg-[#161b22] p-4">
      <h3 className="mb-3 text-[10px] font-semibold text-[#8b949e] uppercase tracking-widest flex items-center gap-2">
        <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
        Game Day Alerts
        {totalAlerts > 0 && (
          <span className="rounded-full bg-red-900/60 border border-red-700/50 px-2 py-0.5 text-[10px] font-bold text-red-300">
            {totalAlerts}
          </span>
        )}
      </h3>
      {urgent_swaps.length > 0 && (
        <div className="mb-3 space-y-1.5">
          <p className="text-[10px] text-[#8b949e] uppercase tracking-widest mb-1.5">Injury / status</p>
          {urgent_swaps.map((s, i) => <SwapCard key={i} swap={s} onExecute={onExecuteSwap} loading={loading} />)}
        </div>
      )}
      {no_game_swaps.length > 0 && (
        <div className="mb-3 space-y-1.5">
          <p className="text-[10px] text-[#8b949e] uppercase tracking-widest mb-1.5">No game today</p>
          {no_game_swaps.map((s, i) => <SwapCard key={i} swap={s} onExecute={onExecuteSwap} loading={loading} />)}
        </div>
      )}
      {questionable.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] text-[#8b949e] uppercase tracking-widest mb-1.5">Monitor (questionable)</p>
          {questionable.map((p, i) => (
            <div key={i} className="flex items-center gap-2 rounded-md bg-[#0d1117] border border-[#30363d] px-3 py-2 text-sm">
              <StatusBadge status={p.status} />
              <span className="text-zinc-300 font-medium">{p.name}</span>
              <span className="text-[#8b949e] text-xs">({p.ppg.toFixed(1)} PPG)</span>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

// --- App ---

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
  const [lastRun, setLastRun] = useState<LastRunData | null>(null)

  useEffect(() => { fetchLastRun() }, [])

  async function fetchLastRun() {
    try {
      const r = await fetch(`${API_BASE}/last-run`)
      if (r.ok) setLastRun(await r.json())
    } catch { /* non-critical */ }
  }

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
      setLineupStatus(await r.json())
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
      fetchLastRun()
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

  const hasSuggestions = suggestions &&
    (suggestions.ir.length > 0 || suggestions.lineup.length > 0 || suggestions.streaming.length > 0)
  const hasStreamingAction = suggestions?.streaming.some((s) => s.startsWith('WOULD DROP')) ?? false

  return (
    <div className="min-h-screen bg-[#0d1117] text-zinc-100">
      <div className="mx-auto max-w-2xl px-4 py-8">

        {/* Header */}
        <div className="mb-6 pb-4 border-b border-[#00d4aa]/20">
          <div className="flex items-start justify-between">
            <div>
              {teamInfo ? (
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-2xl font-bold tracking-tight text-white">{teamInfo.name}</h1>
                  {teamInfo.record && (
                    <span className="rounded-full bg-[#161b22] border border-[#30363d] px-2.5 py-0.5 text-xs font-semibold text-zinc-300">
                      {teamInfo.record}
                    </span>
                  )}
                  {READ_ONLY && (
                    <span className="rounded-full bg-[#161b22] border border-[#30363d] px-2.5 py-0.5 text-xs text-[#8b949e]">
                      View only
                    </span>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-2xl font-bold tracking-tight text-white">Fantasy Bot</h1>
                  {READ_ONLY && (
                    <span className="rounded-full bg-[#161b22] border border-[#30363d] px-2.5 py-0.5 text-xs text-[#8b949e]">
                      View only
                    </span>
                  )}
                </div>
              )}
              <p className="mt-0.5 text-sm text-[#8b949e]">ESPN Basketball · Auto-managed</p>
            </div>
            {lastRun?.last_run_utc && (
              <div className="text-right text-xs text-[#8b949e] flex-shrink-0">
                <div className="flex items-center gap-1 justify-end mb-0.5">
                  <Clock className="h-3 w-3" />
                  <span>Last run</span>
                </div>
                <span className="text-zinc-300 font-medium">{timeAgo(lastRun.last_run_utc)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Action Bar */}
        <div className="mb-6 flex flex-wrap gap-2">
          <button
            onClick={analyze}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-md bg-[#00d4aa]/10 border border-[#00d4aa]/30 px-3.5 py-2 text-sm font-medium text-[#00d4aa] hover:bg-[#00d4aa]/20 disabled:opacity-40 transition-colors"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Analyze roster
          </button>
          <button
            onClick={checkLineup}
            disabled={loading || lineupLoading}
            className="inline-flex items-center gap-2 rounded-md bg-[#161b22] border border-[#30363d] px-3.5 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800 disabled:opacity-40 transition-colors"
          >
            {lineupLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <AlertTriangle className="h-4 w-4 text-amber-400" />}
            Check lineup now
          </button>
          {hasSuggestions && !READ_ONLY && (
            <>
              <button
                onClick={() => setConfirmOpen(true)}
                disabled={loading || !hasStreamingAction}
                className="inline-flex items-center gap-2 rounded-md bg-[#00d4aa] px-3.5 py-2 text-sm font-semibold text-[#0d1117] hover:bg-[#00bfa0] disabled:opacity-40 transition-colors"
              >
                <Play className="h-4 w-4" />
                Execute
              </button>
              <button
                onClick={generateNew}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-md bg-[#161b22] border border-[#30363d] px-3.5 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800 disabled:opacity-40 transition-colors"
              >
                <Sparkles className="h-4 w-4" />
                New suggestions
              </button>
              <button
                onClick={() => { setSuggestions(null); setExecuted(null); setError(null) }}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-md border border-red-800/50 px-3.5 py-2 text-sm font-medium text-red-400 hover:bg-red-950/30 disabled:opacity-40 transition-colors"
              >
                <XCircle className="h-4 w-4" />
                Decline
              </button>
            </>
          )}
        </div>

        {/* Swap result */}
        {swapResult && (
          <div className="mb-5 rounded-lg border border-[#00d4aa]/30 bg-[#00d4aa]/5 p-3.5 text-sm text-[#00d4aa]">
            {swapResult}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-5 rounded-lg border border-red-800/50 bg-red-950/20 p-3.5 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Execution success */}
        {executed && executed.length > 0 && (
          <div className="mb-5 rounded-lg border border-[#00d4aa]/30 bg-[#161b22] p-4">
            <h3 className="mb-2 text-[10px] font-semibold text-[#8b949e] uppercase tracking-widest">Execution complete</h3>
            <ul className="space-y-1.5">
              {executed.map((line, i) => (
                <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                  <span className="text-[#00d4aa] mt-0.5 flex-shrink-0">✓</span>
                  {line}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Last Run Panel */}
        {lastRun && <LastRunPanel data={lastRun} />}

        {/* Suggestions + Game Day Alerts */}
        {(suggestions || lineupStatus) && (
          <div className="space-y-4">
            {lineupStatus && (
              <GameDayAlerts lineupStatus={lineupStatus} onExecuteSwap={executeSwap} loading={lineupLoading} />
            )}
            {suggestions && (
              <>
                <SuggestionPanel title="IR Moves" items={suggestions.ir} emptyMessage="No IR moves suggested." />
                <SuggestionPanel title="Lineup Changes" items={suggestions.lineup} emptyMessage="No lineup changes suggested." />
                <StreamingPanel items={suggestions.streaming} />
              </>
            )}
          </div>
        )}

        {!suggestions && !lineupStatus && !loading && !error && !executed && (
          <p className="text-[#8b949e] text-sm">
            Click "Analyze roster" to load suggestions, or "Check lineup now" for game-day alerts.
          </p>
        )}
      </div>

      {/* Confirm Modal */}
      {confirmOpen && !READ_ONLY && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
          onClick={() => setConfirmOpen(false)}
        >
          <div
            className="w-full max-w-md rounded-xl border border-[#30363d] bg-[#161b22] p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-1 text-lg font-semibold text-white">Execute streaming move?</h3>
            <p className="mb-4 text-sm text-[#8b949e]">
              This will execute the add/drop via ESPN. IR and lineup moves are advisory only.
            </p>
            <div className="space-y-1.5 mb-5">
              {suggestions?.streaming.map((s, i) =>
                s.startsWith('WOULD DROP') ? <StreamingRow key={i} text={s} /> : null
              )}
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmOpen(false)}
                className="rounded-lg border border-[#30363d] px-4 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={execute}
                disabled={loading}
                className="rounded-lg bg-[#00d4aa] px-4 py-2 text-sm font-semibold text-[#0d1117] hover:bg-[#00bfa0] disabled:opacity-50 transition-colors"
              >
                {loading ? <Loader2 className="inline h-4 w-4 animate-spin" /> : 'Confirm Execute'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
