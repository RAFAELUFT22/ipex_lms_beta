const API_BASE = import.meta.env.VITE_LMS_API_URL || 'https://api-lms.ipexdesenvolvimento.cloud';
const ADMIN_KEY = import.meta.env.VITE_ADMIN_KEY;

// Decodifica expiração do token sem biblioteca externa
function getTokenExp(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000;
  } catch { return 0; }
}

async function tryRefresh(token) {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const data = await res.json();
      sessionStorage.setItem('tds_student_token', data.session_token);
      return data.session_token;
    }
  } catch (e) { console.error("Refresh failed", e); }
  return null;
}

async function apiFetch(path, options = {}) {
  let token = sessionStorage.getItem('tds_student_token');
  
  // Pre-emptive refresh: se faltar menos de 30 min, tenta renovar antes de chamar
  if (token) {
    const remaining = getTokenExp(token) - Date.now();
    if (remaining > 0 && remaining < 30 * 60 * 1000) {
      const newToken = await tryRefresh(token);
      if (newToken) token = newToken;
    }
  }

  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // Interceptor Reativo: 401 session_expired -> tenta refresh e repete
  if (res.status === 401) {
    const body = await res.json().catch(() => ({}));
    if (body.detail === 'session_expired' && token) {
      const refreshed = await tryRefresh(token);
      if (refreshed) {
        headers['Authorization'] = `Bearer ${refreshed}`;
        res = await fetch(`${API_BASE}${path}`, { ...options, headers });
      } else {
        // Falha total na sessão
        sessionStorage.clear();
        window.dispatchEvent(new CustomEvent('tds_session_expired'));
        throw new Error('session_expired');
      }
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const lmsLiteApi = {
  getStudents: () => apiFetch('/students'),
  getStudent: (phone) => apiFetch(`/student/${phone}`),
  
  sendOtp: (phone) => apiFetch('/otp/send', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  }),

  verifyOtp: (phone, code) => apiFetch('/otp/verify', {
    method: 'POST',
    body: JSON.stringify({ phone, code }),
  }),

  getMe: () => apiFetch('/session/me'),
  getMyQuizResult: (courseSlug) => apiFetch(`/student/me/quiz/${courseSlug}`),


  getCourses: () => apiFetch('/courses'),
  getQuiz: (courseSlug) => apiFetch(`/quiz/${courseSlug}`),
  saveQuiz: (courseSlug, questions) =>
    apiFetch(`/admin/courses/${courseSlug}/quiz`, {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_KEY },
      body: JSON.stringify({ questions }),
    }),
  submitQuiz: (phone, course_slug, answers) =>
    apiFetch('/quiz/submit', {
      method: 'POST',
      body: JSON.stringify({ phone, course_slug, answers }),
    }),

  requestEnrollment: (data) => apiFetch('/enrollment/request', {
    method: 'POST',
    body: JSON.stringify(data)
  }),

  issueCert: (whatsapp, course_slug) => apiFetch('/issue_cert', {
    method: 'POST',
    body: JSON.stringify({ whatsapp, course_slug }),
  }),

  validateCert: (hash) => apiFetch(`/validate_cert/${hash}`),
  getCertPdfUrl: (hash) => `${API_BASE}/cert/${hash}/pdf`,
  bulkImportStudents: (students) =>
    apiFetch('/admin/students/bulk', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_KEY },
      body: JSON.stringify({ students }),
    }),
  getMetricsSummary: () =>
    apiFetch('/admin/metrics/summary', {
      headers: { 'X-Admin-Key': ADMIN_KEY },
    }),
  exportStudentLgpd: (phone) =>
    apiFetch(`/student/${phone}/export`, {
      headers: { 'X-Admin-Key': ADMIN_KEY },
    }),
  deleteStudentLgpd: (phone) =>
    apiFetch(`/student/${phone}`, {
      method: 'DELETE',
      headers: { 'X-Admin-Key': ADMIN_KEY },
    }),

  getSettings: () => apiFetch('/settings', { headers: { 'X-Admin-Key': ADMIN_KEY } }),
  
  saveSettings: (data) => apiFetch('/settings', {
    method: 'PUT',
    headers: { 'X-Admin-Key': ADMIN_KEY },
    body: JSON.stringify(data),
  }),

  linkWorkspace: (course_slug, workspace_slug) => apiFetch('/admin/courses/link_workspace', {
    method: 'POST',
    headers: { 'X-Admin-Key': ADMIN_KEY },
    body: JSON.stringify({ course_slug, workspace_slug })
  }),

  fetchSheet: (url) => apiFetch(`/external/sheets?url=${encodeURIComponent(url)}`, {
    headers: { 'X-Admin-Key': ADMIN_KEY },
  }),

  getExportUrl: () => `${API_BASE}/admin/students/export?x_admin_key=${ADMIN_KEY}`,
  sendNotification: (data) =>
    apiFetch('/admin/notify', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_KEY },
      body: JSON.stringify(data),
    }),
  scheduleNotification: (data) =>
    apiFetch('/admin/notify/schedule', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_KEY },
      body: JSON.stringify(data),
    }),
  getNotificationLog: () =>
    apiFetch('/admin/notify/log', {
      headers: { 'X-Admin-Key': ADMIN_KEY },
    }),

  // --- COMMUNITIES ---
  getCommunities: () => apiFetch('/communities'),
  createCommunity: (data) => apiFetch('/communities', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  deleteCommunity: (slug) => apiFetch(`/communities/${slug}`, {
    method: 'DELETE'
  }),
  broadcastToCommunity: (slug, message) => apiFetch(`/communities/${slug}/broadcast`, {
    method: 'POST',
    body: JSON.stringify({ message })
  }),

  // --- PROXIES ---
  ragList: () => apiFetch('/admin/rag/documents', { headers: { 'X-Admin-Key': ADMIN_KEY } }),
  ragUpload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${API_BASE}/admin/rag/upload`, {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_KEY },
      body: formData
    }).then(res => res.json());
  },
  ragDelete: (path) => apiFetch(`/admin/rag/documents/${encodeURIComponent(path)}`, {
    method: 'DELETE',
    headers: { 'X-Admin-Key': ADMIN_KEY }
  }),

  evoCreate: (body) => apiFetch('/admin/evolution/instance/create', {
    method: 'POST',
    headers: { 'X-Admin-Key': ADMIN_KEY },
    body: JSON.stringify(body)
  }),
  evoFetch: () => apiFetch('/admin/evolution/instance/fetch', {
    headers: { 'X-Admin-Key': ADMIN_KEY }
  }),
  evoConnect: (name) => apiFetch(`/admin/evolution/instance/connect/${name}`, {
    headers: { 'X-Admin-Key': ADMIN_KEY }
  }),
  evoDelete: (name) => apiFetch(`/admin/evolution/instance/delete/${name}`, {
    method: 'DELETE',
    headers: { 'X-Admin-Key': ADMIN_KEY }
  }),
  evoSendMessage: (instance, number, text) => apiFetch(`/admin/evolution/message/send/${instance}`, {
    method: 'POST',
    headers: { 'X-Admin-Key': ADMIN_KEY },
    body: JSON.stringify({ number, text, linkPreview: false })
  }),

  // --- METRICS ---
  getMetrics: () => apiFetch('/admin/metrics/summary', { headers: { 'X-Admin-Key': ADMIN_KEY } }),

  // --- QUIZ ---
  getQuiz: (course_slug) => apiFetch(`/quiz/${course_slug}`),
  submitQuiz: (phone, course_slug, answers) => apiFetch('/quiz/submit', {
    method: 'POST',
    body: JSON.stringify({ phone, course_slug, answers }),
  }),
  getMyQuizResult: (course_slug) => apiFetch(`/student/me/quiz/${course_slug}`),

  // --- NOTIFICATIONS ---
  sendNotify: (target, message, channel = 'whatsapp') => apiFetch('/admin/notify', {
    method: 'POST',
    headers: { 'X-Admin-Key': ADMIN_KEY },
    body: JSON.stringify({ target, message, channel }),
  }),
  getNotifyLog: () => apiFetch('/admin/notify/log', { headers: { 'X-Admin-Key': ADMIN_KEY } }),

  // --- ADMIN QUIZ BUILDER ---
  saveQuiz: (course_slug, questions) => apiFetch(`/admin/courses/${course_slug}/quiz`, {
    method: 'POST',
    headers: { 'X-Admin-Key': ADMIN_KEY },
    body: JSON.stringify({ questions }),
  }),
};
