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
  LinearProgress
} from '@mui/material'
import ToastNotification from '../components/ToastNotification'
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
  const [toasts, setToasts] = useState<Array<{
    id: string
    message: string
    type: 'success' | 'error' | 'warning'
    position: number
  }>>([])

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
        showToast(`Cache has been successfully updated with the latest market data.\n\nUpdated data for: ${data.result.date}`, 'success')
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

  // Toast notification system
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

    setToasts(prev => [...prev, newToast])
  }

  const removeToast = (toastId: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== toastId))
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

      {/* Toast Notifications */}
      {toasts.map((toast) => (
        <Box
          key={toast.id}
          sx={{
            position: 'fixed',
            bottom: 24 + (toast.position * 60),
            left: 24,
            zIndex: 9999,
            minWidth: 450,
            maxWidth: 600,
            animation: `slideInFromLeft 0.3s ease-out both`
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

      {/* Add custom animation for slide-in */}
      <style>
        {`
          @keyframes slideInFromLeft {
            from {
              transform: translateX(-120%);
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

export default CacheData
