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
  Schedule as ScheduleIcon
} from '@mui/icons-material'
import axios from 'axios'

interface ContinuationStock {
  symbol: string
  added_at: string
  added_from: string
}

const StocksList: React.FC = () => {
  const [continuationStocks, setContinuationStocks] = useState<ContinuationStock[]>([])
  const [loading, setLoading] = useState(true)
  const [finalizing, setFinalizing] = useState(false)
  const [clearDialog, setClearDialog] = useState(false)
  const [sortConfig, setSortConfig] = useState<{key: keyof ContinuationStock, direction: 'asc' | 'desc'} | null>({
    key: 'added_at',
    direction: 'desc'
  })

  // Load continuation stocks on mount
  useEffect(() => {
    loadContinuationStocks()
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
    } catch (error) {
      console.error('Failed to delete stock:', error)
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
      alert('Continuation list finalized successfully!')
    } catch (error) {
      console.error('Failed to finalize list:', error)
      alert('Failed to finalize continuation list')
    } finally {
      setFinalizing(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'scan_results': return '#10b981'
      case 'manual': return '#3b82f6'
      default: return '#6b7280'
    }
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

        {/* Reversal Stocks Section (Placeholder) */}
        <Grid item xs={12} md={6}>
          <Card sx={{
            background: 'linear-gradient(135deg, #111111 0%, #1a1a1a 100%)',
            border: '1px solid rgba(245, 158, 11, 0.2)',
            borderRadius: 3
          }}>
            <CardContent sx={{ p: 3, textAlign: 'center', minHeight: 300 }}>
              <Typography variant="h6" sx={{ color: '#f59e0b', fontWeight: 600, mb: 2 }}>
                Reversal Stocks Management
              </Typography>
              <Typography sx={{ color: '#6b7280' }}>
                Coming Soon...
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Clear All Confirmation Dialog */}
      <Dialog
        open={clearDialog}
        onClose={() => setClearDialog(false)}
        PaperProps={{
          sx: {
            backgroundColor: '#1a1a1a',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 3
          }
        }}
      >
        <DialogTitle sx={{ color: '#f8fafc', fontFamily: '"Inter", sans-serif' }}>
          Clear All Continuation Stocks?
        </DialogTitle>
        <DialogContent>
          <Typography sx={{ color: '#94a3b8' }}>
            This will remove all {continuationStocks.length} stocks from the continuation list.
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClearDialog(false)} sx={{ color: '#6b7280' }}>
            Cancel
          </Button>
          <Button
            onClick={handleClearAll}
            sx={{
              backgroundColor: '#ef4444',
              '&:hover': { backgroundColor: '#dc2626' }
            }}
          >
            Clear All
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default StocksList
