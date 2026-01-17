import React, { useEffect, useState } from 'react'
import { Box, Card, CardContent, Typography, LinearProgress } from '@mui/material'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorIcon from '@mui/icons-material/Error'
import WarningIcon from '@mui/icons-material/Warning'

interface ToastNotificationProps {
  message: string
  type: 'success' | 'error' | 'warning'
  onClose: () => void
  duration?: number
}

const ToastNotification: React.FC<ToastNotificationProps> = ({
  message,
  type,
  onClose,
  duration = 3500
}) => {
  const [isDisappearing, setIsDisappearing] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsDisappearing(true)
      // Wait for animation to complete before removing
      setTimeout(() => {
        onClose()
      }, 600) // Match animation duration
    }, duration - 600) // Start animation 600ms before actual removal

    return () => clearTimeout(timer)
  }, [duration]) // Remove onClose from dependencies to prevent re-running

  const getToastStyles = () => {
    // Clean, professional navy blue theme matching app design
    switch (type) {
      case 'success':
        return {
          background: 'linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #2563eb 100%)',
          glow: '0 0 20px rgba(99, 102, 241, 0.4), 0 0 40px rgba(99, 102, 241, 0.2)',
          border: '2px solid rgba(99, 102, 241, 0.8)',
          icon: <CheckCircleIcon sx={{
            fontSize: 24,
            mr: 1,
            color: '#60a5fa'
          }} />
        }
      case 'error':
        return {
          background: 'linear-gradient(135deg, #7c2d12 0%, #9a3412 50%, #dc2626 100%)',
          glow: '0 0 20px rgba(220, 38, 38, 0.4), 0 0 40px rgba(220, 38, 38, 0.2)',
          border: '2px solid rgba(220, 38, 38, 0.8)',
          icon: <ErrorIcon sx={{
            fontSize: 24,
            mr: 1,
            color: '#f87171'
          }} />
        }
      case 'warning':
        return {
          background: 'linear-gradient(135deg, #92400e 0%, #b45309 50%, #f59e0b 100%)',
          glow: '0 0 20px rgba(245, 158, 11, 0.4), 0 0 40px rgba(245, 158, 11, 0.2)',
          border: '2px solid rgba(245, 158, 11, 0.8)',
          icon: <WarningIcon sx={{
            fontSize: 24,
            mr: 1,
            color: '#fbbf24'
          }} />
        }
      default:
        return {
          background: 'linear-gradient(135deg, #374151 0%, #4b5563 100%)',
          glow: '0 0 20px rgba(107, 114, 128, 0.4)',
          border: '2px solid rgba(107, 114, 128, 0.6)',
          icon: null
        }
    }
  }

  const styles = getToastStyles()

  return (
    <Box
      sx={{
        position: 'relative',
        zIndex: 9999,
        minWidth: 300,
        maxWidth: 400
      }}
    >
      <Card
        className={isDisappearing ? 'toast-disappearing' : ''}
        sx={{
          background: styles.background,
          color: '#ffffff',
          borderRadius: 3,
          boxShadow: `${styles.glow}, 0 0 60px rgba(0, 0, 0, 0.5)`,
          animation: 'slideIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
          border: styles.border,
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 50%, rgba(255,255,255,0.1) 100%)',
            animation: 'shimmer 3s ease-in-out infinite'
          }
        }}
      >
        <CardContent sx={{ p: 2, pb: 1, '&:last-child': { pb: 1 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {styles.icon}
            <Typography variant="body2" sx={{ fontSize: '0.9rem', lineHeight: 1.4, ml: 1 }}>
              {message}
            </Typography>
          </Box>
        </CardContent>
        <Box sx={{
          height: 4,
          backgroundColor: 'rgba(255, 255, 255, 0.2)',
          borderRadius: '0 0 3px 3px',
          overflow: 'hidden'
        }}>
          <Box sx={{
            height: '100%',
            backgroundColor: 'rgba(255, 255, 255, 1)',
            animation: `countdown ${duration}ms linear forwards`,
            transformOrigin: 'left center'
          }} />
        </Box>
      </Card>

      {/* CSS animations */}
      <style>
        {`
          @keyframes slideIn {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
          @keyframes countdown {
            from {
              width: 0%;
            }
            to {
              width: 100%;
            }
          }
          @keyframes shimmer {
            0% {
              transform: translateX(-100%);
            }
            100% {
              transform: translateX(100%);
            }
          }
          @keyframes iconPulse {
            0%, 100% {
              transform: scale(1);
              filter: brightness(1);
            }
            50% {
              transform: scale(1.1);
              filter: brightness(1.2);
            }
          }
          @keyframes fadeOut {
            0% {
              opacity: 1;
            }
            100% {
              opacity: 0;
            }
          }
          .toast-disappearing {
            animation: fadeOut 0.6s ease-out forwards !important;
          }
        `}
      </style>
    </Box>
  )
}

export default ToastNotification
