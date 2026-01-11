import { AppBar, Toolbar, Typography, Box, Button, Chip } from '@mui/material'
import { Link, useLocation } from 'react-router-dom'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import SearchIcon from '@mui/icons-material/Search'
import AnalyticsIcon from '@mui/icons-material/Analytics'
import { styled } from '@mui/material/styles'

const StyledAppBar = styled(AppBar)(({ theme }) => ({
  background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
  borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
  backdropFilter: 'blur(20px)',
  position: 'sticky',
  top: 0,
  zIndex: 1000,
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%)',
    zIndex: -1,
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '1px',
    background: 'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%)',
  },
}))

const LogoContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: 12,
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    left: -6,
    top: -6,
    right: -6,
    bottom: -6,
    background: 'radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%)',
    borderRadius: '50%',
    zIndex: -1,
  },
}))

const LogoIcon = styled(Box)(({ theme }) => ({
  width: 56,
  height: 56,
  borderRadius: '16px',
  background: 'linear-gradient(135deg, #ff6b6b 0%, #4ecdc4 100%)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  position: 'relative',
  overflow: 'hidden',
  boxShadow: '0 10px 30px rgba(255, 107, 107, 0.3), 0 4px 6px rgba(0, 0, 0, 0.3)',
  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
  '&:hover': {
    transform: 'rotate(15deg) scale(1.1)',
    boxShadow: '0 15px 40px rgba(255, 107, 107, 0.4), 0 6px 12px rgba(0, 0, 0, 0.4)',
  },
  '&::before': {
    content: '""',
    position: 'absolute',
    inset: -2,
    borderRadius: '18px',
    padding: '2px',
    background: 'linear-gradient(135deg, #ff6b6b, #4ecdc4)',
    mask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
    maskComposite: 'exclude',
  },
}))

const LogoText = styled(Typography)(({ theme }) => ({
  fontWeight: 800,
  fontFamily: '"Poppins", "Inter", sans-serif',
  letterSpacing: '-0.02em',
  background: 'linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%)',
  backgroundClip: 'text',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  lineHeight: 1.1,
  textShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
  fontSize: '1.5rem',
  position: 'relative',
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: -3,
    left: 0,
    width: '100%',
    height: '2px',
    background: 'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.5) 50%, transparent 100%)',
    borderRadius: '1px',
  },
}))

const NavigationContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: 8,
}))

const NavButton = styled(Button)<{ selected?: boolean }>(({ theme, selected }) => ({
  position: 'relative',
  minHeight: 40,
  fontWeight: 600,
  fontSize: '0.9rem',
  textTransform: 'none',
  fontFamily: '"Inter", sans-serif',
  letterSpacing: '0.3px',
  borderRadius: '10px',
  padding: '8px 16px',
  color: selected ? '#ffffff' : 'rgba(255, 255, 255, 0.7)',
  background: selected ? 'linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.1) 100%)' : 'transparent',
  border: selected ? '1px solid rgba(255, 255, 255, 0.2)' : '1px solid rgba(255, 255, 255, 0.1)',
  backdropFilter: 'blur(10px)',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  boxShadow: selected ? '0 8px 25px rgba(255, 255, 255, 0.1)' : 'none',
  '&:hover': {
    color: '#ffffff',
    background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%)',
    transform: 'translateY(-2px)',
    boxShadow: '0 12px 30px rgba(255, 255, 255, 0.15)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
  },
  '&::before': {
    content: selected ? '""' : 'none',
    position: 'absolute',
    bottom: 0,
    left: '50%',
    transform: 'translateX(-50%)',
    width: '60%',
    height: '2px',
    background: 'linear-gradient(90deg, rgba(255, 255, 255, 0.8) 0%, rgba(255, 255, 255, 0.2) 100%)',
    borderRadius: '1px',
  },
}))

const StatusChip = styled(Chip)(({ theme }) => ({
  backgroundColor: 'rgba(78, 205, 196, 0.1)',
  border: '1px solid rgba(78, 205, 196, 0.3)',
  color: '#b8f7ef',
  fontWeight: 600,
  fontSize: '0.75rem',
  fontFamily: '"Inter", sans-serif',
  letterSpacing: '0.5px',
  textTransform: 'uppercase',
  padding: '4px 12px',
  borderRadius: '20px',
  boxShadow: '0 4px 15px rgba(78, 205, 196, 0.2)',
  '& .MuiChip-label': {
    paddingLeft: '8px',
    paddingRight: '8px',
  },
}))

const Navbar: React.FC = () => {
  const location = useLocation()

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/' || 
             location.pathname.startsWith('/continuation') || 
             location.pathname.startsWith('/reversal')
    }
    return location.pathname.startsWith(path)
  }

  return (
    <StyledAppBar position="sticky">
      <Toolbar sx={{ py: 1, px: 3, minHeight: '64px !important' }}>
        {/* Navigation */}
        <NavigationContainer>
          <Link to="/" style={{ textDecoration: 'none' }}>
            <NavButton
              selected={isActive('/')}
              startIcon={<SearchIcon sx={{ fontSize: 20 }} />}
            >
              Scanner
            </NavButton>
          </Link>

          <Link to="/breadth" style={{ textDecoration: 'none' }}>
            <NavButton
              selected={isActive('/breadth')}
              startIcon={<AnalyticsIcon sx={{ fontSize: 20 }} />}
            >
              Market Breadth
            </NavButton>
          </Link>
        </NavigationContainer>

        {/* Logo/Brand */}
        <LogoContainer sx={{ marginLeft: 'auto' }}>
          <LogoText variant="h4">
            MA Stock Trader
          </LogoText>
        </LogoContainer>
      </Toolbar>
    </StyledAppBar>
  )
}

export default Navbar
