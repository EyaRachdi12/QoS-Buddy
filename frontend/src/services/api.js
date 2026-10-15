import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000,
});

// ── Auth token interceptor ──
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('qos_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('qos_token');
      localStorage.removeItem('qos_user');
    }
    return Promise.reject(err);
  },
);

/**
 * Normalize Axios / network errors for UI messages.
 */
export function getApiError(error) {
  if (!error) return 'Unknown error';
  if (error.response?.data?.detail !== undefined) {
    const d = error.response.data.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d)) {
      return d.map((x) => x?.msg || JSON.stringify(x)).join('; ') || 'Validation error';
    }
    if (typeof d === 'object' && d?.message) return String(d.message);
    try {
      return JSON.stringify(d);
    } catch {
      return 'Request failed';
    }
  }
  if (error.code === 'ECONNABORTED') return 'Request timed out — try a smaller time window or refresh data.';
  if (error.message === 'Network Error') return 'Cannot reach API. Is the backend running?';
  return error.message || 'Request failed';
}

// ── Auth API ──
export const authAPI = {
  register: async (username, password, role = 'viewer') => {
    const response = await api.post('/api/auth/register', { username, password, role });
    return response.data;
  },
  login: async (username, password) => {
    const response = await api.post('/api/auth/login', { username, password });
    return response.data;
  },
  saveSession: (data) => {
    localStorage.setItem('qos_token', data.access_token);
    localStorage.setItem('qos_user', JSON.stringify({ username: data.username, role: data.role }));
  },
  logout: () => {
    localStorage.removeItem('qos_token');
    localStorage.removeItem('qos_user');
  },
  getStoredUser: () => {
    try {
      const u = localStorage.getItem('qos_user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  },
  isLoggedIn: () => !!localStorage.getItem('qos_token'),
};

export const chatAPI = {
  sendMessage: async (message, options = {}) => {
    const response = await api.post('/api/chat', {
      message,
      conversation_id: options.conversationId || null,
      include_live_insights: options.includeLiveInsights !== false,
    });
    return response.data;
  },
};

export const diagnosticAPI = {
  getLatestAlerts: async (limit = 20) => {
    const response = await api.get('/api/diagnostics/latest', {
      params: { limit },
    });
    return response.data;
  },

  triggerAnalysis: async (timeWindowHours = 1) => {
    const response = await api.post('/api/diagnostics/analyze', {
      time_window_hours: timeWindowHours,
    });
    return response.data;
  },

  getSummary: async () => {
    const response = await api.get('/api/summary');
    return response.data;
  },
};

export const kpiAPI = {
  getRealtimeKPIs: async (limit = 100) => {
    const response = await api.get('/api/kpis/realtime', {
      params: { limit },
    });
    return response.data;
  },

  getCellStatus: async (cellId) => {
    const response = await api.get(`/api/cells/${cellId}/status`);
    return response.data;
  },

  listCells: async () => {
    const response = await api.get('/api/cells/list');
    return response.data;
  },
};

export const healthAPI = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export const boAPI = {
  getOverview: async (timeWindowHours = 24, maxZones = 120, boFilter = null) => {
    const params = {
      time_window_hours: timeWindowHours,
      max_zones: maxZones,
    };
    if (boFilter) params.bo_filter = boFilter;
    const response = await api.get('/api/bo/overview', { params });
    return response.data;
  },

  getDashboardBundle: async (boFilter = null, timeWindowHours = 24) => {
    const params = { time_window_hours: timeWindowHours };
    if (boFilter) params.bo_filter = boFilter;
    const response = await api.get('/api/bo/dashboard-bundle', { params });
    return response.data;
  },
};

export const dataAPI = {
  getSourceBoSummary: async () => {
    const response = await api.get('/api/data/source-bo-summary');
    return response.data;
  },
};

export const mlAPI = {
  detect: async (body) => {
    const response = await api.post('/api/ml/detect', body);
    return response.data;
  },
  predict: async (body) => {
    const response = await api.post('/api/ml/predict', body);
    return response.data;
  },
  orchestrate: async (body) => {
    const response = await api.post('/api/ml/orchestrate', body);
    return response.data;
  },
  modelsStatus: async () => {
    const response = await api.get('/api/ml/models/status');
    return response.data;
  },
  refreshData: async () => {
    const response = await api.post('/api/data/refresh');
    return response.data;
  },
  enrichmentCatalog: async (offset = 0, limit = 30) => {
    const response = await api.get('/api/enrichment/catalog', {
      params: { offset, limit },
    });
    return response.data;
  },
  enrichmentScrape: async () => {
    const response = await api.post('/api/enrichment/scrape');
    return response.data;
  },
  driftCheck: async (timeWindowHours = 24, boFilter = null) => {
    const params = { time_window_hours: timeWindowHours };
    if (boFilter) params.bo_filter = boFilter;
    const response = await api.get('/api/ml/drift', { params });
    return response.data;
  },
};

// ── Simulator API ──
export const simulatorAPI = {
  start: async (intervalMinutes = 5) => {
    const response = await api.post('/api/simulator/start', { interval_minutes: intervalMinutes });
    return response.data;
  },
  stop: async () => {
    const response = await api.post('/api/simulator/stop');
    return response.data;
  },
  status: async () => {
    const response = await api.get('/api/simulator/status');
    return response.data;
  },
};

export default api;
