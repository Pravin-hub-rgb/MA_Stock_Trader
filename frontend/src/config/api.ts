// API Configuration
// Central place to configure API endpoints - change here if port changes

export const API_CONFIG = {
  // Use relative URLs - proxy handles routing in development
  BASE_URL: '',

  // API endpoints
  ENDPOINTS: {
    // Scanner endpoints
    SCANNER: {
      CONTINUATION: '/api/scanner/continuation',
      REVERSAL: '/api/scanner/reversal',
      STATUS: (operationId: string) => `/api/scanner/status/${operationId}`,
    },

    // Live trading endpoints
    LIVE_TRADING: {
      START: '/api/live-trading/start',
      STOP: '/api/live-trading/stop',
      LOGS: '/api/live-trading/logs',
      STATUS: '/api/live-trading/status',
      VALIDATE_LISTS: '/api/live-trading/validate-lists',
      VAH_RESULTS: '/api/live-trading/vah-results',
    },

    // Token management
    TOKEN: {
      VALIDATE: '/api/token/validate',
      CURRENT: '/api/token/current',
      UPDATE: '/api/token/update',
    },

    // Stock management
    STOCKS: {
      CONTINUATION: '/api/stocks/continuation',
      REVERSAL: '/api/stocks/reversal',
      TRADING_FILES: (listType: string) => `/api/stocks/trading-files/${listType}`,
    },

    // File operations
    FILES: {
      LIST: '/api/files/list',
      DOWNLOAD: (filename: string) => `/api/files/download/${filename}`,
    },

    // Data operations
    DATA: {
      UPDATE_BHAVCOPY: '/api/data/update-bhavcopy',
      STATUS: (operationId: string) => `/api/data/status/${operationId}`,
      CACHE_INFO: '/api/data/cache-info',
    },

    // Breadth analysis
    BREADTH: {
      DATA: '/api/breadth/data',
      UPDATE: '/api/breadth/update',
    },
  },
};

// Helper function to get full URL (for development proxy)
export const getApiUrl = (endpoint: string): string => {
  // In development, proxy handles routing
  // In production, use relative URLs
  return endpoint;
};

// Export commonly used endpoints
export const {
  SCANNER,
  LIVE_TRADING,
  TOKEN,
  STOCKS,
  FILES,
  DATA,
  BREADTH
} = API_CONFIG.ENDPOINTS;
