import { useEffect, useState } from 'react'

/**
 * Visual representation of the DH key exchange:
 * Alice's public key travels right, Bob's travels left.
 */
export default function KeyExchangeAnim({ alicePub, bobPub }) {
  const [phase, setPhase] = useState(0)

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 200)
    const t2 = setTimeout(() => setPhase(2), 900)
    const t3 = setTimeout(() => setPhase(3), 1600)
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3) }
  }, [])

  const truncate = hex => hex ? hex.slice(0, 10) + '…' : ''

  return (
    <div className="my-3 space-y-2 font-mono text-xs animate-fade-in">
      <div className="flex items-center gap-2 text-gray-500">
        <span className={`text-emerald-400 transition-opacity duration-300 ${phase >= 1 ? 'opacity-100' : 'opacity-20'}`}>
          Alice
        </span>
        <div className="flex-1 relative h-5 flex items-center">
          <div className="w-full h-px bg-gradient-to-r from-emerald-500/30 via-emerald-500/60 to-emerald-500/30" />
          <span className="absolute right-0 text-emerald-500 text-[10px]">▶</span>
          {phase >= 1 && (
            <span className="absolute left-0 right-0 text-center text-[10px] text-emerald-400/70 leading-none -top-3">
              {truncate(alicePub)}
            </span>
          )}
        </div>
        <span className={`text-amber-400 transition-opacity duration-300 ${phase >= 2 ? 'opacity-100' : 'opacity-20'}`}>
          Bob
        </span>
      </div>

      <div className="flex items-center gap-2 text-gray-500">
        <span className={`text-emerald-400 transition-opacity duration-300 ${phase >= 3 ? 'opacity-100' : 'opacity-20'}`}>
          Alice
        </span>
        <div className="flex-1 relative h-5 flex items-center">
          <div className="w-full h-px bg-gradient-to-r from-amber-500/30 via-amber-500/60 to-amber-500/30" />
          <span className="absolute left-0 text-amber-500 text-[10px]">◀</span>
          {phase >= 2 && (
            <span className="absolute left-0 right-0 text-center text-[10px] text-amber-400/70 leading-none -top-3">
              {truncate(bobPub)}
            </span>
          )}
        </div>
        <span className={`text-amber-400 transition-opacity duration-300 ${phase >= 2 ? 'opacity-100' : 'opacity-20'}`}>
          Bob
        </span>
      </div>

      {phase >= 3 && (
        <div className="text-center text-[10px] text-gray-500 animate-fade-in">
          keys exchanged over insecure channel — eavesdropper sees A and B but not g^(ab)
        </div>
      )}
    </div>
  )
}
