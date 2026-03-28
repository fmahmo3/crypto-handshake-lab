import { useState } from 'react'

function classify(val) {
  if (val === null || val === undefined) return 'null'
  if (typeof val === 'boolean') return 'bool'
  if (typeof val === 'number') return 'number'
  if (typeof val === 'string' && /^0x[0-9a-fA-F]+$/.test(val)) return 'hex'
  return 'string'
}

function ValueChip({ val }) {
  const [expanded, setExpanded] = useState(false)
  const type = classify(val)

  if (type === 'null') {
    return <span className="text-gray-600 font-mono text-xs">null</span>
  }
  if (type === 'bool') {
    return (
      <span className={`font-mono text-xs ${val ? 'text-green-400' : 'text-red-400'}`}>
        {String(val)}
      </span>
    )
  }
  if (type === 'number') {
    return <span className="text-amber-300 font-mono text-xs">{val}</span>
  }
  if (type === 'hex') {
    const isLong = val.length > 34
    if (!isLong) {
      return <span className="text-emerald-400 font-mono text-xs break-all">{val}</span>
    }
    return (
      <span className="font-mono text-xs break-all">
        {expanded ? (
          <>
            <span className="text-emerald-400">{val}</span>
            <button
              onClick={() => setExpanded(false)}
              className="ml-2 text-cyan-500 hover:text-cyan-300 underline text-[10px]"
            >
              collapse
            </button>
          </>
        ) : (
          <>
            <span className="text-emerald-400">{val.slice(0, 16)}</span>
            <span className="text-gray-500">…</span>
            <span className="text-emerald-400">{val.slice(-6)}</span>
            <button
              onClick={() => setExpanded(true)}
              className="ml-2 text-cyan-500 hover:text-cyan-300 underline text-[10px]"
            >
              expand
            </button>
          </>
        )}
      </span>
    )
  }
  // plain string
  return <span className="text-sky-300 font-mono text-xs break-all">"{val}"</span>
}

export default function HexInspector({ values, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)

  if (!values || Object.keys(values).length === 0) return null

  const entries = Object.entries(values)

  return (
    <div className="mt-3 rounded border border-gray-700/60 bg-gray-900/60 text-xs">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-3 py-2 text-gray-500 hover:text-gray-300 transition-colors"
      >
        <span className="font-mono flex items-center gap-2">
          <span className="text-cyan-600">{open ? '▼' : '▶'}</span>
          <span>inspect values</span>
        </span>
        <span className="text-gray-700">{entries.length} field{entries.length !== 1 ? 's' : ''}</span>
      </button>

      {open && (
        <div className="border-t border-gray-700/60 px-3 py-2 space-y-1.5">
          {entries.map(([key, val]) => (
            <div key={key} className="flex items-start gap-2 min-w-0">
              <span className="text-gray-600 shrink-0 mt-0.5 select-none">›</span>
              <span className="text-gray-500 font-mono shrink-0 min-w-0">{key}:</span>
              <span className="min-w-0 flex-1">
                <ValueChip val={val} />
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
