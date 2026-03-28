import { useEffect, useState } from 'react'

const SAMPLE_CHARS = 'Hello, Bob!'.split('')
const SAMPLE_HEX = ['a3', 'f1', '7c', 'e9', '2b', '4d', '8f', '05', 'c6', '1a', 'e3']

/**
 * Visual showing plaintext bytes transforming into ciphertext through AES-GCM.
 */
export default function EncryptionAnim() {
  const [phase, setPhase] = useState(0)

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 150)
    const t2 = setTimeout(() => setPhase(2), 900)
    const t3 = setTimeout(() => setPhase(3), 1500)
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3) }
  }, [])

  return (
    <div className="my-3 font-mono text-xs animate-fade-in">
      <div className="flex items-center gap-2 overflow-hidden">
        {/* Plaintext bytes */}
        <div className="flex gap-0.5 flex-wrap">
          {SAMPLE_CHARS.map((ch, i) => (
            <span
              key={i}
              className={`inline-flex items-center justify-center w-5 h-5 rounded border text-[9px]
                transition-all duration-300
                ${phase >= 1
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                  : 'border-gray-700 bg-gray-800 text-gray-500'
                }`}
              style={{ transitionDelay: `${i * 40}ms` }}
            >
              {ch === ' ' ? '·' : ch}
            </span>
          ))}
        </div>

        {/* Arrow + lock */}
        <div className={`flex items-center gap-1 transition-opacity duration-500 ${phase >= 2 ? 'opacity-100' : 'opacity-20'}`}>
          <span className="text-gray-600 text-[10px]">──</span>
          <span className="text-cyan-400">🔒</span>
          <span className="text-gray-600 text-[10px]">──</span>
        </div>

        {/* Ciphertext bytes */}
        <div className="flex gap-0.5 flex-wrap">
          {SAMPLE_HEX.map((h, i) => (
            <span
              key={i}
              className={`inline-flex items-center justify-center w-5 h-5 rounded border text-[9px]
                transition-all duration-300
                ${phase >= 3
                  ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300'
                  : 'border-gray-700 bg-gray-800 text-gray-600'
                }`}
              style={{ transitionDelay: `${i * 40}ms` }}
            >
              {h}
            </span>
          ))}
        </div>
      </div>

      {phase >= 3 && (
        <div className="mt-2 text-[10px] text-gray-600 animate-fade-in text-center">
          + 16-byte GCM auth tag appended
        </div>
      )}
    </div>
  )
}
