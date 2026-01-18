import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  IconButton,
  Tooltip,
  Alert,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material'
import {
  Delete as DeleteIcon,
  ClearAll as ClearAllIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon
} from '@mui/icons-material'
import axios from 'axios'
import ToastNotification from '../components/ToastNotification'

interface ContinuationStock {
  symbol: string
  added_at: string
  added_from: string
}

interface ReversalStock {
  symbol: string
  period: number
  trend: string
  added_at: string
  added_from: string
}

const StocksList: React.FC = () => {
  const [continuationStocks, setContinuationStocks] = useState<ContinuationStock[]>([])
  const [reversalStocks, setReversalStocks] = useState<ReversalStock[]>([])
  const [loading, setLoading] = useState(true)
  const [finalizing, setFinalizing] = useState(false)
  const [clearDialog, setClearDialog] = useState(false)
  const [reversalClearDialog, setReversalClearDialog] = useState(false)
  const [reversalFinalizing, setReversalFinalizing] = useState(false)
  const [sortConfig, setSortConfig] = useState<{key: keyof ContinuationStock, direction: 'asc' | 'desc'} | null>({
    key: 'added_at',
    direction: 'desc'
  })
  const [reversalSortConfig, setReversalSortConfig] = useState<{key: keyof ReversalStock, direction: 'asc' | 'desc'} | null>({
    key: 'added_at',
    direction: 'desc'
  })
  const [toasts, setToasts] = useState<Array<{
    id: string
    message: string
    type: 'success' | 'error' | 'warning'
    position: number
  }>>([])
  const [nextToastPosition, setNextToastPosition] = useState(0)

  // Load stocks on mount
  useEffect(() => {
    loadContinuationStocks()
    loadReversalStocks()
  }, [])

  const loadContinuationStocks = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/stocks/continuation')
      setContinuationStocks(response.data.stocks || [])
    } catch (error) {
      console.error('Failed to load continuation stocks:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadReversalStocks = async () => {
    try {
      const response = await axios.get('/api/stocks/reversal')
      setReversalStocks(response.data.stocks || [])
    } catch (error) {
      console.error('Failed to load reversal stocks:', error)
    }
  }

  const handleSort = (key: keyof ContinuationStock) => {
    const direction = sortConfig?.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc'
    setSortConfig({ key, direction })

    const sorted = [...continuationStocks].sort((a, b) => {
      const aVal = a[key]
      const bVal = b[key]
      if (aVal < bVal) return direction === 'asc' ? -1 : 1
      if (aVal > bVal) return direction === 'asc' ? 1 : -1
      return 0
    })
    setContinuationStocks(sorted)
  }

  const handleDeleteStock = async (symbol: string) => {
    try {
      await axios.delete(`/api/stocks/continuation/${symbol}`)
      setContinuationStocks(prev => prev.filter(stock => stock.symbol !== symbol))
      showToast(`✅ Removed ${symbol} from continuation list`, 'success')
    } catch (error) {
      console.error('Failed to delete stock:', error)
      showToast(`❌ Failed to remove ${symbol} from continuation list`, 'error')
    }
  }

  const handleClearAll = async () => {
    try {
      await axios.delete('/api/stocks/continuation')
      setContinuationStocks([])
      setClearDialog(false)
    } catch (error) {
      console.error('Failed to clear all stocks:', error)
    }
  }

  const handleFinalizeList = async () => {
    try {
      setFinalizing(true)
      await axios.post('/api/stocks/continuation/finalize')
      showToast('✅ Continuation list finalized successfully!', 'success')
    } catch (error) {
      console.error('Failed to finalize list:', error)
      showToast('❌ Failed to finalize continuation list', 'error')
    } finally {
      setFinalizing(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const handleReversalSort = (key: keyof ReversalStock) => {
    const direction = reversalSortConfig?.key === key && reversalSortConfig.direction === 'asc' ? 'desc' : 'asc'
    setReversalSortConfig({ key, direction })

    const sorted = [...reversalStocks].sort((a, b) => {
      const aVal = a[key]
      const bVal = b[key]
      if (aVal < bVal) return direction === 'asc' ? -1 : 1
      if (aVal > bVal) return direction === 'asc' ? 1 : -1
      return 0
    })
    setReversalStocks(sorted)
  }

  const handleDeleteReversalStock = async (symbol: string) => {
    try {
      await axios.delete(`/api/stocks/reversal/${symbol}`)
      setReversalStocks(prev => prev.filter(stock => stock.symbol !== symbol))
      showToast(`✅ Removed ${symbol} from reversal list`, 'success')
    } catch (error) {
      console.error('Failed to delete reversal stock:', error)
      showToast(`❌ Failed to remove ${symbol} from reversal list`, 'error')
    }
  }

  const handleClearAllReversal = async () => {
    try {
      await axios.delete('/api/stocks/reversal')
      setReversalStocks([])
      setReversalClearDialog(false)
    } catch (error) {
      console.error('Failed to clear all reversal stocks:', error)
    }
  }

  const handleFinalizeReversalList = async () => {
    try {
      setReversalFinalizing(true)
      await axios.post('/api/stocks/reversal/finalize')
      showToast('✅ Reversal list finalized successfully!', 'success')
    } catch (error) {
      console.error('Failed to finalize reversal list:', error)
      showToast('❌ Failed to finalize reversal list', 'error')
    } finally {
      setReversalFinalizing(false)
    }
  }

  const formatReversalStock = (stock: ReversalStock) => {
    const trendChar = stock.trend === 'uptrend' ? 'u' : 'd'
    return `${stock.symbol}-${trendChar}${stock.period}`
  }

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'scan_results': return '#10b981'
      case 'manual': return '#3b82f6'
      default: return '#6b7280'
    }
  }

  // Toast notification system - supports unlimited simultaneous toasts
  const showToast = (message: string, type: 'success' | 'error' | 'warning' = 'success') => {
    const toastId = `toast-${Date.now()}-${Math.random()}`

    // Find the lowest available position
    const occupiedPositions = toasts.map(t => t.position).sort((a, b) => a - b)
    let position = 0
    for (let i = 0; i < occupiedPositions.length; i++) {
      if (occupiedPositions[i] !== i) {
        position = i
        break
      }
    }
    if (position === 0 && occupiedPositions.length > 0) {
      position = occupiedPositions.length
    }

    const newToast = { id: toastId, message, type, position }

    setToasts(prev => [...prev, newToast]) // No limit on toasts
  }

  const removeToast = (toastId: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== toastId))
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 4 }}>
        Stock Lists Management
      </Typography>

      <Grid container spacing={4}>
        {/* Continuation Stocks Section */}
        <Grid item xs={12} md={6}>
          <Card sx={{
            background: 'linear-gradient(135deg, #111111 0%, #1a1a1a 100%)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            borderRadius: 3
          }}>
            <CardContent sx={{ p: 0 }}>
              {/* Header */}
              <Box sx={{
                p: 3,
                borderBottom: '1px solid rgba(255,255,255,0.1)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <CheckCircleIcon sx={{ color: '#10b981' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600, color: '#f8fafc' }}>
                    Continuation Stocks ({continuationStocks.length})
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setClearDialog(true)}
                    disabled={continuationStocks.length === 0}
                    startIcon={<ClearAllIcon />}
                    sx={{
                      borderColor: 'rgba(239, 68, 68, 0.5)',
                      color: '#ef4444',
                      '&:hover': {
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)'
                      }
                    }}
                  >
                    Clear All
                  </Button>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={handleFinalizeList}
                    disabled={continuationStocks.length === 0 || finalizing}
                    startIcon={<CheckCircleIcon />}
                    sx={{
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #059669 0%, #047857 100%)'
                      }
                    }}
                  >
                    {finalizing ? 'Finalizing...' : 'Finalize List'}
                  </Button>
                </Box>
              </Box>

              {/* Table */}
              {continuationStocks.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ backgroundColor: 'rgba(255,255,255,0.02)' }}>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 600 }}>
                          <TableSortLabel
                            active={sortConfig?.key === 'symbol'}
                            direction={sortConfig?.key === 'symbol' ? sortConfig.direction : 'asc'}
                            onClick={() => handleSort('symbol')}
                            sx={{ color: '#94a3b8 !important' }}
                          >
                            Symbol
                          </TableSortLabel>
                        </TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 600 }}>
                          <TableSortLabel
                            active={sortConfig?.key === 'added_from'}
                            direction={sortConfig?.key === 'added_from' ? sortConfig.direction : 'asc'}
                            onClick={() => handleSort('added_from')}
                            sx={{ color: '#94a3b8 !important' }}
                          >
                            Source
                          </TableSortLabel>
                        </TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 600 }}>
                          <TableSortLabel
                            active={sortConfig?.key === 'added_at'}
                            direction={sortConfig?.key === 'added_at' ? sortConfig.direction : 'asc'}
                            onClick={() => handleSort('added_at')}
                            sx={{ color: '#94a3b8 !important' }}
                          >
                            Added At
                          </TableSortLabel>
                        </TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 600, width: 80 }}>
                          Actions
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {continuationStocks.map((stock) => (
                        <TableRow key={stock.symbol} sx={{
                          '&:hover': { backgroundColor: 'rgba(255,255,255,0.02)' },
                          borderBottom: '1px solid rgba(255,255,255,0.05)'
                        }}>
                          <TableCell sx={{ color: '#f8fafc', fontWeight: 600 }}>
                            {stock.symbol}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={stock.added_from.replace('_', ' ')}
                              size="small"
                              sx={{
                                backgroundColor: `${getSourceColor(stock.added_from)}20`,
                                color: getSourceColor(stock.added_from),
                                fontSize: '0.7rem'
                              }}
                            />
                          </TableCell>
                          <TableCell sx={{ color: '#94a3b8', fontSize: '0.8rem' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <ScheduleIcon sx={{ fontSize: 14 }} />
                              {formatDate(stock.added_at)}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Tooltip title="Remove from list">
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteStock(stock.symbol)}
                                sx={{ color: '#ef4444' }}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <Typography sx={{ color: '#6b7280', mb: 2 }}>
                    No continuation stocks added yet
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#6b7280' }}>
                    Add stocks from scan results using the "+" button
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Reversal Stocks Section */}
        <Grid item xs={12} md={6}>
          <Card sx={{
            background: 'linear-gradient(135deg, #111111 0%, #1a1a1a 100%)',
            border: '1px solid rgba(245, 158, 11, 0.2)',
            borderRadius: 3
          }}>
            <CardContent sx={{ p: 0 }}>
              {/* Header */}
              <Box sx={{
                p: 3,
                borderBottom: '1px solid rgba(255,255,255,0.1)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <CheckCircleIcon sx={{ color: '#f59e0b' }} />
                  <Typography variant="h6" sx={{ fontWeight: 600, color: '#f8fafc' }}>
                    Reversal Stocks ({reversalStocks.length})
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setReversalClearDialog(true)}
                    disabled={reversalStocks.length === 0}
                    startIcon={<ClearAllIcon />}
                    sx={{
                      borderColor: 'rgba(239, 68, 68, 0.5)',
                      color: '#ef4444',
                      '&:hover': {
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)'
                      }
                    }}
                  >
                    Clear All
                  </Button>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={handleFinalizeReversalList}
                    disabled={reversalStocks.length === 0 || reversalFinalizing}
                    startIcon={<CheckCircleIcon />}
                    sx={{
                      background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)'
                      }
                    }}
                  >
                    {reversalFinalizing ? 'Finalizing...' : 'Finalize List'}
                  </Button>
                </Box>
              </Box>

              {/* Table */}
              {reversalStocks.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow sx={{ backgroundColor: 'rgba(255,255,255,0.02)' }}>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 600 }}>
                          <TableSortLabel
                            active={reversalSortConfig?.key === 'symbol'}
                            direction={reversalSortConfig?.key === 'symbol' ? reversalSortConfig.direction : 'asc'}
                            onClick={() => handleReversalSort('symbol')}
                            sx={{ color: '#94a3b8 !important' }}
                          >
                            Symbol
                          </TableSortLabel>
                        </TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 600 }}>
                          <TableSortLabel
                            active={reversalSortConfig?.key === 'period'}
                            direction={reversalSortConfig?.key === 'period' ? reversalSortConfig.direction : 'asc'}
                            onClick={() => handleReversalSort('period')}
                            sx={{ color: '#94a3b8 !important' }}
                          >
                            Period
                          </TableSortLabel>
                        </TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 600 }}>
                          <TableSortLabel
                            active={reversalSortConfig?.key === 'trend'}
                            direction={reversalSortConfig?.key === 'trend' ? reversalSortConfig.direction : 'asc'}
                            onClick={() => handleReversalSort('trend')}
                            sx={{ color: '#94a3b8 !important' }}
                          >
                            Trend
                          </TableSortLabel>
                        </TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 600 }}>
                          <TableSortLabel
                            active={reversalSortConfig?.key === 'added_at'}
                            direction={reversalSortConfig?.key === 'added_at' ? reversalSortConfig.direction : 'asc'}
                            onClick={() => handleReversalSort('added_at')}
                            sx={{ color: '#94a3b8 !important' }}
                          >
                            Added At
                          </TableSortLabel>
                        </TableCell>
                        <TableCell sx={{ color: '#94a3b8', fontWeight: 600, width: 80 }}>
                          Actions
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {reversalStocks.map((stock) => (
                        <TableRow key={stock.symbol} sx={{
                          '&:hover': { backgroundColor: 'rgba(255,255,255,0.02)' },
                          borderBottom: '1px solid rgba(255,255,255,0.05)'
                        }}>
                          <TableCell sx={{ color: '#f8fafc', fontWeight: 600 }}>
                            {stock.symbol}
                          </TableCell>
                          <TableCell sx={{ color: '#f8fafc' }}>
                            {stock.period}
                          </TableCell>
                          <TableCell sx={{
                            color: stock.trend === 'uptrend' ? '#10b981' : '#ef4444',
                            fontWeight: 600
                          }}>
                            {stock.trend === 'uptrend' ? 'Up' : 'Down'}
                          </TableCell>
                          <TableCell sx={{ color: '#94a3b8', fontSize: '0.8rem' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <ScheduleIcon sx={{ fontSize: 14 }} />
                              {formatDate(stock.added_at)}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Tooltip title="Remove from list">
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteReversalStock(stock.symbol)}
                                sx={{ color: '#ef4444' }}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <Typography sx={{ color: '#6b7280', mb: 2 }}>
                    No reversal stocks added yet
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#6b7280' }}>
                    Add stocks from scan results using the "+" button
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Clear All Continuation Confirmation Dialog */}
      <Dialog
        open={clearDialog}
        onClose={() => setClearDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            background: 'linear-gradient(135deg, #1a1a1a 0%, #111111 100%)',
            border: '2px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 4,
            boxShadow: '0 20px 60px rgba(0,0,0,0.5)'
          }
        }}
      >
        <DialogTitle sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          color: '#f8fafc',
          fontFamily: '"Inter", sans-serif',
          fontWeight: 700,
          fontSize: '1.25rem',
          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%)',
          borderBottom: '1px solid rgba(239, 68, 68, 0.2)',
          p: 3
        }}>
          <WarningIcon sx={{ color: '#ef4444', fontSize: 28 }} />
          Clear All Continuation Stocks?
        </DialogTitle>

        <DialogContent sx={{ p: 3 }}>
          <Typography sx={{
            color: '#f8fafc',
            fontSize: '1rem',
            fontWeight: 500,
            mb: 2
          }}>
            ⚠️ This action cannot be undone
          </Typography>

          <Typography sx={{ color: '#94a3b8', mb: 3, lineHeight: 1.6 }}>
            You are about to remove <strong style={{ color: '#ef4444' }}>{continuationStocks.length} stocks</strong> from your continuation list.
            This will permanently delete all continuation stocks and cannot be recovered.
          </Typography>

          {continuationStocks.length > 0 && continuationStocks.length <= 5 && (
            <Box sx={{ mb: 3 }}>
              <Typography sx={{ color: '#6b7280', fontSize: '0.9rem', mb: 1 }}>
                Stocks to be removed:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {continuationStocks.slice(0, 5).map((stock) => (
                  <Chip
                    key={stock.symbol}
                    label={stock.symbol}
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(239, 68, 68, 0.1)',
                      color: '#ef4444',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      fontWeight: 600
                    }}
                  />
                ))}
              </Box>
            </Box>
          )}

          {continuationStocks.length > 5 && (
            <Typography sx={{ color: '#6b7280', fontSize: '0.9rem', fontStyle: 'italic' }}>
              Including {continuationStocks.slice(0, 3).map(s => s.symbol).join(', ')} and {continuationStocks.length - 3} more...
            </Typography>
          )}
        </DialogContent>

        <DialogActions sx={{
          p: 3,
          pt: 0,
          gap: 2,
          justifyContent: 'flex-end'
        }}>
          <Button
            onClick={() => setClearDialog(false)}
            variant="outlined"
            sx={{
              borderColor: 'rgba(107, 114, 128, 0.5)',
              color: '#6b7280',
              px: 3,
              py: 1.5,
              borderRadius: 2,
              fontWeight: 600,
              '&:hover': {
                borderColor: '#6b7280',
                backgroundColor: 'rgba(107, 114, 128, 0.1)'
              }
            }}
          >
            Keep Stocks
          </Button>
          <Button
            onClick={handleClearAll}
            variant="contained"
            sx={{
              background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
              color: '#ffffff',
              px: 3,
              py: 1.5,
              borderRadius: 2,
              fontWeight: 700,
              fontSize: '0.95rem',
              boxShadow: '0 4px 15px rgba(239, 68, 68, 0.4)',
              '&:hover': {
                background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
                transform: 'translateY(-1px)',
                boxShadow: '0 6px 20px rgba(239, 68, 68, 0.6)'
              }
            }}
          >
            🗑️ Clear All Stocks
          </Button>
        </DialogActions>
      </Dialog>

      {/* Clear All Reversal Confirmation Dialog */}
      <Dialog
        open={reversalClearDialog}
        onClose={() => setReversalClearDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            background: 'linear-gradient(135deg, #1a1a1a 0%, #111111 100%)',
            border: '2px solid rgba(245, 158, 11, 0.3)',
            borderRadius: 4,
            boxShadow: '0 20px 60px rgba(0,0,0,0.5)'
          }
        }}
      >
        <DialogTitle sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          color: '#f8fafc',
          fontFamily: '"Inter", sans-serif',
          fontWeight: 700,
          fontSize: '1.25rem',
          background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%)',
          borderBottom: '1px solid rgba(245, 158, 11, 0.2)',
          p: 3
        }}>
          <WarningIcon sx={{ color: '#f59e0b', fontSize: 28 }} />
          Clear All Reversal Stocks?
        </DialogTitle>

        <DialogContent sx={{ p: 3 }}>
          <Typography sx={{
            color: '#f8fafc',
            fontSize: '1rem',
            fontWeight: 500,
            mb: 2
          }}>
            ⚠️ This action cannot be undone
          </Typography>

          <Typography sx={{ color: '#94a3b8', mb: 3, lineHeight: 1.6 }}>
            You are about to remove <strong style={{ color: '#f59e0b' }}>{reversalStocks.length} stocks</strong> from your reversal list.
            This will permanently delete all reversal stocks and cannot be recovered.
          </Typography>

          {reversalStocks.length > 0 && reversalStocks.length <= 5 && (
            <Box sx={{ mb: 3 }}>
              <Typography sx={{ color: '#6b7280', fontSize: '0.9rem', mb: 1 }}>
                Stocks to be removed:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {reversalStocks.slice(0, 5).map((stock) => (
                  <Chip
                    key={stock.symbol}
                    label={`${stock.symbol}-${stock.trend === 'uptrend' ? 'u' : 'd'}${stock.period}`}
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(245, 158, 11, 0.1)',
                      color: '#f59e0b',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      fontWeight: 600
                    }}
                  />
                ))}
              </Box>
            </Box>
          )}

          {reversalStocks.length > 5 && (
            <Typography sx={{ color: '#6b7280', fontSize: '0.9rem', fontStyle: 'italic' }}>
              Including {reversalStocks.slice(0, 3).map(s => `${s.symbol}-${s.trend === 'uptrend' ? 'u' : 'd'}${s.period}`).join(', ')} and {reversalStocks.length - 3} more...
            </Typography>
          )}
        </DialogContent>

        <DialogActions sx={{
          p: 3,
          pt: 0,
          gap: 2,
          justifyContent: 'flex-end'
        }}>
          <Button
            onClick={() => setReversalClearDialog(false)}
            variant="outlined"
            sx={{
              borderColor: 'rgba(107, 114, 128, 0.5)',
              color: '#6b7280',
              px: 3,
              py: 1.5,
              borderRadius: 2,
              fontWeight: 600,
              '&:hover': {
                borderColor: '#6b7280',
                backgroundColor: 'rgba(107, 114, 128, 0.1)'
              }
            }}
          >
            Keep Stocks
          </Button>
          <Button
            onClick={handleClearAllReversal}
            variant="contained"
            sx={{
              background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
              color: '#ffffff',
              px: 3,
              py: 1.5,
              borderRadius: 2,
              fontWeight: 700,
              fontSize: '0.95rem',
              boxShadow: '0 4px 15px rgba(245, 158, 11, 0.4)',
              '&:hover': {
                background: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)',
                transform: 'translateY(-1px)',
                boxShadow: '0 6px 20px rgba(245, 158, 11, 0.6)'
              }
            }}
          >
            🗑️ Clear All Stocks
          </Button>
        </DialogActions>
      </Dialog>

      {/* Toast Notifications - Fixed position layout */}
      {toasts.map((toast) => (
        <Box
          key={toast.id}
          sx={{
            position: 'fixed',
            bottom: 24 + (toast.position * 60), // Fixed position per toast
            left: 24,
            zIndex: 9999, // Same z-index since they're not overlapping
            minWidth: 450, // Wider to fit text on one line
            maxWidth: 600, // Allow even wider if needed
            animation: `slideInFromRight 0.3s ease-out both`
          }}
        >
          <ToastNotification
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
            duration={3500}
          />
        </Box>
      ))}

      {/* Add custom animation for staggered slide-in */}
      <style>
        {`
          @keyframes slideInFromRight {
            from {
              transform: translateX(120%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `}
      </style>
    </Box>
  )
}

export default StocksList
