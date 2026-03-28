import { useEffect, useRef, useState } from 'react'
import { useHandshake } from '../hooks/useHandshake'
import StepCard from './StepCard'
import PartyColumn from './PartyColumn'
import TamperToggle from './TamperToggle'

/** Extract display keys for a party from the accumulated step list. */
function extractKeys(steps, party) {
  const keys = {}
  for (const s of steps) {
    const v = s.values ?? {}
    if (party === 'alice') {
      if (v.alice_public_key) keys.publicKey = v.alice_public_key
      if (v.alice_public_key_sent) keys.publicKey = v.alice_public_key_sent
      if (v.alice_computed_secret) keys.sharedSecret = v.alice_computed_secret
      if (v.encryption_key) keys.encKey = v.encryption_key
    } else {
      if (v.bob_public_key) keys.publicKey = v.bob_public_key
      if (v.bob_public_key_sent) keys.publicKey = v.bob_public_key_sent
      if (v.bob_computed_secret) keys.sharedSecret = v.bob_computed_secret
      if (v.encryption_key) keys.encKey = v.encryption_key
    }
  }
  return Object.keys(keys).length ? keys : null
}

function Spinner({ className = '' }) {
  return (
    <div
      className={`w-3.5 h-3.5 rounded-full border-2 border-t-transparent animate-spin ${className}`}
    />
  )
}

function ControlButton({ onClick, disabled, variant, children }) {
  const base = 'flex items-center gap-2 px-4 py-2.5 rounded-lg border font-mono text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed'
  const variants = {
    cyan: 'bg-cyan-500/10 border-cyan-500/40 text-cyan-400 hover:bg-cyan-500/20 hover:border-cyan-400/70',
    purple: 'bg-purple-500/10 border-purple-500/40 text-purple-400 hover:bg-purple-500/20 hover:border-purple-400/70',
    gray: 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-300',
  }
  return (
    <button onClick={onClick} disabled={disabled} className={`${base} ${variants[variant] ?? variants.gray}`}>
      {children}
    </button>
  )
}

