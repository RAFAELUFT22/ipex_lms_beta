import React, { useState, useEffect, useRef } from 'react';
import { Save, Eye, EyeOff, CheckCircle, AlertCircle, RefreshCw, Upload, Link, Table } from 'lucide-react';
import { lmsLiteApi } from '../api/lms_lite';

const OPENROUTER_MODELS = [
  { value: 'openai/gpt-4o-mini', label: 'GPT-4o Mini (rápido, barato)' },
  { value: 'openai/gpt-4o', label: 'GPT-4o (alta qualidade)' },
  { value: 'anthropic/claude-3-haiku', label: 'Claude 3 Haiku (rápido)' },
  { value: 'anthropic/claude-3.5-sonnet', label: 'Claude 3.5 Sonnet (melhor)' },
  { value: 'google/gemini-flash-1.5', label: 'Gemini Flash 1.5' },
  { value: 'meta-llama/llama-3.1-8b-instruct:free', label: 'Llama 3.1 8B (gratuito)' },
];

function Field({ label, name, value, onChange, type = 'text', sensitive = false, placeholder = '' }) {
  const [show, setShow] = useState(false);
  const inputType = sensitive ? (show ? 'text' : 'password') : type;

  return (
    <div className="input-group">
      <label className="input-label">{label}</label>
      <div className="relative">
        <input
          type={inputType}
          className="w-full pr-10"
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
          placeholder={placeholder}
          autoComplete="off"
        />
        {sensitive && (
          <button
            type="button"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-main"
            onClick={() => setShow(!show)}
            tabIndex={-1}
          >
            {show ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="glass-card p-6 space-y-4">
      <h3 className="text-base font-bold text-text-main border-b border-border pb-3">{title}</h3>
      {children}
    </div>
  );
}

function GoogleSheetsSection({ settings, onChange }) {
  const fileInputRef = useRef(null);
  const [keyStatus, setKeyStatus] = useState(null); // null | { configured, project_id, client_email }
  const [keyLoading, setKeyLoading] = useState(false);
  const [keyMsg, setKeyMsg] = useState(null);

  useEffect(() => {
    lmsLiteApi.googleKeyStatus()
      .then(setKeyStatus)
      .catch(() => setKeyStatus({ configured: false }));
  }, []);

  const handleKeyUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setKeyLoading(true);
    setKeyMsg(null);
    try {
      const result = await lmsLiteApi.uploadGoogleKey(file);
      setKeyStatus({ configured: true, project_id: result.project_id, client_email: result.client_email });
      setKeyMsg({ type: 'success', text: `Chave configurada: ${result.client_email}` });
    } catch (err) {
      setKeyMsg({ type: 'error', text: err.message || 'Erro ao enviar chave' });
    } finally {
      setKeyLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="glass-card p-6 space-y-4">
      <h3 className="text-base font-bold text-text-main border-b border-border pb-3 flex items-center gap-2">
        <Table size={16} /> Google Sheets — Importação de Dados
      </h3>

      {/* Service account key upload */}
      <div className="space-y-2">
        <label className="input-label">Chave de Conta de Serviço Google (JSON)</label>
        {keyStatus?.configured ? (
          <div className="flex items-center gap-3 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-sm">
            <CheckCircle size={16} className="text-emerald-400 shrink-0" />
            <div className="min-w-0">
              <p className="text-emerald-400 font-semibold">Chave configurada</p>
              <p className="text-text-dim truncate">{keyStatus.client_email}</p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-sm text-yellow-400">
            <AlertCircle size={16} className="shrink-0" />
            Sem chave — apenas planilhas públicas (CSV) serão acessíveis.
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,application/json"
          className="hidden"
          onChange={handleKeyUpload}
        />
        <button
          type="button"
          className="btn btn-secondary flex items-center gap-2 text-sm px-4 py-2"
          disabled={keyLoading}
          onClick={() => fileInputRef.current?.click()}
        >
          {keyLoading
            ? <><RefreshCw size={14} className="animate-spin" /> Enviando...</>
            : <><Upload size={14} /> {keyStatus?.configured ? 'Substituir chave' : 'Fazer upload da chave'}</>}
        </button>
        {keyMsg && (
          <p className={`text-sm font-medium ${keyMsg.type === 'success' ? 'text-emerald-400' : 'text-red-400'}`}>
            {keyMsg.text}
          </p>
        )}
        <p className="text-xs text-text-dim">
          No Google Cloud Console: IAM → Contas de serviço → criar chave JSON. Compartilhe a planilha com o e-mail da conta de serviço.
        </p>
      </div>

      {/* Default spreadsheet */}
      <div className="input-group">
        <label className="input-label flex items-center gap-1"><Link size={12} /> URL padrão da Planilha</label>
        <input
          type="text"
          className="w-full"
          value={settings?.google_sheets_url || ''}
          onChange={(e) => onChange('google_sheets_url', e.target.value)}
          placeholder="https://docs.google.com/spreadsheets/d/..."
        />
      </div>

      <div className="input-group">
        <label className="input-label">Aba padrão (Sheet/Tab)</label>
        <input
          type="text"
          className="w-full"
          value={settings?.google_sheets_tab || 'Sheet1'}
          onChange={(e) => onChange('google_sheets_tab', e.target.value)}
          placeholder="Sheet1"
        />
      </div>
    </div>
  );
}

export default function SettingsPanel() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState(null); // { type: 'success'|'error', message: string }

  useEffect(() => {
    lmsLiteApi.getSettings()
      .then(setSettings)
      .catch((e) => setStatus({ type: 'error', message: `Erro ao carregar: ${e.message}` }))
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setStatus(null);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setStatus(null);
    try {
      await lmsLiteApi.saveSettings(settings);
      setStatus({ type: 'success', message: 'Configurações salvas com sucesso.' });
    } catch (err) {
      setStatus({ type: 'error', message: err.message || 'Erro ao salvar.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 text-text-dim">
        <RefreshCw size={20} className="animate-spin mr-3" /> Carregando configurações...
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="glass-card p-6 text-red-400">
        Não foi possível carregar as configurações. Verifique se a API está em execução.
      </div>
    );
  }

  return (
    <form onSubmit={handleSave} className="space-y-6 max-w-2xl">
      {/* AnythingLLM */}
      <Section title="AnythingLLM — RAG / Tutores IA">
        <Field label="URL" name="anythingllm_url" value={settings.anythingllm_url} onChange={handleChange} placeholder="https://llm.ipexdesenvolvimento.cloud" />
        <Field label="API Key" name="anythingllm_key" value={settings.anythingllm_key} onChange={handleChange} sensitive placeholder="sk-..." />
        <Field label="Workspace" name="anythingllm_workspace" value={settings.anythingllm_workspace} onChange={handleChange} placeholder="tds-lms-knowledge" />
      </Section>

      {/* OpenRouter */}
      <Section title="OpenRouter — Modelo de IA">
        <Field label="API Key" name="openrouter_key" value={settings.openrouter_key} onChange={handleChange} sensitive placeholder="sk-or-..." />
        <div className="input-group">
          <label className="input-label">Modelo padrão</label>
          <select
            className="w-full"
            value={settings.openrouter_model}
            onChange={(e) => handleChange('openrouter_model', e.target.value)}
          >
            {OPENROUTER_MODELS.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
        </div>
      </Section>

      {/* Evolution API */}
      <Section title="Evolution API — WhatsApp">
        <Field label="URL" name="evolution_url" value={settings.evolution_url} onChange={handleChange} placeholder="https://evolution.ipexdesenvolvimento.cloud" />
        <Field label="API Key" name="evolution_key" value={settings.evolution_key} onChange={handleChange} sensitive placeholder="sua-chave-evolution" />
        <Field label="Instância padrão" name="evolution_instance" value={settings.evolution_instance} onChange={handleChange} placeholder="tds_suporte_audiovisual" />
      </Section>

      {/* Chatwoot */}
      <Section title="Chatwoot — Inbox Humana">
        <Field label="URL" name="chatwoot_url" value={settings.chatwoot_url} onChange={handleChange} placeholder="https://chat.ipexdesenvolvimento.cloud" />
        <Field label="Token de Agente" name="chatwoot_token" value={settings.chatwoot_token} onChange={handleChange} sensitive placeholder="seu-token-chatwoot" />
        <Field label="ID do Inbox" name="chatwoot_inbox_id" value={settings.chatwoot_inbox_id} onChange={handleChange} placeholder="1" />
      </Section>

      {/* WhatsApp Cloud API */}
      <Section title="WhatsApp Cloud API — Oficial (OTP/Certs)">
        <Field label="Phone Number ID" name="wa_phone_number_id" value={settings.wa_phone_number_id || ''} onChange={handleChange} placeholder="1234567890" />
        <Field label="Business Account ID" name="wa_business_id" value={settings.wa_business_id || ''} onChange={handleChange} placeholder="1234567890" />
        <Field label="Access Token" name="wa_cloud_token" value={settings.wa_cloud_token || ''} onChange={handleChange} sensitive placeholder="EAAB..." />
      </Section>

      {/* Supabase */}
      <Section title="Supabase — Realtime & Auth">
        <Field label="URL do Projeto" name="supabase_url" value={settings.supabase_url || ''} onChange={handleChange} placeholder="https://xyzabc.supabase.co" />
        <Field label="Service Role Key" name="supabase_service_key" value={settings.supabase_service_key || ''} onChange={handleChange} sensitive placeholder="eyJhbGci..." />
        <Field label="Website Token (Chatwoot Widget)" name="chatwoot_website_token" value={settings.chatwoot_website_token || ''} onChange={handleChange} sensitive placeholder="token do widget do portal" />
      </Section>

      {/* Google Sheets */}
      <GoogleSheetsSection settings={settings} onChange={handleChange} />

      {/* Identidade Visual */}
      <Section title="Identidade Visual — Personalização (White Label)">
        <Field label="Nome da Empresa/Projeto" name="company_name" value={settings.company_name || ''} onChange={handleChange} placeholder="TDS - Territórios de Desenvolvimento Social" />
        <Field label="URL do Logotipo (PNG/SVG)" name="logo_url" value={settings.logo_url || ''} onChange={handleChange} placeholder="https://exemplo.com/logo.png" />
        
        <div className="grid grid-cols-2 gap-4">
          <div className="input-group">
            <label className="input-label">Cor Primária</label>
            <div className="flex gap-2">
              <input 
                type="color" 
                className="h-10 w-12 p-1 bg-transparent border-none" 
                value={settings.theme_primary || '#6366f1'} 
                onChange={(e) => handleChange('theme_primary', e.target.value)}
              />
              <input 
                type="text" 
                className="flex-1 font-mono text-sm" 
                value={settings.theme_primary || '#6366f1'} 
                onChange={(e) => handleChange('theme_primary', e.target.value)}
              />
            </div>
          </div>
          <div className="input-group">
            <label className="input-label">Cor Secundária</label>
            <div className="flex gap-2">
              <input 
                type="color" 
                className="h-10 w-12 p-1 bg-transparent border-none" 
                value={settings.theme_secondary || '#f43f5e'} 
                onChange={(e) => handleChange('theme_secondary', e.target.value)}
              />
              <input 
                type="text" 
                className="flex-1 font-mono text-sm" 
                value={settings.theme_secondary || '#f43f5e'} 
                onChange={(e) => handleChange('theme_secondary', e.target.value)}
              />
            </div>
          </div>
        </div>
      </Section>

      {/* Feedback + Save */}
      {status && (
        <div className={`flex items-center gap-3 p-4 rounded-xl text-sm font-semibold ${
          status.type === 'success'
            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
            : 'bg-red-500/10 text-red-400 border border-red-500/20'
        }`}>
          {status.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          {status.message}
        </div>
      )}

      <button type="submit" className="btn btn-primary px-8 py-3" disabled={saving}>
        {saving ? (
          <><RefreshCw size={16} className="inline animate-spin mr-2" />Salvando...</>
        ) : (
          <><Save size={16} className="inline mr-2" />Salvar Configurações</>
        )}
      </button>
    </form>
  );
}
