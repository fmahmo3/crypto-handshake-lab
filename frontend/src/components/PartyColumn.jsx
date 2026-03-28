/**
 * Sticky side panel showing Alice or Bob's current cryptographic state.
 * Glows when the most recent step belongs to this party.
 */
export default function PartyColumn({ name, color, isActive, keys }) {
  const cfg = color === 'emerald'
    ? {
        border: 'border-emerald-500/30',
        activeBorder: 'border-emerald-400/60',
        text: 'text-emerald-400',
        bg: 'bg-emerald-500/5',
        activeBg: 'bg-emerald-500/10',
        glow: 'shadow-[0_0_24px_rgba(16,185,129,0.15)]',
        dot: 'bg-emerald-400',
        ring: 'ring-emerald-400/50',
        pub: 'text-emerald-300/80',
        secret: 'text-cyan-300/80',
      }
    : {
        border: 'border-amber-500/30',
        activeBorder: 'border-amber-400/60',
        text: 'text-amber-400',
        bg: 'bg-amber-500/5',
        activeBg: 'bg-amber-500/10',
        glow: 'shadow-[0_0_24px_rgba(245,158,11,0.15)]',
        dot: 'bg-amber-400',
        ring: 'ring-amber-400/50',
        pub: 'text-amber-300/80',
        secret: 'text-cyan-300/80',
      }

  return (
    <div
      className={`
        rounded-xl border p-4 transition-all duration-500
        ${isActive ? `${cfg.activeBorder} ${cfg.activeBg} ${cfg.glow}` : `${cfg.border} ${cfg.bg}`}
      `}
    >
      {/* Avatar + name */}
      <div className="flex flex-col items-center gap-2 mb-4">
        <div
          className={`
            w-14 h-14 rounded-full border-2 flex items-center justify-center text-2xl
            transition-all duration-500
            ${isActive ? `${cfg.activeBorder} ring-2 ${cfg.ring}` : cfg.border}
          `}
        >
          {name === 'Alice' ? '👩' : '👨'}
        </div>

        <div className="flex items-center gap-1.5">
          {isActive && (
            <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} animate-pulse`} />
          )}
          <span className={`font-mono font-bold text-sm tracking-wider ${cfg.text}`}>
            {name.toUpperCase()}
          </span>
        </div>

        {isActive && (
          <span className="text-[10px] font-mono text-gray-600 animate-fade-in">
            active
          </span>
        )}
      </div>

      {/* Key state */}
      {keys ? (
        <div className="space-y-3 font-mono text-[10px]">
          {keys.publicKey && (
            <div>
              <div className="text-gray-600 mb-1 flex items-center gap-1">
                <span className={`w-1 h-1 rounded-full ${cfg.dot}`} />
                <span>public key</span>
              </div>
              <div className={`${cfg.pub} bg-gray-900/60 rounded p-1.5 break-all leading-relaxed border border-gray-800`}>
                {keys.publicKey.slice(0, 20)}…
              </div>
            </div>
          )}

          {keys.sharedSecret && (
            <div>
              <div className="text-gray-600 mb-1 flex items-center gap-1">
                <span className="w-1 h-1 rounded-full bg-cyan-400" />
                <span>shared secret</span>
              </div>
              <div className={`${cfg.secret} bg-gray-900/60 rounded p-1.5 break-all leading-relaxed border border-gray-800`}>
                {keys.sharedSecret.slice(0, 20)}…
              </div>
            </div>
          )}

          {keys.encKey && (
            <div>
              <div className="text-gray-600 mb-1 flex items-center gap-1">
                <span className="w-1 h-1 rounded-full bg-purple-400" />
                <span>enc key (HKDF)</span>
              </div>
              <div className="text-purple-300/70 bg-gray-900/60 rounded p-1.5 break-all leading-relaxed border border-gray-800">
                {keys.encKey.slice(0, 20)}…
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center">
          <span className="text-gray-700 font-mono text-[10px]">no keys yet</span>
        </div>
      )}
    </div>
  )
}
