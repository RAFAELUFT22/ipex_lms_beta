const API_BASE = import.meta.env.VITE_LMS_API_URL || 'https://api-lms.ipexdesenvolvimento.cloud';
const ADMIN_KEY = import.meta.env.VITE_ADMIN_KEY || 'admin-tds-2026';

async function apiFetch(path, options = {}) {
  const token = sessionStorage.getItem('tds_student_token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const lmsLiteApi = {
  getStudents: () => apiFetch('/students'),

  getStudent: (phone) => apiFetch(`/student/${phone}`),

  sendOtp: (phone) =>
    apiFetch('/otp/send', {
      method: 'POST',
      body: JSON.stringify({ phone }),
    }),

  verifyOtp: (phone, code) =>
    apiFetch('/otp/verify', {
      method: 'POST',
      body: JSON.stringify({ phone, code }),
    }),

  getMe: () => apiFetch('/session/me'),
  getMyQuizResult: (courseSlug) => apiFetch(`/student/me/quiz/${courseSlug}`),

  getCourses: () => apiFetch('/courses'),

  issueCert: (whatsapp, course_slug) =>
    apiFetch('/issue_cert', {
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

  getSettings: () =>
    apiFetch('/settings', { headers: { 'X-Admin-Key': ADMIN_KEY } }),

  saveSettings: (data) =>
    apiFetch('/settings', {
      method: 'PUT',
      headers: { 'X-Admin-Key': ADMIN_KEY },
      body: JSON.stringify(data),
    }),

  fetchSheet: (url) =>
    apiFetch(`/external/sheets?url=${encodeURIComponent(url)}`, {
      headers: { 'X-Admin-Key': ADMIN_KEY },
    }),

  getExportUrl: () => `${API_BASE}/admin/students/export?x_admin_key=${ADMIN_KEY}`,

  // --- PROXIES ---

  // RAG Proxy
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

  // Evolution Proxy
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
  evoSetChatwoot: (instance, body) => apiFetch(`/admin/evolution/chatwoot/set/${instance}`, {
    method: 'POST',
    headers: { 'X-Admin-Key': ADMIN_KEY },
    body: JSON.stringify(body)
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

  // Chatwoot Proxy
  cwSearch: (q) => apiFetch(`/admin/chatwoot/contacts/search?q=${encodeURIComponent(q)}`, {
    headers: { 'X-Admin-Key': ADMIN_KEY }
  }),
  cwGetConvs: (contactId) => apiFetch(`/admin/chatwoot/contacts/${contactId}/conversations`, {
    headers: { 'X-Admin-Key': ADMIN_KEY }
  }),
  cwToggleStatus: (convId, status) => apiFetch(`/admin/chatwoot/conversations/${convId}/toggle_status`, {
    method: 'POST',
    headers: { 'X-Admin-Key': ADMIN_KEY },
    body: JSON.stringify({ status })
  }),
  cwSendMsg: (convId, content) => apiFetch(`/admin/chatwoot/conversations/${convId}/messages`, {
    method: 'POST',
    headers: { 'X-Admin-Key': ADMIN_KEY },
    body: JSON.stringify({ content, message_type: "outgoing" })
  }),
  cwCreateInbox: (name) => apiFetch('/admin/chatwoot/inboxes', {
    method: 'POST',
    headers: { 'X-Admin-Key': ADMIN_KEY },
    body: JSON.stringify({ name, channel: { type: "api", webhook_url: "" } })
  }),
};
