import { Routes, Route } from 'react-router-dom'
import { Box, Container } from '@mui/material'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import MarketBreadth from './pages/MarketBreadth'
import Results from './pages/Results'
import LiveTrading from './pages/LiveTrading'
import CacheData from './pages/CacheData'
import { AppStateProvider } from './contexts/AppStateContext'

function App() {
  return (
    <AppStateProvider>
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Navbar />
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4, flex: 1 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/breadth" element={<MarketBreadth />} />
            <Route path="/results" element={<Results />} />
            <Route path="/live-trading" element={<LiveTrading />} />
          </Routes>
        </Container>
      </Box>
    </AppStateProvider>
  )
}

export default App
