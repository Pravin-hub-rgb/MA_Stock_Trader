import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material'

interface BreadthData {
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

const CacheData: React.FC = () => {
  const [breadthData, setBreadthData] = useState<BreadthData[]>([])
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)
  const [showSuccessDialog, setShowSuccessDialog] = useState(false)

  // Load breadth data on component mount
  useEffect(() => {
    loadBreadthData()
  }, [])

  const loadBreadthData = async () => {
    try {
      const response = await fetch('/api/breadth/data')
      const data = await response.json()
      setBreadthData(data.data || [])
      setLastUpdated(data.last_updated)
    } catch (error) {
      console.error('Failed to load breadth data:', error)
    }
  }

  const handleUpdateBreadth = async () => {
    setIsUpdating(true)
    try {
      const response = await fetch('/api/breadth/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const data = await response.json()

      if (data.status === 'success') {
        setBreadthData(data.data || [])
        setLastUpdated(data.last_updated)
        setShowSuccessDialog(true)
      }
    } catch (error) {
      console.error('Failed to update breadth data:', error)
    } finally {
      setIsUpdating(false)
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 4, fontWeight: 600 }}>
        📊 Market Breadth Data
      </Typography>

      {/* Status and Update Button */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Status: {breadthData.length > 0 ? `${breadthData.length} dates cached` : 'No data cached'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Last Updated: {lastUpdated ? new Date(lastUpdated).toLocaleString() : 'Never'}
              </Typography>
            </Box>
            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={handleUpdateBreadth}
              disabled={isUpdating}
              size="large"
            >
              {isUpdating ? 'Updating...' : 'Update'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Data Display */}
      <Card>
        <CardContent>
          {breadthData.length > 0 ? (
            <Box>
              <Typography variant="h6" gutterBottom>
                Latest Breadth Data:
              </Typography>
              {breadthData.slice(0, 5).map((row, index) => (
                <Box key={row.date} sx={{ mb: 2, p: 2, border: '1px solid #eee', borderRadius: 1 }}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {new Date(row.date).toLocaleDateString('en-US', {
                      month: '2-digit',
                      day: '2-digit',
                      year: 'numeric'
                    })}
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 1, mt: 1 }}>
                    <Typography variant="body2">Up 4.5%: <strong>{row.up_4_5_pct}</strong></Typography>
                    <Typography variant="body2">Down 4.5%: <strong>{row.down_4_5_pct}</strong></Typography>
                    <Typography variant="body2">Up 20% 5d: <strong>{row.up_20_pct_5d}</strong></Typography>
                    <Typography variant="body2">Down 20% 5d: <strong>{row.down_20_pct_5d}</strong></Typography>
                    <Typography variant="body2">Above 20MA: <strong>{row.above_20ma}</strong></Typography>
                    <Typography variant="body2">Below 20MA: <strong>{row.below_20ma}</strong></Typography>
                    <Typography variant="body2">Above 50MA: <strong>{row.above_50ma}</strong></Typography>
                    <Typography variant="body2">Below 50MA: <strong>{row.below_50ma}</strong></Typography>
                  </Box>
                </Box>
              ))}
              {breadthData.length > 5 && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  ... and {breadthData.length - 5} more dates
                </Typography>
              )}
            </Box>
          ) : (
            <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
              No breadth data available. Click "Update" to calculate and cache the latest market breadth analysis.
            </Typography>
          )}
        </CardContent>
      </Card>

      {/* Success Dialog */}
      <Dialog open={showSuccessDialog} onClose={() => setShowSuccessDialog(false)}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <CheckCircleIcon sx={{ mr: 1, color: 'success.main' }} />
          Update Successful
        </DialogTitle>
        <DialogContent>
          <Typography>
            Market breadth data has been successfully updated and cached.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSuccessDialog(false)}>OK</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default CacheData
