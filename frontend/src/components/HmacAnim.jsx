import { useEffect, useState } from 'react'

/**
 * HMAC sign/verify visual.
 * mode: 'sign' | 'verify'
 * verified: boolean (for verify mode)
 */
export default function HmacAnim({ mode = 'sign', verified = true }) {
  const [phase, setPhase] = useState(0)

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 200)
    const t2 = setTimeout(() => setPhase(2), 800)
    const t3 = setTimeout(() => setPhase(3), 1300)
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3) }
  }, [])

  const resultColor = verified ? 'text-green-400' : 'text-red-400'
  const resultBg = verified ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'
  const resultLabel = mode === 'sign'
    ? '✓ signature'
    : verified ? '✓ verified' : '✗ INVALID'

  return (
    <div className="my-3 flex items-center gap-2 font-mono text-xs animate-fade-in overflow-hidden">
      <div className={`transition-opacity duration-300 ${phase >= 1 ? 'opacity-100' : 'opacity-20'}`}>
        <div className="text-[10px] text-gray-600 mb-0.5">ciphertext</div>
        <div className="px-2 py-1 rounded border border-cyan-500/30 bg-cyan-500/10 text-cyan-400">
          ct bytes
        </div>
      </div>

      <span className={`text-gray-600 transition-opacity duration-300 ${phase >= 1 ? 'opacity-100' : 'opacity-20'}`}>+</span>

      <div className={`transition-opacity duration-300 ${phase >= 1 ? 'opacity-100' : 'opacity-20'}`}>
        <div className="text-[10px] text-gray-600 mb-0.5">mac_key</div>
        <div className="px-2 py-1 rounded border border-purple-500/30 bg-purple-500/10 text-purple-400">
          k bytes
        </div>
      </div>

      <div className={`flex items-center gap-1 transition-opacity duration-500 ${phase >= 2 ? 'opacity-100' : 'opacity-20'}`}>
        <span className="text-gray-600 text-[10px]">──▶</span>
        <div className="text-[10px] text-center">
          <div className="text-gray-500">HMAC</div>
          <div className="text-gray-600">SHA-256</div>
        </div>
        <span className="text-gray-600 text-[10px]">──▶</span>
      </div>

      <div className={`transition-all duration-500 ${phase >= 3 ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}>
        <div className="text-[10px] text-gray-600 mb-0.5">
          {mode === 'sign' ? 'output' : 'result'}
        </div>
        <div className={`px-2 py-1 rounded border ${resultBg} ${resultColor} font-semibold`}>
          {resultLabel}
        </div>
      </div>
    </div>
  )
}
