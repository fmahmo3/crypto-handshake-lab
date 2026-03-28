/**
 * Toggle button for enabling tamper mode.
 * Once enabled it cannot be undone for the current session — reset to start fresh.
 */
export default function TamperToggle({ enabled, onToggle, disabled }) {
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onToggle}
        disabled={disabled || enabled}
        className={`
          relative flex items-center gap-2.5 px-4 py-2.5 rounded-lg border font-mono text-sm
          transition-all duration-300 select-none
          ${enabled
            ? 'bg-red-950/60 border-red-500/70 text-red-400 cursor-not-allowed shadow-[0_0_24px_rgba(239,68,68,0.25)]'
            : disabled
              ? 'bg-gray-900/30 border-gray-800 text-gray-700 cursor-not-allowed'
              : 'bg-orange-950/30 border-orange-500/40 text-orange-400 cursor-pointer hover:bg-orange-950/60 hover:border-orange-400/70 hover:shadow-[0_0_16px_rgba(249,115,22,0.2)]'
          }
        `}
      >
        {enabled && (
          <span className="absolute -top-1.5 -right-1.5 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
          </span>
        )}

        <span className={`text-base ${enabled ? 'animate-glow-pulse' : ''}`} role="img" aria-label="tamper">
          {enabled ? '💀' : '⚠️'}
        </span>

        <span className="tracking-wide">
          {enabled ? 'TAMPER MODE ACTIVE' : 'Enable Tamper Mode'}
        </span>
      </button>

      {!enabled && !disabled && (
        <span className="text-xs text-gray-600 font-mono max-w-[200px] leading-tight">
          flips a ciphertext byte before step 9 to break HMAC verification
        </span>
      )}

      {enabled && (
        <span className="text-xs text-red-500/70 font-mono max-w-[200px] leading-tight animate-fade-in">
          byte 0 of ciphertext will be XOR'd with 0xFF before verification
        </span>
      )}
    </div>
  )
}
