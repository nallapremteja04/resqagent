// ResQAgent REST API Client with Production & Local Dynamic Resolution
function getApiBase() {
  let base = '/api';

  if (typeof window !== 'undefined') {
    // 1. Explicit window override (e.g. window.RESQAGENT_API_URL = "https://resqagent.onrender.com")
    if (window.RESQAGENT_API_URL) {
      base = window.RESQAGENT_API_URL;
    } else {
      // 2. Query param override (e.g. ?api=https://resqagent.onrender.com)
      try {
        const params = new URLSearchParams(window.location.search);
        const queryUrl = params.get('api') || params.get('api_url');
        if (queryUrl) {
          base = queryUrl;
          localStorage.setItem('resqagent_api_url', queryUrl);
        } else {
          // 3. Stored API URL from previous setting
          const stored = localStorage.getItem('resqagent_api_url');
          if (stored) base = stored;
        }
      } catch (e) {}
    }
  }

  base = base.trim().replace(/\/+$/, '');

  // If a full domain is supplied without the /api prefix, append /api
  if ((base.startsWith('http://') || base.startsWith('https://')) && !base.endsWith('/api')) {
    base += '/api';
  }

  return base;
}

function getAuthToken() {
  return localStorage.getItem('resqagent_token');
}

function setAuthToken(token) {
  if (token) {
    localStorage.setItem('resqagent_token', token);
  } else {
    localStorage.removeItem('resqagent_token');
  }
}

async function request(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const base = getApiBase();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const url = `${base}${cleanEndpoint}`;

  const res = await fetch(url, {
    ...options,
    headers
  });

  if (res.status === 401) {
    // If not already on auth endpoint, trigger session expired
    if (!endpoint.startsWith('/auth/login') && !endpoint.startsWith('/auth/register')) {
      setAuthToken(null);
      window.dispatchEvent(new CustomEvent('session-expired'));
    }
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Network or server error' }));
    throw new Error(errorData.detail || `Request failed with status ${res.status}`);
  }

  return res.json();
}

const api = {
  // Authentication Endpoints
  async register(payload) {
    const data = await request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (data.access_token) {
      setAuthToken(data.access_token);
    }
    return data;
  },

  async login(email, password) {
    const data = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    if (data.access_token) {
      setAuthToken(data.access_token);
    }
    return data;
  },

  async logout() {
    try {
      await request('/auth/logout', { method: 'POST' });
    } catch (e) {
      // Ignore network errors on logout
    } finally {
      setAuthToken(null);
    }
  },

  async getMe() {
    return request('/auth/me');
  },

  async changePassword(payload) {
    return request('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // Admin Endpoints
  async adminGetUsers(role = null) {
    const url = role ? `/admin/users?role=${role}` : '/admin/users';
    return request(url);
  },

  async adminCreateUser(payload) {
    return request('/admin/users', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async adminToggleUserStatus(userId, isActive) {
    return request(`/admin/users/${userId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: isActive })
    });
  },

  async adminGetStats() {
    return request('/admin/system-stats');
  },

  // Operational APIs
  async getHealth() {
    return request('/health');
  },

  async getResponders(availability = null) {
    const url = availability 
      ? `/responders/?availability=${encodeURIComponent(availability)}` 
      : `/responders/`;
    return request(url);
  },

  async updateResponderStatus(id, availability) {
    return request(`/responders/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ availability })
    });
  },

  async createIncident(payload) {
    return request('/incidents/', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async getIncidents(status = null) {
    const url = status 
      ? `/incidents/?status=${encodeURIComponent(status)}` 
      : `/incidents/`;
    return request(url);
  },

  async getIncident(id) {
    return request(`/incidents/${id}`);
  },

  async getTimeline(incidentId) {
    return request(`/incidents/${incidentId}/timeline`);
  },

  async getAgentActions(incidentId) {
    return request(`/incidents/${incidentId}/actions`);
  },

  async getNotifications(incidentId) {
    return request(`/incidents/${incidentId}/notifications`);
  },

  async getAssignments(incidentId = null, responderId = null) {
    let url = `/assignments/?`;
    if (incidentId) url += `incident_id=${incidentId}&`;
    if (responderId) url += `responder_id=${responderId}&`;
    return request(url);
  },

  async respondToAssignment(assignmentId, status, notes = '') {
    return request(`/assignments/${assignmentId}/respond`, {
      method: 'POST',
      body: JSON.stringify({ status, notes })
    });
  },

  async timeoutAssignment(assignmentId) {
    return request(`/assignments/${assignmentId}/timeout`, {
      method: 'POST'
    });
  },

  async updateAssignmentProgress(assignmentId, status, notes = '') {
    return request(`/assignments/${assignmentId}/progress`, {
      method: 'POST',
      body: JSON.stringify({ status, notes })
    });
  },

  async getReport(incidentId) {
    try {
      return await request(`/reports/${incidentId}`);
    } catch (e) {
      return null;
    }
  },

  async generateReport(incidentId) {
    return request(`/reports/${incidentId}/generate`, {
      method: 'POST'
    });
  },

  async triggerTimeout(incidentId) {
    return request(`/simulation/timeout/${incidentId}`, {
      method: 'POST'
    });
  },

  async resetSimulation() {
    return request('/simulation/reset', {
      method: 'POST'
    });
  }
};

window.api = api;
window.getAuthToken = getAuthToken;
window.setAuthToken = setAuthToken;
window.getApiBase = getApiBase;
window.setApiBase = function(url) {
  if (url) {
    localStorage.setItem('resqagent_api_url', url);
    window.RESQAGENT_API_URL = url;
  } else {
    localStorage.removeItem('resqagent_api_url');
    delete window.RESQAGENT_API_URL;
  }
};
