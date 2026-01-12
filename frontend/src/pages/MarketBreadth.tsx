import React, { useState, useEffect } from 'react'
import {
  Typography,
  Box,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent
} from '@mui/material'
import {
  Refresh as RefreshIcon
} from '@mui/icons-material'
import axios from 'axios'

interface BreadthResult {
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

interface AnalysisResponse {
  status: string
  data?: BreadthResult[]
  total_dates?: number
  last_updated?: string
  message: string
}

// Standard color scheme: Firebrick → Orange → Gold → Khaki → Lime → Forest Green
const getUp45Color = (value: number): string => {
  if (value < 50) return '#ff7300ff'      // Below 50: Firebrick (dark red)

  // Standard ranges with exact colors
  if (value >= 50 && value <= 69) return '#ff9900ff'  // 50-69: Orange Red (strong dark orange)
  if (value >= 70 && value <= 89) return '#ffcd00'  // 70-89: Dark Orange (lighter orange)
  if (value >= 90 && value <= 109) return '#eee418' // 90-109: Gold (bright gold/yellow)
  if (value >= 110 && value <= 129) return '#cae627' // 110-129: Khaki (pale khaki/yellowish-green)
  if (value >= 130 && value <= 149) return '#7ec019' // 130-149: Lime Green (lime green)
  if (value >= 150) return '#2A9915'                // 150+: Dark Green (dark forest green)

  return '#B22222' // Fallback
}

// Custom down column color scheme with agreed ranges
const getDown45Color = (value: number): string => {
  if (value < 35) return '#2A9915'        // <35: Dark Green (from up >150)
  if (value >= 35 && value < 50) return '#7ec019'   // 35-49: Green → yellow transition
  if (value >= 50 && value <= 65) return '#eee418'  // 50-65: Yellow (from up 90-109)
  if (value >= 66 && value <= 99) return '#ffcd00'  // 66-99: Yellow → orange transition
  if (value > 100) return '#ff7300ff'               // >100: Dark orange (from up <50)

  return '#2A9915' // Fallback
}

// Up 20% 5d color scheme: extreme orange → lighter orange → lighter green → extreme green
const getUp20Color = (value: number): string => {
  if (value < 25) return '#ff7300ff'     // <25: Extreme orange (from up <50)
  if (value >= 25 && value <= 37) return '#FF8C00'  // 25-37: Lighter orange
  if (value >= 38 && value <= 50) return '#32CD32'  // 38-50: Lighter green
  if (value > 50) return '#2A9915'       // >50: Extreme green (from up >150)

  return '#ff7300ff' // Fallback
}

// Down 20% 5d color scheme: white → light orange → orange (instructor's Excel style)
const getDown20Color = (value: number): string => {
  if (value < 20) return '#ffffff'       // <20: White background (few stocks down = neutral)
  if (value >= 20 && value < 30) return 'rgba(255, 187, 102, 0.6)'  // 20-29: Lighter orange with more opacity
  if (value >= 30 && value <= 50) return 'rgba(255, 140, 0, 0.4)'   // 30-50: Light orange with opacity
  if (value > 50) return '#ff7300ff'     // >50: Extreme orange (many stocks down = bad)

  return '#ffffff' // Fallback
}

// Above 20MA color scheme: same shades as Up 4.5% but scaled for higher values
const getAbove20MAColor = (value: number): string => {
  if (value < 200) return '#ff7300ff'     // <200: Extreme orange (very few stocks above MA)
  if (value >= 200 && value < 500) return '#ff9900ff'  // 200-499: Orange-yellow (concerning)
  if (value >= 500 && value < 800) return '#ffcd00'    // 500-799: Yellow-orange (transition)
  if (value >= 800 && value < 900) return '#eee418'    // 800-899: Yellow (neutral)
  if (value >= 900 && value < 1200) return '#cae627'   // 900-1199: Yellow-green (improving)
  if (value >= 1200 && value < 1400) return '#7ec019'  // 1200-1399: Green (good)
  if (value >= 1400) return '#2A9915'    // >=1400: Dark green (excellent)

  return '#ff7300ff' // Fallback
}

// Below 20MA color scheme: flipped colors from Above 20MA
const getBelow20MAColor = (value: number): string => {
  if (value < 200) return '#2A9915'       // <200: Dark green (from Above >=1400)
  if (value >= 200 && value < 500) return '#7ec019'   // 200-499: Green (from Above 1200-1399)
  if (value >= 500 && value < 800) return '#cae627'  // 500-799: Yellow-green (from Above 900-1199)
  if (value >= 800 && value < 900) return '#eee418'  // 800-899: Yellow (from Above 800-899)
  if (value >= 900 && value < 1200) return '#ffcd00' // 900-1199: Yellow-orange (from Above 500-799)
  if (value >= 1200 && value < 1400) return '#ff9900ff' // 1200-1399: Orange-yellow (from Above 200-499)
  if (value >= 1400) return '#ff7300ff'  // >=1400: Extreme orange (from Above <200)

  return '#2A9915' // Fallback
}

// Above 50MA color scheme: same as Above 20MA
const getAbove50MAColor = (value: number): string => {
  if (value < 200) return '#ff7300ff'     // <200: Extreme orange (very few stocks above MA)
  if (value >= 200 && value < 500) return '#ff9900ff'  // 200-499: Orange-yellow (concerning)
  if (value >= 500 && value < 800) return '#ffcd00'    // 500-799: Yellow-orange (transition)
  if (value >= 800 && value < 900) return '#eee418'    // 800-899: Yellow (neutral)
  if (value >= 900 && value < 1200) return '#cae627'   // 900-1199: Yellow-green (improving)
  if (value >= 1200 && value < 1400) return '#7ec019'  // 1200-1399: Green (good)
  if (value >= 1400) return '#2A9915'    // >=1400: Dark green (excellent)

  return '#ff7300ff' // Fallback
}

// Below 50MA color scheme: flipped colors from Above 50MA (same as Below 20MA)
const getBelow50MAColor = (value: number): string => {
  if (value < 200) return '#2A9915'       // <200: Dark green (from Above >=1400)
  if (value >= 200 && value < 500) return '#7ec019'   // 200-499: Green (from Above 1200-1399)
  if (value >= 500 && value < 800) return '#cae627'  // 500-799: Yellow-green (from Above 900-1199)
  if (value >= 800 && value < 900) return '#eee418'  // 800-899: Yellow (from Above 800-899)
  if (value >= 900 && value < 1200) return '#ffcd00' // 900-1199: Yellow-orange (from Above 500-799)
  if (value >= 1200 && value < 1400) return '#ff9900ff' // 1200-1399: Orange-yellow (from Above 200-499)
  if (value >= 1400) return '#ff7300ff'  // >=1400: Extreme orange (from Above <200)

  return '#2A9915' // Fallback
}

const MarketBreadth: React.FC = () => {
  const [results, setResults] = useState<BreadthResult[]>([])
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)
  const [showSuccessDialog, setShowSuccessDialog] = useState(false)

