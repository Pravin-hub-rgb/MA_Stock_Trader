import React, { useState } from 'react'
import {
  Typography,
  Box,
  Tabs,
  Tab
} from '@mui/material'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import ContinuationScanner from './ContinuationScanner'
import ReversalScanner from './ReversalScanner'

interface ScanResult {
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
  adr_pct?: number
  // Reversal specific fields
  period?: number
  red_days?: number
  green_days?: number
  decline_percent?: number
  trend_context?: string
  liquidity_verified?: boolean
  adr_percent?: number
}

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'continuation' | 'reversal'>('continuation')
  const [continuationResults, setContinuationResults] = useState<ScanResult[]>([])
  const [reversalResults, setReversalResults] = useState<ScanResult[]>([])

  const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    setActiveTab(newValue as 'continuation' | 'reversal')
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      {/* Scanner Tabs - Always Visible */}
      <Box sx={{ mb: 4 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          sx={{
            backgroundColor: 'rgba(255,255,255,0.02)',
            borderRadius: 3,
            padding: 1,
            '& .MuiTab-root': {
              fontSize: '0.95rem',
              fontWeight: 600,
              textTransform: 'none',
              minHeight: 48,
              borderRadius: 2,
              fontFamily: '"Inter", sans-serif',
              transition: 'all 0.3s ease',
              '&:hover': {
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
              },
            },
            '& .MuiTabs-indicator': {
              display: 'none',
            },
          }}
        >
          <Tab
            label="Continuation"
            value="continuation"
            icon={<TrendingUpIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            sx={{
              minWidth: 160,
              backgroundColor: activeTab === 'continuation' ? 'rgba(16, 185, 129, 0.1)' : 'transparent',
              color: activeTab === 'continuation' ? '#10b981 !important' : undefined,
            }}
          />
          <Tab
            label="Reversal"
            value="reversal"
            icon={<TrendingDownIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            sx={{
              minWidth: 160,
              backgroundColor: activeTab === 'reversal' ? 'rgba(245, 158, 11, 0.1)' : 'transparent',
              color: activeTab === 'reversal' ? '#f59e0b !important' : undefined,
            }}
          />
        </Tabs>
      </Box>

      {/* Scanner Content */}
      <Box>
        {activeTab === 'continuation' && (
          <ContinuationScanner
            scanResults={continuationResults}
            setScanResults={setContinuationResults}
          />
        )}
        {activeTab === 'reversal' && (
          <ReversalScanner
            scanResults={reversalResults}
            setScanResults={setReversalResults}
          />
        )}
      </Box>
    </Box>
  )
}

export default Dashboard
