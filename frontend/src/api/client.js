/**
 * Unified API Client for AutoBotix & Google Review Automation Backend
 */

function getCookieValue(name) {
  if (typeof document === 'undefined') return '';
  const match = document.cookie.match(new RegExp('(?:^|;\\s*)' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[1]) : '';
}

async function getOrFetchCsrfToken() {
  let token = '';
  try {
    token = localStorage.getItem('csrf_token') || '';
  } catch {}
  if (!token) {
    token = getCookieValue('csrf_token');
    if (token) {
      try { localStorage.setItem('csrf_token', token); } catch {}
    }
  }
  if (!token) {
    try {
      const res = await fetch('/api/csrf-token', { credentials: 'include' });
      if (res.ok) {
        const json = await res.json();
        if (json && json.csrf_token) {
          token = json.csrf_token;
          try { localStorage.setItem('csrf_token', token); } catch {}
        }
      }
    } catch {}
  }
  return token;
}

async function request(url, options = {}, isRetry = false) {
  const defaultHeaders = {
    'Accept': 'application/json',
  };

  if (options.body && !(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  const isMutating = ['POST', 'PUT', 'PATCH', 'DELETE'].includes((options.method || 'GET').toUpperCase());
  if (isMutating) {
    const csrfToken = await getOrFetchCsrfToken();
    if (csrfToken) {
      defaultHeaders['X-CSRF-Token'] = csrfToken;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    credentials: 'include', // send session cookie
  });

  if (response.status === 401) {
    // Unauthorized
    return { error: 'Unauthorized', status: 401 };
  }

  // Handle CSRF expiration retry
  if (response.status === 400 && !isRetry && isMutating) {
    const errorText = await response.clone().text();
    if (errorText.toLowerCase().includes('csrf')) {
      try {
        localStorage.removeItem('csrf_token');
      } catch {}
      await getOrFetchCsrfToken();
      return request(url, options, true);
    }
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || data.error || `HTTP error ${response.status}`);
    }
    return data;
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP error ${response.status}`);
  }

  return await response.text();
}

export const api = {
  // Auth
  async checkAuth() {
    try {
      const data = await request('/api/auth/me');
      if (data && data.csrf_token) {
        localStorage.setItem('csrf_token', data.csrf_token);
      }
      return data;
    } catch {
      return { authenticated: false };
    }
  },

  async login(password) {
    const res = await request('/api/login', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
    if (res && res.csrf_token) {
      localStorage.setItem('csrf_token', res.csrf_token);
    }
    return res;
  },

  async logout() {
    try {
      await request('/api/logout', { method: 'POST' });
    } finally {
      localStorage.removeItem('csrf_token');
    }
    return { status: 'ok' };
  },

  // Dashboard & Core Reviews
  async getDashboard() {
    return request('/api/dashboard');
  },

  async getAnalytics() {
    return request('/api/analytics');
  },

  // Review Studio & AI Templates
  async getTemplates() {
    return request('/api/templates');
  },

  async addTemplate(data) {
    return request('/api/templates', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async deleteTemplate(id) {
    return request(`/api/templates/${id}`, { method: 'DELETE' });
  },

  async batchGenerate(params) {
    return request('/api/templates/batch-generate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async pushToBusiness(params) {
    return request('/api/templates/push-to-business', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  // Drip Campaign & Scheduler
  async getCampaigns() {
    return request('/api/campaigns');
  },

  async saveCampaignConfig(config) {
    return request('/api/campaigns/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  },

  // Live Worker Console
  async getWorkerStatus() {
    return request('/api/worker/status');
  },

  async emergencyStopWorker() {
    return request('/api/worker/emergency-stop', { method: 'POST' });
  },

  async generatePreview(params) {
    // params: { business_name, description, star_rating, persona, language, review_style }
    return request('/api/generate-preview', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async addBusiness(name, url) {
    return request('/api/businesses', {
      method: 'POST',
      body: JSON.stringify({ name, url }),
    });
  },

  async deleteBusiness(id) {
    return request(`/api/businesses/${id}`, { method: 'DELETE' });
  },

  async addEmail(email, password, totp_secret) {
    return request('/api/emails', {
      method: 'POST',
      body: JSON.stringify({ email, password, totp_secret }),
    });
  },

  async deleteEmail(id) {
    return request(`/api/emails/${id}`, { method: 'DELETE' });
  },

  async updateEmail(id, email, password, totp_secret) {
    return request(`/api/emails/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ email, password: password || undefined, totp_secret: totp_secret || undefined }),
    });
  },

  async testLoginEmail(id) {
    return request(`/api/emails/${id}/test-login`, { method: 'POST' });
  },

  async unflagEmail(id) {
    return request(`/api/emails/${id}/unflag`, { method: 'POST' });
  },

  async unflagAllEmails() {
    return request('/api/emails/unflag-all', { method: 'POST' });
  },

  async getGoogleOAuthUrl() {
    return request('/api/auth/google/url');
  },

  async addCookie(email, cookie_json) {
    return request('/api/cookies', {
      method: 'POST',
      body: JSON.stringify({ cookie_email: email, cookie_json }),
    });
  },

  async deleteCookie(id) {
    return request(`/api/cookies/${id}`, { method: 'DELETE' });
  },

  async testCookie(id) {
    return request(`/api/cookies/${id}/test`, { method: 'POST' });
  },

  async checkAccountNames() {
    return request('/api/cli/cookies/check-names', { method: 'POST' });
  },

  async getCliStatus() {
    return request('/api/cli/status');
  },

  async getCookieHealth() {
    return request('/api/cookies/health');
  },

  // Business Detail & Queue Control
  async getBusinessDetail(id) {
    return request(`/api/businesses/${id}`);
  },

  async getBusiness(id) {
    return this.getBusinessDetail(id);
  },

  async saveBusinessConfig(id, config) {
    return request(`/api/businesses/${id}/config`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  },

  async testGeminiReview(id, payload) {
    return request(`/api/businesses/${id}/test-gemini`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async startBot(id, params) {
    // params: { star_1_count...star_5_count, selected_email_ids, selected_language, review_style }
    return request(`/api/businesses/${id}/start-bot`, {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async stopBot(id) {
    return request(`/api/businesses/${id}/stop-bot`, { method: 'POST' });
  },

  async resetAllBusinessReviews(id) {
    return request(`/api/businesses/${id}/reset-all-reviews`, { method: 'POST' });
  },

  async deleteBusinessComments(id) {
    return request(`/api/businesses/${id}/dark-mode/delete-comments`, { method: 'POST' });
  },

  async deleteOwnReviewsOnMaps(id, payload = {}) {
    return request(`/api/businesses/${id}/dark-mode/delete-maps-reviews`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async reportBusinessMap(id, payload) {
    return request(`/api/businesses/${id}/dark-mode/report-map`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getProcessLogs(id) {
    return request(`/api/businesses/${id}/process-log`);
  },

  async clearProcessLogs(id) {
    return request(`/api/businesses/${id}/clear-logs`, { method: 'POST' });
  },

  async inspectReview(businessId, reviewId) {
    return request(`/api/businesses/${businessId}/inspect-review/${reviewId}`);
  },

  async resetReview(businessId, reviewId) {
    return request(`/api/businesses/${businessId}/reset-review/${reviewId}`, { method: 'POST' });
  },

  async deleteReview(businessId, reviewId) {
    return request(`/api/businesses/${businessId}/delete-review/${reviewId}`, { method: 'DELETE' });
  },

  // AutoBotix Modules
  async getAutobotixOverview() {
    return request('/api/autobotix/overview');
  },

  async getDomains(search = '', status = '') {
    const q = new URLSearchParams();
    if (search) q.append('q', search);
    if (status) q.append('status', status);
    return request(`/api/autobotix/domains?${q.toString()}`);
  },

  async getDomain(id) {
    return request(`/api/autobotix/domains/${id}`);
  },

  async getTunnels() {
    return request('/api/autobotix/tunnels');
  },

  async getTunnel(id) {
    return request(`/api/autobotix/tunnels/${id}`);
  },

  async getMonitoring() {
    return request('/api/autobotix/monitoring');
  },

  async getActivity() {
    return request('/api/autobotix/activity');
  },

  async importSnapshot() {
    return request('/api/autobotix/import-snapshot', { method: 'POST' });
  },

  // Grok Mascot AI Chat Assistant
  async chatMascot(message, businessId) {
    return request('/api/mascot/chat', {
      method: 'POST',
      body: JSON.stringify({ message, business_id: businessId }),
    });
  },

  // Remote VM Control (VM 101-106)
  async controlVm(vmid, action, params = {}) {
    return request(`/api/vm/${vmid}/control`, {
      method: 'POST',
      body: JSON.stringify({ action, ...params }),
    });
  },

  // Live Screen Logs
  async getScreenLogs(limit = 25) {
    return request(`/api/screen/logs?limit=${limit}`);
  },
};
