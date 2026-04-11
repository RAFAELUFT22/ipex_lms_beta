const API_BASE = import.meta.env.VITE_LMS_API_URL || 'https://api-lms.ipexdesenvolvimento.cloud';

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

  getCourses: () => apiFetch('/courses'),

  issueCert: (whatsapp, course_slug) =>
    apiFetch('/issue_cert', {
      method: 'POST',
      body: JSON.stringify({ whatsapp, course_slug }),
    }),

  validateCert: (hash) => apiFetch(`/validate_cert/${hash}`),
};
