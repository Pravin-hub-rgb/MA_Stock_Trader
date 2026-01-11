import { Routes, Route } from 'react-router-dom'
import { Box, Container } from '@mui/material'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import MarketBreadth from './pages/MarketBreadth'
import Results from './pages/Results'

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar />
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4, flex: 1 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/breadth" element={<MarketBreadth />} />
          <Route path="/results" element={<Results />} />
        </Routes>
      </Container>
    </Box>
  )
}

export default App
