import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Typography,
  Paper,
  Button,
  Alert,
  CircularProgress,
  Chip,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormControl,
  FormLabel,
  TextField,
  InputAdornment,
  IconButton
} from '@mui/material';
import { styled } from '@mui/material/styles';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import { useAppState } from '../contexts/AppStateContext';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginBottom: theme.spacing(3),
  background: 'linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  borderRadius: '12px',
  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
}));

const ValidationResult = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(2),
  padding: theme.spacing(2),
  backgroundColor: '#0d0d0d',
  borderRadius: '8px',
  fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
  fontSize: '0.85rem',
  whiteSpace: 'pre-wrap',
  overflowY: 'auto',
  border: '1px solid #333333',
  color: '#e0e0e0',
}));

const StatusChip = styled(Chip)<{ status: 'success' | 'error' | 'warning' }>(({ theme, status }) => ({
  marginLeft: theme.spacing(1),
  backgroundColor: status === 'success' ? '#d4edda' :
                   status === 'error' ? '#f8d7da' : '#fff3cd',
  color: status === 'success' ? '#155724' :
         status === 'error' ? '#721c24' : '#856404',
  border: `1px solid ${status === 'success' ? '#c3e6cb' :
                      status === 'error' ? '#f5c6cb' : '#ffeaa7'}`,
}));

