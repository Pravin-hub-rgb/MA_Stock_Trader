import React, { useState } from 'react'
import {
  Typography,
  Box,
  Tabs,
  Tab
} from '@mui/material'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import StorageIcon from '@mui/icons-material/Storage'
import ListIcon from '@mui/icons-material/List'
import ContinuationScanner from './ContinuationScanner'
import ReversalScanner from './ReversalScanner'
import CacheData from './CacheData'
import StocksList from './StocksList'
import { useAppState, ScanResult } from '../contexts/AppStateContext'

const Dashboard: React.FC = () => {
  const { state, setContinuationResults, setReversalResults, updateState } = useAppState()

  const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    updateState({ activeScannerTab: newValue as 'cache' | 'continuation' | 'reversal' | 'stocks-list' })
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      {/* Scanner Tabs - Always Visible */}
      <Box sx={{ mb: 4 }}>
        <Tabs
          value={state.activeScannerTab}
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
            label="Cache Data"
            value="cache"
            icon={<StorageIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            sx={{
              minWidth: 160,
              backgroundColor: state.activeScannerTab === 'cache' ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
              color: state.activeScannerTab === 'cache' ? '#3b82f6 !important' : undefined,
            }}
          />
          <Tab
            label="Continuation"
            value="continuation"
            icon={<TrendingUpIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            sx={{
              minWidth: 160,
              backgroundColor: state.activeScannerTab === 'continuation' ? 'rgba(16, 185, 129, 0.1)' : 'transparent',
              color: state.activeScannerTab === 'continuation' ? '#10b981 !important' : undefined,
            }}
          />
          <Tab
            label="Reversal"
            value="reversal"
            icon={<TrendingDownIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            sx={{
              minWidth: 160,
              backgroundColor: state.activeScannerTab === 'reversal' ? 'rgba(245, 158, 11, 0.1)' : 'transparent',
              color: state.activeScannerTab === 'reversal' ? '#f59e0b !important' : undefined,
            }}
          />
          <Tab
            label="Stocks List"
            value="stocks-list"
            icon={<ListIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            sx={{
              minWidth: 160,
              backgroundColor: state.activeScannerTab === 'stocks-list' ? 'rgba(139, 92, 246, 0.1)' : 'transparent',
              color: state.activeScannerTab === 'stocks-list' ? '#8b5cf6 !important' : undefined,
            }}
          />
        </Tabs>
      </Box>

      {/* Scanner Content */}
      <Box>
        {state.activeScannerTab === 'cache' && <CacheData />}
        {state.activeScannerTab === 'continuation' && (
          <ContinuationScanner
            scanResults={state.continuationResults}
            setScanResults={setContinuationResults}
          />
        )}
        {state.activeScannerTab === 'reversal' && (
          <ReversalScanner
            scanResults={state.reversalResults}
            setScanResults={setReversalResults}
          />
        )}
        {state.activeScannerTab === 'stocks-list' && <StocksList />}
      </Box>
    </Box>
  )
}

export default Dashboard
