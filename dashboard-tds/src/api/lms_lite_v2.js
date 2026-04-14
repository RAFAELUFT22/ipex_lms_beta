import { lmsLiteApi } from './lms_lite';

const API_BASE = import.meta.env.VITE_LMS_API_URL || 'https://api-lms.ipexdesenvolvimento.cloud';
const ADMIN_KEY = import.meta.env.VITE_ADMIN_KEY;

async function apiFetch(path, options = {}) {
  const token = sessionStorage.getItem('tds_student_token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const lmsLiteApiV2 = {
  ...lmsLiteApi,
  getCommunities: () => apiFetch('/communities', { headers: { 'X-Admin-Key': ADMIN_KEY } }),
  createCommunity: (data) =>
    apiFetch('/communities', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_KEY },
      body: JSON.stringify(data),
    }),
  broadcastToCommunity: (slug, message) =>
    apiFetch(`/communities/${slug}/broadcast`, {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_KEY },
      body: JSON.stringify({ message }),
    }),
  getWebhookEvents: (filter = '') =>
    apiFetch(`/admin/webhook/events?filter=${encodeURIComponent(filter)}`, {
      headers: { 'X-Admin-Key': ADMIN_KEY },
    }),
  setStudentMode: (phone, mode) =>
    apiFetch('/chat/set_mode', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_KEY },
      body: JSON.stringify({ phone, mode }),
    }),
  chatQuery: (phone, message, workspace) =>
    apiFetch('/chat/query', {
      method: 'POST',
      body: JSON.stringify({ phone, message, workspace }),
    }),
  getStudentConversation: (phone) =>
    apiFetch(`/admin/students/${encodeURIComponent(phone)}/conversation`, {
      headers: { 'X-Admin-Key': ADMIN_KEY },
    }),
};

export { lmsLiteApi };