const LiveTrading: React.FC = () => {
  const { state, updateState } = useAppState();
  const [validationResult, setValidationResult] = useState<string>('');
  const [isValidating, setIsValidating] = useState(false);
  const [validationStatus, setValidationStatus] = useState<'idle' | 'success' | 'error'>('idle');

  // Live trading state
  const [tradingMode, setTradingMode] = useState<'continuation' | 'reversal'>('continuation');
  const [botStatus, setBotStatus] = useState<'stopped' | 'running'>('stopped');
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [liveLogs, setLiveLogs] = useState<string[]>([]);
  const [isCheckingBotStatus, setIsCheckingBotStatus] = useState(true);
  const [terminalHeight, setTerminalHeight] = useState(300);
  const startYRef = useRef(0);
  const startHeightRef = useRef(300);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    startYRef.current = e.clientY;
    startHeightRef.current = terminalHeight;

    // Set cursor immediately
    document.body.style.cursor = 'ns-resize';
    document.body.style.userSelect = 'none';

    const handleMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      const deltaY = e.clientY - startYRef.current;
      const newHeight = Math.max(200, startHeightRef.current + deltaY);

      // Direct state update without throttling for immediate response
      setTerminalHeight(newHeight);
    };

    const handleMouseUp = () => {
      // Clean up immediately
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    // Add listeners directly
    document.addEventListener('mousemove', handleMouseMove, { passive: false });
    document.addEventListener('mouseup', handleMouseUp, { passive: true });
  }, [terminalHeight]);

  // Token session state
  const [accessToken, setAccessToken] = useState<string>('');
  const [isValidatingToken, setIsValidatingToken] = useState(false);
  const [tokenValidationResult, setTokenValidationResult] = useState<string>('');
  const [tokenStatus, setTokenStatus] = useState<'unknown' | 'valid' | 'invalid'>('unknown');
  const [showUpdateForm, setShowUpdateForm] = useState(false);
  const [isRefreshingToken, setIsRefreshingToken] = useState(false);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    updateState({ activeLiveTradingTab: newValue as 'token' | 'validation' | 'trading' });
  };

  const [showToken, setShowToken] = useState(false);

  // Auto-check existing token and bot status on component mount
  useEffect(() => {
    const checkExistingToken = async () => {
      try {
        const response = await fetch('/api/token/current');
        const data = await response.json();

        if (data.exists && data.token) {
          setAccessToken(data.token);

          // Auto-validate the existing token
          setIsValidatingToken(true);
          setTokenValidationResult('🔄 Checking current token...\n⏳ Verifying stored token validity...\n⏳ Testing API access...\n\nPlease wait...');

          try {
            const validateResponse = await fetch('/api/token/validate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ token: data.token })
            });

            const validateData = await validateResponse.json();

            if (validateResponse.ok && validateData.valid) {
              const stockResults = validateData.test_results ? validateData.test_results.join('\n') : '';
              setTokenValidationResult('✅ Current Token is Valid!\n\n' +
                `🔑 Token: ${data.masked || '****...****'}\n` +
                `📊 Test Results:\n${stockResults}\n` +
                `⏰ Last validated: ${new Date().toLocaleString()}\n\n` +
                'You can proceed to list validation or enter a new token if needed.');
              setTokenStatus('valid');
            } else {
              setTokenValidationResult(`❌ Current Token Invalid\n\n${validateData.error || 'Token expired or invalid'}`);
              setTokenStatus('invalid');
            }
          } catch (error) {
            setTokenValidationResult(`❌ Token Check Failed\n\nUnable to verify current token: ${error}`);
            setTokenStatus('invalid');
          } finally {
            setIsValidatingToken(false);
          }
        } else {
          setTokenValidationResult('ℹ️ No token configured\n\nPlease enter your Upstox access token to begin.');
          setTokenStatus('unknown');
        }
      } catch (error) {
        setTokenValidationResult(`❌ Configuration Error\n\nUnable to read token config: ${error}`);
        setTokenStatus('invalid');
      }
    };

    const checkBotStatus = async () => {
      try {
        setIsCheckingBotStatus(true);
        const response = await fetch('/api/live-trading/logs');
        const data = await response.json();

        if (response.ok && data.is_running !== undefined) {
          setBotStatus(data.is_running ? 'running' : 'stopped');
          if (data.logs && data.logs.length > 0) {
            const formattedLogs = data.logs.map((log: any) =>
              `[${new Date(log.timestamp).toLocaleTimeString()}] ${log.message}`
            );
            setLiveLogs(formattedLogs);

            // Determine trading mode from logs
            if (data.is_running) {
              const modeFromLogs = data.logs.find((log: any) =>
                log.message && log.message.includes('Bot Mode:')
              );
              if (modeFromLogs) {
                const modeText = modeFromLogs.message.toUpperCase();
                if (modeText.includes('REVERSAL')) {
                  setTradingMode('reversal');
                } else if (modeText.includes('CONTINUATION')) {
                  setTradingMode('continuation');
                }
              }
            }
          }
          // Start polling if bot is running
          if (data.is_running) {
            startLogPolling();
          }
        }
      } catch (error) {
        console.log('Could not check bot status:', error);
      } finally {
        setIsCheckingBotStatus(false);
      }
    };

    checkExistingToken();
    checkBotStatus();
  }, []);

  const handleRefreshTokenStatus = async () => {
    setIsRefreshingToken(true);
    setTokenValidationResult('🔄 Refreshing token status...\n⏳ Re-reading config file...\n⏳ Testing Upstox API connection...\n⏳ Checking stock data access...\n⏳ Verifying token validity...\n\nPlease wait...');

    try {
      // First, get the current token from config
      const currentResponse = await fetch('/api/token/current');
      const currentData = await currentResponse.json();

      if (currentData.exists && currentData.token) {
        setAccessToken(currentData.token);

        // Use the new simple token check endpoint instead of validate
        const checkResponse = await fetch('/api/token/check');
        const checkData = await checkResponse.json();

        if (checkResponse.ok && checkData.valid) {
          setTokenValidationResult('✅ Token Status Refreshed - Valid!\n\n' +
            `🔑 Token: ${currentData.masked || '****...****'}\n` +
            `📊 Test Results:\n${checkData.test_result || 'Token validation successful'}\n` +
            `⏰ Refreshed at: ${new Date().toLocaleString()}\n\n` +
            'Token is working correctly for live trading.');
          setTokenStatus('valid');
        } else {
          setTokenValidationResult(`❌ Token Status Refreshed - Invalid\n\n${checkData.message || 'Token expired or invalid'}`);
          setTokenStatus('invalid');
        }
      } else {
        setTokenValidationResult('ℹ️ Token Status Refreshed - No token configured\n\nPlease enter your Upstox access token to begin.');
        setTokenStatus('unknown');
        setAccessToken('');
      }
    } catch (error) {
      setTokenValidationResult(`❌ Refresh Failed\n\nUnable to refresh token status: ${error}`);
      setTokenStatus('invalid');
    } finally {
      setIsRefreshingToken(false);
    }
  };

  const handleValidateToken = async () => {
    if (!accessToken.trim()) {
      setTokenValidationResult('❌ Please enter an access token first');
      setTokenStatus('invalid');
      return;
    }

    setIsValidatingToken(true);
    setTokenValidationResult('🔄 Validating token...\n⏳ Testing Upstox API connection...\n⏳ Checking stock data access...\n⏳ Verifying token validity...\n\nPlease wait...');

    try {
      const response = await fetch('/api/token/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: accessToken.trim() })
      });

      const data = await response.json();

      if (response.ok && data.valid) {
        const stockResults = data.test_results ? data.test_results.join('\n') : '';
        setTokenValidationResult('✅ Token Validated Successfully!\n\n' +
          `🔑 Token: ${accessToken.substring(0, 10)}...${accessToken.substring(accessToken.length - 4)}\n` +
          `📊 Test Results:\n${stockResults}\n` +
          `⏰ Validated at: ${new Date().toLocaleString()}\n\n` +
          'Token has been saved to config. You can now proceed to list validation.');
        setTokenStatus('valid');
        
        // Auto-close the form on success
        setShowUpdateForm(false);
        setAccessToken(''); // Clear the input field
      } else {
        setTokenValidationResult(`❌ Token Validation Failed\n\n${data.error || 'Invalid or expired token'}`);
        setTokenStatus('invalid');
        // Keep the form open on error so user can try again
      }
    } catch (error) {
      setTokenValidationResult(`❌ Network Error\n\nFailed to validate token: ${error}`);
      setTokenStatus('invalid');
      // Keep the form open on error
    } finally {
      setIsValidatingToken(false);
    }
  };

  const handleValidateLists = async () => {
    setIsValidating(true);
    setValidationStatus('idle');
    setValidationResult('🔄 Processing...\n⏳ Checking Upstox API connections...\n⏳ Validating instrument keys...\n⏳ Verifying live price data...\n⏳ Analyzing list formatting...\n\nPlease wait...');

    try {
      const response = await fetch('/api/live-trading/validate-lists');
      const data = await response.json();

      if (response.ok) {
        setValidationResult(data.validation_output || 'Validation completed successfully');
        setValidationStatus('success');
      } else {
        setValidationResult(`❌ Validation Failed\n\nError: ${data.error || 'Unknown error'}`);
        setValidationStatus('error');
      }
    } catch (error) {
      setValidationResult(`❌ Network Error\n\nFailed to connect to validation service: ${error}`);
      setValidationStatus('error');
    } finally {
      setIsValidating(false);
    }
  };

  const handleStartTrading = async () => {
    setIsStarting(true);
    try {
      const response = await fetch('/api/live-trading/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: tradingMode })
      });

      const data = await response.json();

      if (response.ok) {
        setBotStatus('running');
        setLiveLogs(['🚀 Starting live trading bot...', `📊 Mode: ${tradingMode}`]);

        // Start polling for logs
        startLogPolling();
      } else {
        alert(`Failed to start bot: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      alert(`Network error: ${error}`);
    } finally {
      setIsStarting(false);
    }
  };

  // Log polling
  const startLogPolling = () => {
    const pollLogs = async () => {
      try {
        const response = await fetch('/api/live-trading/logs');
        const data = await response.json();

        if (response.ok && data.logs) {
          const formattedLogs = data.logs.map((log: any) =>
            `[${new Date(log.timestamp).toLocaleTimeString()}] ${log.message}`
          );
          setLiveLogs(formattedLogs);
        }

        // Continue polling if bot is still running, otherwise stop after a few more polls
        if (data.is_running) {
          setTimeout(pollLogs, 500); // Poll every 500ms while running
        } else {
          // Bot stopped, do a few more polls to catch any remaining logs
          setTimeout(() => {
            // Final poll to ensure we got all logs
            fetch('/api/live-trading/logs').then(res => res.json()).then(finalData => {
              if (finalData.logs) {
                const finalLogs = finalData.logs.map((log: any) =>
                  `[${new Date(log.timestamp).toLocaleTimeString()}] ${log.message}`
                );
                setLiveLogs(finalLogs);
              }
            }).catch(() => {});
          }, 1000);
        }
      } catch (error) {
        // Continue polling even on error, but slow down
        setTimeout(pollLogs, 1000);
      }
    };

    // Start polling immediately (no delay)
    pollLogs();
  };

  const handleStopTrading = async () => {
    setIsStopping(true);
    try {
      const response = await fetch('/api/live-trading/stop', {
        method: 'POST'
      });

      if (response.ok) {
        setBotStatus('stopped');
        setLiveLogs(prev => [...prev, '🛑 Bot stopped']);
      } else {
        const data = await response.json();
        alert(`Failed to stop bot: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      alert(`Network error: ${error}`);
    } finally {
      setIsStopping(false);
    }
  };



  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      {/* Live Trading Sub-navigation - Similar to Scanner */}
      <Box sx={{ mb: 4 }}>
        <Tabs
          value={state.activeLiveTradingTab}
          onChange={handleTabChange}
          sx={{
            backgroundColor: 'rgba(255,255,255,0.02)',
            borderRadius: 3,
            padding: 1,
            '& .MuiTab-root': {
              fontSize: '0.95rem',
              fontWeight: 600,
              textTransform: 'none',
              minHeight: 48,
              borderRadius: 2,
              fontFamily: '"Inter", sans-serif',
              transition: 'all 0.3s ease',
              '&:hover': {
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
              },
            },
            '& .MuiTabs-indicator': {
              display: 'none',
            },
          }}
        >
          <Tab
            label="Token Session"
            value="token"
            icon={<VpnKeyIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            sx={{
              minWidth: 160,
              backgroundColor: state.activeLiveTradingTab === 'token' ? 'rgba(147, 51, 234, 0.1)' : 'transparent',
              color: state.activeLiveTradingTab === 'token' ? '#9333ea !important' : undefined,
            }}
          />
          <Tab
            label="List Validation"
            value="validation"
            icon={<AnalyticsIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            sx={{
              minWidth: 160,
              backgroundColor: state.activeLiveTradingTab === 'validation' ? 'rgba(16, 185, 129, 0.1)' : 'transparent',
              color: state.activeLiveTradingTab === 'validation' ? '#10b981 !important' : undefined,
            }}
          />
          <Tab
            label="Live Trading"
            value="trading"
            icon={<CheckCircleIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            sx={{
              minWidth: 160,
              backgroundColor: state.activeLiveTradingTab === 'trading' ? 'rgba(245, 158, 11, 0.1)' : 'transparent',
              color: state.activeLiveTradingTab === 'trading' ? '#f59e0b !important' : undefined,
            }}
          />
        </Tabs>
      </Box>

      {/* Content Area */}
      <StyledPaper>
        <Box sx={{ mt: 0 }}>
          {state.activeLiveTradingTab === 'token' && (
            <Box>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Token Session Management
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Validate and update your Upstox access token. Required before live trading to ensure API connectivity.
              </Typography>

              {/* Token Status Display */}
              <Box sx={{ mb: 3, p: 3, backgroundColor: '#1a1a1a', borderRadius: '8px', border: '1px solid rgba(147, 51, 234, 0.3)' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <VpnKeyIcon sx={{ color: '#9333ea', fontSize: 24 }} />
                  <Typography variant="h6" sx={{ color: '#9333ea', fontWeight: 600 }}>
                    Access Token Status
                  </Typography>
                  {tokenStatus === 'valid' && (
                    <Chip
                      label="WORKING"
                      sx={{
                        backgroundColor: '#d1fae5',
                        color: '#065f46',
                        fontWeight: 600,
                        fontSize: '0.75rem'
                      }}
                      size="small"
                    />
                  )}
                </Box>

                {tokenStatus === 'valid' && (
                  <Typography variant="body1" sx={{ color: '#10b981', fontWeight: 500, mb: 1 }}>
                    ✅ Your access token is working correctly
                  </Typography>
                )}

                {tokenStatus === 'unknown' && (
                  <Typography variant="body2" sx={{ color: '#6b7280' }}>
                    ℹ️ No token configured yet
                  </Typography>
                )}

                {tokenStatus === 'invalid' && (
                  <Typography variant="body2" sx={{ color: '#ef4444' }}>
                    ❌ Current token is invalid or expired
                  </Typography>
                )}

                {/* Show update form when requested */}
                {showUpdateForm && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" sx={{ mb: 1, color: '#6b7280' }}>
                      Enter your new Upstox access token:
                    </Typography>
                    <TextField
                      fullWidth
                      size="small"
                      type={showToken ? 'text' : 'password'}
                      value={accessToken}
                      onChange={(e) => setAccessToken(e.target.value)}
                      placeholder="Paste your new access token here"
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <VpnKeyIcon sx={{ color: '#9333ea', fontSize: 18 }} />
                          </InputAdornment>
                        ),
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              size="small"
                              onClick={() => setShowToken(!showToken)}
                              edge="end"
                              sx={{ color: '#666' }}
                            >
                              {showToken ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          backgroundColor: '#0d0d0d',
                          '& fieldset': {
                            borderColor: 'rgba(255, 255, 255, 0.23)',
                          },
                          '&:hover fieldset': {
                            borderColor: '#9333ea',
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: '#9333ea',
                          },
                        },
                        '& .MuiInputLabel-root': {
                          color: 'rgba(255, 255, 255, 0.7)',
                        },
                        '& .MuiOutlinedInput-input': {
                          color: '#ffffff',
                        },
                      }}
                    />
                    <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                      <Button
                        variant="contained"
                        size="small"
                        onClick={handleValidateToken}
                        disabled={isValidatingToken || !accessToken.trim()}
                        startIcon={isValidatingToken ? <CircularProgress size={16} /> : <CheckCircleIcon />}
                        sx={{
                          background: 'linear-gradient(135deg, #9333ea 0%, #7c3aed 100%)',
                          '&:hover': {
                            background: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)',
                          },
                          '&:disabled': {
                            background: '#374151',
                          },
                          fontSize: '0.75rem',
                        }}
                      >
                        {isValidatingToken ? 'Validating...' : 'Validate & Update'}
                      </Button>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          setShowUpdateForm(false);
                          setAccessToken('');
                        }}
                        sx={{
                          color: '#6b7280',
                          borderColor: '#666',
                          fontSize: '0.75rem',
                          '&:hover': {
                            color: '#ffffff',
                            borderColor: '#9333ea',
                            backgroundColor: 'rgba(147, 51, 234, 0.1)'
                          }
                        }}
                      >
                        Cancel
                      </Button>
                    </Box>
                  </Box>
                )}

                {/* Action buttons */}
                {!showUpdateForm && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={handleRefreshTokenStatus}
                      disabled={isRefreshingToken}
                      startIcon={isRefreshingToken ? <CircularProgress size={14} /> : null}
                      sx={{
                        color: '#6b7280',
                        borderColor: '#ffffff',
                        fontSize: '0.75rem',
                        textTransform: 'none',
                        borderRadius: '6px',
                        padding: '4px 12px',
                        '&:hover': {
                          color: '#ffffff',
                          borderColor: '#10b981',
                          backgroundColor: 'rgba(16, 185, 129, 0.1)'
                        },
                        '&:disabled': {
                          color: '#6b7280',
                          borderColor: '#374151',
                        }
                      }}
                    >
                      {isRefreshingToken ? 'Refreshing...' : 'Refresh Status'}
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => setShowUpdateForm(true)}
                      sx={{
                        color: '#6b7280',
                        borderColor: '#ffffff',
                        fontSize: '0.75rem',
                        textTransform: 'none',
                        borderRadius: '6px',
                        padding: '4px 12px',
                        '&:hover': {
                          color: '#ffffff',
                          borderColor: '#9333ea',
                          backgroundColor: 'rgba(147, 51, 234, 0.1)'
                        }
                      }}
                    >
                      Update Token
                    </Button>
                  </Box>
                )}
              </Box>

              {/* Validation Results */}
              {tokenValidationResult && (
                <ValidationResult>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                    Token Validation Results:
                  </Typography>
                  {tokenValidationResult}
                </ValidationResult>
              )}

              <Alert severity="info" sx={{ mt: 3 }}>
                <Typography variant="body2">
                  <strong>Note:</strong> This validation:
                  <br />• Tests Upstox API connectivity using your token
                  <br />• Retrieves stock price data to verify access
                  <br />• Saves valid token to config.json for live trading
                  <br />• Must be completed before proceeding to list validation
                </Typography>
              </Alert>
            </Box>
          )}

          {state.activeLiveTradingTab === 'validation' && (
            <Box>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Trading Lists Validation
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Validate continuation_list.txt and reversal_list.txt for live trading readiness.
                Ensures all stocks have valid Upstox instrument keys and LTP data.
              </Typography>

              <Box sx={{ mb: 3 }}>
                <Button
                  variant="contained"
                  onClick={handleValidateLists}
                  disabled={isValidating}
                  startIcon={isValidating ? <CircularProgress size={20} /> : <AnalyticsIcon />}
                  sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                    },
                    borderRadius: '8px',
                    padding: '10px 24px',
                    fontWeight: 600,
                  }}
                >
                  {isValidating ? 'Validating...' : 'Validate Lists'}
                </Button>

                {validationStatus !== 'idle' && (
                  <StatusChip
                    status={validationStatus}
                    label={validationStatus === 'success' ? 'Validation Complete' :
                           validationStatus === 'error' ? 'Validation Failed' : 'Validating...'}
                    size="small"
                  />
                )}
              </Box>

              {validationResult && (
                <ValidationResult>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                    Validation Results:
                  </Typography>
                  {validationResult}
                </ValidationResult>
              )}
            </Box>
          )}

          {state.activeLiveTradingTab === 'trading' && (
            <Box>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Live Trading Control
              </Typography>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Start and stop the live trading bot. Choose between continuation and reversal trading modes.
              </Typography>

              {/* Mode Selection */}
              <Box sx={{ mb: 4 }}>
                <FormControl component="fieldset">
                  <FormLabel component="legend" sx={{ color: 'text.primary', fontWeight: 600, mb: 2 }}>
                    Trading Mode
                  </FormLabel>
                  <RadioGroup
                    row
                    value={tradingMode}
                    onChange={(e) => setTradingMode(e.target.value as 'continuation' | 'reversal')}
                    sx={{ gap: 4 }}
                  >
                    <FormControlLabel
                      value="continuation"
                      control={<Radio sx={{ color: '#10b981', '&.Mui-checked': { color: '#10b981' } }} />}
                      label="Continuation Trading"
                      disabled={botStatus === 'running'}
                    />
                    <FormControlLabel
                      value="reversal"
                      control={<Radio sx={{ color: '#f59e0b', '&.Mui-checked': { color: '#f59e0b' } }} />}
                      label="Reversal Trading"
                      disabled={botStatus === 'running'}
                    />
                  </RadioGroup>
                </FormControl>
              </Box>



              {/* Control Buttons */}
              <Box sx={{ mb: 4, display: 'flex', gap: 2, alignItems: 'center' }}>
                <Button
                  variant="contained"
                  onClick={handleStartTrading}
                  disabled={botStatus === 'running' || isStarting || isStopping}
                  startIcon={isStarting ? <CircularProgress size={20} /> : <PlayArrowIcon />}
                  sx={{
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                    },
                    '&:disabled': {
                      background: '#374151',
                    },
                    borderRadius: '8px',
                    padding: '12px 32px',
                    fontWeight: 600,
                    fontSize: '1rem',
                  }}
                >
                  {isStarting ? 'Starting...' : 'Start Trading'}
                </Button>

                <Button
                  variant="contained"
                  onClick={handleStopTrading}
                  disabled={botStatus === 'stopped' || isStarting || isStopping}
                  startIcon={isStopping ? <CircularProgress size={20} /> : <StopIcon />}
                  sx={{
                    background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
                    },
                    '&:disabled': {
                      background: '#374151',
                    },
                    borderRadius: '8px',
                    padding: '12px 32px',
                    fontWeight: 600,
                    fontSize: '1rem',
                  }}
                >
                  {isStopping ? 'Stopping...' : 'Stop Trading'}
                </Button>

                {/* Status Display */}
                <Box sx={{ ml: 4, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    Status:
                  </Typography>
                  {isCheckingBotStatus ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CircularProgress size={16} sx={{ color: '#6b7280' }} />
                      <Typography variant="body2" sx={{ color: '#6b7280', fontWeight: 500 }}>
                        Checking...
                      </Typography>
                    </Box>
                  ) : (
                    <>
                      <Chip
                        label={botStatus.toUpperCase()}
                        sx={{
                          backgroundColor: botStatus === 'running' ? '#d1fae5' : '#fee2e2',
                          color: botStatus === 'running' ? '#065f46' : '#991b1b',
                          fontWeight: 600,
                          fontSize: '0.875rem',
                        }}
                        size="small"
                      />
                      {botStatus === 'running' && (
                        <Typography variant="body2" sx={{ color: '#10b981', fontWeight: 500 }}>
                          ({tradingMode})
                        </Typography>
                      )}
                    </>
                  )}
                </Box>
              </Box>

              {/* Live Logs */}
              {liveLogs.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
                    Live Activity
                  </Typography>
                  <Box sx={{ position: 'relative' }}>
                    <ValidationResult sx={{ height: `${terminalHeight}px`, overflowY: 'auto' }}>
                      {liveLogs.map((log, index) => (
                        <div key={index} style={{ marginBottom: '4px' }}>
                          {log}
                        </div>
                      ))}
                    </ValidationResult>
                    {/* Resize Handle */}
                    <Box
                      sx={{
                        position: 'absolute',
                        bottom: 0,
                        left: 0,
                        right: 0,
                        height: '8px',
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        cursor: 'ns-resize',
                        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        '&:hover': {
                          backgroundColor: 'rgba(147, 51, 234, 0.2)',
                        },
                      }}
                      onMouseDown={handleMouseDown}
                    >
                      <Box
                        sx={{
                          width: '30px',
                          height: '2px',
                          backgroundColor: 'rgba(255, 255, 255, 0.3)',
                          borderRadius: '1px',
                        }}
                      />
                    </Box>
                  </Box>
                </Box>
              )}

              <Alert severity="warning" sx={{ mt: 3 }}>
                <Typography variant="body2">
                  <strong>⚠️ Live Trading Notice:</strong> This will execute real trades using your Upstox account.
                  Ensure you have validated your trading lists and understand the selected mode before starting.
                </Typography>
              </Alert>
            </Box>
          )}
        </Box>
      </StyledPaper>
    </Box>
  );
};

export default LiveTrading;
