import React, { useState, useEffect } from 'react'
import {
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Checkbox,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  TextField,
  Grid
} from '@mui/material'
import {
  Download as DownloadIcon,
  CopyAll as CopyIcon,
  Assessment as ResultsIcon
} from '@mui/icons-material'
import axios from 'axios'

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
  // Reversal specific fields
  period?: number
  red_days?: number
  green_days?: number
  decline_percent?: number
  trend_context?: string
  liquidity_verified?: boolean
  // Common fields
  adr_pct: number
}

interface ContinuationScannerProps {
  scanResults: ScanResult[]
  setScanResults: React.Dispatch<React.SetStateAction<ScanResult[]>>
}

const ContinuationScanner: React.FC<ContinuationScannerProps> = ({ scanResults, setScanResults }) => {
  // Load filter values from localStorage or use defaults
  const loadFilterValue = (key: string, defaultValue: number) => {
    const stored = localStorage.getItem(`continuation_${key}`)
    return stored ? parseInt(stored, 10) : defaultValue
  }

  const [isScanning, setIsScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState(0)
  const [scanStatus, setScanStatus] = useState('')
  const [selectedRows, setSelectedRows] = useState<string[]>([])
  const [sortConfig, setSortConfig] = useState<{key: keyof ScanResult, direction: 'asc' | 'desc'} | null>(null)
  const [watchlistDialog, setWatchlistDialog] = useState(false)
  const [watchlists, setWatchlists] = useState<string[]>(['Default', 'Continuation', 'High Potential'])
  const [operationId, setOperationId] = useState<string | null>(null)

  // Filter states with localStorage persistence
  const [minPrice, setMinPrice] = useState(() => loadFilterValue('minPrice', 100))
  const [maxPrice, setMaxPrice] = useState(() => loadFilterValue('maxPrice', 2000))
  const [nearMaThreshold, setNearMaThreshold] = useState(() => loadFilterValue('nearMaThreshold', 5))
  const [maxBodySize, setMaxBodySize] = useState(() => loadFilterValue('maxBodySize', 5))

  // Save filter values to localStorage when they change
  useEffect(() => {
    localStorage.setItem('continuation_minPrice', minPrice.toString())
  }, [minPrice])

  useEffect(() => {
    localStorage.setItem('continuation_maxPrice', maxPrice.toString())
  }, [maxPrice])

  useEffect(() => {
    localStorage.setItem('continuation_nearMaThreshold', nearMaThreshold.toString())
  }, [nearMaThreshold])

  useEffect(() => {
    localStorage.setItem('continuation_maxBodySize', maxBodySize.toString())
  }, [maxBodySize])

  const runScan = async () => {
    setIsScanning(true)
    setScanProgress(0)
    setScanStatus('Starting continuation scan...')
    setScanResults([])
    setOperationId(null)

    try {
      // Start the scan with filter parameters
      const scanParams = {
        date: null,
        filters: {
          min_price: minPrice,
          max_price: maxPrice,
          near_ma_threshold: nearMaThreshold,
          max_body_percentage: maxBodySize
        }
      }
      const response = await axios.post('http://localhost:8000/api/scanner/continuation', scanParams)
      const opId = response.data.operation_id
      setOperationId(opId)

      // Poll for status updates
      pollScanStatus(opId)

    } catch (error) {
      setScanStatus('Failed to start scan. Please try again.')
      console.error('Scan start error:', error)
      setIsScanning(false)
    }
  }

  const pollScanStatus = (opId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/scanner/status/${opId}`)
        const status = response.data

        setScanProgress(status.progress || 0)
        setScanStatus(status.message || 'Processing...')

        if (status.status === 'completed') {
          clearInterval(pollInterval)
          setIsScanning(false)

          if (status.result && status.result.results) {
            setScanResults(status.result.results)
          }

          setScanStatus(`Scan completed! Found ${status.result?.results_count || 0} continuation setups`)

        } else if (status.status === 'error') {
          clearInterval(pollInterval)
          setIsScanning(false)
          setScanStatus(`Scan failed: ${status.error || 'Unknown error'}`)
        }

      } catch (error) {
        console.error('Status poll error:', error)
        clearInterval(pollInterval)
        setIsScanning(false)
        setScanStatus('Lost connection to scan process')
      }
    }, 1000) // Poll every second
  }

  // Sort results
  const handleSort = (key: keyof ScanResult) => {
    const direction = sortConfig?.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc'
    setSortConfig({ key, direction })

    const sorted = [...scanResults].sort((a, b) => {
      const aVal = a[key] || 0
      const bVal = b[key] || 0
      if (aVal < bVal) return direction === 'asc' ? -1 : 1
      if (aVal > bVal) return direction === 'asc' ? 1 : -1
      return 0
    })
    setScanResults(sorted)
  }

  // Handle row selection
  const handleRowSelect = (symbol: string) => {
    setSelectedRows(prev =>
      prev.includes(symbol)
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    )
  }

  // Export to CSV
  const exportToCSV = () => {
    if (scanResults.length === 0) return

    const headers = ['Symbol', 'Close', 'SMA20', 'Dist to MA %', 'Phase1 High', 'Phase2 Low', 'Phase3 High', 'Depth Rs', 'Depth %', 'ADR %']
    const csvContent = [
      headers.join(','),
      ...scanResults.map(row => [
        row.symbol,
        row.close.toFixed(2),
        (row.sma20 || 0).toFixed(2),
        (row.dist_to_ma_pct || 0).toFixed(1),
        (row.phase1_high || 0).toFixed(2),
        (row.phase2_low || 0).toFixed(2),
        (row.phase3_high || 0).toFixed(2),
        (row.depth_rs || 0).toFixed(2),
        (row.depth_pct || 0).toFixed(1),
        row.adr_pct.toFixed(1)
      ].join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `continuation_scan_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  // Copy to clipboard in Fyers format
  const copyToClipboard = () => {
    const selectedSymbols = selectedRows.length > 0 ? selectedRows : scanResults.map(r => r.symbol)
    const fyersFormat = selectedSymbols.map(symbol => `NSE:${symbol}-EQ`).join(',')
    navigator.clipboard.writeText(fyersFormat)
    setScanStatus(`Copied ${selectedSymbols.length} symbols to clipboard in Fyers format`)
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      {/* Scan Controls */}
      <Card sx={{
        mb: 4,
        background: 'linear-gradient(135deg, #111111 0%, #1a1a1a 100%)',
        border: '1px solid rgba(99, 102, 241, 0.2)',
        borderRadius: 3
      }}>
        <CardContent sx={{ p: 4 }}>
          <Typography
            variant="h6"
            gutterBottom
            sx={{
              fontWeight: 600,
              fontFamily: '"Inter", sans-serif',
              color: '#f8fafc',
              mb: 3
            }}
          >
            Scan Controls
          </Typography>

          {/* Filter Inputs */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Min Price (₹)"
                type="number"
                value={minPrice}
                onChange={(e) => setMinPrice(Number(e.target.value))}
                InputLabelProps={{ sx: { color: '#94a3b8' } }}
                InputProps={{
                  sx: {
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                      '&:hover fieldset': { borderColor: 'rgba(99, 102, 241, 0.5)' },
                      '&.Mui-focused fieldset': { borderColor: '#6366f1' }
                    },
                    '& .MuiInputBase-input': { color: '#f8fafc' }
                  }
                }}
                inputProps={{ min: 10, max: 5000 }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Max Price (₹)"
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(Number(e.target.value))}
                InputLabelProps={{ sx: { color: '#94a3b8' } }}
                InputProps={{
                  sx: {
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                      '&:hover fieldset': { borderColor: 'rgba(99, 102, 241, 0.5)' },
                      '&.Mui-focused fieldset': { borderColor: '#6366f1' }
                    },
                    '& .MuiInputBase-input': { color: '#f8fafc' }
                  }
                }}
                inputProps={{ min: 100, max: 10000 }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Near MA Threshold (%)"
                type="number"
                value={nearMaThreshold}
                onChange={(e) => setNearMaThreshold(Number(e.target.value))}
                InputLabelProps={{ sx: { color: '#94a3b8' } }}
                InputProps={{
                  sx: {
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                      '&:hover fieldset': { borderColor: 'rgba(99, 102, 241, 0.5)' },
                      '&.Mui-focused fieldset': { borderColor: '#6366f1' }
                    },
                    '& .MuiInputBase-input': { color: '#f8fafc' }
                  }
                }}
                inputProps={{ min: 1, max: 20 }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Max Body Size (%)"
                type="number"
                value={maxBodySize}
                onChange={(e) => setMaxBodySize(Number(e.target.value))}
                InputLabelProps={{ sx: { color: '#94a3b8' } }}
                InputProps={{
                  sx: {
                    '& .MuiOutlinedInput-root': {
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                      '&:hover fieldset': { borderColor: 'rgba(99, 102, 241, 0.5)' },
                      '&.Mui-focused fieldset': { borderColor: '#6366f1' }
                    },
                    '& .MuiInputBase-input': { color: '#f8fafc' }
                  }
                }}
                inputProps={{ min: 1, max: 10 }}
              />
            </Grid>
          </Grid>

          {/* Run Scan Button */}
          <Box sx={{ textAlign: 'center' }}>
            <Button
              variant="contained"
              size="large"
              onClick={runScan}
              disabled={isScanning}
              sx={{
                px: 6,
                py: 2,
                fontSize: '1.1rem',
                fontWeight: 700,
                fontFamily: '"Inter", sans-serif',
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                borderRadius: 3,
                boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)',
                textTransform: 'none',
                '&:hover': {
                  background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 8px 25px rgba(99, 102, 241, 0.6)'
                },
                '&:disabled': {
                  background: 'rgba(255,255,255,0.1)',
                  color: 'rgba(255,255,255,0.5)'
                }
              }}
            >
              {isScanning ? 'Running Scan...' : 'Run Continuation Scan'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Progress & Status */}
      {isScanning && (
        <Card sx={{
          mb: 4,
          background: 'linear-gradient(135deg, #111111 0%, #1a1a1a 100%)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 3
        }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" sx={{ color: '#94a3b8', mb: 1 }}>
                {scanStatus}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={scanProgress}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: '#6366f1'
                  },
                  backgroundColor: 'rgba(255,255,255,0.1)'
                }}
              />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Status Message */}
      {scanStatus && !isScanning && (
        <Card sx={{
          mb: 4,
          background: 'linear-gradient(135deg, #111111 0%, #1a1a1a 100%)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 3
        }}>
          <CardContent sx={{ p: 3 }}>
            <Typography
              sx={{
                color: scanStatus.includes('completed') ? '#10b981' :
                       scanStatus.includes('failed') ? '#ef4444' : '#f8fafc',
                fontFamily: '"Inter", sans-serif'
              }}
            >
              {scanStatus}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Results Section */}
      {scanResults.length > 0 && (
        <Card sx={{
          background: 'linear-gradient(135deg, #111111 0%, #1a1a1a 100%)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 3
        }}>
          <CardContent sx={{ p: 0 }}>
            {/* Results Header */}
            <Box sx={{
              p: 3,
              borderBottom: '1px solid rgba(255,255,255,0.1)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <ResultsIcon sx={{ color: '#10b981' }} />
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 600,
                    fontFamily: '"Inter", sans-serif',
                    color: '#f8fafc'
                  }}
                >
                  Scan Results ({scanResults.length} stocks)
                </Typography>
                {selectedRows.length > 0 && (
                  <Chip
                    label={`${selectedRows.length} selected`}
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(99, 102, 241, 0.1)',
                      color: '#6366f1',
                      border: '1px solid rgba(99, 102, 241, 0.3)'
                    }}
                  />
                )}
              </Box>

              <Box sx={{ display: 'flex', gap: 1 }}>
                <Tooltip title="Copy to Clipboard (Fyers format)">
                  <IconButton
                    onClick={copyToClipboard}
                    sx={{ color: '#06b6d4' }}
                  >
                    <CopyIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Export to CSV">
                  <IconButton
                    onClick={exportToCSV}
                    sx={{ color: '#10b981' }}
                  >
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => setWatchlistDialog(true)}
                  disabled={selectedRows.length === 0}
                  sx={{
                    borderColor: 'rgba(255,255,255,0.2)',
                    color: '#f8fafc',
                    '&:hover': {
                      borderColor: '#6366f1',
                      backgroundColor: 'rgba(99, 102, 241, 0.1)'
                    }
                  }}
                >
                  Add to Watchlist
                </Button>
              </Box>
            </Box>

            {/* Results Table */}
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ backgroundColor: 'rgba(255,255,255,0.02)' }}>
                    <TableCell padding="checkbox">
                      <Checkbox
                        indeterminate={selectedRows.length > 0 && selectedRows.length < scanResults.length}
                        checked={selectedRows.length === scanResults.length && scanResults.length > 0}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedRows(scanResults.map(r => r.symbol))
                          } else {
                            setSelectedRows([])
                          }
                        }}
                        sx={{
                          color: 'rgba(255,255,255,0.5)',
                          '&.Mui-checked': { color: '#6366f1' }
                        }}
                      />
                    </TableCell>
                    {[
                      { key: 'symbol', label: 'Symbol' },
                      { key: 'close', label: 'Close' },
                      { key: 'dist_to_ma_pct', label: 'Dist to MA %' },
                      { key: 'phase1_high', label: 'Phase1 High' },
                      { key: 'phase2_low', label: 'Phase2 Low' },
                      { key: 'depth_pct', label: 'Depth %' },
                      { key: 'adr_pct', label: 'ADR %' }
                    ].map((column) => (
                      <TableCell
                        key={column.key}
                        sx={{
                          color: '#94a3b8',
                          fontWeight: 600,
                          fontFamily: '"Inter", sans-serif',
                          borderBottom: '1px solid rgba(255,255,255,0.1)'
                        }}
                      >
                        <TableSortLabel
                          active={sortConfig?.key === column.key}
                          direction={sortConfig?.key === column.key ? sortConfig.direction : 'asc'}
                          onClick={() => handleSort(column.key as keyof ScanResult)}
                          sx={{
                            color: '#94a3b8 !important',
                            '&:hover': { color: '#f8fafc !important' },
                            '&.MuiTableSortLabel-active': { color: '#6366f1 !important' }
                          }}
                        >
                          {column.label}
                        </TableSortLabel>
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {scanResults.map((row) => (
                    <TableRow
                      key={row.symbol}
                      sx={{
                        '&:hover': { backgroundColor: 'rgba(255,255,255,0.02)' },
                        borderBottom: '1px solid rgba(255,255,255,0.05)'
                      }}
                    >
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedRows.includes(row.symbol)}
                          onChange={() => handleRowSelect(row.symbol)}
                          sx={{
                            color: 'rgba(255,255,255,0.5)',
                            '&.Mui-checked': { color: '#6366f1' }
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ color: '#f8fafc', fontWeight: 600 }}>{row.symbol}</TableCell>
                      <TableCell sx={{ color: '#f8fafc' }}>₹{row.close.toFixed(2)}</TableCell>
                      <TableCell sx={{ color: (row.dist_to_ma_pct || 0) <= 5 ? '#10b981' : '#f8fafc' }}>
                        {(row.dist_to_ma_pct || 0).toFixed(1)}%
                      </TableCell>
                      <TableCell sx={{ color: '#f8fafc' }}>₹{(row.phase1_high || 0).toFixed(2)}</TableCell>
                      <TableCell sx={{ color: '#f8fafc' }}>₹{(row.phase2_low || 0).toFixed(2)}</TableCell>
                      <TableCell sx={{ color: '#f8fafc' }}>{(row.depth_pct || 0).toFixed(1)}%</TableCell>
                      <TableCell sx={{ color: row.adr_pct >= 3 ? '#10b981' : '#f8fafc' }}>
                        {row.adr_pct.toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Watchlist Dialog */}
      <Dialog
        open={watchlistDialog}
        onClose={() => setWatchlistDialog(false)}
        PaperProps={{
          sx: {
            backgroundColor: '#1a1a1a',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 3
          }
        }}
      >
        <DialogTitle sx={{ color: '#f8fafc', fontFamily: '"Inter", sans-serif' }}>
          Add to Watchlist
        </DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel sx={{ color: '#94a3b8' }}>Select Watchlist</InputLabel>
            <Select
              value=""
              label="Select Watchlist"
              sx={{
                '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.2)' },
                '& .MuiSelect-select': { color: '#f8fafc' },
                '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(99, 102, 241, 0.5)' }
              }}
            >
              {watchlists.map((watchlist) => (
                <MenuItem key={watchlist} value={watchlist} sx={{ color: '#f8fafc' }}>
                  {watchlist}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setWatchlistDialog(false)} sx={{ color: '#94a3b8' }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            sx={{
              backgroundColor: '#6366f1',
              '&:hover': { backgroundColor: '#4f46e5' }
            }}
          >
            Add Selected Stocks
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ContinuationScanner
