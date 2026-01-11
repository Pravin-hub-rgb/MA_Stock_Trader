import React, { useState, useEffect } from 'react'
import {
  Typography,
  Box,
  Paper,
  Button,
  LinearProgress,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  FormControlLabel,
  Switch,
  Card,
  CardContent,
  IconButton,
  Tooltip
} from '@mui/material'
import {
  PlayArrow as PlayIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Analytics as AnalyticsIcon
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
  operation_id: string
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
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [forceRefresh, setForceRefresh] = useState(false)
  const [lastAnalysis, setLastAnalysis] = useState<string | null>(null)

  // Load breadth data on component mount
  useEffect(() => {
    loadBreadthData()
  }, [])

  const loadBreadthData = async () => {
    try {
      const response = await axios.get('/api/breadth/data')
      if (response.data.data && response.data.data.length > 0) {
        setResults(response.data.data)
        setLastAnalysis(response.data.last_updated)
      }
    } catch (err) {
      console.error('Failed to load breadth data:', err)
      // If no real data, show mock data for demonstration
      loadMockResults()
    }
  }

  const runAnalysis = async () => {
    setLoading(true)
    setProgress(0)
    setError('')
    setStatus('Starting breadth analysis...')

    try {
      const response = await axios.post<AnalysisResponse>('/api/breadth/analyze', {
        force_refresh: forceRefresh,
        max_dates: 30
      })

      if (response.data.status === 'started') {
        setStatus('Analysis in progress...')
        // Simulate progress (in real implementation, use WebSocket)
        simulateProgress(response.data.operation_id)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start analysis')
      setLoading(false)
    }
  }

  const simulateProgress = (operationId: string) => {
    let progress = 0
    const interval = setInterval(() => {
      progress += Math.random() * 15
      if (progress >= 100) {
        progress = 100
        clearInterval(interval)
        setLoading(false)
        setStatus('Analysis completed!')
        // Load mock results
        loadMockResults()
        setLastAnalysis(new Date().toISOString())
      }
      setProgress(progress)
      setStatus(`Analyzing market breadth... ${Math.round(progress)}%`)
    }, 500)
  }

  const loadMockResults = () => {
    // Mock data for demonstration - expanded to show more variety
    const mockResults: BreadthResult[] = [
      {
        date: '2026-01-10',
        up_4_5_pct: 157,
        down_4_5_pct: 89,
        up_20_pct_5d: 23,
        down_20_pct_5d: 45,
        above_20ma: 1234,
        below_20ma: 567,
        above_50ma: 1456,
        below_50ma: 345
      },
      {
        date: '2026-01-09',
        up_4_5_pct: 142,
        down_4_5_pct: 95,
        up_20_pct_5d: 18,
        down_20_pct_5d: 52,
        above_20ma: 1189,
        below_20ma: 612,
        above_50ma: 1398,
        below_50ma: 403
      },
      {
        date: '2026-01-08',
        up_4_5_pct: 89,
        down_4_5_pct: 148,
        up_20_pct_5d: 31,
        down_20_pct_5d: 38,
        above_20ma: 1345,
        below_20ma: 456,
        above_50ma: 1523,
        below_50ma: 278
      },
      {
        date: '2026-01-07',
        up_4_5_pct: 134,
        down_4_5_pct: 103,
        up_20_pct_5d: 27,
        down_20_pct_5d: 42,
        above_20ma: 1278,
        below_20ma: 523,
        above_50ma: 1434,
        below_50ma: 367
      },
      {
        date: '2026-01-06',
        up_4_5_pct: 76,
        down_4_5_pct: 161,
        up_20_pct_5d: 19,
        down_20_pct_5d: 50,
        above_20ma: 1156,
        below_20ma: 645,
        above_50ma: 1324,
        below_50ma: 477
      },
      {
        date: '2026-01-05',
        up_4_5_pct: 123,
        down_4_5_pct: 124,
        up_20_pct_5d: 34,
        down_20_pct_5d: 35,
        above_20ma: 1423,
        below_20ma: 378,
        above_50ma: 1589,
        below_50ma: 212
      },
      {
        date: '2026-01-04',
        up_4_5_pct: 67,
        down_4_5_pct: 180,
        up_20_pct_5d: 12,
        down_20_pct_5d: 57,
        above_20ma: 1098,
        below_20ma: 703,
        above_50ma: 1256,
        below_50ma: 545
      },
      {
        date: '2026-01-03',
        up_4_5_pct: 98,
        down_4_5_pct: 149,
        up_20_pct_5d: 28,
        down_20_pct_5d: 41,
        above_20ma: 1367,
        below_20ma: 434,
        above_50ma: 1498,
        below_50ma: 303
      },
      {
        date: '2026-01-02',
        up_4_5_pct: 145,
        down_4_5_pct: 102,
        up_20_pct_5d: 36,
        down_20_pct_5d: 33,
        above_20ma: 1489,
        below_20ma: 312,
        above_50ma: 1634,
        below_50ma: 167
      },
      {
        date: '2026-01-01',
        up_4_5_pct: 112,
        down_4_5_pct: 135,
        up_20_pct_5d: 29,
        down_20_pct_5d: 40,
        above_20ma: 1321,
        below_20ma: 480,
        above_50ma: 1456,
        below_50ma: 345
      },
      {
        date: '2025-12-31',
        up_4_5_pct: 78,
        down_4_5_pct: 169,
        up_20_pct_5d: 16,
        down_20_pct_5d: 53,
        above_20ma: 1178,
        below_20ma: 623,
        above_50ma: 1345,
        below_50ma: 456
      },
      {
        date: '2025-12-30',
        up_4_5_pct: 156,
        down_4_5_pct: 91,
        up_20_pct_5d: 42,
        down_20_pct_5d: 27,
        above_20ma: 1523,
        below_20ma: 278,
        above_50ma: 1678,
        below_50ma: 123
      },
      {
        date: '2025-12-29',
        up_4_5_pct: 89,
        down_4_5_pct: 158,
        up_20_pct_5d: 21,
        down_20_pct_5d: 48,
        above_20ma: 1234,
        below_20ma: 567,
        above_50ma: 1412,
        below_50ma: 389
      },
      {
        date: '2025-12-28',
        up_4_5_pct: 134,
        down_4_5_pct: 113,
        up_20_pct_5d: 33,
        down_20_pct_5d: 36,
        above_20ma: 1398,
        below_20ma: 403,
        above_50ma: 1543,
        below_50ma: 258
      },
      {
        date: '2025-12-27',
        up_4_5_pct: 67,
        down_4_5_pct: 180,
        up_20_pct_5d: 14,
        down_20_pct_5d: 55,
        above_20ma: 1123,
        below_20ma: 678,
        above_50ma: 1289,
        below_50ma: 512
      }
    ]
    setResults(mockResults)
  }

  const downloadResults = () => {
    // In real implementation, this would download the latest CSV
    alert('Download functionality will be implemented with backend integration')
  }

  return (
    <Box>

      {/* Control Panel */}
      <Card sx={{ mb: 4, background: 'linear-gradient(135deg, #111111 0%, #1a1a1a 100%)', border: '1px solid rgba(255,255,255,0.1)' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Analysis Controls
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={<PlayIcon />}
              onClick={runAnalysis}
              disabled={loading}
              sx={{
                background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
                px: 4,
                py: 1.5,
                fontWeight: 600,
                '&:hover': {
                  background: 'linear-gradient(135deg, #6366f1dd 0%, #ec4899dd 100%)',
                  transform: 'translateY(-2px)',
                }
              }}
            >
              {loading ? 'Running Analysis...' : 'Run Breadth Analysis'}
            </Button>

            <FormControlLabel
              control={
                <Switch
                  checked={forceRefresh}
                  onChange={(e) => setForceRefresh(e.target.checked)}
                  color="primary"
                />
              }
              label="Force Refresh Cache"
              sx={{ color: 'text.secondary' }}
            />

            <Box sx={{ flex: 1 }} />

            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={loadBreadthData}
              sx={{ borderColor: 'rgba(255,255,255,0.2)' }}
            >
              Refresh
            </Button>

            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={downloadResults}
              disabled={results.length === 0}
              sx={{ borderColor: 'rgba(255,255,255,0.2)' }}
            >
              Download CSV
            </Button>
          </Box>

          {/* Progress Bar */}
          {loading && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="body2" sx={{ mb: 1, color: 'text.secondary' }}>
                {status}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'rgba(255,255,255,0.1)',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 4,
                    background: 'linear-gradient(90deg, #6366f1 0%, #ec4899 100%)'
                  }
                }}
              />
            </Box>
          )}

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mt: 3 }}>
              {error}
            </Alert>
          )}
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
      {results.length === 0 && !loading && (
        <Card sx={{ p: 6, textAlign: 'center', background: 'linear-gradient(135deg, #111111 0%, #1a1a1a 100%)', border: '1px solid rgba(255,255,255,0.1)' }}>
          <AnalyticsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 3, opacity: 0.5 }} />
          <Typography variant="h6" gutterBottom sx={{ color: 'text.secondary' }}>
            No Breadth Analysis Results
          </Typography>
          <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
            Run a breadth analysis to see market momentum indicators with color-coded visualization
          </Typography>
          <Button
            variant="outlined"
            startIcon={<PlayIcon />}
            onClick={runAnalysis}
            sx={{
              borderColor: 'rgba(99, 102, 241, 0.5)',
              color: '#6366f1',
              '&:hover': {
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)'
              }
            }}
          >
            Start Analysis
          </Button>
        </Card>
      )}
    </Box>
  )
}

export default MarketBreadth
