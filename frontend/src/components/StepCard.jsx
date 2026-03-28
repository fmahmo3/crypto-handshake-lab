import { useEffect, useState } from 'react'
import HexInspector from './HexInspector'
import ConnectionLine from './ConnectionLine'
import KeyExchangeAnim from './KeyExchangeAnim'
import EncryptionAnim from './EncryptionAnim'
import HmacAnim from './HmacAnim'

// Per-party visual config — all class strings are complete for Tailwind JIT scanning.
const PARTY = {
  alice: {
    label: 'Alice',
    border: 'border-emerald-500/50',
    header: 'from-emerald-500/10 to-transparent',
    badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
    dot: 'bg-emerald-400',
  },
  bob: {
    label: 'Bob',
    border: 'border-amber-500/50',
    header: 'from-amber-500/10 to-transparent',
    badge: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
    dot: 'bg-amber-400',
  },
  shared: {
    label: 'Shared',
    border: 'border-cyan-500/30',
    header: 'from-cyan-500/10 to-transparent',
    badge: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40',
    dot: 'bg-cyan-400',
  },
}

const STEP_ICON = {
  1: '⚙️',
  2: '🔑',
  3: '🔑',
  4: '↔️',
  5: '🤝',
  6: '🔀',
  7: '🔒',
  8: '✍️',
  9: '✅',
}

export default function StepCard({ step, isNew }) {
  const [visible, setVisible] = useState(!isNew)

  // Entrance animation for newly arriving cards
  useEffect(() => {
    if (!isNew) return
    const t = setTimeout(() => setVisible(true), 60)
    return () => clearTimeout(t)
  }, [isNew])

  const party = PARTY[step.party] ?? PARTY.shared
  const isTampered = step.tampered === true
  const isFailure = isTampered && step.values?.hmac_verified === false
  const isSuccess = step.step === 9 && step.values?.handshake_success === true

  // Connection line config for steps that involve transmission
  const lineProps =
    step.step === 4
      ? { show: true, direction: 'both', color: 'cyan', label: 'A  ⟶  B    B  ⟶  A' }
      : step.step === 7 || step.step === 8
        ? { show: true, direction: 'right', color: 'emerald', label: 'Alice  ⟶  Bob' }
        : step.step === 9
          ? { show: false }
          : { show: false }

  return (
    <div
      className={`
        rounded-xl border overflow-hidden
        transition-all duration-500 ease-out
        ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-3'}
        ${isFailure
          ? 'border-red-500/70 shadow-[0_0_32px_rgba(239,68,68,0.3)] animate-tamper-flash'
          : isSuccess
            ? 'border-green-500/50 shadow-[0_0_20px_rgba(34,197,94,0.15)]'
            : party.border
        }
      `}
    >
      {/* ── Card header ────────────────────────────────── */}
      <div
        className={`
          flex items-center justify-between px-4 py-3
          bg-gradient-to-r
          ${isFailure ? 'from-red-500/15 to-transparent' : party.header}
        `}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-xl shrink-0" role="img" aria-label="icon">
            {isFailure ? '💥' : isSuccess ? '🎉' : (STEP_ICON[step.step] ?? '🔷')}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-gray-200 font-semibold text-sm leading-tight">
                {step.name}
              </span>
              {isTampered && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-red-500/25 text-red-400 border border-red-500/50 shrink-0">
                  TAMPERED
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 ml-2">
          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${party.badge}`}>
            {party.label}
          </span>
          <span className="text-[10px] text-gray-600 font-mono hidden sm:block">
            {step.step}/9
          </span>
        </div>
      </div>

      {/* ── Card body ──────────────────────────────────── */}
      <div className="px-4 py-3 bg-gray-900/20">
        {/* Description */}
        <p className="text-gray-300 text-sm leading-relaxed">{step.description}</p>

        {/* Step-specific animations */}
        {step.step === 4 && (
          <KeyExchangeAnim
            alicePub={step.values?.alice_public_key_sent}
            bobPub={step.values?.bob_public_key_sent}
          />
        )}

        {step.step === 7 && <EncryptionAnim />}

        {step.step === 8 && <HmacAnim mode="sign" verified={true} />}

        {step.step === 9 && (
          <HmacAnim mode="verify" verified={step.values?.hmac_verified !== false} />
        )}

        {/* Connection line for transmission steps */}
        {lineProps.show && (
          <ConnectionLine
            direction={lineProps.direction}
            color={lineProps.color}
            label={lineProps.label}
          />
        )}

        {/* ── Step 9 outcome banner ──────────────────── */}
        {step.step === 9 && (
          <div
            className={`
              mt-4 flex items-center gap-3 p-3 rounded-lg border font-mono text-sm font-bold
              ${isFailure
                ? 'bg-red-950/60 border-red-500/60 text-red-400 animate-shake'
                : 'bg-green-950/60 border-green-500/50 text-green-400'
              }
            `}
          >
            <span className="text-xl">{isFailure ? '🚫' : '✅'}</span>
            <div>
              <div>{isFailure ? 'HANDSHAKE FAILED' : 'HANDSHAKE SUCCESSFUL'}</div>
              {isFailure && (
                <div className="text-xs font-normal text-red-500/80 mt-0.5 tracking-normal">
                  {step.values?.error}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Decrypted message reveal */}
        {step.values?.decrypted_message && (
          <div className="mt-3 p-3 rounded-lg bg-green-950/40 border border-green-500/30 animate-fade-in">
            <div className="text-[10px] text-green-600 font-mono mb-1">
              ✓ decrypted message:
            </div>
            <div className="text-green-300 font-mono text-sm">
              "{step.values.decrypted_message}"
            </div>
          </div>
        )}

        {/* Hex inspector */}
        <HexInspector values={step.values} />
      </div>
    </div>
  )
}
