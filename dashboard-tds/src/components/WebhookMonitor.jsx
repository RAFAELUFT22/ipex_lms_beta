import { useEffect, useMemo, useState } from 'react';
import { MessageSquare, Bot, User, Filter, ChevronRight, RefreshCw } from 'lucide-react';
import { lmsLiteApiV2 } from '../api/lms_lite_v2';
import { ModeToggle } from './shared/ModeToggle';
import { StudentBadge } from './shared/StudentBadge';

const FILTERS = ['Todos', 'Bot', 'Humano', 'Resolvidos'];

export default function WebhookMonitor() {
  const [events, setEvents] = useState([]);
  const [activeFilter, setActiveFilter] = useState('Todos');
  const [selectedPhone, setSelectedPhone] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void loadEvents();
  }, [activeFilter]);

  const filteredEvents = useMemo(() => {
    return [...events].sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0));
  }, [events]);

  async function loadEvents() {
    setLoading(true);
    try {
      const backendFilter = activeFilter === 'Todos' ? '' : activeFilter.toLowerCase();
      const data = await lmsLiteApiV2.getWebhookEvents(backendFilter);
      setEvents(Array.isArray(data) ? data : []);
    } catch (error) {
      // TODO: show toast
      console.error('Failed to load webhook events', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleMode(phone, nextMode) {
    try {
      await lmsLiteApiV2.setStudentMode(phone, nextMode);
      await loadEvents();
    } catch (error) {
      // TODO: show toast
      console.error('Failed to update mode', error);
    }
  }

  async function openConversation(phone) {
    setSelectedPhone(phone);
    try {
      const data = await lmsLiteApiV2.getStudentConversation(phone);
      setHistory(Array.isArray(data?.messages) ? data.messages : []);
    } catch (error) {
      // TODO: show toast
      console.error('Failed to fetch conversation', error);
    }
  }

  return (
    <section className="grid gap-4 lg:grid-cols-[1fr_360px]">
      <div className="space-y-4">
        <header className="flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-xl font-semibold text-white">
            <MessageSquare className="h-5 w-5 text-teal-300" />
            Webhook Monitor
          </h2>
          <button type="button" onClick={loadEvents} className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </header>

        <nav className="flex flex-wrap gap-2">
          {FILTERS.map((filter) => (
            <button
              key={filter}
              type="button"
              onClick={() => setActiveFilter(filter)}
              className={`rounded-full px-3 py-1 text-sm ${activeFilter === filter ? 'bg-teal-500/30 text-teal-100' : 'bg-white/5 text-slate-300'}`}
            >
              <Filter className="mr-1 inline h-3 w-3" />
              {filter}
            </button>
          ))}
        </nav>

        <ul className="space-y-2">
          {filteredEvents.map((event) => (
            <li key={event.id || `${event.phone}-${event.timestamp}`} className="rounded-xl border border-white/10 bg-white/5 p-3">
              <div className="flex items-start justify-between gap-3">
                <StudentBadge phone={event.phone} name={event.name || 'Aluno'} mode={event.mode || 'new'} />
                <button type="button" onClick={() => openConversation(event.phone)} className="text-slate-400 hover:text-slate-200">
                  <ChevronRight className="h-5 w-5" />
                </button>
              </div>

              <p className="mt-2 line-clamp-2 text-sm text-slate-300">{event.message_preview || event.message || 'Sem conteúdo'}</p>

              <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                <span>{event.timestamp || '---'}</span>
                <span className="inline-flex items-center gap-1">
                  {(event.mode || 'new') === 'bot' ? <Bot className="h-3 w-3" /> : <User className="h-3 w-3" />}
                  {(event.mode || 'new').toUpperCase()}
                </span>
              </div>

              <div className="mt-3">
                <ModeToggle phone={event.phone} currentMode={event.mode || 'new'} onToggle={handleToggleMode} />
              </div>
            </li>
          ))}
        </ul>
      </div>

      <aside className={`fixed right-0 top-0 h-full w-full max-w-sm border-l border-white/10 bg-slate-950 p-4 transition-transform lg:static lg:h-auto ${selectedPhone ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}`}>
        <header className="mb-3 flex items-center justify-between">
          <h3 className="text-base font-semibold text-white">Conversa</h3>
          {selectedPhone && (
            <button type="button" onClick={() => setSelectedPhone('')} className="text-xs text-slate-400">Fechar</button>
          )}
        </header>
        {/* TODO: add richer timeline UI */}
        <div className="space-y-2 text-sm text-slate-300">
          {history.length === 0 ? <p>Nenhuma mensagem carregada.</p> : history.map((item, idx) => <p key={idx}>{item.content || JSON.stringify(item)}</p>)}
        </div>
      </aside>
    </section>
  );
}
