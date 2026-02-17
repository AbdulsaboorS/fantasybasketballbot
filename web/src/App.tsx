import { useState } from 'react'
import { RefreshCw, Play, XCircle, Sparkles, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

const API_BASE = '/api'

type Suggestions = {
  ir: string[]
  lineup: string[]
  streaming: string[]
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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [executed, setExecuted] = useState<string[] | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)

  async function analyze() {
    setLoading(true)
    setError(null)
    setExecuted(null)
    try {
      const r = await fetch(`${API_BASE}/analyze`)
      if (!r.ok) throw new Error(await r.text())
      const data: Suggestions = await r.json()
      setSuggestions(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
      setSuggestions(null)
    } finally {
      setLoading(false)
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
        <h1 className="mb-2 text-2xl font-bold tracking-tight">
          ESPN Fantasy Bot
        </h1>
        <p className="mb-8 text-zinc-400">
          Analyze your roster and run suggested IR, lineup, and streaming changes.
        </p>

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

        {error && (
          <div className="mb-6 rounded-lg border border-red-800/50 bg-red-950/30 p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        {executed && executed.length > 0 && (
          <div className="mb-6 rounded-lg border border-emerald-800/50 bg-emerald-950/20 p-4">
            <h3 className="mb-2 font-semibold text-emerald-200">
              Execution complete
            </h3>
            <ul className="space-y-1 text-sm text-emerald-300/90">
              {executed.map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
          </div>
        )}

        {suggestions && (
          <div className="space-y-4">
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
          </div>
        )}

        {!suggestions && !loading && !error && !executed && (
          <p className="text-zinc-500">
            Click &quot;Analyze roster&quot; to load suggestions.
          </p>
        )}
      </div>

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
