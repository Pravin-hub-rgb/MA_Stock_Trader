import React, { createContext, useContext, useState, ReactNode } from 'react'

export interface ScanResult {
  symbol: string
  close: number
  // Continuation specific fields
  sma20?: number
  dist_to_ma_pct?: number
  phase1_high?: number
  phase2_low?: number
  phase3_high?: number
  depth_rs?: number
  depth_pct?: number
  // Common required fields
  adr_pct: number
  // Reversal specific fields
  period?: number
  red_days?: number
  green_days?: number
  decline_percent?: number
  trend_context?: string
  liquidity_verified?: boolean
  adr_percent?: number
}

export interface BreadthData {
  date: string
  up_4_5_pct: number
  down_4_5_pct: number
  up_20_pct_5d: number
  down_20_pct_5d: number
  above_20ma: number
  below_20ma: number
  above_50ma: number
  below_50ma: number
}

export interface OperationStatus {
  type: string
  status: 'running' | 'completed' | 'error'
  progress: number
  message: string
  error?: string
  result?: any
}

export interface CacheInfo {
  cache_exists: boolean
  total_files: number
  total_size_mb: number
  last_updated: string | null
}

export interface AppState {
  // Navigation state
  activeScannerTab: 'cache' | 'continuation' | 'reversal' | 'stocks-list'
  activeLiveTradingTab: 'token' | 'validation' | 'trading'

  // Scan results
  continuationResults: ScanResult[]
  reversalResults: ScanResult[]

  // Live trading
  liveTradingLogs: string[]
  isBotRunning: boolean
  botProcessId: number | null

  // Market breadth
  breadthData: BreadthData[]
  breadthLastUpdated: string | null

  // Cache operations
  cacheInfo: CacheInfo | null
  currentOperation: OperationStatus | null

  // Operation tracking
  activeOperations: { [key: string]: OperationStatus }
}

interface AppStateContextType {
  state: AppState
  updateState: (updates: Partial<AppState>) => void
  setContinuationResults: (results: ScanResult[]) => void
  setReversalResults: (results: ScanResult[]) => void
  setLiveTradingLogs: (logs: string[]) => void
  setBotStatus: (running: boolean, processId?: number | null) => void
  setBreadthData: (data: BreadthData[], lastUpdated?: string) => void
  setCacheInfo: (info: CacheInfo) => void
  setCurrentOperation: (operation: OperationStatus | null) => void
  addActiveOperation: (id: string, operation: OperationStatus) => void
  updateActiveOperation: (id: string, updates: Partial<OperationStatus>) => void
  removeActiveOperation: (id: string) => void
}

const initialState: AppState = {
  // Navigation state
  activeScannerTab: 'cache',
  activeLiveTradingTab: 'token',

  // Scan results
  continuationResults: [],
  reversalResults: [],

  // Live trading
  liveTradingLogs: [],
  isBotRunning: false,
  botProcessId: null,

  // Market breadth
  breadthData: [],
  breadthLastUpdated: null,

  // Cache operations
  cacheInfo: null,
  currentOperation: null,

  // Operation tracking
  activeOperations: {}
}

const AppStateContext = createContext<AppStateContextType | undefined>(undefined)

export const AppStateProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AppState>(initialState)

  const updateState = (updates: Partial<AppState>) => {
    setState(prev => ({ ...prev, ...updates }))
  }

  // Specific setters for common operations
  const setContinuationResults = (results: ScanResult[]) => {
    updateState({ continuationResults: results })
  }

  const setReversalResults = (results: ScanResult[]) => {
    updateState({ reversalResults: results })
  }

  const setLiveTradingLogs = (logs: string[]) => {
    updateState({ liveTradingLogs: logs })
  }

  const setBotStatus = (running: boolean, processId?: number | null) => {
    updateState({
      isBotRunning: running,
      botProcessId: processId ?? state.botProcessId
    })
  }

  const setBreadthData = (data: BreadthData[], lastUpdated?: string) => {
    updateState({
      breadthData: data,
      breadthLastUpdated: lastUpdated ?? state.breadthLastUpdated
    })
  }

  const setCacheInfo = (info: CacheInfo) => {
    updateState({ cacheInfo: info })
  }

  const setCurrentOperation = (operation: OperationStatus | null) => {
    updateState({ currentOperation: operation })
  }

  const addActiveOperation = (id: string, operation: OperationStatus) => {
    updateState({
      activeOperations: { ...state.activeOperations, [id]: operation }
    })
  }

  const updateActiveOperation = (id: string, updates: Partial<OperationStatus>) => {
    if (state.activeOperations[id]) {
      updateState({
        activeOperations: {
          ...state.activeOperations,
          [id]: { ...state.activeOperations[id], ...updates }
        }
      })
    }
  }

  const removeActiveOperation = (id: string) => {
    const newOperations = { ...state.activeOperations }
    delete newOperations[id]
    updateState({ activeOperations: newOperations })
  }

  const value: AppStateContextType = {
    state,
    updateState,
    setContinuationResults,
    setReversalResults,
    setLiveTradingLogs,
    setBotStatus,
    setBreadthData,
    setCacheInfo,
    setCurrentOperation,
    addActiveOperation,
    updateActiveOperation,
    removeActiveOperation
  }

  return (
    <AppStateContext.Provider value={value}>
      {children}
    </AppStateContext.Provider>
  )
}

export const useAppState = () => {
  const context = useContext(AppStateContext)
  if (context === undefined) {
    throw new Error('useAppState must be used within an AppStateProvider')
  }
  return context
}