export default function HandshakeViewer() {
  const {
    sessionId, steps, currentStep, totalSteps, isComplete,
    tamperMode, plaintext, isLoading, isRunningAll, error,
    reset, advance, toggleTamper, runAll,
  } = useHandshake()

  const [customPlaintext, setCustomPlaintext] = useState('')
  const [showPlaintextInput, setShowPlaintextInput] = useState(false)
  const stepsEndRef = useRef(null)

  // Bootstrap: create the initial session on mount.
  useEffect(() => {
    reset()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Scroll to latest step.
  useEffect(() => {
    if (steps.length > 0) {
      stepsEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [steps.length])

  const latestStep = steps[steps.length - 1]
  const aliceActive = latestStep?.party === 'alice'
  const bobActive = latestStep?.party === 'bob'
  const aliceKeys = extractKeys(steps, 'alice')
  const bobKeys = extractKeys(steps, 'bob')

  // Show tamper toggle once key exchange is done (step 4+) but before completion.
  const showTamper = currentStep >= 4 && !isComplete

  const progressPct = totalSteps > 0 ? Math.round((currentStep / totalSteps) * 100) : 0

  function handleReset() {
    reset(customPlaintext || undefined)
    setShowPlaintextInput(false)
    setCustomPlaintext('')
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">

      {/* ── Top bar ───────────────────────────────────── */}
      <header className="sticky top-0 z-20 border-b border-gray-800/80 bg-gray-950/90 backdrop-blur">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-cyan-500 text-xl shrink-0">⬡</span>
            <h1 className="font-mono font-bold text-sm text-gray-200 tracking-widest whitespace-nowrap">
              CRYPTO HANDSHAKE LAB
            </h1>
            <span className="text-gray-700 text-xs font-mono hidden md:block truncate">
              DH·2048 + AES-256-GCM + HMAC-SHA256
            </span>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {tamperMode && (
              <span className="flex items-center gap-1.5 text-xs font-mono text-red-400 animate-glow-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                tamper active
              </span>
            )}
            {sessionId && (
              <span className="font-mono text-[10px] text-gray-700 hidden lg:block">
                {sessionId.slice(0, 8)}…
              </span>
            )}
          </div>
        </div>
      </header>

      {/* ── Progress bar ──────────────────────────────── */}
      {sessionId && (
        <div className="h-0.5 bg-gray-800">
          <div
            className={`
              h-full transition-all duration-700 ease-out
              ${tamperMode
                ? 'bg-gradient-to-r from-orange-600 to-red-500'
                : isComplete
                  ? 'bg-gradient-to-r from-emerald-600 to-cyan-400'
                  : 'bg-gradient-to-r from-cyan-700 to-cyan-400'
              }
            `}
            style={{ width: `${progressPct}%` }}
          />
        </div>
      )}

      {/* ── Main area ─────────────────────────────────── */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 py-6">

        {/* Error banner */}
        {error && (
          <div className="mb-5 flex items-start gap-3 p-3 rounded-lg bg-red-950/50 border border-red-500/40 font-mono text-sm text-red-400">
            <span className="shrink-0">⚠</span>
            <span>{error}</span>
          </div>
        )}

        {/* Step counter */}
        {sessionId && (
          <div className="mb-5 flex items-center justify-between text-xs font-mono text-gray-600">
            <span>
              step <span className="text-gray-400">{currentStep}</span> / {totalSteps}
              {isRunningAll && <span className="text-purple-400 ml-2 animate-pulse">● auto-advancing…</span>}
            </span>
            {isComplete && (
              <span className="text-green-500 animate-fade-in flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                handshake complete
              </span>
            )}
          </div>
        )}

        {/* 3-column grid */}
        <div className="grid grid-cols-1 lg:grid-cols-[180px_1fr_180px] gap-5">

          {/* ── Alice column ──────────────────────────── */}
          <div className="hidden lg:block">
            <div className="sticky top-20">
              <PartyColumn
                name="Alice"
                color="emerald"
                isActive={aliceActive}
                keys={aliceKeys}
              />
            </div>
          </div>

          {/* ── Steps + controls ──────────────────────── */}
          <div className="space-y-4 min-w-0">

            {/* Empty state */}
            {steps.length === 0 && !isLoading && sessionId && (
              <div className="text-center py-20 animate-fade-in">
                <div className="text-5xl mb-4">🔐</div>
                <p className="text-gray-400 font-mono text-sm mb-1">session ready</p>
                <p className="text-gray-600 text-xs font-mono">
                  press <span className="text-cyan-400">Next Step</span> to begin the handshake
                </p>
                {plaintext && (
                  <p className="mt-3 text-gray-700 text-[11px] font-mono max-w-xs mx-auto leading-relaxed">
                    message: "{plaintext}"
                  </p>
                )}
              </div>
            )}

            {/* Step cards */}
            {steps.map((step, idx) => (
              <StepCard
                key={step.step}
                step={step}
                isNew={idx === steps.length - 1 && !isRunningAll}
              />
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex items-center justify-center py-8">
                <div className="flex items-center gap-3 text-cyan-500 font-mono text-sm">
                  <Spinner className="border-cyan-500" />
                  <span>computing step {currentStep + 1}…</span>
                </div>
              </div>
            )}

            <div ref={stepsEndRef} />

            {/* ── Controls ──────────────────────────── */}
            <div className={`pt-2 space-y-4 ${steps.length > 0 ? 'border-t border-gray-800/60' : ''}`}>

              {/* Tamper toggle */}
              {showTamper && (
                <div className="animate-fade-in">
                  <TamperToggle
                    enabled={tamperMode}
                    onToggle={toggleTamper}
                    disabled={isLoading || isRunningAll}
                  />
                </div>
              )}

              {/* Action row */}
              <div className="flex flex-wrap gap-3 items-center">
                {!isComplete && (
                  <>
                    <ControlButton
                      onClick={advance}
                      disabled={isLoading || isRunningAll}
                      variant="cyan"
                    >
                      {isLoading && !isRunningAll
                        ? <Spinner className="border-cyan-400" />
                        : <span>▶</span>
                      }
                      Next Step
                    </ControlButton>

                    <ControlButton
                      onClick={runAll}
                      disabled={isLoading || isRunningAll}
                      variant="purple"
                    >
                      {isRunningAll
                        ? <><Spinner className="border-purple-400" /> Running…</>
                        : <><span>⏩</span> Run All</>
                      }
                    </ControlButton>
                  </>
                )}

                <ControlButton
                  onClick={() => setShowPlaintextInput(v => !v)}
                  disabled={isLoading || isRunningAll}
                  variant="gray"
                >
                  <span>✎</span>
                  {showPlaintextInput ? 'Cancel' : 'Custom Message'}
                </ControlButton>

                <ControlButton
                  onClick={handleReset}
                  disabled={isLoading && !sessionId}
                  variant="gray"
                >
                  <span>↺</span>
                  Reset
                </ControlButton>
              </div>

              {/* Custom plaintext input */}
              {showPlaintextInput && (
                <div className="flex gap-2 animate-fade-in">
                  <input
                    type="text"
                    value={customPlaintext}
                    onChange={e => setCustomPlaintext(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleReset()}
                    placeholder="Enter a secret message for Alice to send…"
                    className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 font-mono text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30"
                  />
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 bg-cyan-500/15 border border-cyan-500/40 text-cyan-400 rounded-lg font-mono text-sm hover:bg-cyan-500/25 transition-colors"
                  >
                    Start
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* ── Bob column ──────────────────────────────── */}
          <div className="hidden lg:block">
            <div className="sticky top-20">
              <PartyColumn
                name="Bob"
                color="amber"
                isActive={bobActive}
                keys={bobKeys}
              />
            </div>
          </div>
        </div>

        {/* Mobile party strip (shown below steps on small screens) */}
        <div className="flex gap-4 mt-6 lg:hidden">
          <div className="flex-1">
            <PartyColumn name="Alice" color="emerald" isActive={aliceActive} keys={aliceKeys} />
          </div>
          <div className="flex-1">
            <PartyColumn name="Bob" color="amber" isActive={bobActive} keys={bobKeys} />
          </div>
        </div>
      </main>

      {/* ── Footer ────────────────────────────────────── */}
      <footer className="border-t border-gray-800/60 py-4 text-center text-[10px] font-mono text-gray-700">
        DH RFC-3526-G14 · AES-256-GCM · HMAC-SHA256 · HKDF-SHA256
      </footer>
    </div>
  )
}
