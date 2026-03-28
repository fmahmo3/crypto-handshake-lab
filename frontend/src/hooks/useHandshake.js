import { useState, useCallback, useRef } from 'react'
import { startHandshake, advanceStep, enableTamper } from '../utils/api'

export function useHandshake() {
  const [sessionId, setSessionId] = useState(null)
  const [steps, setSteps] = useState([])
  const [currentStep, setCurrentStep] = useState(0)
  const [totalSteps, setTotalSteps] = useState(9)
  const [isComplete, setIsComplete] = useState(false)
  const [tamperMode, setTamperMode] = useState(false)
  const [plaintext, setPlaintext] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isRunningAll, setIsRunningAll] = useState(false)
  const [error, setError] = useState(null)

  // Ref allows the runAll loop to detect a reset mid-flight.
  const activeSessionRef = useRef(null)

  const reset = useCallback(async (customPlaintext) => {
    // Signal any running loop to stop.
    activeSessionRef.current = null
    setIsRunningAll(false)
    setIsLoading(true)
    setError(null)
    setSteps([])
    setCurrentStep(0)
    setIsComplete(false)
    setTamperMode(false)
    try {
      const data = await startHandshake(customPlaintext)
      activeSessionRef.current = data.session_id
      setSessionId(data.session_id)
      setCurrentStep(data.current_step)
      setTotalSteps(data.total_steps)
      setIsComplete(data.is_complete)
      setTamperMode(data.tamper_mode)
      setPlaintext(data.plaintext)
    } catch (e) {
      setError(e.response?.data?.detail ?? e.message)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const advance = useCallback(async () => {
    if (!sessionId || isComplete || isLoading || isRunningAll) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await advanceStep(sessionId)
      setCurrentStep(data.current_step)
      setIsComplete(data.is_complete)
      setTamperMode(data.tamper_mode)
      setSteps(prev => [...prev, data.step])
    } catch (e) {
      setError(e.response?.data?.detail ?? e.message)
    } finally {
      setIsLoading(false)
    }
  }, [sessionId, isComplete, isLoading, isRunningAll])

  const toggleTamper = useCallback(async () => {
    if (!sessionId || tamperMode || isComplete) return
    setError(null)
    try {
      const data = await enableTamper(sessionId)
      setTamperMode(data.tamper_mode)
    } catch (e) {
      setError(e.response?.data?.detail ?? e.message)
    }
  }, [sessionId, tamperMode, isComplete])

  const runAll = useCallback(async () => {
    if (!sessionId || isComplete || isRunningAll) return
    const thisSession = sessionId
    setIsRunningAll(true)
    setError(null)
    try {
      let done = false
      while (!done) {
        // Abort if a reset happened while waiting.
        if (activeSessionRef.current !== thisSession) break
        setIsLoading(true)
        const data = await advanceStep(thisSession)
        setIsLoading(false)
        // Double-check after await — reset may have fired.
        if (activeSessionRef.current !== thisSession) break
        setCurrentStep(data.current_step)
        setIsComplete(data.is_complete)
        setTamperMode(data.tamper_mode)
        setSteps(prev => [...prev, data.step])
        done = data.is_complete
        if (!done) {
          await new Promise(resolve => setTimeout(resolve, 1500))
        }
      }
    } catch (e) {
      if (activeSessionRef.current === thisSession) {
        setError(e.response?.data?.detail ?? e.message)
      }
    } finally {
      setIsLoading(false)
      if (activeSessionRef.current === thisSession) {
        setIsRunningAll(false)
      }
    }
  }, [sessionId, isComplete, isRunningAll])

  return {
    sessionId,
    steps,
    currentStep,
    totalSteps,
    isComplete,
    tamperMode,
    plaintext,
    isLoading,
    isRunningAll,
    error,
    reset,
    advance,
    toggleTamper,
    runAll,
  }
}
