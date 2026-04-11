import { useEffect, useMemo, useState } from 'react';
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

  // Auto-refresh every 10 seconds
  useEffect(() => {
    const id = setInterval(loadEvents, 10000);
    return () => clearInterval(id);
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
    <section className="min-h-screen bg-surface text-on-surface">
      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        {/* Main column */}
        <div className="space-y-6">
          {/* Header */}
          <header className="flex items-center justify-between">
            <div>
              <p className="text-tertiary uppercase tracking-[0.05em] text-xs font-bold mb-1">
                Monitor em Tempo Real
              </p>
              <h2 className="text-on-surface font-headline font-bold text-3xl tracking-tight">
                Monitor WhatsApp
              </h2>
            </div>

            <button
              type="button"
              onClick={loadEvents}
              className="flex items-center gap-2 bg-surface-container-high text-on-surface rounded-xl px-4 py-2 font-bold text-sm hover:bg-surface-container-highest transition-colors"
            >
              <span className={`material-symbols-outlined text-base ${loading ? 'animate-spin' : ''}`}>
                refresh
              </span>
              Atualizar
            </button>
          </header>

          {/* Filter chips */}
          <nav className="flex flex-wrap gap-2">
            {FILTERS.map((filter) => (
              <button
                key={filter}
                type="button"
                onClick={() => setActiveFilter(filter)}
                className={`rounded-full px-4 py-1 text-xs font-bold uppercase tracking-widest transition-colors ${
                  activeFilter === filter
                    ? 'bg-primary text-white'
                    : 'bg-secondary-fixed text-on-secondary-fixed hover:bg-surface-container-highest'
                }`}
              >
                <span className="material-symbols-outlined text-xs mr-1 align-middle">filter_list</span>
                {filter}
              </button>
            ))}
          </nav>

          {/* Event list */}
          <ul className="space-y-3">
            {filteredEvents.map((event) => (
              <li
                key={event.id || `${event.phone}-${event.timestamp}`}
                className="cerrado-card p-4 cursor-pointer"
                onClick={() => openConversation(event.phone)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <StudentBadge
                      phone={event.phone}
                      name={event.name || 'Aluno'}
                      mode={event.mode || 'new'}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); openConversation(event.phone); }}
                    className="text-on-surface-variant hover:text-on-surface shrink-0"
                    aria-label="Ver conversa"
                  >
                    <span className="material-symbols-outlined text-xl">chevron_right</span>
                  </button>
                </div>

                <p className="text-sm text-on-surface-variant mt-2 line-clamp-2">
                  {event.message_preview || event.message || 'Sem conteúdo'}
                </p>

                <div className="mt-3 flex items-center justify-between text-xs text-on-surface-variant">
                  <span>{event.timestamp || '---'}</span>
                  <span className="inline-flex items-center gap-1">
                    <span className="material-symbols-outlined text-sm">
                      {(event.mode || 'new') === 'bot' ? 'smart_toy' : 'person'}
                    </span>
                    {(event.mode || 'new').toUpperCase()}
                  </span>
                </div>

                <div className="mt-3" onClick={(e) => e.stopPropagation()}>
                  <ModeToggle
                    phone={event.phone}
                    currentMode={event.mode || 'new'}
                    onToggle={handleToggleMode}
                  />
                </div>
              </li>
            ))}

            {!loading && filteredEvents.length === 0 && (
              <li className="bg-surface-container-low rounded-xl p-12 text-center space-y-3">
                <span className="material-symbols-outlined text-on-surface-variant text-5xl block">forum</span>
                <p className="text-on-surface-variant text-sm font-bold">
                  Nenhum evento encontrado.
                </p>
              </li>
            )}
          </ul>
        </div>

        {/* Conversation sidebar */}
        <aside
          className={`
            bg-surface-container-low rounded-xl p-6 h-fit sticky top-6
            fixed right-0 top-0 h-full w-full max-w-sm z-40 transition-transform
            lg:static lg:h-auto lg:w-auto lg:max-w-none lg:translate-x-0 lg:z-auto
            ${selectedPhone ? 'translate-x-0' : 'translate-x-full'}
          `}
        >
          <header className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-xl">forum</span>
              <h3 className="font-bold text-on-surface text-base">Conversa</h3>
            </div>
            {selectedPhone && (
              <button
                type="button"
                onClick={() => setSelectedPhone('')}
                className="text-xs font-bold text-on-surface-variant hover:text-on-surface transition-colors"
              >
                Fechar
              </button>
            )}
          </header>

          {!selectedPhone ? (
            <div className="text-center py-8">
              <span className="material-symbols-outlined text-on-surface-variant text-4xl block mb-2">forum</span>
              <p className="text-on-surface-variant text-sm">
                Selecione um evento para ver a conversa.
              </p>
            </div>
          ) : (
            // TODO: add richer timeline UI
            <div className="space-y-3">
              {history.length === 0 ? (
                <p className="text-on-surface-variant text-sm">Nenhuma mensagem carregada.</p>
              ) : (
                history.map((item, idx) => {
                  const isBot = item.role === 'assistant' || item.sender === 'bot';
                  return (
                    <div key={idx} className={isBot ? '' : 'ml-8'}>
                      <p
                        className={`rounded-xl p-3 text-sm ${
                          isBot
                            ? 'bg-surface-container-highest text-on-surface'
                            : 'bg-primary-fixed text-on-primary-fixed'
                        }`}
                      >
                        {item.content || JSON.stringify(item)}
                      </p>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}