  // Load breadth data on component mount
  useEffect(() => {
    loadBreadthData()
  }, [])

  const loadBreadthData = async () => {
    try {
      const response = await axios.get('/api/breadth/data')
      if (response.data.data && response.data.data.length > 0) {
        setResults(response.data.data)
        setLastUpdated(response.data.last_updated)
      }
    } catch (err) {
      console.error('Failed to load breadth data:', err)
    }
  }

  const handleUpdateBreadth = async () => {
    setIsUpdating(true)
    try {
      const response = await axios.post<AnalysisResponse>('/api/breadth/update')

      if (response.data.status === 'success') {
        setResults(response.data.data || [])
        setLastUpdated(response.data.last_updated || null)
        setShowSuccessDialog(true)
      }
    } catch (err: any) {
      console.error('Failed to update breadth data:', err)
      setIsUpdating(false)
    } finally {
      setIsUpdating(false)
    }
  }



  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 4, fontWeight: 600 }}>
        📊 Market Breadth Data
      </Typography>

      {/* Status and Update Button */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Status: {results.length > 0 ? `${results.length} dates cached` : 'No data cached'}
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

      {/* Results Table */}
      {results.length > 0 && (
        <Card sx={{ background: 'linear-gradient(135deg, #111111 0%, #1a1a1a 100%)', border: '1px solid rgba(255,255,255,0.1)' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
              Breadth Analysis Results
            </Typography>

            <TableContainer component={Paper} sx={{ backgroundColor: 'transparent' }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ color: '#f8fafc', fontWeight: 600, borderBottom: '1px solid black', borderRight: '1px solid black', textAlign: 'center' }}>Date</TableCell>
                    <TableCell sx={{ color: '#f8fafc', fontWeight: 600, borderBottom: '1px solid black', borderRight: '1px solid black', textAlign: 'center' }}>
                      Up 4.5%
                    </TableCell>
                    <TableCell sx={{ color: '#f8fafc', fontWeight: 600, borderBottom: '1px solid black', borderRight: '1px solid black', textAlign: 'center' }}>Down 4.5%</TableCell>
                    <TableCell sx={{ color: '#f8fafc', fontWeight: 600, borderBottom: '1px solid black', borderRight: '1px solid black', textAlign: 'center' }}>Up 20% 5d</TableCell>
                    <TableCell sx={{ color: '#f8fafc', fontWeight: 600, borderBottom: '1px solid black', borderRight: '1px solid black', textAlign: 'center' }}>Down 20% 5d</TableCell>
                    <TableCell sx={{ color: '#f8fafc', fontWeight: 600, borderBottom: '1px solid black', borderRight: '1px solid black', textAlign: 'center' }}>Above 20MA</TableCell>
                    <TableCell sx={{ color: '#f8fafc', fontWeight: 600, borderBottom: '1px solid black', borderRight: '1px solid black', textAlign: 'center' }}>Below 20MA</TableCell>
                    <TableCell sx={{ color: '#f8fafc', fontWeight: 600, borderBottom: '1px solid black', borderRight: '1px solid black', textAlign: 'center' }}>Above 50MA</TableCell>
                    <TableCell sx={{ color: '#f8fafc', fontWeight: 600, borderBottom: '1px solid black', textAlign: 'center' }}>Below 50MA</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {results.map((row, index) => (
                    <TableRow key={row.date} sx={{
                      '&:hover': { backgroundColor: 'rgba(255,255,255,0.02)' }
                    }}>
                      <TableCell sx={{
                        color: '#f8fafc',
                        borderBottom: '1px solid black',
                        borderRight: '1px solid black',
                        fontSize: '0.85rem',
                        py: '2px',
                        textAlign: 'center'
                      }}>
                        {row.date}
                      </TableCell>
                      <TableCell
                        sx={{
                          backgroundColor: getUp45Color(row.up_4_5_pct),
                          color: '#000000',
                          fontWeight: 'bold',
                          borderBottom: '1px solid black',
                          borderRight: '1px solid black',
                          textAlign: 'center',
                          fontSize: '0.9rem',
                          py: '2px'
                        }}
                      >
                        {row.up_4_5_pct}
                      </TableCell>
                      <TableCell
                        sx={{
                          backgroundColor: getDown45Color(row.down_4_5_pct),
                          color: '#000000',
                          fontWeight: 'bold',
                          borderBottom: '1px solid black',
                          borderRight: '1px solid black',
                          textAlign: 'center',
                          fontSize: '0.9rem',
                          py: '2px'
                        }}
                      >
                        {row.down_4_5_pct}
                      </TableCell>
                      <TableCell
                        sx={{
                          backgroundColor: getUp20Color(row.up_20_pct_5d),
                          color: '#000000',
                          fontWeight: 'bold',
                          borderBottom: '1px solid black',
                          borderRight: '1px solid black',
                          textAlign: 'center',
                          fontSize: '0.9rem',
                          py: '2px'
                        }}
                      >
                        {row.up_20_pct_5d}
                      </TableCell>
                      <TableCell
                        sx={{
                          backgroundColor: getDown20Color(row.down_20_pct_5d),
                          color: '#000000',
                          fontWeight: 'bold',
                          borderBottom: '1px solid black',
                          borderRight: '1px solid black',
                          textAlign: 'center',
                          fontSize: '0.9rem',
                          py: '2px'
                        }}
                      >
                        {row.down_20_pct_5d}
                      </TableCell>
                      <TableCell
                        sx={{
                          backgroundColor: getAbove20MAColor(row.above_20ma),
                          color: '#000000',
                          fontWeight: 'bold',
                          borderBottom: '1px solid black',
                          borderRight: '1px solid black',
                          textAlign: 'center',
                          fontSize: '0.9rem',
                          py: '2px'
                        }}
                      >
                        {row.above_20ma}
                      </TableCell>
                      <TableCell
                        sx={{
                          backgroundColor: getBelow20MAColor(row.below_20ma),
                          color: '#000000',
                          fontWeight: 'bold',
                          borderBottom: '1px solid black',
                          borderRight: '1px solid black',
                          textAlign: 'center',
                          fontSize: '0.9rem',
                          py: '2px'
                        }}
                      >
                        {row.below_20ma}
                      </TableCell>
                      <TableCell
                        sx={{
                          backgroundColor: getAbove50MAColor(row.above_50ma),
                          color: '#000000',
                          fontWeight: 'bold',
                          borderBottom: '1px solid black',
                          borderRight: '1px solid black',
                          textAlign: 'center',
                          fontSize: '0.9rem',
                          py: '2px'
                        }}
                      >
                        {row.above_50ma}
                      </TableCell>
                      <TableCell
                        sx={{
                          backgroundColor: getBelow50MAColor(row.below_50ma),
                          color: '#000000',
                          fontWeight: 'bold',
                          borderBottom: '1px solid black',
                          textAlign: 'center',
                          fontSize: '0.9rem',
                          py: '2px'
                        }}
                      >
                        {row.below_50ma}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {results.length === 0 && (
        <Card sx={{ p: 6, textAlign: 'center', background: 'linear-gradient(135deg, #111111 0%, #1a1a1a 100%)', border: '1px solid rgba(255,255,255,0.1)' }}>
          <Typography variant="h6" gutterBottom sx={{ color: 'text.secondary' }}>
            No Breadth Analysis Results
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
            Click "Update" to calculate and cache the latest market breadth analysis
          </Typography>
        </Card>
      )}
    </Box>
  )
}

export default MarketBreadth
