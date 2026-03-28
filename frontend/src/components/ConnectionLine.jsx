import { useEffect, useState } from 'react'

/**
 * Animated horizontal connection line showing data flowing between parties.
 * direction: 'right' (Alice→Bob) | 'left' (Bob→Alice) | 'both' (bidirectional)
 * color: 'emerald' | 'amber' | 'cyan'
 */
export default function ConnectionLine({ direction = 'right', color = 'cyan', label = '' }) {
  const [phase, setPhase] = useState(0)

  // Trigger animation on mount
  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 100)
    const t2 = setTimeout(() => setPhase(direction === 'both' ? 2 : 0), 900)
    const t3 = direction === 'both' ? setTimeout(() => setPhase(0), 1700) : null
    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
      if (t3) clearTimeout(t3)
    }
  }, [direction])

  const colorMap = {
    emerald: {
      dot: 'bg-emerald-400',
      line: 'from-transparent via-emerald-500/50 to-transparent',
      label: 'text-emerald-400',
      track: 'bg-emerald-500/20',
    },
    amber: {
      dot: 'bg-amber-400',
      line: 'from-transparent via-amber-500/50 to-transparent',
      label: 'text-amber-400',
      track: 'bg-amber-500/20',
    },
    cyan: {
      dot: 'bg-cyan-400',
      line: 'from-transparent via-cyan-500/50 to-transparent',
      label: 'text-cyan-400',
      track: 'bg-cyan-500/20',
    },
  }

  const c = colorMap[color] || colorMap.cyan

  return (
    <div className="flex flex-col items-center gap-1 my-1 animate-fade-in">
      {label && (
        <span className={`font-mono text-[10px] ${c.label} opacity-70`}>{label}</span>
      )}
      <div className="relative w-full h-6 flex items-center">
        {/* Dashed track */}
        <div className="absolute inset-y-0 left-0 right-0 flex items-center">
          <div className="w-full h-px border-t border-dashed border-gray-700" />
        </div>

        {/* Arrowhead left */}
        {(direction === 'left' || direction === 'both') && (
          <span className="absolute left-0 text-gray-600 text-xs leading-none z-10">◄</span>
        )}

        {/* Arrowhead right */}
        {(direction === 'right' || direction === 'both') && (
          <span className="absolute right-0 text-gray-600 text-xs leading-none z-10">►</span>
        )}

        {/* Traveling dot — right */}
        {phase === 1 && (direction === 'right' || direction === 'both') && (
          <div
            className={`absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full ${c.dot} shadow-[0_0_6px_currentColor] animate-travel-right`}
          />
        )}

        {/* Traveling dot — left */}
        {phase === 2 && direction === 'both' && (
          <div
            className={`absolute top-1/2 -translate-y-1/2 w-2 h-2 rounded-full ${c.dot} shadow-[0_0_6px_currentColor] animate-travel-left`}
          />
        )}
      </div>
    </div>
  )
}
