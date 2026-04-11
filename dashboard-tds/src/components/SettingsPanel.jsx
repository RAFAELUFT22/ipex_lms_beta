import React, { useState, useEffect } from 'react';
import { Save, Eye, EyeOff, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
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
        <Field label="URL" name="chatwoot_url" value={settings.chatwoot_url} onChange={handleChange} placeholder="https://chatwoot.ipexdesenvolvimento.cloud" />
        <Field label="Token de Agente" name="chatwoot_token" value={settings.chatwoot_token} onChange={handleChange} sensitive placeholder="seu-token-chatwoot" />
        <Field label="ID do Inbox" name="chatwoot_inbox_id" value={settings.chatwoot_inbox_id} onChange={handleChange} placeholder="1" />
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
