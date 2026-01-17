import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon
} from '@mui/icons-material'

interface CacheInfo {
  cache_exists: boolean
  total_files: number
  total_size_mb: number
  last_updated: string | null
}

interface OperationStatus {
  type: string
  status: 'running' | 'completed' | 'error'
  progress: number
  message: string
  error?: string
  result?: any
}

const CacheData: React.FC = () => {
  const [cacheInfo, setCacheInfo] = useState<CacheInfo | null>(null)
  const [operationStatus, setOperationStatus] = useState<OperationStatus | null>(null)
  const [operationId, setOperationId] = useState<string | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)
  const [showSuccessDialog, setShowSuccessDialog] = useState(false)
  const [lastUpdateResult, setLastUpdateResult] = useState<any>(null)

  // Load cache information on component mount
  useEffect(() => {
    loadCacheInfo()
  }, [])

  // Poll for operation status if there's an active operation
  useEffect(() => {
    let interval: number | null = null

    if (operationId && operationStatus?.status === 'running') {
      interval = setInterval(() => {
        checkOperationStatus()
      }, 2000) // Check every 2 seconds
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [operationId, operationStatus?.status])

  const loadCacheInfo = async () => {
    try {
      const response = await fetch('/api/data/cache-info')
      const data = await response.json()
      setCacheInfo(data)
    } catch (error) {
      console.error('Failed to load cache info:', error)
    }
  }

  const handleUpdateBhavcopy = async () => {
    setIsUpdating(true)
    try {
      const response = await fetch('/api/data/update-bhavcopy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const data = await response.json()

      if (data.status === 'started') {
        setOperationId(data.operation_id)
        setOperationStatus({
          type: 'bhavcopy_update',
          status: 'running',
          progress: 0,
          message: 'Bhavcopy data update started'
        })
      }
    } catch (error) {
      console.error('Failed to start bhavcopy update:', error)
      setIsUpdating(false)
    }
  }

  const checkOperationStatus = async () => {
    if (!operationId) return

    try {
      const response = await fetch(`/api/data/status/${operationId}`)
      const data = await response.json()

      setOperationStatus(data)

      if (data.status === 'completed') {
        setIsUpdating(false)
        setOperationId(null)
        setLastUpdateResult(data.result)
        setShowSuccessDialog(true)
        loadCacheInfo() // Refresh cache info
      } else if (data.status === 'error') {
        setIsUpdating(false)
        setOperationId(null)
      }
    } catch (error) {
      console.error('Failed to check operation status:', error)
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleString()
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'info'
      case 'completed': return 'success'
      case 'error': return 'error'
      default: return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon />
      case 'error': return <ErrorIcon />
      default: return <InfoIcon />
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 4, fontWeight: 600 }}>
        📊 Cache Data Management
      </Typography>

      <Grid container spacing={3}>
        {/* Cache Information Card */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <StorageIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Cache Status</Typography>
              </Box>

              {cacheInfo ? (
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Last date on cache:
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {cacheInfo.last_updated ? new Date(cacheInfo.last_updated).toLocaleDateString('en-GB', {
                      day: '2-digit',
                      month: 'short',
                      year: 'numeric'
                    }) : 'No data'}
                  </Typography>

                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Files: <strong>{cacheInfo.total_files}</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Cache Size: <strong>{cacheInfo.total_size_mb.toFixed(2)} MB</strong>
                    </Typography>
                  </Box>
                </Box>
              ) : (
                <Typography>Loading cache information...</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Update Controls Card */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Update Market Data
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Download the latest NSE bhavcopy data and update the local cache.
                This ensures your scanner has the most recent market information.
              </Typography>

              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={handleUpdateBhavcopy}
                disabled={isUpdating}
                fullWidth
                sx={{ mb: 2 }}
              >
                {isUpdating ? 'Updating...' : 'Update Bhavcopy Data'}
              </Button>

              <Typography variant="caption" color="text.secondary">
                Recommended: Run after market close (6 PM IST+) for same-day EOD data
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Operation Status */}
        {operationStatus && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {getStatusIcon(operationStatus.status)}
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    Operation Status
                  </Typography>
                  <Chip
                    label={operationStatus.status.toUpperCase()}
                    color={getStatusColor(operationStatus.status)}
                    size="small"
                    sx={{ ml: 'auto' }}
                  />
                </Box>

                <Typography variant="body1" sx={{ mb: 2 }}>
                  {operationStatus.message}
                </Typography>

                {operationStatus.status === 'running' && (
                  <LinearProgress
                    variant="determinate"
                    value={operationStatus.progress}
                    sx={{ mb: 1 }}
                  />
                )}

                {operationStatus.error && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    {operationStatus.error}
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Success Dialog */}
      <Dialog open={showSuccessDialog} onClose={() => setShowSuccessDialog(false)}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <CheckCircleIcon sx={{ mr: 1, color: 'success.main' }} />
          Data Update Successful
        </DialogTitle>
        <DialogContent>
          <Typography>
            Cache has been successfully updated with the latest market data.
          </Typography>
          {lastUpdateResult && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              Updated data for: {lastUpdateResult.date}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSuccessDialog(false)}>OK</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default CacheData
